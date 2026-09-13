import React from 'react';

const C = { acs:'#ef4444', pe:'#f97316', sepsis:'#eab308', stroke:'#a855f7',
            resp:'#06b6d4', abdo:'#8b5cf6', benign:'#22c55e' };

export default function BeliefChart({ belief }) {
  if (!belief) return null;
  const u = belief.normalised_uncertainty;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-white font-semibold text-sm">Differential Considerations</h3>
        <span className="text-[10px] text-gray-400">
          entropy {belief.entropy_bits} bits
        </span>
      </div>
      <p className="text-[10px] text-amber-400/80 mb-4">
        ⚕️ For clinician review only — this is NOT a diagnosis.
      </p>

      {/* uncertainty meter */}
      <div className="mb-4">
        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
          <span>Certainty</span><span>Uncertainty {(u * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-700"
               style={{ width: `${u * 100}%`,
                        background: u > .7 ? '#ef4444' : u > .45 ? '#eab308' : '#22c55e' }} />
        </div>
      </div>

      <div className="space-y-2">
        {belief.distribution.map(d => (
          <div key={d.key}>
            <div className="flex justify-between text-[11px] mb-0.5">
              <span className="text-gray-300">{d.label}</span>
              <span className="text-gray-400 font-mono">{(d.p * 100).toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700"
                   style={{ width: `${d.p * 100}%`, background: C[d.key] }} />
            </div>
          </div>
        ))}
      </div>

      {belief.evidence_used?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {belief.evidence_used.map((e, i) => (
            <span key={i} className="text-[9px] bg-gray-800 text-gray-400 px-1.5 py-0.5
                                     rounded font-mono">{e}</span>
          ))}
        </div>
      )}
    </div>
  );
}