"""
LLM converts free text -> structured findings. It NEVER scores or routes.
Falls back to deterministic regex if the API is unavailable (demo-safe).
"""
import os, json, re
from typing import Dict, Any

EXTRACTION_PROMPT = """You are a clinical information EXTRACTOR for a simulated triage sandbox.
You do NOT diagnose, advise, or score risk.

Return ONLY valid JSON:
{"facts": {"<slot>": <value>}, "unknown": ["<slot>"], "notes": "<=15 words"}

Allowed slots and types:
age:number, chest_pain:bool, pain_radiation:bool, pain_exertional:bool, diaphoresis:bool,
dyspnea:bool, full_sentences:bool, spo2:number, resp_rate:number, heart_rate:number,
systolic_bp:number, severe_bleeding:bool, consciousness:one of[alert,voice,pain,unresponsive],
focal_weakness:bool, facial_droop:bool, speech_difficulty:bool, worst_headache:bool,
neck_stiffness:bool, temperature:number, abdominal_pain:bool, vomiting:bool,
calf_swelling:bool, recent_immobility:bool, pregnancy:bool, cardiac_history:bool,
immunocompromised:bool

Rules:
- Only include slots explicitly supported by the text.
- If the patient says they don't know / can't tell, put the slot in "unknown".
- Never invent vitals.

Question asked: "{question}"
Patient said: "{utterance}"
JSON:"""

BOOL_PATTERNS = {
    "chest_pain": r"chest (pain|pressure|tight|discomfort)|heart hurt",
    "dyspnea": r"(short(ness)? of breath|breathless|can'?t breathe|difficulty breathing|gasping)",
    "severe_bleeding": r"(heavy|severe|lot of|uncontrolled) bleed",
    "focal_weakness": r"(one side|left side|right side).*(weak|numb)|weakness on",
    "speech_difficulty": r"(slurr|can'?t speak|words.*not com|speech.*difficult)",
    "worst_headache": r"worst headache|thunderclap",
    "neck_stiffness": r"stiff neck|neck.*stiff",
    "abdominal_pain": r"(stomach|abdomen|belly|tummy).*(pain|ache|hurt)",
    "vomiting": r"vomit|throw(ing)? up|puk",
    "diaphoresis": r"sweat|clammy",
    "calf_swelling": r"(calf|leg).*(swell|swollen|red|painful)",
    "pregnancy": r"pregnan",
    "cardiac_history": r"(heart attack|stent|bypass|angina|cardiac)",
}
NEG = r"(no|not|never|deny|denies|don'?t have|without)\s+"
UNKNOWN_PAT = r"\b(i don'?t know|not sure|can'?t say|no idea|unsure|dunno)\b"


class NLU:
    def __init__(self, api_key: str = ""):
        self.model = None
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.model = None

    def extract(self, utterance: str, question: str = "", expected_slot: str = None) -> Dict[str, Any]:
        if self.model:
            try:
                r = self.model.generate_content(
                    EXTRACTION_PROMPT.format(question=question, utterance=utterance),
                    generation_config={"temperature": 0.0})
                txt = re.sub(r"```(json)?", "", r.text).strip()
                data = json.loads(txt)
                if isinstance(data, dict) and "facts" in data:
                    data["source"] = "gemini-1.5-flash"
                    return data
            except Exception as e:
                pass
        out = self._regex(utterance, expected_slot)
        out["source"] = "deterministic-fallback"
        return out

    def _regex(self, text: str, expected_slot: str = None) -> Dict[str, Any]:
        low = (text or "").lower().strip()
        facts, unknown = {}, []

        if re.search(UNKNOWN_PAT, low) and expected_slot:
            return {"facts": {}, "unknown": [expected_slot], "notes": "patient unsure"}

        # direct yes/no to the asked slot
        if expected_slot:
            if re.fullmatch(r"(yes|yeah|yep|y|haan|ha)\W*", low):
                facts[expected_slot] = True
            elif re.fullmatch(r"(no|nope|n|nahi)\W*", low):
                facts[expected_slot] = False

        for slot, pat in BOOL_PATTERNS.items():
            if re.search(pat, low):
                facts[slot] = not bool(re.search(NEG + pat, low))

        for slot, pat in {
            "age": r"(\d{1,3})\s*(?:years?|yrs?|y/?o|saal)",
            "spo2": r"(?:spo2|sat(?:uration)?|oxygen)\D{0,10}(\d{2,3})",
            "heart_rate": r"(?:hr|pulse|heart rate)\D{0,10}(\d{2,3})",
            "systolic_bp": r"(?:bp|blood pressure)\D{0,10}(\d{2,3})",
            "resp_rate": r"(?:rr|resp(?:iratory)? rate)\D{0,10}(\d{1,2})",
            "temperature": r"(?:temp(?:erature)?|fever)\D{0,10}(\d{2}(?:\.\d)?)",
        }.items():
            m = re.search(pat, low)
            if m:
                facts[slot] = float(m.group(1))

        if expected_slot == "age" and expected_slot not in facts:
            m = re.fullmatch(r"\s*(\d{1,3})\s*", low)
            if m: facts["age"] = float(m.group(1))

        for w, lvl in [("unresponsive", "unresponsive"), ("unconscious", "unresponsive"),
                       ("responds to pain", "pain"), ("drowsy", "voice"), ("alert", "alert")]:
            if w in low: facts["consciousness"] = lvl

        return {"facts": facts, "unknown": unknown, "notes": ""}
