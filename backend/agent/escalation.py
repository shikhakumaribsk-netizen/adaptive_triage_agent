"""
Escalation ladder. Encodes the rule:
'Escalate unresolved high-risk cases rather than inventing certainty.'
"""
from typing import Dict, List
from agent.state import PatientState, SLOTS
from tools.risk_tool import ROUTING_OUTCOMES, tier_for

MAX_QUESTIONS = 9
ENTROPY_ESCALATE = 1.45          # bits
CONFIDENCE_FLOOR = 55.0          # %


class EscalationPolicy:

    def evaluate(self, state: PatientState, risk: Dict, belief: Dict,
                 questions_asked: int) -> Dict:
        reasons: List[str] = []
        escalate = False

        open_contra = [c for c in state.contradictions if c["status"] == "OPEN"]
        red_flag_unknowns = [k for k in state.unknown_declared if SLOTS.get(k) and SLOTS[k].red_flag]

        # 1) budget exhausted but band still ambiguous & dangerous
        if (questions_asked >= MAX_QUESTIONS and risk["band_spans_boundary"]
                and risk["tier_max"]["tier"] >= 3):
            escalate = True
            reasons.append(
                f"Question budget exhausted ({questions_asked}/{MAX_QUESTIONS}) but risk band "
                f"still spans {risk['tier_min']['code']}→{risk['tier_max']['code']}.")

        # 2) unresolved contradiction on a red-flag item
        if any(c["severity"] == "HIGH" for c in open_contra):
            escalate = True
            reasons.append("Unresolved HIGH-severity contradiction in patient history.")

        # 3) patient cannot answer a red-flag question
        if red_flag_unknowns:
            escalate = True
            reasons.append(
                f"Patient unable to answer red-flag item(s): {', '.join(red_flag_unknowns)}. "
                "Worst case assumed; human assessment required.")

        # 4) high differential uncertainty with meaningful downside
        if belief["entropy_bits"] > ENTROPY_ESCALATE and risk["tier_max"]["tier"] >= 3:
            escalate = True
            reasons.append(
                f"Differential entropy {belief['entropy_bits']} bits exceeds threshold "
                f"{ENTROPY_ESCALATE} with a plausible high-acuity outcome.")

        # 5) low confidence
        if risk["confidence_pct"] < CONFIDENCE_FLOOR and risk["tier_max"]["tier"] >= 3:
            escalate = True
            reasons.append(f"Decision confidence {risk['confidence_pct']}% below floor "
                           f"{CONFIDENCE_FLOOR}%.")

        return {
            "escalate": escalate,
            "reasons": reasons,
            "open_contradictions": open_contra,
            "red_flag_unknowns": red_flag_unknowns,
        }

    def decide_routing(self, risk: Dict, esc: Dict) -> Dict:
        """SAFETY RULE: when uncertain, always take the HIGHER tier."""
        if risk["hard_override"]:
            out = next(o for o in ROUTING_OUTCOMES if o["code"] == risk["hard_override"]["code"])
            return {**out,
                    "decision_basis": "HARD_OVERRIDE",
                    "explanation": risk["hard_override"]["why"],
                    "human_review_required": True}

        chosen = risk["tier_max"] if (esc["escalate"] or risk["band_spans_boundary"]) \
                 else risk["tier_min"]

        basis = ("ESCALATED_UNCERTAIN" if esc["escalate"]
                 else "SAFETY_UPPER_BOUND" if risk["band_spans_boundary"]
                 else "CONFIDENT_BAND")

        explanation = {
            "ESCALATED_UNCERTAIN": ("Residual uncertainty could not be safely resolved by "
                                    "questioning. Routed to the higher-acuity option and flagged "
                                    "for human clinician review."),
            "SAFETY_UPPER_BOUND": ("Risk band still spans a boundary; the safer (higher) tier "
                                   "was selected."),
            "CONFIDENT_BAND": ("Best-case and worst-case risk both fall inside a single tier, "
                               "so no further questions were needed."),
        }[basis]

        return {**chosen,
                "decision_basis": basis,
                "explanation": explanation,
                "human_review_required": esc["escalate"]}