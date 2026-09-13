import os, uuid
from typing import Optional, Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.state import PatientState, SLOTS
from agent.orchestrator import TriageOrchestrator
from agent.guardrails import DISCLAIMER
from tools.case_bank import CaseBank
from tools.risk_tool import ROUTING_OUTCOMES, RiskTool
from tools.patient_db import PatientDataTool

load_dotenv()

app = FastAPI(title="Adaptive Emergency Triage Agent", version="2.0.0",
              description="Simulated triage decision support — NOT a diagnostic device.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"], allow_credentials=True)

AGENT = TriageOrchestrator(os.getenv("GEMINI_API_KEY", ""))
CASES = CaseBank()
RISK = RiskTool()
PDB = PatientDataTool()

SESSIONS: Dict[str, PatientState] = {}
QUEUE: List[Dict] = []


# ── models ────────────────────────────────────────────────────
class StartReq(BaseModel):
    patient_name: str = "Anonymous"
    case_id: Optional[str] = None

class ReplyReq(BaseModel):
    session_id: str
    text: str
    answered_slot: Optional[str] = None

class VitalsReq(BaseModel):
    session_id: str
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    resp_rate: Optional[float] = None
    temperature: Optional[float] = None

class WhatIfReq(BaseModel):
    session_id: str
    slot: str
    value: Any

class OverrideReq(BaseModel):
    session_id: str
    new_routing_code: str
    clinician_id: str
    reason: str


def _sess(sid) -> PatientState:
    if sid not in SESSIONS:
        raise HTTPException(404, "Session not found")
    return SESSIONS[sid]


def _sync_queue(st: PatientState, payload: Dict):
    r = payload.get("routing")
    if not r: return
    entry = {"session_id": st.session_id, "patient_name": st.patient_name,
             "code": r["code"], "label": r["label"], "tier": r["tier"],
             "color": r["color"], "target": r["target"],
             "score_min": payload["risk"]["score_min"],
             "score_max": payload["risk"]["score_max"],
             "confidence": payload["risk"]["confidence_pct"],
             "human_review": r["human_review_required"],
             "top_consideration": payload["belief"]["top"]["label"],
             "questions_asked": payload.get("questions_asked", 0),
             "created_at": st.created_at}
    for i, q in enumerate(QUEUE):
        if q["session_id"] == st.session_id:
            QUEUE[i] = entry; return
    QUEUE.append(entry)


# ── endpoints ─────────────────────────────────────────────────
@app.get("/")
def root():
    return {"service": "Adaptive Emergency Triage Agent", "version": "2.0.0",
            "rule_version": RISK.version, "disclaimer": DISCLAIMER,
            "routing_outcomes": [o["code"] for o in ROUTING_OUTCOMES]}


@app.post("/api/session/start")
def start(req: StartReq):
    sid = str(uuid.uuid4())
    st = PatientState(session_id=sid, patient_name=req.patient_name)
    SESSIONS[sid] = st

    opening = None
    if req.case_id:
        c = CASES.get(req.case_id)
        if c:
            st.patient_name = c["name"]
            st.facts["_case_id"] = c["id"] if False else None  # keep facts clean
            st.facts.pop("_case_id", None)
            opening = c["opening"]

    st.log_tool("session.start", req.patient_name, f"state initialised, 0/{len(SLOTS)} slots known")
    result = AGENT.step(st, utterance=opening) if opening else AGENT.step(st)
    return {"session_id": sid, "case_opening": opening, **result}


@app.post("/api/session/reply")
def reply(req: ReplyReq):
    st = _sess(req.session_id)
    out = AGENT.step(st, utterance=req.text, answered_slot=req.answered_slot)
    if out.get("phase") == "DECIDED":
        _sync_queue(st, out)
    return out


@app.post("/api/session/vitals")
def vitals(req: VitalsReq):
    """New vitals arriving mid-interview must trigger a full reassessment (Step 6)."""
    st = _sess(req.session_id)
    parts = []
    for k in ("heart_rate", "systolic_bp", "spo2", "resp_rate", "temperature"):
        v = getattr(req, k)
        if v is not None:
            parts.append(f"{k} {v}")
    if not parts:
        raise HTTPException(400, "No vitals supplied")
    st.log_tool("vitals_monitor.ingest", ", ".join(parts), "triggering reassessment")
    out = AGENT.step(st, utterance=", ".join(parts))
    out["reassessment_triggered_by"] = "NEW_VITALS"
    if out.get("phase") == "DECIDED":
        _sync_queue(st, out)
    return out


