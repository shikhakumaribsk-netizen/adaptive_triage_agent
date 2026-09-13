import React, { useState, useEffect } from 'react';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CaseSimulator({ onFrame, onDone }) {
  const [cases, setCases] = useState([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/cases`).then(r => r.json()).then(d => setCases(d.cases));
  }, []);

  const play = async (id) => {
    setRunning(true); setResult(null);
    const r = await fetch(`${API}/api/cases/${id}/autoplay`, { method: 'POST' });
    const d = await r.json();
    // replay frames like a live interview
    for (const f of d.frames) {
      onFrame?.(f);
      await new Promise(res => setTimeout(res, 900));
    }
    setResult(d); onDone?.(d); setRunning(false);
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h3 className="text-white font-semibold text-sm mb-1">Synthetic Case Sandbox</h3>
      <p className="text-[11px] text-gray-500 mb-4">
        Auto-run the agent against a validated synthetic patient and compare with ground truth.
      </p>

      <div className="grid gap-2 max-h-64 overflow-y-auto">
        {cases.map(c => (
          <button key={c.id} disabled={running} onClick={() => play(c.id)}
                  className="text-left bg-gray-800/60 hover:bg-gray-800 disabled:opacity-40
                             border border-gray-700 hover:border-emerald-500/50
                             rounded-xl p-3 transition-all">
            <div className="flex justify-between items-center">
              <span className="text-xs text-white font-medium">{c.label}</span>
              <span className="text-[9px] bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">
                truth: {c.ground_truth}
              </span>
            </div>
            <p className="text-[11px] text-gray-500 mt-1 italic">"{c.opening}"</p>
          </button>
        ))}
      </div>

      {running && <p className="mt-3 text-xs text-emerald-400 animate-pulse">
        ▶ Agent interviewing patient…</p>}

      {result && (
        <div className={`mt-4 rounded-xl p-3 border ${
          result.match ? 'border-emerald-500/50 bg-emerald-500/10'
                       : 'border-yellow-500/50 bg-yellow-500/10'}`}>
          <p className="text-sm font-bold text-white">
            {result.match ? '✅ Correct routing' : '⚠️ Routing differs from ground truth'}
          </p>
          <p className="text-xs text-gray-300 mt-1">
            Predicted <b>{result.predicted}</b> · Truth <b>{result.ground_truth}</b> ·
            Questions asked <b>{result.questions_asked}</b>
          </p>
        </div>
      )}
    </div>
  );
}