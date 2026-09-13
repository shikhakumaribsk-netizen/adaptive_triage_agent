"""
DETERMINISTIC RISK TOOL.
No LLM touches this file. Same inputs -> same outputs, always.
Produces: point score, [min,max] uncertainty band, fired-rule trace, routing tier.
"""
from typing import Dict, List, Any, Tuple
from agent.state import PatientState, SLOTS, UNKNOWN

RULE_VERSION = "TRIAGE-RULES-v2.0.1"

# ── Predefined routing outcomes (FIXED SET — spec requirement) ──────────
ROUTING_OUTCOMES = [
    {"tier": 0, "code": "SELF_CARE",  "label": "Self-care / Telehealth",
     "range": (0, 12),  "color": "#16a34a", "target": "Advice only, no ED visit needed"},
    {"tier": 1, "code": "STANDARD",   "label": "Standard OPD",
     "range": (12, 28), "color": "#22c55e", "target": "Seen within 2–4 hours"},
    {"tier": 2, "code": "URGENT",     "label": "Urgent Care",
     "range": (28, 45), "color": "#eab308", "target": "Seen within 60 minutes"},
    {"tier": 3, "code": "EMERGENCY",  "label": "Emergency Department",
     "range": (45, 62), "color": "#f97316", "target": "Seen within 15 minutes"},
    {"tier": 4, "code": "CRITICAL",   "label": "Immediate Emergency Bay",
     "range": (62, 80), "color": "#ef4444", "target": "Seen immediately"},
    {"tier": 5, "code": "RESUS",      "label": "Resuscitation Room (Code Red)",
     "range": (80, 101), "color": "#a855f7", "target": "Resuscitation team now"},
]


def tier_for(score: float) -> Dict:
    for o in ROUTING_OUTCOMES:
        lo, hi = o["range"]
        if lo <= score < hi:
            return o
    return ROUTING_OUTCOMES[-1]


# ── Rule definitions ────────────────────────────────────────────────────
# Each rule: (id, [required_slots], scoring_fn, max_possible_points, citation)
def _r(state: PatientState, k):
    return state.get(k)


