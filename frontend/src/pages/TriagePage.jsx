import React, { useState, useRef, useEffect } from 'react';
import UncertaintyBand from '../components/UncertaintyBand';
import EVOIPanel from '../components/EVOIPanel';
import BeliefChart from '../components/BeliefChart';
import ToolTrace from '../components/ToolTrace';
import EscalationBanner from '../components/EscalationBanner';
import ContradictionLedger from '../components/ContradictionLedger';
import CaseSimulator from '../components/CaseSimulator';
import WhatIfPanel from '../components/WhatIfPanel';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function TriagePage() {
  const [sid, setSid] = useState(null);
  const [name, setName] = useState('');
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [q, setQ] = useState(null);
  const [data, setData] = useState({});
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const end = useRef(null);

  useEffect(() => end.current?.scrollIntoView({ behavior: 'smooth' }), [msgs]);

  const ingest = (d, userText) => {
    setData(d);
    setMsgs(m => {
      const next = [...m];
      if (userText) next.push({ role: 'patient', text: userText });
      if (d.refusal) next.push({ role: 'guard', text: d.message });
      if (d.contradiction_alert)
        d.contradiction_alert.forEach(c =>
          next.push({ role: 'alert', text: `⚠ ${c.message}` }));
      if (d.next_question) next.push({ role: 'agent', text: d.next_question.question,
                                       why: d.next_question.why_this_question });
      if (d.phase === 'DECIDED')
        next.push({ role: 'decision', text: `ROUTING: ${d.routing.label} — ${d.routing.target}`,
                    why: d.routing.explanation });
      return next;
    });
    setQ(d.next_question || null);
  };

  const start = async () => {
    setBusy(true);
    const r = await fetch(`${API}/api/session/start`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_name: name || 'Anonymous' }),
    });
    const d = await r.json();
    setSid(d.session_id); ingest(d); setBusy(false);
  };

  const send = async (text = input) => {
    if (!text.trim() || !sid) return;
    setBusy(true); setInput('');
    const r = await fetch(`${API}/api/session/reply`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sid, text, answered_slot: q?.slot }),
    });
    ingest(await r.json(), text); setBusy(false);
  };

  const mic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert('Use Chrome for voice input');
    const rec = new SR(); rec.lang = 'en-IN'; rec.interimResults = false;
    rec.onstart = () => setListening(true);
    rec.onend = () => setListening(false);
    rec.onresult = e => send(e.results[0][0].transcript);
    rec.start();
  };

  const BUBBLE = {
    patient: 'bg-red-600 text-white ml-auto',
    agent: 'bg-gray-800 text-gray-100',
    alert: 'bg-yellow-500/15 text-yellow-200 border border-yellow-500/40',
    guard: 'bg-fuchsia-500/15 text-fuchsia-200 border border-fuchsia-500/40',
    decision: 'bg-emerald-500/15 text-emerald-200 border border-emerald-500/40 font-semibold',
  };

  return (
    <div className="max-w-[1500px] mx-auto px-4 py-6">
      {/* sticky guardrail */}
      <div className="sticky top-0 z-40 mb-4 bg-amber-500/10 border border-amber-500/40
                      rounded-xl px-4 py-2 text-[11px] text-amber-300 backdrop-blur">
        ⚕️ SIMULATED DECISION SUPPORT — determines routing urgency only. Not a diagnosis,
        not treatment advice. Real emergency → call 108 / 112.
      </div>

      {!sid ? (
        <div className="max-w-md mx-auto bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h2 className="text-xl font-bold text-white mb-4">Begin Triage Assessment</h2>
          <input value={name} onChange={e => setName(e.target.value)}
                 onKeyDown={e => e.key === 'Enter' && start()}
                 placeholder="Patient name"
                 className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3
                            text-white focus:border-red-500 outline-none" />
          <button onClick={start} disabled={busy}
                  className="mt-3 w-full bg-red-600 hover:bg-red-700 text-white py-3
                             rounded-xl font-semibold">
            {busy ? 'Starting…' : 'Start Adaptive Interview →'}
          </button>
          <div className="mt-6"><CaseSimulator onDone={d => setSid(d.session_id)} /></div>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-4">

          {/* LEFT: interview */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl flex flex-col h-[520px]">
              <div className="px-4 py-3 border-b border-gray-800 flex justify-between items-center">
                <span className="text-white text-sm font-medium">Adaptive Interview</span>
                <span className="text-[10px] text-gray-400">
                  Q {data.questions_asked ?? 0}/{data.question_budget ?? 9} ·
                  state {data.completeness ?? 0}% complete
                </span>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {msgs.map((m, i) => (
                  <div key={i} className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm
                                           ${BUBBLE[m.role]} ${m.role === 'patient' ? 'ml-auto' : ''}`}>
                    <p>{m.text}</p>
                    {m.why && <p className="text-[10px] opacity-60 mt-1 italic">↳ {m.why}</p>}
                  </div>
                ))}
                {busy && <p className="text-xs text-gray-500 animate-pulse">agent thinking…</p>}
                <div ref={end} />
              </div>
              <div className="p-3 border-t border-gray-800 flex gap-2">
                <button onClick={mic}
                        className={`px-3 rounded-xl ${listening ? 'bg-red-600 animate-pulse' : 'bg-gray-800'}`}>
                  🎤</button>
                <input value={input} onChange={e => setInput(e.target.value)}
                       onKeyDown={e => e.key === 'Enter' && send()}
                       placeholder={q?.dtype === 'bool' ? 'Yes / No / I don\'t know' : 'Type your answer…'}
                       className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2
                                  text-sm text-white outline-none focus:border-red-500" />
                <button onClick={() => send()} disabled={busy}
                        className="bg-red-600 px-4 rounded-xl text-sm font-medium">Send</button>
              </div>
              {q?.dtype === 'bool' && (
                <div className="px-3 pb-3 flex gap-2">
                  {['Yes', 'No', "I don't know"].map(o => (
                    <button key={o} onClick={() => send(o)}
                            className="flex-1 bg-gray-800 hover:bg-gray-700 text-xs
                                       text-gray-200 py-2 rounded-lg">{o}</button>
                  ))}
                </div>
              )}
            </div>
            <ToolTrace trace={data.tool_trace} />
          </div>

          {/* MIDDLE: reasoning */}
          <div className="col-span-12 lg:col-span-4 space-y-4">
            <UncertaintyBand risk={data.risk} />
            <EVOIPanel candidates={data.question_candidates} chosen={data.next_question} />
          </div>

          {/* RIGHT: belief + safety */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <EscalationBanner routing={data.routing} escalation={data.escalation}
                              contradictions={data.contradiction_alert} />
            <BeliefChart belief={data.belief} />
            <ContradictionLedger items={data.contradiction_alert || []} />
            {data.citations?.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                <h3 className="text-white text-sm font-semibold mb-2">Protocol Basis</h3>
                {data.citations.map(c => (
                  <div key={c.id} className="mb-2 bg-blue-500/10 border border-blue-500/25
                                             rounded-lg p-2">
                    <p className="text-[10px] text-blue-300 font-semibold">{c.source}</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">{c.snippet}</p>
                  </div>
                ))}
              </div>
            )}
            {data.handoff_sbar && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
                <h3 className="text-white text-sm font-semibold mb-2">SBAR Handoff</h3>
                {Object.entries(data.handoff_sbar).map(([k, v]) => (
                  <p key={k} className="text-[11px] text-gray-300 mb-1">
                    <b className="text-gray-500">{k}:</b> {v}</p>
                ))}
                <p className="text-[9px] text-gray-600 mt-2 font-mono">
                  audit {data.audit_hash} · {data.rule_version}
                </p>
              </div>
            )}
            <WhatIfPanel sessionId={sid} />
          </div>
        </div>
      )}
    </div>
  );
}