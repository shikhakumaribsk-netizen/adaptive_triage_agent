"""
THE AGENT LOOP — implements all 7 required workflow steps in order.
"""
import time
from typing import Dict, Any
from agent.state import PatientState, SLOTS
from agent.question_selector import QuestionSelector
from agent.belief import BeliefEngine
from agent.contradiction import ContradictionDetector
from agent.escalation import EscalationPolicy, MAX_QUESTIONS
from agent.guardrails import Guardrails
from agent.nlu import NLU
from tools.risk_tool import RiskTool
from tools.patient_db import PatientDataTool
from tools.rag_tool import ClinicalRAG


class TriageOrchestrator:
    def __init__(self, gemini_key: str = ""):
        self.risk = RiskTool()
        self.belief = BeliefEngine()
        self.selector = QuestionSelector()
        self.contra = ContradictionDetector()
        self.escalate = EscalationPolicy()
        self.guard = Guardrails()
        self.nlu = NLU(gemini_key)
        self.pdb = PatientDataTool()
        self.rag = ClinicalRAG()

    # ───────────────────────────────────────────────────────────
    def step(self, state: PatientState, utterance: str = None,
             answered_slot: str = None) -> Dict[str, Any]:

        t0 = time.time()

        # ── GUARDRAIL PRE-CHECK ────────────────────────────────
        if utterance:
            g = self.guard.inspect(utterance)
            if g["blocked"]:
                state.log_tool("guardrails.inspect", utterance[:40],
                               f"BLOCKED intent={g['intent']}")
                state.transcript.append({"role": "agent", "text": g["response"],
                                         "kind": "refusal"})
                return self.guard.wrap({
                    "refusal": True, "intent": g["intent"], "message": g["response"],
                    "repeat_question": True, "tool_trace": state.tool_trace[-6:],
                })

        # ── STEP 3+4: INGEST + UPDATE STATE ────────────────────
        new_contradictions = []
        if utterance:
            state.transcript.append({"role": "patient", "text": utterance})

            tA = time.time()
            parsed = self.nlu.extract(utterance, question=answered_slot or "",
                                      expected_slot=answered_slot)
            state.log_tool("nlu.extract", utterance[:40],
                           f"{list(parsed['facts'].keys())} src={parsed.get('source')}",
                           int((time.time()-tA)*1000))

            for slot, value in parsed["facts"].items():
                if slot not in SLOTS:
                    continue
                # STEP 6: contradiction check BEFORE overwrite
                found = self.contra.check(state, slot, value)
                if found:
                    new_contradictions.extend(found)
                    state.contradictions.extend(found)
                    state.log_tool("contradiction.check", slot,
                                   f"{len(found)} contradiction(s) found")

                state.facts[slot] = value
                if value is False and slot not in state.denied:
                    state.denied.append(slot)

                # reference-range enrichment
                ref = self.pdb.reference(slot, value)
                if ref:
                    state.log_tool("patient_db.reference", f"{slot}={value}", ref["summary"])

            for slot in parsed.get("unknown", []):
                if slot in SLOTS and slot not in state.unknown_declared:
                    state.unknown_declared.append(slot)
                    state.log_tool("state.mark_unknown", slot,
                                   "worst-case assumed (safety)")

        # ── STEP 3: RISK + BELIEF TOOLS ────────────────────────
        tR = time.time()
        risk = self.risk.score(state)
        state.log_tool("risk_engine.score", f"{len(state.facts)} facts",
                       f"band=[{risk['score_min']},{risk['score_max']}] "
                       f"{risk['tier_min']['code']}→{risk['tier_max']['code']}",
                       int((time.time()-tR)*1000))

        belief = self.belief.compute(state)
        state.log_tool("belief_engine.compute", f"{len(belief['evidence_used'])} findings",
                       f"top={belief['top']['key']} p={belief['top']['p']} "
                       f"H={belief['entropy_bits']}b")

        prev = state.risk_history[-1] if state.risk_history else None
        state.risk_history.append({
            "n": len(state.risk_history),
            "score_min": risk["score_min"], "score_max": risk["score_max"],
            "confidence": risk["confidence_pct"],
            "entropy": belief["entropy_bits"],
        })

        delta = None
        if prev:
            delta = {"band_narrowed_by": (prev["score_max"] - prev["score_min"])
                                          - (risk["score_max"] - risk["score_min"]),
                     "confidence_change": round(risk["confidence_pct"] - prev["confidence"], 1)}

        # ── STEP 6: contradiction takes priority over normal flow ──
        open_high = [c for c in state.contradictions
                     if c["status"] == "OPEN" and c["severity"] == "HIGH"]
        if new_contradictions and open_high and len(state.asked) < MAX_QUESTIONS + 2:
            q = self.contra.resolution_question(open_high[0])
            state.asked.append(q["slot"])
            state.transcript.append({"role": "agent", "text": q["question"],
                                     "kind": "resolution"})
            return self.guard.wrap({
                "phase": "RE_ASSESSING",
                "contradiction_alert": new_contradictions,
                "next_question": q,
                "risk": risk, "belief": belief, "delta": delta,
                "completeness": state.completeness(),
                "tool_trace": state.tool_trace[-8:],
                "latency_ms": int((time.time()-t0)*1000),
            })

        # ── STEP 7: ESCALATION EVALUATION ──────────────────────
        esc = self.escalate.evaluate(state, risk, belief, len(state.asked))

        # ── STEP 2: STOPPING RULE + NEXT QUESTION SELECTION ────
        must_stop = (risk["hard_override"] is not None
                     or not risk["band_spans_boundary"]
                     or len(state.asked) >= MAX_QUESTIONS
                     or len(state.unknown_slots()) == 0)

        if not must_stop:
            nq, ranked = self.selector.next_question(state)
            if nq:
                state.asked.append(nq["slot"])
                state.transcript.append({"role": "agent", "text": nq["question"],
                                         "kind": "question"})
                return self.guard.wrap({
                    "phase": "INTERVIEWING",
                    "next_question": nq,
                    "question_candidates": ranked,
                    "risk": risk, "belief": belief, "delta": delta,
                    "escalation_watch": esc,
                    "completeness": state.completeness(),
                    "questions_asked": len(state.asked),
                    "question_budget": MAX_QUESTIONS,
                    "tool_trace": state.tool_trace[-8:],
                    "latency_ms": int((time.time()-t0)*1000),
                })

        # ── STEP 5: FINAL ROUTING DECISION ─────────────────────
        routing = self.escalate.decide_routing(risk, esc)

        tG = time.time()
        citations = self.rag.retrieve(state, risk, top_k=3)
        state.log_tool("clinical_rag.retrieve", routing["code"],
                       f"{len(citations)} protocol chunk(s)", int((time.time()-tG)*1000))

        state.status = "ESCALATED" if routing["human_review_required"] else "DECIDED"

        return self.guard.wrap({
            "phase": "DECIDED",
            "routing": routing,
            "risk": risk, "belief": belief, "delta": delta,
            "escalation": esc,
            "citations": citations,
            "handoff_sbar": self.build_sbar(state, risk, belief, routing),
            "completeness": state.completeness(),
            "questions_asked": len(state.asked),
            "audit_hash": state.audit_hash(),
            "rule_version": self.risk.version,
            "tool_trace": state.tool_trace,
            "latency_ms": int((time.time()-t0)*1000),
        })

    # ───────────────────────────────────────────────────────────
    def build_sbar(self, state, risk, belief, routing) -> Dict[str, str]:
        pos = [k for k, v in state.facts.items() if v is True]
        vitals = {k: v for k, v in state.facts.items()
                  if k in ("heart_rate", "systolic_bp", "spo2", "resp_rate", "temperature")}
        return {
            "S": f"{state.patient_name}, age {state.facts.get('age','unknown')}. "
                 f"Presenting concern: {state.facts.get('chief_complaint','not stated')}.",
            "B": f"Relevant positives: {', '.join(pos) or 'none recorded'}. "
                 f"Explicitly denied: {', '.join(state.denied) or 'none'}.",
            "A": f"Risk band {risk['score_min']}–{risk['score_max']}/100 "
                 f"(confidence {risk['confidence_pct']}%). "
                 f"Leading consideration for review: {belief['top']['label']} "
                 f"(p={belief['top']['p']}). Vitals: {vitals or 'not obtained'}.",
            "R": f"Route to {routing['label']} — {routing['target']}. "
                 f"{'HUMAN CLINICIAN REVIEW REQUIRED.' if routing['human_review_required'] else ''}",
        }