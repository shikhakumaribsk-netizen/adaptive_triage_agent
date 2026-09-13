"""Lightweight offline clinical RAG (Pure Python TF-IDF + Cosine Similarity)."""
import math
import re
from collections import Counter, defaultdict

KB = [
 {"id":"ESI-2","src":"Emergency Severity Index v4 §Level 2",
  "text":"High-risk situations requiring rapid assessment include chest pain suggestive of "
         "acute coronary syndrome, signs of stroke within the treatment window, severe "
         "respiratory distress, and altered mental status. These patients should not wait."},
 {"id":"NEWS2-RR","src":"NEWS2 §Respiratory Rate",
  "text":"Respiratory rate is the earliest and most sensitive indicator of clinical "
         "deterioration. A rate of 25 or more, or 8 or fewer, scores maximum points and "
         "mandates urgent clinical review."},
 {"id":"NEWS2-AGG","src":"NEWS2 §Aggregate Response",
  "text":"An aggregate NEWS2 score of 7 or more triggers an emergency response with critical "
         "care involvement. A score of 5 to 6 is a key threshold for urgent review."},
 {"id":"FAST","src":"FAST Stroke Pathway",
  "text":"Facial droop, arm weakness and speech difficulty indicate possible acute stroke. "
         "Establish time last known well. Thrombolysis window is typically 4.5 hours."},
 {"id":"OTTAWA-SAH","src":"Ottawa Subarachnoid Haemorrhage Rule",
  "text":"For alert patients with sudden severe non-traumatic headache reaching maximum "
         "intensity within one hour, investigate for subarachnoid haemorrhage, especially "
         "with neck pain or stiffness, age over 40, or witnessed loss of consciousness."},
 {"id":"SEPSIS-6","src":"Sepsis Recognition",
  "text":"Suspect sepsis with infection plus temperature above 38.3 or below 36, heart rate "
         "over 90, respiratory rate over 20, or altered mental state. Hypotension indicates "
         "septic shock requiring immediate resuscitation."},
 {"id":"WELLS-PE","src":"Wells Criteria for Pulmonary Embolism",
  "text":"Clinical signs of deep vein thrombosis, heart rate above 100, immobilisation or "
         "surgery within four weeks, previous VTE, and haemoptysis raise pulmonary embolism "
         "probability."},
 {"id":"PAEDS","src":"Paediatric Triage Considerations",
  "text":"Children compensate well and then deteriorate abruptly. Normal vital sign ranges "
         "differ by age. Reduced feeding, reduced wet nappies and lethargy are significant "
         "warning signs in infants."},
 {"id":"GERI","src":"Geriatric Triage Considerations",
  "text":"Older adults may present atypically. Myocardial infarction can occur without chest "
         "pain and sepsis without fever. A lower threshold for escalation is recommended."},
 {"id":"UNCERTAIN","src":"Triage Safety Principle",
  "text":"Where triage acuity is uncertain, the higher acuity category should be assigned. "
         "Under-triage carries far greater patient risk than over-triage."},
]


def tokenize(text: str):
    text = text.lower()
    tokens = re.findall(r"[a-zA-Z0-9]+", text)
    return tokens


class ClinicalRAG:
    def __init__(self):
        self.docs = [d["text"] for d in KB]
        self.doc_tokens_list = [tokenize(t) for t in self.docs]

        vocab_set = set()
        for toks in self.doc_tokens_list:
            vocab_set.update(toks)
        self.vocab = sorted(vocab_set)

        self.idf = defaultdict(float)
        N = len(self.docs)
        for term in self.vocab:
            df = 0
            for toks in self.doc_tokens_list:
                if term in toks:
                    df += 1
            if df > 0:
                self.idf[term] = math.log((1 + N) / (1 + df)) + 1.0

        self.tfidf_docs = []
        for toks in self.doc_tokens_list:
            tf = Counter(toks)
            total = len(toks)
            if total == 0:
                total = 1
            vec = {}
            for term, c in tf.items():
                tf_w = c / total
                vec[term] = tf_w * self.idf[term]
            self.tfidf_docs.append(vec)

    @staticmethod
    def _cosine(v1: dict, v2: dict):
        dot = 0.0
        if len(v1) > len(v2):
            v_small, v_large = v2, v1
        else:
            v_small, v_large = v1, v2

        for term, w in v_small.items():
            dot += w * v_large.get(term, 0.0)

        def norm(v):
            s = 0.0
            for w in v.values():
                s += w * w
            return math.sqrt(s) or 1e-12

        return dot / (norm(v1) * norm(v2))

    def _tfidf_query(self, query_tokens):
        tf = Counter(query_tokens)
        total = len(query_tokens)
        if total == 0:
            total = 1
        qv = {}
        for term, c in tf.items():
            if term in self.idf:
                tf_w = c / total
                qv[term] = tf_w * self.idf[term]
        return qv

    def retrieve(self, state, risk=None, top_k=3):
        terms_bool = []
        for k, v in state.facts.items():
            if v is True:
                terms_bool.append(k)

        terms_rules = []
        if risk is not None:
            fired = risk.get("fired_rules", [])
            for r in fired:
                terms_rules.append(r["rule"])

            tier_max = risk.get("tier_max", {})
            if tier_max:
                terms_rules.append(tier_max["code"])

        age = state.facts.get("age")
        if isinstance(age, (int, float)):
            if age < 12:
                terms_bool.append("paediatric")
            elif age >= 65:
                terms_bool.append("geriatric")

        query_text = " ".join(terms_bool + terms_rules)
        if query_text.strip() == "":
            query_text = "general triage"

        qv = self._tfidf_query(tokenize(query_text))

        sims = []
        for i, dv in enumerate(self.tfidf_docs):
            sc = self._cosine(qv, dv)
            sims.append((i, sc))

        sims.sort(key=lambda x: x[1], reverse=True)

        out = []
        for i, sc in sims[:top_k]:
            if sc > 0.02:
                d = KB[i]
                snippet = d["text"][:200] + "…"
                out.append({
                    "id": d["id"],
                    "source": d["src"],
                    "snippet": snippet,
                    "relevance": round(float(sc), 3)
                })
        return out