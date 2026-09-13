"""
Naive-Bayes belief state over acuity hypotheses.
NOTE: Presented to users as 'differential considerations for clinician review',
      NEVER as a diagnosis (guardrail requirement).
"""
import math
from typing import Dict
from agent.state import PatientState

HYPOTHESES = {
    "acs":      {"label": "Acute Coronary Syndrome pattern", "prior": 0.07},
    "pe":       {"label": "Pulmonary Embolism pattern",      "prior": 0.04},
    "sepsis":   {"label": "Sepsis / Serious Infection",      "prior": 0.09},
    "stroke":   {"label": "Acute Stroke pattern",            "prior": 0.05},
    "resp":     {"label": "Asthma / COPD Exacerbation",      "prior": 0.08},
    "abdo":     {"label": "Acute Abdomen",                   "prior": 0.10},
    "benign":   {"label": "Low-acuity / Self-limiting",      "prior": 0.57},
}

# LIKELIHOOD[finding][hypothesis] = (LR_if_present, LR_if_absent)
LIKELIHOOD = {
    "chest_pain":       {"acs": (7.0, 0.2), "pe": (3.0, 0.5), "benign": (0.6, 1.2)},
    "pain_radiation":   {"acs": (4.0, 0.5), "benign": (0.4, 1.1)},
    "pain_exertional":  {"acs": (3.2, 0.7)},
    "diaphoresis":      {"acs": (3.5, 0.7), "sepsis": (2.0, 0.9), "benign": (0.3, 1.1)},
    "dyspnea":          {"pe": (4.0, 0.3), "resp": (5.0, 0.2), "acs": (1.8, 0.8), "benign": (0.5, 1.2)},
    "calf_swelling":    {"pe": (6.0, 0.8)},
    "recent_immobility":{"pe": (3.0, 0.85)},
    "focal_weakness":   {"stroke": (12.0, 0.2), "benign": (0.2, 1.1)},
    "speech_difficulty":{"stroke": (8.0, 0.4)},
    "worst_headache":   {"stroke": (5.0, 0.8), "benign": (0.3, 1.1)},
    "neck_stiffness":   {"sepsis": (4.0, 0.9)},
    "abdominal_pain":   {"abdo": (7.0, 0.3), "benign": (0.7, 1.1)},
    "vomiting":         {"abdo": (2.2, 0.8), "sepsis": (1.6, 0.9)},
    "immunocompromised":{"sepsis": (2.2, 0.9)},
    "cardiac_history":  {"acs": (2.6, 0.8)},
}

# numeric findings -> boolean triggers
NUMERIC_TRIGGERS = {
    "temperature": lambda v: ("fever", v >= 38.0),
    "spo2":        lambda v: ("hypoxia", v < 94),
    "heart_rate":  lambda v: ("tachycardia", v > 100),
    "resp_rate":   lambda v: ("tachypnea", v > 20),
    "systolic_bp": lambda v: ("hypotension", v < 100),
}
LIKELIHOOD.update({
    "fever":        {"sepsis": (6.0, 0.3), "benign": (0.5, 1.1)},
    "hypoxia":      {"pe": (3.5, 0.6), "resp": (4.0, 0.5), "sepsis": (2.0, 0.9), "benign": (0.2, 1.1)},
    "tachycardia":  {"sepsis": (2.4, 0.7), "pe": (2.8, 0.6), "acs": (1.5, 0.9)},
    "tachypnea":    {"sepsis": (2.6, 0.7), "pe": (3.0, 0.6), "resp": (3.0, 0.6)},
    "hypotension":  {"sepsis": (4.0, 0.85), "acs": (2.0, 0.95)},
})


class BeliefEngine:
    def compute(self, state: PatientState) -> Dict:
        post = {h: v["prior"] for h, v in HYPOTHESES.items()}
        evidence_used = []

        findings = {}
        for k, v in state.facts.items():
            if isinstance(v, bool):
                findings[k] = v
            elif k in NUMERIC_TRIGGERS and isinstance(v, (int, float)):
                name, truth = NUMERIC_TRIGGERS[k](v)
                findings[name] = truth

        for finding, present in findings.items():
            table = LIKELIHOOD.get(finding)
            if not table:
                continue
            evidence_used.append(f"{finding}={'+' if present else '−'}")
            for h in post:
                lr_p, lr_a = table.get(h, (1.0, 1.0))
                post[h] *= (lr_p if present else lr_a)

        total = sum(post.values()) or 1.0
        post = {h: p / total for h, p in post.items()}

        entropy = -sum(p * math.log2(p) for p in post.values() if p > 1e-9)
        max_entropy = math.log2(len(post))

        ranked = sorted(
            [{"key": h, "label": HYPOTHESES[h]["label"], "p": round(p, 4)}
             for h, p in post.items()],
            key=lambda x: -x["p"])

        return {
            "distribution": ranked,
            "top": ranked[0],
            "entropy_bits": round(entropy, 3),
            "normalised_uncertainty": round(entropy / max_entropy, 3),
            "evidence_used": evidence_used,
            "disclaimer": "Differential considerations for clinician review only. Not a diagnosis.",
        }