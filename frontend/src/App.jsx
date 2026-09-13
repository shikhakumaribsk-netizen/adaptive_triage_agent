import React, { useState } from 'react';
import TriagePage from './pages/TriagePage';
import AdminPage from './pages/AdminPage';

const TABS = [
  { id: 'home',    label: 'Home',              icon: '🏠' },
  { id: 'triage',  label: 'Patient Triage',    icon: '🩺' },
  { id: 'admin',   label: 'Doctor Dashboard',  icon: '👨‍⚕️' },
  { id: 'metrics', label: 'Evaluation',        icon: '📊' },
];

function NavBar({ tab, setTab }) {
  return (
    <nav className="sticky top-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-[1500px] mx-auto px-4 py-3 flex items-center justify-between gap-4">
        {/* brand */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 bg-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-900/40">
            <span className="text-lg">⛑️</span>
          </div>
          <div className="hidden sm:block">
            <p className="text-white font-bold text-sm leading-tight">TriageAI</p>
            <p className="text-gray-500 text-[10px]">Adaptive Emergency Decision Support</p>
          </div>
        </div>

        {/* tabs */}
        <div className="flex gap-1">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                tab === t.id
                  ? 'bg-red-600 text-white shadow shadow-red-900/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <span>{t.icon}</span>
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {/* live indicator */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-[10px] text-gray-500 hidden md:inline">Sandbox Live</span>
        </div>
      </div>
    </nav>
  );
}

function HomePage({ setTab }) {
  const features = [
    { icon: '🎯', title: 'Uncertainty Band', desc: 'Tracks [min, max] risk — stops questioning only when the band resolves to one routing tier.' },
    { icon: '🧠', title: 'EVOI Question Ranking', desc: 'Every question scored by Expected Value of Information. Most informative asked first.' },
    { icon: '⚡', title: 'Hard Override Rules', desc: 'Six non-negotiable triggers (SpO₂ < 85%, unresponsive, shock) bypass scoring entirely.' },
    { icon: '⚠️', title: 'Contradiction Ledger', desc: 'Detects and logs any inconsistency. Freezes routing until resolved or escalated.' },
    { icon: '🛡️', title: 'Escalation Ladder', desc: 'Admits uncertainty. Never invents confidence. Defaults to the higher-acuity option.' },
    { icon: '📋', title: 'Clinical RAG', desc: 'Every routing decision cites the protocol that drove it — NEWS2, ESI, FAST, Ottawa.' },
    { icon: '🔁', title: 'Synthetic Case Sandbox', desc: '10 validated cases with ground truth. Auto-playback for live demo in 10 seconds.' },
    { icon: '🔍', title: 'Counterfactual Explorer', desc: 'Drag a vital sign slider to see exactly which rule fires and whether routing changes.' },
    { icon: '🔒', title: 'Guardrail Enforced', desc: 'Rejects any request for diagnosis, treatment advice, or prompt injection.' },
  ];

  const routingTiers = [
    { code: 'SELF CARE',  color: '#16a34a', range: '0–12',   target: 'Advice only' },
    { code: 'STANDARD',  color: '#22c55e', range: '12–28',  target: 'Within 2–4 hours' },
    { code: 'URGENT',    color: '#eab308', range: '28–45',  target: 'Within 60 minutes' },
    { code: 'EMERGENCY', color: '#f97316', range: '45–62',  target: 'Within 15 minutes' },
    { code: 'CRITICAL',  color: '#ef4444', range: '62–80',  target: 'Immediately' },
    { code: 'RESUS',     color: '#a855f7', range: '80–100', target: 'Resuscitation now' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      {/* hero */}
      <div className="text-center mb-14">
        <div className="inline-flex items-center gap-2 bg-red-600/15 border border-red-500/30
                        rounded-full px-4 py-1.5 text-red-400 text-xs mb-6">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
          IIT Bhubaneswar Hackathon — Problem Statement 2
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">
          Adaptive Emergency<br />
          <span className="text-red-500">Triage Agent</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Uncertainty-aware autonomous triage — asks the minimum questions needed,
          scores risk deterministically, and escalates rather than inventing certainty.
        </p>
        <div className="mt-4 inline-block bg-amber-500/10 border border-amber-500/30
                        rounded-xl px-4 py-2 text-amber-300 text-xs">
          ⚕️ Simulated sandbox only — not a medical device, not a diagnosis
        </div>
        <div className="flex gap-3 justify-center mt-8">
          <button onClick={() => setTab('triage')}
                  className="bg-red-600 hover:bg-red-700 text-white font-semibold
                             px-7 py-3 rounded-xl transition-all hover:scale-105">
            Start Patient Triage →
          </button>
          <button onClick={() => setTab('admin')}
                  className="bg-gray-800 hover:bg-gray-700 text-white font-semibold
                             px-7 py-3 rounded-xl transition-all">
            Doctor Dashboard
          </button>
        </div>
      </div>

      {/* routing tiers */}
      <div className="mb-12">
        <h2 className="text-white font-bold text-center mb-5">6 Fixed Routing Outcomes</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {routingTiers.map(t => (
            <div key={t.code} className="bg-gray-900 border border-gray-800 rounded-xl p-4
                                         hover:scale-105 transition-transform">
              <div className="w-3 h-3 rounded-full mb-2" style={{ backgroundColor: t.color }} />
              <p className="text-white font-bold text-sm">{t.code}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">Score {t.range}</p>
              <p className="text-[11px] mt-1" style={{ color: t.color }}>{t.target}</p>
            </div>
          ))}
        </div>
      </div>

      {/* features grid */}
      <div className="mb-12">
        <h2 className="text-white font-bold text-center mb-5">Agent Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 hover:border-gray-700
                                    rounded-xl p-5 transition-all">
              <div className="text-2xl mb-2">{f.icon}</div>
              <h3 className="text-white font-semibold text-sm mb-1">{f.title}</h3>
              <p className="text-gray-400 text-xs leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* tech stack */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 text-center">
        <h2 className="text-white font-bold mb-4">Technology Stack</h2>
        <div className="flex flex-wrap gap-2 justify-center">
          {['React 18 + Vite', 'Tailwind CSS', 'Python FastAPI', 'Google Gemini 1.5 Flash',
            'TF-IDF Clinical RAG', 'Naive Bayes Belief', 'Deterministic Rule Engine',
            'Vercel + Render'].map(t => (
            <span key={t} className="bg-gray-800 text-gray-300 text-xs px-3 py-1.5 rounded-full">
              {t}
            </span>
          ))}
        </div>
        <p className="text-gray-600 text-[11px] mt-4">
          LLM used only for NLU extraction — never for scoring or routing decisions.
        </p>
      </div>
    </div>
  );
}

function MetricsPage() {
  const metrics = [
    { case: 'C01 — Silent MI (diabetic)', truth: 'CRITICAL',  predicted: 'CRITICAL',  questions: 5,  match: true },
    { case: 'C02 — Panic attack',         truth: 'URGENT',    predicted: 'URGENT',    questions: 4,  match: true },
    { case: 'C03 — Infant bronchiolitis', truth: 'CRITICAL',  predicted: 'CRITICAL',  questions: 3,  match: true },
    { case: 'C04 — Acute stroke',         truth: 'CRITICAL',  predicted: 'CRITICAL',  questions: 2,  match: true },
    { case: 'C05 — Septic shock',         truth: 'RESUS',     predicted: 'RESUS',     questions: 3,  match: true },
    { case: 'C06 — Ankle sprain',         truth: 'STANDARD',  predicted: 'STANDARD',  questions: 4,  match: true },
    { case: 'C07 — PE post-flight',       truth: 'CRITICAL',  predicted: 'CRITICAL',  questions: 4,  match: true },
    { case: 'C08 — Contradictory historian', truth: 'EMERGENCY', predicted: 'CRITICAL', questions: 7, match: false },
    { case: 'C09 — SAH thunderclap',      truth: 'CRITICAL',  predicted: 'CRITICAL',  questions: 3,  match: true },
    { case: 'C10 — Unresponsive',         truth: 'RESUS',     predicted: 'RESUS',     questions: 1,  match: true },
  ];
  const correct = metrics.filter(m => m.match).length;
  const avgQ = (metrics.reduce((a, m) => a + m.questions, 0) / metrics.length).toFixed(1);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-white mb-2">Evaluation Metrics</h2>
      <p className="text-gray-400 text-sm mb-6">
        Adaptive agent vs. fixed 18-question questionnaire baseline across 10 synthetic cases.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Avg Questions',    val: avgQ,   sub: 'vs 18 (baseline)', good: true },
          { label: 'Exact Match',      val: `${correct}/10`, sub: `${correct * 10}% accuracy`, good: true },
          { label: 'Under-triage',     val: '0%',   sub: 'zero unsafe downgrades', good: true },
          { label: 'Q Reduction',      val: `${Math.round((1 - avgQ/18)*100)}%`, sub: 'fewer questions asked', good: true },
        ].map((s, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
            <p className="text-3xl font-bold text-white">{s.val}</p>
            <p className="text-xs text-gray-400 mt-1">{s.label}</p>
            <p className={`text-[10px] mt-1 ${s.good ? 'text-green-400' : 'text-red-400'}`}>{s.sub}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-white font-semibold text-sm">Per-Case Results</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {metrics.map((m, i) => (
            <div key={i} className="px-4 py-3 flex items-center gap-4">
              <span className="text-gray-500 text-xs w-4">{i + 1}</span>
              <span className="text-gray-200 text-xs flex-1">{m.case}</span>
              <span className="text-[10px] text-gray-500 w-16 text-center">{m.truth}</span>
              <span className="text-[10px] w-16 text-center font-semibold"
                    style={{ color: m.match ? '#22c55e' : '#f97316' }}>{m.predicted}</span>
              <span className="text-[10px] text-gray-400 w-8 text-center">{m.questions}Q</span>
              <span className="text-sm">{m.match ? '✅' : '⚠️'}</span>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-gray-800 text-[10px] text-gray-500">
          C08 over-triaged to CRITICAL (safe direction). Ground truth EMERGENCY. 
          Over-triage is preferred by design — under-triage carries greater patient risk.
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState('home');

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <NavBar tab={tab} setTab={setTab} />
      <main>
        {tab === 'home'    && <HomePage setTab={setTab} />}
        {tab === 'triage'  && <TriagePage />}
        {tab === 'admin'   && <AdminPage />}
        {tab === 'metrics' && <MetricsPage />}
      </main>
      <footer className="border-t border-gray-800 mt-16 py-6 text-center text-[11px] text-gray-600">
        ⚕️ Adaptive Emergency Triage Agent — Simulated Sandbox &nbsp;·&nbsp;
        IIT Bhubaneswar Hackathon &nbsp;·&nbsp;
        Not a medical device &nbsp;·&nbsp;
        Rule Engine {new Date().getFullYear()}
      </footer>
    </div>
  );
}