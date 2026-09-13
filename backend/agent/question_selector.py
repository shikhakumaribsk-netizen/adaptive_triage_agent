"""
Selects the next question by Expected Value of Information.
This module IS the 'select next question based on uncertainty/risk' requirement.
"""
import copy, math
from typing import Dict, List
from agent.state import PatientState, SLOTS
from tools.risk_tool import RiskTool, tier_for
from agent.belief import BeliefEngine

W_BAND     = 1.0    # weight: risk-band narrowing
W_ENTROPY  = 18.0   # weight: differential disambiguation
W_REDFLAG  = 12.0   # weight: life-threat rule-out bonus
W_TIERFLIP = 20.0   # weight: answer could change the routing decision


class QuestionSelector:
    def __init__(self):
        self.risk = RiskTool()
        self.belief = BeliefEngine()

    # ── candidate answer space for EVOI simulation ──────────────
    def _answer_space(self, key: str):
        s = SLOTS[key]
        if s.dtype == "bool":
            return [(True, s.prior_true), (False, 1 - s.prior_true)]
        if s.dtype == "choice":
            n = len(s.choices)
            return [(c, 1 / n) for c in s.choices]
        if s.dtype == "number":
            probes = {
                "age":         [(30, .55), (70, .3), (3, .15)],
                "spo2":        [(98, .6), (92, .25), (86, .15)],
                "heart_rate":  [(78, .55), (115, .3), (140, .15)],
                "systolic_bp": [(125, .6), (95, .25), (78, .15)],
                "resp_rate":   [(16, .55), (23, .3), (30, .15)],
                "temperature": [(36.8, .55), (38.6, .3), (39.8, .15)],
            }
            return probes.get(key, [(0, 1.0)])
        return [(None, 1.0)]

    def evaluate(self, state: PatientState) -> List[Dict]:
        base_risk = self.risk.score(state)
        base_belief = self.belief.compute(state)
        base_band = base_risk["band_width_points"]
        base_tier = base_risk["tier_min"]["tier"]
        base_H = base_belief["entropy_bits"]

        candidates = []
        for key in state.unknown_slots():
            slot = SLOTS[key]
            exp_band, exp_H, tier_flip = 0.0, 0.0, 0.0

            for value, prob in self._answer_space(key):
                ghost = copy.deepcopy(state)
                ghost.facts[key] = value
                r = self.risk.score(ghost)
                b = self.belief.compute(ghost)
                exp_band += prob * r["band_width_points"]
                exp_H    += prob * b["entropy_bits"]
                if r["tier_min"]["tier"] != base_tier:
                    tier_flip += prob

            band_gain    = max(0.0, base_band - exp_band)
            entropy_gain = max(0.0, base_H - exp_H)
            redflag      = 1.0 if slot.red_flag else 0.0

            raw = (W_BAND * band_gain
                   + W_ENTROPY * entropy_gain
                   + W_REDFLAG * redflag
                   + W_TIERFLIP * tier_flip)
            utility = raw / max(slot.ask_cost, 1.0)

            candidates.append({
                "slot": key,
                "question": slot.question,
                "dtype": slot.dtype,
                "choices": slot.choices,
                "red_flag": slot.red_flag,
                "ask_cost_s": slot.ask_cost,
                "evoi_band_pts": round(band_gain, 2),
                "evoi_entropy_bits": round(entropy_gain, 3),
                "p_changes_routing": round(tier_flip, 3),
                "utility": round(utility, 3),
                "why_this_question": slot.rationale,
            })

        candidates.sort(key=lambda c: -c["utility"])
        return candidates

    def next_question(self, state: PatientState):
        ranked = self.evaluate(state)
        state.log_tool("question_selector.evaluate",
                       f"{len(ranked)} candidates",
                       f"top={ranked[0]['slot'] if ranked else 'none'}")
        return (ranked[0] if ranked else None), ranked[:6]