import React from 'react';

const TIERS = [
  { code: 'SELF_CARE', lo: 0,  hi: 12,  color: '#16a34a' },
  { code: 'STANDARD',  lo: 12, hi: 28,  color: '#22c55e' },
  { code: 'URGENT',    lo: 28, hi: 45,  color: '#eab308' },
  { code: 'EMERGENCY', lo: 45, hi: 62,  color: '#f97316' },
  { code: 'CRITICAL',  lo: 62, hi: 80,  color: '#ef4444' },
  { code: 'RESUS',     lo: 80, hi: 100, color: '#a855f7' },
];

export default function UncertaintyBand({ risk }) {
  if (!risk) return null;
  const { score_min, score_max, tier_min, tier_max, band_spans_boundary, confidence_pct } = risk;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-white font-semibold text-sm">Risk Band (Uncertainty Interval)</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
          band_spans_boundary ? 'bg-yellow-500/20 text-yellow-300'
                              : 'bg-green-500/20 text-green-300'}`}>
          {band_spans_boundary ? 'AMBIGUOUS — keep asking' : 'RESOLVED — can decide'}
        </span>
      </div>
      <p className="text-[11px] text-gray-500 mb-4">
        Best case {score_min} · Worst case {score_max} · Confidence {confidence_pct}%
      </p>

      <div className="relative h-14">
        {/* tier strip */}
        <div className="absolute inset-x-0 top-4 h-6 flex rounded-lg overflow-hidden">
          {TIERS.map(t => (
            <div key={t.code} style={{ width: `${t.hi - t.lo}%`, background: `${t.color}28` }}
                 className="border-r border-gray-950/60" />
          ))}
        </div>

        {/* the band */}
        <div className="absolute top-4 h-6 rounded-lg transition-all duration-700 ease-out
                        border-2 shadow-lg"
             style={{
               left: `${score_min}%`,
               width: `${Math.max(score_max - score_min, 1.5)}%`,
               background: `linear-gradient(90deg, ${tier_min.color}, ${tier_max.color})`,
               borderColor: '#ffffff55',
             }} />

        {/* endpoint labels */}
        <span className="absolute top-11 text-[10px] text-gray-400"
              style={{ left: `${score_min}%`, transform: 'translateX(-50%)' }}>{score_min}</span>
        <span className="absolute top-11 text-[10px] text-gray-400"
              style={{ left: `${score_max}%`, transform: 'translateX(-50%)' }}>{score_max}</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-800/60 rounded-lg p-2">
          <p className="text-gray-500">If all unknowns benign</p>
          <p className="font-bold" style={{ color: tier_min.color }}>{tier_min.label}</p>
        </div>
        <div className="bg-gray-800/60 rounded-lg p-2">
          <p className="text-gray-500">If all unknowns worst-case</p>
          <p className="font-bold" style={{ color: tier_max.color }}>{tier_max.label}</p>
        </div>
      </div>

      {band_spans_boundary && (
        <p className="mt-3 text-[11px] text-yellow-300/80 bg-yellow-500/10 border
                      border-yellow-500/25 rounded-lg p-2">
          ⓘ The band still crosses a routing boundary, so the agent will keep asking the
          single highest-information question until it resolves — or escalate.
        </p>
      )}
    </div>
  );
}