@app.post("/api/session/whatif")
def whatif(req: WhatIfReq):
    """Counterfactual explainability — does not mutate real state."""
    st = _sess(req.session_id)
    before = RISK.score(st)
    after = RISK.score_hypothetical(st, req.slot, req.value)
    changed = [r for r in after["fired_rules"] if r not in before["fired_rules"]]
    return {"slot": req.slot, "value": req.value,
            "before": {"band": [before["score_min"], before["score_max"]],
                       "tier": before["tier_max"]["code"]},
            "after": {"band": [after["score_min"], after["score_max"]],
                      "tier": after["tier_max"]["code"]},
            "routing_changed": before["tier_max"]["code"] != after["tier_max"]["code"],
            "newly_fired_rules": changed, "disclaimer": DISCLAIMER}


@app.get("/api/session/{sid}")
def get_session(sid: str):
    st = _sess(sid)
    return {"session_id": sid, "patient_name": st.patient_name, "facts": st.facts,
            "denied": st.denied, "unknown_declared": st.unknown_declared,
            "asked": st.asked, "transcript": st.transcript,
            "contradictions": st.contradictions, "risk_history": st.risk_history,
            "tool_trace": st.tool_trace, "completeness": st.completeness(),
            "audit_hash": st.audit_hash(), "status": st.status,
            "disclaimer": DISCLAIMER}


@app.get("/api/queue")
def queue():
    return {"queue": sorted(QUEUE, key=lambda q: (-q["tier"], q["created_at"])),
            "total": len(QUEUE),
            "needs_human_review": sum(1 for q in QUEUE if q["human_review"])}


@app.post("/api/session/override")
def override(req: OverrideReq):
    st = _sess(req.session_id)
    st.log_tool("clinician.override", f"{req.clinician_id} → {req.new_routing_code}", req.reason)
    for q in QUEUE:
        if q["session_id"] == req.session_id:
            outcome = next(o for o in ROUTING_OUTCOMES if o["code"] == req.new_routing_code)
            q.update({"code": outcome["code"], "label": outcome["label"],
                      "tier": outcome["tier"], "color": outcome["color"],
                      "overridden_by": req.clinician_id})
    return {"ok": True, "message": "Clinician override recorded and queue re-sorted."}


@app.get("/api/cases")
def cases():
    return {"cases": CASES.list()}


@app.post("/api/cases/{case_id}/autoplay")
def autoplay(case_id: str, max_turns: int = 12):
    """Run the full agent loop against a synthetic case — the demo button."""
    c = CASES.get(case_id)
    if not c:
        raise HTTPException(404, "Case not found")

    sid = str(uuid.uuid4())
    st = PatientState(session_id=sid, patient_name=c["name"])
    SESSIONS[sid] = st

    frames = []
    out = AGENT.step(st, utterance=c["opening"])
    frames.append({"turn": 0, "patient": c["opening"], "result": out})

    turn = 1
    while out.get("phase") in ("INTERVIEWING", "RE_ASSESSING") and turn <= max_turns:
        q = out["next_question"]
        ans = CASES.answer_for(c, q["slot"], turn)
        out = AGENT.step(st, utterance=ans, answered_slot=q["slot"])
        frames.append({"turn": turn, "agent_question": q["question"],
                       "why": q.get("why_this_question"), "patient": ans, "result": out})
        turn += 1

    if out.get("phase") == "DECIDED":
        _sync_queue(st, out)

    predicted = out.get("routing", {}).get("code")
    return {"session_id": sid, "case": c["label"],
            "ground_truth": c["ground_truth"], "predicted": predicted,
            "match": predicted == c["ground_truth"],
            "questions_asked": len(st.asked), "frames": frames, "final": out}


@app.get("/api/meta/slots")
def slots():
    return {"slots": [{"key": s.key, "question": s.question, "dtype": s.dtype,
                       "red_flag": s.red_flag, "ask_cost_s": s.ask_cost,
                       "max_points": s.max_points, "rationale": s.rationale}
                      for s in SLOTS.values()],
            "routing_outcomes": ROUTING_OUTCOMES,
            "normal_ranges": PDB.all_normals()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)