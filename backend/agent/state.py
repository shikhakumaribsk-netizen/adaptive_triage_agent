"""
Patient state with explicit UNKNOWN handling.
Every askable fact is a "slot" with metadata used by the EVOI engine.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib, json

UNKNOWN = None


@dataclass
class Slot:
    key: str
    question: str
    dtype: str                    # bool | number | choice
    ask_cost: float               # seconds of patient burden
    max_points: int               # worst-case risk contribution
    red_flag: bool = False        # is this a life-threat rule-out?
    choices: Optional[List[str]] = None
    depends_on: Optional[str] = None     # only ask if this slot is True
    prior_true: float = 0.3              # P(answer=yes) used for EVOI expectation
    rationale: str = ""


# ────────────────────────────────────────────────────────────────
# SLOT REGISTRY  (the agent's entire question universe)
# ────────────────────────────────────────────────────────────────
SLOTS: Dict[str, Slot] = {s.key: s for s in [
    Slot("age", "What is the patient's age (in years)?", "number",
         5, 15, prior_true=0.5, rationale="Age extremes change acuity thresholds"),

    Slot("chief_complaint", "What is the main problem bringing you in today?", "text",
         12, 0, red_flag=True, rationale="Seeds the entire differential"),

    # ── Cardiac cluster
    Slot("chest_pain", "Are you having any chest pain or chest pressure?", "bool",
         5, 25, red_flag=True, prior_true=0.25,
         rationale="Primary ACS screen"),
    Slot("pain_radiation", "Does the pain spread to your arm, jaw, neck or back?", "bool",
         6, 12, red_flag=True, depends_on="chest_pain", prior_true=0.45,
         rationale="Radiation raises ACS likelihood ratio"),
    Slot("pain_exertional", "Did the pain start or worsen with exertion?", "bool",
         6, 8, depends_on="chest_pain", prior_true=0.4,
         rationale="Exertional pattern suggests ischemia"),
    Slot("diaphoresis", "Are you sweating heavily or feeling clammy?", "bool",
         5, 10, red_flag=True, prior_true=0.2,
         rationale="Autonomic sign of serious pathology"),

    # ── Respiratory cluster
    Slot("dyspnea", "Are you having any difficulty breathing?", "bool",
         5, 20, red_flag=True, prior_true=0.3,
         rationale="Airway/Breathing priority in ABCDE"),
    Slot("full_sentences", "Can you speak a full sentence without pausing for breath?", "bool",
         5, 18, red_flag=True, depends_on="dyspnea", prior_true=0.7,
         rationale="Bedside marker of respiratory failure severity"),
    Slot("spo2", "What is the oxygen saturation (SpO2 %)?", "number",
         8, 25, red_flag=True, rationale="NEWS2 oxygenation parameter"),
    Slot("resp_rate", "What is the respiratory rate (breaths/min)?", "number",
         8, 18, red_flag=True, rationale="Most sensitive early deterioration sign"),

    # ── Circulation
    Slot("heart_rate", "What is the heart rate (bpm)?", "number", 8, 20,
         rationale="NEWS2 pulse parameter"),
    Slot("systolic_bp", "What is the systolic blood pressure (mmHg)?", "number", 10, 25,
         red_flag=True, rationale="Shock detection"),
    Slot("severe_bleeding", "Is there any heavy or uncontrolled bleeding?", "bool",
         4, 25, red_flag=True, prior_true=0.05,
         rationale="Catastrophic haemorrhage = immediate"),

    # ── Neuro
    Slot("consciousness", "Is the patient Alert, responsive to Voice, to Pain, or Unresponsive?",
         "choice", 6, 30, red_flag=True, choices=["alert", "voice", "pain", "unresponsive"],
         rationale="AVPU — disability assessment"),
    Slot("focal_weakness", "Is there sudden weakness or numbness on one side of the body?", "bool",
         6, 28, red_flag=True, prior_true=0.08, rationale="FAST stroke screen"),
    Slot("facial_droop", "Is one side of the face drooping?", "bool",
         5, 12, red_flag=True, depends_on="focal_weakness", prior_true=0.5,
         rationale="FAST stroke screen"),
    Slot("speech_difficulty", "Is speech slurred or is it hard to find words?", "bool",
         5, 12, red_flag=True, prior_true=0.08, rationale="FAST stroke screen"),
    Slot("worst_headache", "Is this the worst headache of your life, starting suddenly?", "bool",
         6, 22, red_flag=True, prior_true=0.06,
         rationale="Thunderclap headache → SAH rule-out"),
    Slot("neck_stiffness", "Do you have a stiff neck or discomfort in bright light?", "bool",
         5, 14, prior_true=0.1, rationale="Meningism screen"),

    # ── Infection / other
    Slot("temperature", "What is the body temperature (°C)?", "number", 8, 18,
         rationale="NEWS2 temperature parameter"),
    Slot("abdominal_pain", "Do you have abdominal pain?", "bool", 5, 12, prior_true=0.2,
         rationale="Broad abdominal differential"),
    Slot("vomiting", "Have you been vomiting?", "bool", 4, 8, prior_true=0.2,
         rationale="Dehydration/obstruction indicator"),
    Slot("calf_swelling", "Is one calf swollen, red or painful?", "bool", 5, 14,
         prior_true=0.06, rationale="DVT → PE risk (Wells criteria element)"),
    Slot("recent_immobility", "Any recent surgery, long travel, or bed rest in the last 4 weeks?",
         "bool", 6, 10, prior_true=0.12, rationale="VTE risk factor"),
    Slot("pregnancy", "Is the patient currently pregnant or possibly pregnant?", "bool",
         5, 10, prior_true=0.05, rationale="Alters acuity and differential"),
    Slot("cardiac_history", "Any history of heart disease, stent, or prior heart attack?", "bool",
         6, 10, prior_true=0.15, rationale="Pre-test probability modifier"),
    Slot("immunocompromised", "Any diabetes, cancer treatment, or immune-suppressing condition?",
         "bool", 6, 8, prior_true=0.15, rationale="Blunts normal warning signs"),
]}


@dataclass
class PatientState:
    session_id: str
    patient_name: str = "Unknown"
    facts: Dict[str, Any] = field(default_factory=dict)      # answered slots
    denied: List[str] = field(default_factory=list)          # explicitly = False
    unknown_declared: List[str] = field(default_factory=list)# patient said "I don't know"
    asked: List[str] = field(default_factory=list)
    transcript: List[Dict] = field(default_factory=list)
    tool_trace: List[Dict] = field(default_factory=list)
    contradictions: List[Dict] = field(default_factory=list)
    risk_history: List[Dict] = field(default_factory=list)
    status: str = "IN_PROGRESS"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ── helpers ────────────────────────────────────────────
    def is_known(self, key: str) -> bool:
        return key in self.facts and self.facts[key] is not UNKNOWN

    def get(self, key: str, default=UNKNOWN):
        return self.facts.get(key, default)

    def unknown_slots(self) -> List[str]:
        """Applicable slots that are still unanswered — the uncertainty frontier."""
        out = []
        for key, slot in SLOTS.items():
            if self.is_known(key) or key in self.unknown_declared:
                continue
            if slot.depends_on and self.get(slot.depends_on) is not True:
                continue     # not applicable yet (conditional branch)
            out.append(key)
        return out

    def completeness(self) -> float:
        applicable = len(self.unknown_slots()) + len(self.facts)
        return round(len(self.facts) / max(applicable, 1) * 100, 1)

    def log_tool(self, tool: str, args: Any, result_summary: str, ms: int = 0):
        self.tool_trace.append({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "tool": tool, "args": str(args)[:120],
            "result": result_summary[:160], "ms": ms,
        })

    def audit_hash(self) -> str:
        payload = json.dumps({"facts": self.facts, "asked": self.asked},
                             sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]