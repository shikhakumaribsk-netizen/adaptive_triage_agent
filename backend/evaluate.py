"""Benchmark: adaptive agent vs. fixed-questionnaire baseline."""
import statistics
from agent.state import PatientState, SLOTS
from agent.orchestrator import TriageOrchestrator
from tools.case_bank import CaseBank, CASES
from tools.risk_tool import ROUTING_OUTCOMES

TIER = {o["code"]: o["tier"] for o in ROUTING_OUTCOMES}
AGENT = TriageOrchestrator("")      # deterministic fallback NLU = reproducible
BANK = CaseBank()


def run_adaptive(case):
    st = PatientState(session_id=case["id"], patient_name=case["name"])
    out = AGENT.step(st, utterance=case["opening"])
    turn = 1
    while out.get("phase") in ("INTERVIEWING", "RE_ASSESSING") and turn <= 14:
        q = out["next_question"]
        out = AGENT.step(st, utterance=BANK.answer_for(case, q["slot"], turn),
                         answered_slot=q["slot"])
        turn += 1
    return out.get("routing", {}).get("code", "UNKNOWN"), len(st.asked)


def run_baseline(case):
    """Baseline asks EVERY applicable slot in fixed order."""
    st = PatientState(session_id=case["id"] + "-b", patient_name=case["name"])
    AGENT.step(st, utterance=case["opening"])
    asked = 0
    for key in SLOTS:
        if key == "chief_complaint" or st.is_known(key):
            continue
        slot = SLOTS[key]
        if slot.depends_on and st.get(slot.depends_on) is not True:
            continue
        AGENT.step(st, utterance=BANK.answer_for(case, key, 99), answered_slot=key)
        asked += 1
    out = AGENT.step(st)
    return out.get("routing", {}).get("code", "UNKNOWN"), asked


def report():
    rows, a_q, b_q = [], [], []
    a_under = a_over = b_under = b_over = 0

    for c in CASES:
        gt = TIER[c["ground_truth"]]
        ac, an = run_adaptive(c)
        bc, bn = run_baseline(c)
        a_q.append(an); b_q.append(bn)
        at, bt = TIER.get(ac, 0), TIER.get(bc, 0)
        if at < gt: a_under += 1
        if at > gt: a_over += 1
        if bt < gt: b_under += 1
        if bt > gt: b_over += 1
        rows.append((c["id"], c["label"][:34], c["ground_truth"], ac, an, bc, bn))

    n = len(CASES)
    print("\n" + "="*104)
    print("ADAPTIVE TRIAGE AGENT — EVALUATION REPORT")
    print("="*104)
    print(f"{'ID':<5}{'CASE':<36}{'TRUTH':<11}{'AGENT':<11}{'Q':<4}{'BASELINE':<11}{'Q':<4}{'OK'}")
    print("-"*104)
    for r in rows:
        print(f"{r[0]:<5}{r[1]:<36}{r[2]:<11}{r[3]:<11}{r[4]:<4}{r[5]:<11}{r[6]:<4}"
              f"{'✅' if r[2]==r[3] else '⚠️'}")
    print("-"*104)
    print(f"Avg questions   ADAPTIVE {statistics.mean(a_q):5.1f}   |  BASELINE {statistics.mean(b_q):5.1f}"
          f"   →  {100*(1-statistics.mean(a_q)/statistics.mean(b_q)):.0f}% fewer questions")
    print(f"Under-triage    ADAPTIVE {100*a_under/n:5.1f}%  |  BASELINE {100*b_under/n:5.1f}%   (lower = safer)")
    print(f"Over-triage     ADAPTIVE {100*a_over/n:5.1f}%  |  BASELINE {100*b_over/n:5.1f}%")
    print(f"Exact match     ADAPTIVE {100*sum(1 for r in rows if r[2]==r[3])/n:5.1f}%")
    print("="*104 + "\n")


if __name__ == "__main__":
    report()