"""Enforces the 'decision support, not diagnosis' guardrail."""
import re

DISCLAIMER = ("⚕️ SIMULATED DECISION SUPPORT ONLY — This system does not provide a medical "
              "diagnosis or treatment advice. It supports triage routing in a synthetic "
              "sandbox environment. In a real emergency, call 108 / 112.")

BLOCKED_INTENTS = [
    (r"\b(what|which)\s+(disease|illness|condition)\s+do i have\b", "diagnosis_request"),
    (r"\b(diagnos(e|is)|confirm i have)\b", "diagnosis_request"),
    (r"\b(what|which)\s+(medicine|medication|tablet|drug|dose|dosage)\b", "treatment_request"),
    (r"\b(should i take|prescribe|prescription)\b", "treatment_request"),
    (r"\b(am i going to die|will i die)\b", "prognosis_request"),
    (r"\b(ignore|disregard|forget)\s+(all\s+)?(previous\s+)?(instructions|rules|prompt)\b",
     "prompt_injection"),
    (r"\byou are now\b|\bact as\b.*\b(doctor|physician)\b", "prompt_injection"),
]

REFUSALS = {
    "diagnosis_request": ("I can't provide a diagnosis — that requires a qualified clinician. "
                          "What I can do is assess urgency and route you to the right level of "
                          "care. Let's continue the assessment."),
    "treatment_request": ("I can't advise on medicines or doses. I only determine how urgently "
                          "you should be seen and by whom."),
    "prognosis_request": ("I can't predict outcomes. I can make sure you're seen at the right "
                          "urgency level — let's keep going."),
    "prompt_injection": ("My triage safety rules can't be modified during an assessment. "
                         "Continuing with the clinical questions."),
}


class Guardrails:
    def inspect(self, text: str):
        low = (text or "").lower()
        for pattern, intent in BLOCKED_INTENTS:
            if re.search(pattern, low):
                return {"blocked": True, "intent": intent, "response": REFUSALS[intent]}
        return {"blocked": False}

    def wrap(self, payload: dict) -> dict:
        payload["disclaimer"] = DISCLAIMER
        payload["environment"] = "SIMULATED_SANDBOX"
        payload["is_diagnosis"] = False
        return payload