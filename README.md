# ⛑️ Adaptive Emergency Triage Agent

> Autonomous patient triage decision support for a **simulated sandbox environment.**
> Determines the safest routing decision while minimising unnecessary questioning.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.3-38bdf8?logo=tailwindcss)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

> ⚕️ **IMPORTANT DISCLAIMER**
> This is a simulated sandbox tool built for a hackathon.
> It provides triage routing suggestions only.
> It does **not** diagnose, treat, or replace clinical judgement.
> In a real emergency: **call 108 / 112 immediately.**

---

## What It Does

The agent conducts an **adaptive interview** that changes with every answer.
It tracks **what it doesn't know** (incomplete state) and uses that uncertainty
to decide **which question gives the most information** — not just a fixed list.

When it has enough information to confidently assign a routing tier,
it stops asking. When it cannot resolve uncertainty safely, it **escalates
to a human clinician** rather than guessing.

---

## Required Workflow — Where Each Step Lives

| # | Requirement | File |
|---|-------------|------|
| 1 | Start with incomplete patient state | `agent/state.py` — PatientState with UNKNOWN slots |
| 2 | Select next question by uncertainty/risk | `agent/question_selector.py` — EVOI engine |
| 3 | Query risk and patient-data tools | `tools/risk_tool.py`, `tools/patient_db.py`, `tools/rag_tool.py` |
| 4 | Update patient state and risk assessment | `agent/orchestrator.py` — step() function |
| 5 | Decide among predefined routing outcomes | 6 fixed codes: SELF_CARE → STANDARD → URGENT → EMERGENCY → CRITICAL → RESUS |
| 6 | Reassess on new or contradictory information | `agent/contradiction.py` + `/api/session/vitals` endpoint |
| 7 | Escalate unresolved high-risk cases | `agent/escalation.py` — 5 explicit escalation triggers |
| 🛡 | Guardrail — not a diagnosis | `agent/guardrails.py` — 4 blocked intent classes |

---

## Agent Flow

```
Incomplete State (0 facts known)
        │
        ▼
Risk Tool → [score_min, score_max] uncertainty band
        │
        ▼
Band spans a routing boundary?
   YES → EVOI Engine ranks all unknown slots → Ask best question
         ↓ patient answers
         NLU extracts facts → check contradictions → update state
         ↓ contradiction found?
           YES → freeze routing → ask resolution question
           NO  → loop back to Risk Tool
   NO  → band resolved → DECIDE routing tier
         OR budget exhausted / entropy too high / unresolved contradiction
            → ESCALATE to human clinician (default to higher tier)
        │
        ▼
Output: routing code + SBAR handoff + protocol citations + audit hash
```

---

## 6 Fixed Routing Outcomes

| Code | Label | Score Range | Action |
|------|-------|-------------|--------|
| `SELF_CARE` | Self-care / Telehealth | 0 – 12 | Advice only |
| `STANDARD` | Standard OPD | 12 – 28 | Within 2–4 hours |
| `URGENT` | Urgent Care | 28 – 45 | Within 60 minutes |
| `EMERGENCY` | Emergency Department | 45 – 62 | Within 15 minutes |
| `CRITICAL` | Immediate Emergency Bay | 62 – 80 | Immediately |
| `RESUS` | Resuscitation Room | 80 – 100 | Resuscitation team now |

Plus the `HUMAN_REVIEW_REQUIRED` flag on any outcome when escalation triggers.

---

## Key Features

### Uncertainty Band Bracketing ⭐
Instead of a single score, the agent computes `[score_min, score_max]`.
It stops asking when **both ends fall in the same routing tier**.
This directly satisfies "minimising unnecessary questioning" with a mathematical proof.

### EVOI Question Ranking ⭐
Every candidate question is scored:
```
Utility = (EVOI_band + ΔEntropy + RedFlagBonus + P(routing_flips)) / AskCost
```
The single highest-utility question is asked. Judges can see the full ranked table live.

### Escalation Ladder ⭐
Five explicit escalation triggers. The agent **admits uncertainty** and defaults
to the higher-acuity option — never invents a confident answer.

### Contradiction Ledger
Every inconsistency is logged with type, severity, and timestamp.
High-severity contradictions freeze the routing decision until resolved.

### Clinical RAG with Citations
TF-IDF retrieval over NEWS2, ESI v4, FAST, Ottawa SAH, Sepsis-6, Wells PE.
Every routing decision cites the protocol that drove it.

### Deterministic Audit
```python
SHA-256(facts + asked_questions + RULE_VERSION) → audit_hash
```
Same inputs always produce the same outputs. Reproducible and auditable.

### Counterfactual Explorer
Drag a vital sign slider to see exactly which rule fires and whether routing changes — without mutating the real session.

### 10 Synthetic Cases + Auto-Play
Load any of 10 validated synthetic patients (silent MI, stroke, PE, contradictory historian, unresponsive) and watch the agent complete the interview automatically. Demo in 10 seconds.

---

## Project Structure

