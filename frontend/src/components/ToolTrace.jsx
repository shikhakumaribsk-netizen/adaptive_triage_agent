import React, { useEffect, useRef } from 'react';

const COLORS = {
  'risk_engine': 'text-orange-400', 'belief_engine': 'text-purple-400',
  'nlu': 'text-cyan-400', 'clinical_rag': 'text-blue-400',
  'contradiction': 'text-yellow-400', 'guardrails': 'text-red-400',
  'patient_db': 'text-green-400', 'question_selector': 'text-emerald-400',
  'vitals_monitor': 'text-pink-400', 'clinician': 'text-fuchsia-400',
};

export default function ToolTrace({ trace = [] }) {
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [trace]);

  return (
    <div className="bg-black border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-900 border-b border-gray-800">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
        <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
        <span className="ml-2 text-[11px] text-gray-400 font-mono">agent://tool-call-trace</span>
      </div>
      <div className="h-52 overflow-y-auto p-3 font-mono text-[11px] leading-relaxed">
        {trace.length === 0 && <p className="text-gray-600">awaiting agent activity…</p>}
        {trace.map((t, i) => {
          const ns = t.tool.split('.')[0];
          return (
            <div key={i} className="mb-0.5">
              <span className="text-gray-600">[{t.ts}]</span>{' '}
              <span className={COLORS[ns] || 'text-gray-300'}>{t.tool}</span>
              <span className="text-gray-600">(</span>
              <span className="text-gray-500">{t.args}</span>
              <span className="text-gray-600">)</span>
              <span className="text-gray-600"> → </span>
              <span className="text-gray-300">{t.result}</span>
              {t.ms > 0 && <span className="text-gray-700"> {t.ms}ms</span>}
            </div>
          );
        })}
        <div ref={end} />
      </div>
    </div>
  );
}