RULES: List[Dict] = [

    # ===== AIRWAY / BREATHING =====
    dict(id="R-SPO2", slots=["spo2"], max_pts=25, cite="NEWS2 §SpO2",
         fn=lambda s: 25 if _r(s,"spo2") < 90 else 12 if _r(s,"spo2") < 94 else 4 if _r(s,"spo2") < 96 else 0),

    dict(id="R-RR", slots=["resp_rate"], max_pts=18, cite="NEWS2 §Respiratory Rate",
         fn=lambda s: 18 if (_r(s,"resp_rate") >= 25 or _r(s,"resp_rate") <= 8)
                      else 8 if (_r(s,"resp_rate") >= 21 or _r(s,"resp_rate") <= 11) else 0),

    dict(id="R-SPEECH", slots=["full_sentences"], max_pts=18, cite="Resp. distress bedside marker",
         fn=lambda s: 18 if _r(s,"full_sentences") is False else 0),

    dict(id="R-DYSPNEA", slots=["dyspnea"], max_pts=20, cite="ABCDE §Breathing",
         fn=lambda s: 20 if _r(s,"dyspnea") else 0),

    # ===== CIRCULATION =====
    dict(id="R-SBP", slots=["systolic_bp"], max_pts=25, cite="NEWS2 §Systolic BP",
         fn=lambda s: 25 if _r(s,"systolic_bp") < 90 else 15 if _r(s,"systolic_bp") < 100
                      else 12 if _r(s,"systolic_bp") > 180 else 0),

    dict(id="R-HR", slots=["heart_rate"], max_pts=20, cite="NEWS2 §Pulse",
         fn=lambda s: 20 if (_r(s,"heart_rate") > 130 or _r(s,"heart_rate") < 40)
                      else 10 if (_r(s,"heart_rate") > 110 or _r(s,"heart_rate") < 51) else 0),

    dict(id="R-BLEED", slots=["severe_bleeding"], max_pts=25, cite="Catastrophic haemorrhage",
         fn=lambda s: 25 if _r(s,"severe_bleeding") else 0),

    # ===== DISABILITY =====
    dict(id="R-AVPU", slots=["consciousness"], max_pts=30, cite="AVPU / GCS proxy",
         fn=lambda s: {"alert":0, "voice":15, "pain":25, "unresponsive":30}.get(_r(s,"consciousness"), 0)),

    dict(id="R-STROKE", slots=["focal_weakness"], max_pts=28, cite="FAST stroke pathway",
         fn=lambda s: 28 if _r(s,"focal_weakness") else 0),

    dict(id="R-SPEECHDIFF", slots=["speech_difficulty"], max_pts=12, cite="FAST stroke pathway",
         fn=lambda s: 12 if _r(s,"speech_difficulty") else 0),

    dict(id="R-SAH", slots=["worst_headache"], max_pts=22, cite="Ottawa SAH Rule",
         fn=lambda s: 22 if _r(s,"worst_headache") else 0),

    # ===== CARDIAC =====
    dict(id="R-CP", slots=["chest_pain"], max_pts=25, cite="ACS screen",
         fn=lambda s: 25 if _r(s,"chest_pain") else 0),

    dict(id="R-CP-RAD", slots=["pain_radiation"], max_pts=12, cite="ACS likelihood ratio",
         fn=lambda s: 12 if _r(s,"pain_radiation") else 0),

    dict(id="R-CP-EXERT", slots=["pain_exertional"], max_pts=8, cite="Ischaemic pattern",
         fn=lambda s: 8 if _r(s,"pain_exertional") else 0),

    dict(id="R-DIAPH", slots=["diaphoresis"], max_pts=10, cite="Autonomic distress sign",
         fn=lambda s: 10 if _r(s,"diaphoresis") else 0),

    # ===== INFECTION =====
    dict(id="R-TEMP", slots=["temperature"], max_pts=18, cite="NEWS2 §Temperature",
         fn=lambda s: 18 if (_r(s,"temperature") >= 39.5 or _r(s,"temperature") <= 35.0)
                      else 8 if _r(s,"temperature") >= 38.3 else 0),

    dict(id="R-MENINGISM", slots=["neck_stiffness","temperature"], max_pts=14, cite="Meningitis screen",
         fn=lambda s: 14 if (_r(s,"neck_stiffness") and _r(s,"temperature") >= 38.0) else 0),

    # ===== VTE =====
    dict(id="R-DVT", slots=["calf_swelling"], max_pts=14, cite="Wells criteria element",
         fn=lambda s: 14 if _r(s,"calf_swelling") else 0),
    dict(id="R-IMMOB", slots=["recent_immobility"], max_pts=10, cite="Wells criteria element",
         fn=lambda s: 10 if _r(s,"recent_immobility") else 0),

    # ===== MODIFIERS =====
    dict(id="R-AGE", slots=["age"], max_pts=15, cite="Age-based acuity modifier",
         fn=lambda s: 15 if _r(s,"age") >= 75 else 10 if _r(s,"age") >= 65
                      else 12 if _r(s,"age") < 2 else 8 if _r(s,"age") < 6 else 0),

    dict(id="R-CARDHX", slots=["cardiac_history"], max_pts=10, cite="Pre-test probability",
         fn=lambda s: 10 if _r(s,"cardiac_history") else 0),
    dict(id="R-IMMUNO", slots=["immunocompromised"], max_pts=8, cite="Masked sepsis risk",
         fn=lambda s: 8 if _r(s,"immunocompromised") else 0),
    dict(id="R-PREG", slots=["pregnancy"], max_pts=10, cite="Obstetric pathway trigger",
         fn=lambda s: 10 if _r(s,"pregnancy") else 0),
    dict(id="R-ABDO", slots=["abdominal_pain"], max_pts=12, cite="Abdominal differential",
         fn=lambda s: 12 if _r(s,"abdominal_pain") else 0),
    dict(id="R-VOMIT", slots=["vomiting"], max_pts=8, cite="Dehydration risk",
         fn=lambda s: 8 if _r(s,"vomiting") else 0),
]


