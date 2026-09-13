import React from 'react';

const SEV = { HIGH: 'border-red-500/50 bg-red-500/10 text-red-300',
              MEDIUM: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-300',
              LOW: 'border-gray-600 bg-gray-800 text-gray-300' };

export default function ContradictionLedger({ items = [] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
      <h3 className="text-white font-semibold text-sm mb-3">
        Contradiction Ledger {items.length > 0 && (
          <span className="ml-1 text-[10px] bg-red-500/25 text-red-300 px-2 py-0.5 rounded-full">
            {items.length}
          </span>)}
      </h3>
      {items.length === 0 ? (
        <p className="text-[11px] text-gray-600">No inconsistencies detected in patient history.</p>
      ) : items.map(c => (
        <div key={c.id} className={`border rounded-xl p-3 mb-2 ${SEV[c.severity]}`}>
          <div className="flex justify-between text-[10px] font-mono opacity-70">
            <span>{c.type}</span><span>{c.ts}</span>
          </div>
          <p className="text-xs mt-1">{c.message}</p>
          <div className="mt-1.5 flex gap-2 text-[10px]">
            <span className="opacity-70">severity: {c.severity}</span>
            <span className="opacity-70">status: {c.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}