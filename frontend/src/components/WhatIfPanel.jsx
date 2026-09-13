import React, { useState } from 'react';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const KNOBS = [
  { slot: 'spo2', label: 'SpO₂ (%)', min: 75, max: 100, def: 97, step: 1 },
  { slot: 'systolic_bp', label: 'Systolic BP', min: 60, max: 200, def: 120, step: 2 },
  { slot: 'heart_rate', label: 'Heart Rate', min: 30, max: 180, def: 80, step: 2 },
  { slot: 'resp_rate', label: 'Resp Rate', min: 6, max: 45, def: 16, step: 1 },
  { slot: 'temperature', label: 'Temp (°C)', min: 33, max: 42, def: 37, step: 0.1 },
];

export default function WhatIfPanel({ sessionId }) {
  const [state, setState] = useState({});
  const [res, setRes] = useState(null);

  const probe = async (slot, value) => {
    setState(s => ({ ...s, [slot]: value }));
    const r = await fetch(`${API}/api/session/whatif`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, slot, value: Number(value) }),
    });
    setRes(await r.json());
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h3 className="text-white font-semibold text-sm mb-1">Counterfactual Explorer</h3>
      <p className="text-[11px] text-gray-500 mb-4">
        Drag a vital to see exactly which rule fires and whether routing changes.
      </p>

      {KNOBS.map(k => (
        <div key={k.slot} className="mb-3">
          <div className="flex justify-between text-[11px] text-gray-400 mb-1">
            <span>{k.label}</span>
            <span className="font-mono text-white">{state[k.slot] ?? k.def}</span>
          </div>
          <input type="range" min={k.min} max={k.max} step={k.step}
                 value={state[k.slot] ?? k.def}
                 onChange={e => probe(k.slot, e.target.value)}
                 className="w-full accent-red-500" />
        </div>
      ))}

      {res && (
        <div className={`mt-4 rounded-xl p-3 border ${
          res.routing_changed ? 'border-red-500/50 bg-red-500/10'
                              : 'border-gray-700 bg-gray-800/50'}`}>
          <p className="text-xs text-white">
            {res.routing_changed ? '⚡ Routing WOULD change: ' : 'No routing change: '}
            <b>{res.before.tier}</b> → <b>{res.after.tier}</b>
          </p>
          <p className="text-[10px] text-gray-400 mt-1">
            band [{res.before.band.join('–')}] → [{res.after.band.join('–')}]
          </p>
          {res.newly_fired_rules?.map((r, i) => (
            <p key={i} className="text-[10px] text-orange-300 mt-1 font-mono">
              + {r.rule} ({r.points} pts) — {r.citation}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}