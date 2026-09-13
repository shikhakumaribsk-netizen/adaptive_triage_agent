"""Vitals/symptom reference database tool (queried by the agent)."""
from typing import Any, Dict, Optional

NORMALS = {
    "heart_rate":  {"adult": (60, 100), "child": (80, 130), "infant": (100, 160), "unit": "bpm"},
    "resp_rate":   {"adult": (12, 20),  "child": (20, 30),  "infant": (30, 60),  "unit": "/min"},
    "systolic_bp": {"adult": (90, 140), "child": (80, 120), "infant": (70, 100), "unit": "mmHg"},
    "spo2":        {"adult": (95, 100), "child": (95, 100), "infant": (95, 100), "unit": "%"},
    "temperature": {"adult": (36.1, 37.5), "child": (36.1, 37.8), "infant": (36.5, 37.8), "unit": "°C"},
}

SYMPTOM_META = {
    "chest_pain": dict(system="Cardiovascular",
                       red_flags=["radiation to arm/jaw", "diaphoresis", "exertional onset"],
                       must_exclude=["ACS", "Aortic dissection", "PE"]),
    "dyspnea": dict(system="Respiratory",
                    red_flags=["cannot speak full sentences", "SpO2 < 94%", "RR > 25"],
                    must_exclude=["PE", "Severe asthma", "Pneumothorax", "Pulmonary oedema"]),
    "focal_weakness": dict(system="Neurological",
                           red_flags=["facial droop", "slurred speech", "onset < 4.5h"],
                           must_exclude=["Ischaemic stroke", "Haemorrhagic stroke"]),
    "abdominal_pain": dict(system="Gastrointestinal",
                           red_flags=["rigid abdomen", "hypotension", "age > 65"],
                           must_exclude=["AAA", "Perforation", "Ectopic pregnancy"]),
    "worst_headache": dict(system="Neurological",
                           red_flags=["thunderclap onset", "neck stiffness", "vomiting"],
                           must_exclude=["Subarachnoid haemorrhage", "Meningitis"]),
}


class PatientDataTool:
    def age_band(self, age) -> str:
        if age is None: return "adult"
        if age < 1: return "infant"
        if age < 12: return "child"
        return "adult"

    def reference(self, slot: str, value: Any, age=None) -> Optional[Dict]:
        if slot not in NORMALS or not isinstance(value, (int, float)):
            return None
        band = self.age_band(age)
        lo, hi = NORMALS[slot][band]
        status = "NORMAL" if lo <= value <= hi else ("LOW" if value < lo else "HIGH")
        return {"slot": slot, "value": value, "normal_range": f"{lo}–{hi}",
                "unit": NORMALS[slot]["unit"], "status": status, "age_band": band,
                "summary": f"{slot}={value}{NORMALS[slot]['unit']} is {status} "
                           f"(normal {lo}–{hi} for {band})"}

    def symptom_profile(self, symptom: str) -> Optional[Dict]:
        return SYMPTOM_META.get(symptom)

    def all_normals(self) -> Dict:
        return NORMALS