"""Synthetic patient cases for the sandbox + evaluation harness."""

CASES = [
 {"id":"C01","name":"Ramesh Kumar","label":"Silent MI in a diabetic",
  "opening":"I've been feeling very tired and sweaty since morning, and a bit sick.",
  "ground_truth":"CRITICAL",
  "truth":{"age":68,"chest_pain":False,"diaphoresis":True,"dyspnea":True,"cardiac_history":True,
           "immunocompromised":True,"heart_rate":108,"systolic_bp":102,"spo2":93,
           "resp_rate":22,"temperature":36.8,"consciousness":"alert","full_sentences":True}},

 {"id":"C02","name":"Anita Sharma","label":"Panic attack mimicking ACS",
  "opening":"My chest feels really tight and my heart is racing, I think I'm dying.",
  "ground_truth":"URGENT",
  "truth":{"age":26,"chest_pain":True,"pain_radiation":False,"pain_exertional":False,
           "diaphoresis":False,"dyspnea":True,"full_sentences":True,"heart_rate":112,
           "systolic_bp":128,"spo2":99,"resp_rate":24,"temperature":36.9,
           "consciousness":"alert","cardiac_history":False}},

 {"id":"C03","name":"Baby Aarav","label":"Infant with bronchiolitis",
  "opening":"My baby is breathing very fast and not feeding properly since last night.",
  "ground_truth":"CRITICAL",
  "truth":{"age":0.5,"dyspnea":True,"full_sentences":False,"resp_rate":58,"heart_rate":168,
           "spo2":91,"temperature":38.1,"consciousness":"alert","chest_pain":False}},

 {"id":"C04","name":"Suresh Patel","label":"Acute stroke, FAST positive",
  "opening":"My right arm went weak suddenly and my speech sounds strange.",
  "ground_truth":"CRITICAL",
  "truth":{"age":61,"focal_weakness":True,"facial_droop":True,"speech_difficulty":True,
           "chest_pain":False,"heart_rate":92,"systolic_bp":168,"spo2":97,
           "resp_rate":18,"temperature":36.7,"consciousness":"alert"}},

 {"id":"C05","name":"Meera Das","label":"Septic shock from UTI",
  "opening":"I've had a high fever for two days and now I feel dizzy and confused.",
  "ground_truth":"RESUS",
  "truth":{"age":74,"temperature":39.6,"heart_rate":126,"systolic_bp":78,"spo2":92,
           "resp_rate":28,"consciousness":"voice","immunocompromised":True,
           "chest_pain":False,"vomiting":True}},

 {"id":"C06","name":"Karan Mehta","label":"Minor ankle sprain",
  "opening":"I twisted my ankle playing football, it hurts but I can walk on it.",
  "ground_truth":"STANDARD",
  "truth":{"age":22,"chest_pain":False,"dyspnea":False,"heart_rate":78,"systolic_bp":122,
           "spo2":99,"resp_rate":16,"temperature":36.6,"consciousness":"alert",
           "abdominal_pain":False}},

 {"id":"C07","name":"Fatima Sheikh","label":"PE after long flight",
  "opening":"I suddenly can't catch my breath and my left calf has been sore.",
  "ground_truth":"CRITICAL",
  "truth":{"age":44,"dyspnea":True,"full_sentences":False,"calf_swelling":True,
           "recent_immobility":True,"chest_pain":True,"pain_radiation":False,
           "heart_rate":118,"systolic_bp":108,"spo2":89,"resp_rate":30,
           "temperature":37.2,"consciousness":"alert"}},

 {"id":"C08","name":"Vikram Rao","label":"Contradictory / inconsistent historian",
  "opening":"No chest pain at all, I'm totally fine, my family made me come.",
  "ground_truth":"EMERGENCY",
  "contradiction_script":[(3,"chest_pain",True)],   # flips at question 3
  "truth":{"age":57,"chest_pain":False,"diaphoresis":True,"cardiac_history":True,
           "heart_rate":104,"systolic_bp":142,"spo2":95,"resp_rate":20,
           "temperature":36.9,"consciousness":"alert","full_sentences":True}},

 {"id":"C09","name":"Priya Nair","label":"Thunderclap headache (SAH)",
  "opening":"The worst headache of my life started suddenly an hour ago.",
  "ground_truth":"CRITICAL",
  "truth":{"age":41,"worst_headache":True,"neck_stiffness":True,"vomiting":True,
           "chest_pain":False,"heart_rate":94,"systolic_bp":158,"spo2":98,
           "resp_rate":18,"temperature":37.0,"consciousness":"alert"}},

 {"id":"C10","name":"Unknown Male","label":"Unresponsive — unable to answer",
  "opening":"He collapsed at the bus stand and isn't responding to us.",
  "ground_truth":"RESUS",
  "unknown_slots":["chest_pain","pain_radiation","abdominal_pain"],
  "truth":{"age":50,"consciousness":"unresponsive","heart_rate":44,"systolic_bp":76,
           "spo2":84,"resp_rate":7,"temperature":35.2}},
]


class CaseBank:
    def list(self):
        return [{"id": c["id"], "name": c["name"], "label": c["label"],
                 "opening": c["opening"], "ground_truth": c["ground_truth"]} for c in CASES]

    def get(self, case_id):
        return next((c for c in CASES if c["id"] == case_id), None)

    def answer_for(self, case, slot, turn=0):
        """Simulate the patient answering a specific slot."""
        if slot in case.get("unknown_slots", []):
            return "I don't know, I can't say."
        for t, s, v in case.get("contradiction_script", []):
            if turn >= t and s == slot:
                return "Actually yes, now that you ask, I do have that."
        v = case["truth"].get(slot)
        if v is None:
            return "I don't know."
        if isinstance(v, bool):
            return "Yes" if v else "No"
        if slot == "consciousness":
            return f"The patient is {v}."
        return f"{slot.replace('_',' ')} is {v}"