# ── HARD OVERRIDE RULES (bypass scoring entirely — never negotiable) ────
HARD_OVERRIDES = [
    dict(id="HO-UNRESP", code="RESUS",
         test=lambda s: s.get("consciousness") == "unresponsive",
         why="Unresponsive patient → immediate resuscitation."),
    dict(id="HO-SPO2", code="RESUS",
         test=lambda s: (s.get("spo2") is not None and s.get("spo2") < 85),
         why="SpO2 < 85% → immediate resuscitation."),
    dict(id="HO-SHOCK", code="RESUS",
         test=lambda s: (s.get("systolic_bp") is not None and s.get("systolic_bp") < 80),
         why="Systolic BP < 80 mmHg → shock, resuscitation."),
    dict(id="HO-STROKE", code="CRITICAL",
         test=lambda s: bool(s.get("focal_weakness")) and bool(s.get("speech_difficulty")),
         why="FAST-positive → time-critical stroke pathway."),
    dict(id="HO-ACS", code="CRITICAL",
         test=lambda s: bool(s.get("chest_pain")) and bool(s.get("pain_radiation"))
                        and bool(s.get("diaphoresis")),
         why="Classic ACS triad → immediate ECG/cardiac pathway."),
]


class RiskTool:
    """Pure deterministic risk engine."""

    version = RULE_VERSION

    def score(self, state: PatientState) -> Dict[str, Any]:
        fired, known_pts = [], 0
        unknown_max = 0
        pending_rules = []

        for rule in RULES:
            if all(state.is_known(k) for k in rule["slots"]):
                try:
                    pts = rule["fn"](state)
                except Exception:
                    pts = 0
                if pts:
                    known_pts += pts
                    fired.append({"rule": rule["id"], "points": pts, "citation": rule["cite"]})
            else:
                # unresolved rule -> contributes [0, max_pts] to the band
                missing = [k for k in rule["slots"] if not state.is_known(k)]
                # if patient declared unknown on a red-flag slot, assume worst case (safety)
                if any(k in state.unknown_declared and SLOTS[k].red_flag for k in missing):
                    known_pts += rule["max_pts"]
                    fired.append({"rule": rule["id"], "points": rule["max_pts"],
                                  "citation": rule["cite"] + " [WORST-CASE: unknown red flag]"})
                else:
                    unknown_max += rule["max_pts"]
                    pending_rules.append({"rule": rule["id"], "missing": missing,
                                          "max_points": rule["max_pts"]})

        score_min = min(known_pts, 100)
        score_max = min(known_pts + unknown_max, 100)
        point = score_min  # conservative point estimate = what we can prove

        tier_min, tier_max = tier_for(score_min), tier_for(score_max)

        # hard overrides
        override = None
        for ho in HARD_OVERRIDES:
            if ho["test"](state.facts):
                override = ho
                break

        band_width = tier_max["tier"] - tier_min["tier"]
        confidence = round(max(0.0, 1 - (band_width / 5)) * 100, 1)

        return {
            "rule_version": RULE_VERSION,
            "score": point,
            "score_min": score_min,
            "score_max": score_max,
            "band_width_points": score_max - score_min,
            "tier_min": tier_min,
            "tier_max": tier_max,
            "band_spans_boundary": tier_min["code"] != tier_max["code"],
            "confidence_pct": confidence,
            "fired_rules": fired,
            "pending_rules": pending_rules,
            "hard_override": override and {"id": override["id"], "code": override["code"],
                                           "why": override["why"]},
        }

    def score_hypothetical(self, state: PatientState, key: str, value: Any) -> Dict:
        """Score a 'what-if' without mutating real state (used by EVOI)."""
        import copy
        ghost = copy.deepcopy(state)
        ghost.facts[key] = value
        return self.score(ghost)