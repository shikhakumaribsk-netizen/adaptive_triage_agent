import React from 'react';

export default function EscalationBanner({ routing, escalation, contradictions = [] }) {
  if (!routing?.human_review_required) return null;

  return (
    <div className="rounded-2xl border-2 border-fuchsia-500/60 bg-fuchsia-500/10 p-5 animate-pulse-slow">
      <div className="flex items-start gap-3">
        <div className="text-3xl">🧑‍⚕️</div>
        <div className="flex-1">
          <h3 className="text-fuchsia-300 font-bold text-lg">HUMAN CLINICIAN REVIEW REQUIRED</h3>
          <p className="text-fuchsia-100/80 text-sm mt-1">
            The agent could not resolve the remaining uncertainty safely. Rather than asserting a
            confident answer, it escalated and defaulted to the higher-acuity option.
          </p>

          <div className="mt-3 space-y-1.5">
            {escalation?.reasons?.map((r, i) => (
              <div key={i} className="flex gap-2 text-xs text-fuchsia-200/90">
                <span className="text-fuchsia-400">▸</span><span>{r}</span>
              </div>
            ))}
          </div>

          {escalation?.red_flag_unknowns?.length > 0 && (
            <div className="mt-3 bg-black/30 rounded-lg p-2">
              <p className="text-[11px] text-fuchsia-300 font-semibold mb-1">
                Unanswerable red-flag items (worst case assumed):
              </p>
              <div className="flex flex-wrap gap-1">
                {escalation.red_flag_unknowns.map(s => (
                  <span key={s} className="text-[10px] bg-fuchsia-500/20 text-fuchsia-200
                                           px-2 py-0.5 rounded-full">{s}</span>
                ))}
              </div>
            </div>
          )}

          {contradictions.filter(c => c.status === 'OPEN').length > 0 && (
            <p className="mt-3 text-xs text-yellow-300">
              ⚠ {contradictions.filter(c => c.status === 'OPEN').length} unresolved contradiction(s)
              in the patient history.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}