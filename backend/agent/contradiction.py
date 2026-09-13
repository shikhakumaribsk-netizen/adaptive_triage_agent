from datetime import datetime
from typing import Dict, List, Any
from agent.state import PatientState, SLOTS

# vitals that shouldn't swing wildly within one triage encounter
PLAUSIBLE_DELTA = {"heart_rate": 35, "systolic_bp": 40, "spo2": 8, "temperature": 1.5}

MUTUALLY_ODD = [
    ("full_sentences", True, "dyspnea", True,
     "Reports severe breathlessness yet speaks in full sentences"),
    ("consciousness", "unresponsive", "chest_pain", True,
     "Reported as unresponsive but also self-reporting chest pain"),
]


class ContradictionDetector:
    def check(self, state: PatientState, key: str, new_value: Any) -> List[Dict]:
        found = []
        old = state.facts.get(key, None)

        # 1) direct flip
        if old is not None and isinstance(old, bool) and isinstance(new_value, bool) and old != new_value:
            found.append(self._mk("DIRECT_FLIP", key,
                f"Previously answered '{old}' for '{SLOTS[key].question}', now '{new_value}'",
                "HIGH" if SLOTS[key].red_flag else "MEDIUM"))

        # 2) implausible vital jump
        if key in PLAUSIBLE_DELTA and isinstance(old, (int, float)) and isinstance(new_value, (int, float)):
            if abs(old - new_value) > PLAUSIBLE_DELTA[key]:
                found.append(self._mk("VITAL_JUMP", key,
                    f"{key} changed {old} → {new_value} (exceeds plausible delta "
                    f"{PLAUSIBLE_DELTA[key]}). Possible measurement error or true deterioration.",
                    "HIGH"))

        # 3) semantic inconsistency
        probe = dict(state.facts); probe[key] = new_value
        for a, av, b, bv, msg in MUTUALLY_ODD:
            if probe.get(a) == av and probe.get(b) == bv:
                found.append(self._mk("SEMANTIC", f"{a}|{b}", msg, "MEDIUM"))

        # 4) previously denied, now reported
        if key in state.denied and new_value is True:
            found.append(self._mk("DENIED_THEN_REPORTED", key,
                f"Patient earlier denied '{key}' but now reports it.",
                "HIGH" if SLOTS[key].red_flag else "MEDIUM"))

        return found

    def _mk(self, ctype, slot, msg, severity):
        return {"id": f"C{datetime.now().strftime('%H%M%S%f')[:-3]}",
                "type": ctype, "slot": slot, "message": msg,
                "severity": severity, "status": "OPEN",
                "ts": datetime.now().strftime("%H:%M:%S")}

    def resolution_question(self, c: Dict) -> Dict:
        slot = c["slot"].split("|")[0]
        base = SLOTS.get(slot)
        return {
            "slot": slot,
            "question": (f"I want to make sure I have this right — {base.question}"
                         if base else "Could you please confirm your last answer?"),
            "dtype": base.dtype if base else "bool",
            "choices": base.choices if base else None,
            "is_resolution": True,
            "contradiction_id": c["id"],
            "why_this_question": "Resolving a contradiction before any routing decision is made.",
        }