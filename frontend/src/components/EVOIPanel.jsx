import React from 'react';

export default function EVOIPanel({ candidates = [], chosen }) {
  if (!candidates.length) return null;
  const max = Math.max(...candidates.map(c => c.utility), 0.001);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h3 className="text-white font-semibold text-sm">Question Selection — Value of Information</h3>
      <p className="text-[11px] text-gray-500 mb-4">
        Utility = (band narrowing + entropy reduction + red-flag bonus + P(routing flips)) ÷ ask cost
      </p>

      <div className="space-y-2">
        {candidates.map((c, i) => {
          const isChosen = chosen && c.slot === chosen.slot;
          return (
            <div key={c.slot}
                 className={`rounded-xl p-3 border transition-all ${
                   isChosen ? 'border-emerald-500/60 bg-emerald-500/10'
                            : 'border-gray-800 bg-gray-800/40'}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-gray-500">#{i + 1}</span>
                    <span className="text-xs text-gray-200">{c.question}</span>
                    {c.red_flag && (
                      <span className="text-[9px] bg-red-500/20 text-red-300 px-1.5
                                       py-0.5 rounded">RED FLAG</span>
                    )}
                    {isChosen && (
                      <span className="text-[9px] bg-emerald-500/25 text-emerald-300
                                       px-1.5 py-0.5 rounded font-bold">SELECTED</span>
                    )}
                  </div>
                  <div className="mt-1.5 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500"
                         style={{ width: `${(c.utility / max) * 100}%`,
                                  background: isChosen ? '#10b981' : '#6b7280' }} />
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-gray-500">
                    <span>Δband {c.evoi_band_pts} pts</span>
                    <span>ΔH {c.evoi_entropy_bits} bits</span>
                    <span>P(flip) {(c.p_changes_routing * 100).toFixed(0)}%</span>
                    <span>cost {c.ask_cost_s}s</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${isChosen ? 'text-emerald-400' : 'text-gray-400'}`}>
                    {c.utility.toFixed(2)}
                  </div>
                  <div className="text-[9px] text-gray-600">utility</div>
                </div>
              </div>
              {isChosen && c.why_this_question && (
                <p className="mt-2 text-[11px] text-emerald-200/80 italic">
                  ↳ {c.why_this_question}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}