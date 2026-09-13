# Architecture — Adaptive Emergency Triage Agent

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (React + Vite)                │
│  TriagePage │ AdminPage │ MetricsPage │ HomePage         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ UncertaintyBand │ EVOIPanel │ BeliefChart         │   │
│  │ ToolTrace │ EscalationBanner │ ContradictionLedger│   │
│  │ CaseSimulator │ WhatIfPanel │ RiskGauge           │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / REST (JSON)
┌──────────────────────▼──────────────────────────────────┐
│               FastAPI Backend (Python)                   │
│  main.py — routes, session store, queue                  │
│  schemas.py — Pydantic v2 request/response models        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              agent/ (The Agent Loop)              │   │
│  │  orchestrator.py ←── implements 7 workflow steps  │   │
│  │  state.py        — PatientState + 27 slot registry│   │
│  │  question_selector.py — EVOI engine               │   │
│  │  belief.py       — Bayesian differential + entropy│   │
│  │  contradiction.py — Contradiction ledger          │   │
│  │  escalation.py   — Escalation ladder              │   │
│  │  guardrails.py   — Non-diagnosis enforcement      │   │
│  │  nlu.py          — Gemini extraction + regex      │   │
│  └────────────────────┬─────────────────────────────┘   │
│                       │ tool calls (logged)              │
│  ┌────────────────────▼─────────────────────────────┐   │
│  │              tools/                               │   │
│  │  risk_tool.py    — Deterministic scorer + band    │   │
│  │  patient_db.py   — Vitals reference ranges        │   │
│  │  rag_tool.py     — TF-IDF clinical protocol RAG   │   │
│  │  case_bank.py    — 10 synthetic patients          │   │
│  └──────────────────────────────────────────────────┘   │
│                       │                                  │
│  ┌────────────────────▼─────────────────────────────┐   │
│  │              data/                                │   │
│  │  knowledge_base.json — 20 protocol chunks         │   │
│  │  synthetic_cases.json — 10 validated cases        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       │ API only (extraction)
               ┌───────▼────────┐
               │ Google Gemini  │
               │ 1.5 Flash API  │
               │ (NLU only)     │
               └────────────────┘
```

## The 7 Workflow Steps — Where Each Lives

| Step | Requirement | File | Function |
|------|-------------|------|----------|
| 1 | Start with incomplete patient state | `agent/state.py` | `PatientState` — all slots initialise as `UNKNOWN` |
| 2 | Select next question by uncertainty/risk | `agent/question_selector.py` | `QuestionSelector.evaluate()` — EVOI scoring |
| 3 | Query risk and patient-data tools | `tools/risk_tool.py`, `tools/patient_db.py`, `tools/rag_tool.py` | `RiskTool.score()`, `PatientDataTool.reference()`, `ClinicalRAG.retrieve()` |
| 4 | Update patient state and risk assessment | `agent/orchestrator.py` | `TriageOrchestrator.step()` lines 40–80 |
| 5 | Decide among predefined routing outcomes | `tools/risk_tool.py` | `ROUTING_OUTCOMES` enum (6 fixed codes) |
| 6 | Reassess on new/contradictory information | `agent/contradiction.py`, `main.py /api/session/vitals` | `ContradictionDetector.check()`, vitals endpoint |
| 7 | Escalate unresolved high-risk cases | `agent/escalation.py` | `EscalationPolicy.evaluate()` — 5 explicit triggers |

## EVOI Question Selection Formula

```
For each unanswered slot q:
  EVOI(q) = Σ P(answer=a) × [BandWidth_before − BandWidth_after(a)]
  Utility(q) = (w₁·EVOI + w₂·ΔEntropy + w₃·RedFlagBonus + w₄·P(tier_flips)) / AskCost(q)

Weights: w₁=1.0, w₂=18.0, w₃=12.0, w₄=20.0

Stop condition: band_min and band_max both fall in the same routing tier
```

## Risk Band Bracketing

```
score_min = sum of points from known facts only
score_max = score_min + sum of max_points from all unresolved rules

Routing = tier_for(score_min) if tier_for(score_min) == tier_for(score_max)
        else keep asking (band spans a boundary)
        OR  tier_for(score_max) if escalation triggered (safety — higher tier wins)
```

## Escalation Triggers (5 explicit conditions)

1. Question budget exhausted AND band still spans boundary AND max tier ≥ HIGH
2. Unresolved HIGH-severity contradiction in patient history
3. Patient declared unknown on a red-flag slot (worst case assumed + human review)
4. Differential entropy > 1.45 bits AND max acuity ≥ HIGH
5. Decision confidence < 55% AND max acuity ≥ HIGH

## Safety Design Decisions

| Principle | Implementation |
|-----------|---------------|
| LLM never scores | Gemini receives only extraction prompt, returns structured JSON |
| Deterministic audit | SHA-256 hash of (facts + asked + rule_version) per session |
| Under-triage prevention | Tie always goes to higher tier; escalation defaults to upper bound |
| No diagnosis | `guardrails.py` inspects every utterance; 4 blocked intent classes |
| Offline resilience | Regex NLU fallback + TF-IDF RAG; agent works with no API key |
| Reproducibility | Same inputs + same RULE_VERSION = same outputs, always |