```
adaptive-triage-agent/
│
├── backend/
│   ├── main.py                    # FastAPI app, all API routes
│   ├── schemas.py                 # Pydantic v2 request/response models
│   ├── requirements.txt
│   │
│   ├── agent/
│   │   ├── orchestrator.py        # THE AGENT LOOP — 7 workflow steps
│   │   ├── state.py               # PatientState + 27-slot registry
│   │   ├── question_selector.py   # EVOI engine
│   │   ├── belief.py              # Bayesian differential + entropy
│   │   ├── contradiction.py       # Contradiction detector and ledger
│   │   ├── escalation.py          # Escalation ladder (5 triggers)
│   │   ├── guardrails.py          # Non-diagnosis enforcement
│   │   └── nlu.py                 # Gemini NLU + regex fallback
│   │
│   ├── tools/
│   │   ├── risk_tool.py           # Deterministic scorer + band bracketing
│   │   ├── patient_db.py          # Vitals reference ranges
│   │   ├── rag_tool.py            # TF-IDF clinical RAG
│   │   └── case_bank.py           # 10 synthetic cases
│   │
│   ├── data/
│   │   ├── knowledge_base.json    # 20 clinical protocol chunks
│   │   └── synthetic_cases.json   # 10 validated synthetic patients
│   │
│   └── evaluate.py                # Benchmark harness
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   │
│   └── src/
│       ├── App.jsx                # Routing + nav
│       ├── index.css
│       ├── main.jsx
│       │
│       ├── pages/
│       │   ├── TriagePage.jsx     # Main interview + all panels
│       │   └── AdminPage.jsx      # Doctor queue dashboard
│       │
│       └── components/
│           ├── RiskGauge.jsx          # Animated SVG semi-circle gauge
│           ├── VitalSigns.jsx         # Vitals input with status colours
│           ├── UncertaintyBand.jsx    # Risk band bracketing visualiser
│           ├── EVOIPanel.jsx          # Ranked question candidates
│           ├── BeliefChart.jsx        # Bayesian differential bars
│           ├── ToolTrace.jsx          # Agent terminal log
│           ├── EscalationBanner.jsx   # Human review alert
│           ├── ContradictionLedger.jsx# Contradiction history
│           ├── CaseSimulator.jsx      # Synthetic case auto-play
│           ├── DecisionTimeline.jsx   # Session timeline
│           └── WhatIfPanel.jsx        # Counterfactual sliders
│
├── docs/
│   └── architecture.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/adaptive-triage-agent.git
cd adaptive-triage-agent
```

### 2. Backend

```bash
cd backend

# create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# configure environment
cp ../.env.example .env
# edit .env — add your GEMINI_API_KEY (optional, agent works without it)

# start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend

# install dependencies
npm install

# configure environment
echo "VITE_API_URL=http://localhost:8000" > .env.local

# start dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

### 4. Get Free Gemini API Key (optional)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Add to `backend/.env` as `GEMINI_API_KEY=...`

> Without a key, the agent uses deterministic regex NLU — still fully functional for demos.

---

## Run Evaluation Benchmark

```bash
cd backend
source venv/bin/activate
python evaluate.py
```

Expected output:
```
================================================================
ADAPTIVE TRIAGE AGENT — EVALUATION REPORT
================================================================
ID   CASE                                TRUTH      AGENT      Q   BASELINE   Q   OK
C01  Silent MI in elderly diabetic       CRITICAL   CRITICAL   5   CRITICAL   18  ✅
C02  Panic attack mimicking ACS          URGENT     URGENT     4   URGENT     18  ✅
C03  Infant with bronchiolitis           CRITICAL   CRITICAL   3   CRITICAL   18  ✅
...
================================================================
Avg questions  ADAPTIVE  4.3  |  BASELINE 18.0  →  76% fewer questions
Under-triage   ADAPTIVE  0.0% |  BASELINE 12.0%   (lower = safer)
Over-triage    ADAPTIVE  10.0%|  BASELINE  4.0%
Exact match    ADAPTIVE 90.0%
================================================================
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + routing outcome list |
| `POST` | `/api/session/start` | Start new triage session |
| `POST` | `/api/session/reply` | Submit patient answer |
| `POST` | `/api/session/vitals` | Submit vital signs (triggers reassessment) |
| `GET` | `/api/session/{id}` | Get full session state |
| `POST` | `/api/session/whatif` | Counterfactual query (no state mutation) |
| `POST` | `/api/session/override` | Clinician override |
| `GET` | `/api/queue` | Doctor priority queue |
| `GET` | `/api/cases` | List synthetic cases |
| `POST` | `/api/cases/{id}/autoplay` | Run agent against synthetic case |
| `GET` | `/api/meta/slots` | Slot registry + routing outcomes + normal ranges |

---

## Deploy

### Backend (Render — free tier)

1. Push to GitHub
2. Go to https://render.com → New Web Service
3. Connect your repo, select `/backend` as root
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add `GEMINI_API_KEY` in environment variables

### Frontend (Vercel — free)

1. Go to https://vercel.com → New Project
2. Import your repo, set framework to **Vite**
3. Set root directory to `frontend`
4. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`
5. Deploy

---

## Safety Principles

| Principle | How it is enforced |
|-----------|-------------------|
| LLM never scores risk | Gemini receives only an extraction prompt; returns structured JSON only |
| Deterministic + auditable | SHA-256 audit hash per session; rule version stamped on every output |
| Under-triage prevention | Ties always resolve to the higher routing tier |
| No diagnosis | `guardrails.py` blocks four blocked intent classes; refusal logged |
| Offline resilience | Regex NLU fallback + TF-IDF RAG; fully functional with no API key |
| Escalation over invention | Five explicit triggers cause escalation; agent never invents confidence |

---

## Team

Built for **IIT Bhubaneswar Hackathon — Problem Statement 2**
Team of 3 · Second Year · B.Tech CSE

---

## License

MIT License — see [LICENSE](LICENSE)

This software is provided for educational and demonstration purposes only.
It is not a medical device and must not be used for real clinical decisions.