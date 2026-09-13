import React, { useState, useEffect, useCallback } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TIER_COLORS = {
  SELF_CARE:  '#16a34a',
  STANDARD:   '#22c55e',
  URGENT:     '#eab308',
  EMERGENCY:  '#f97316',
  CRITICAL:   '#ef4444',
  RESUS:      '#a855f7',
};

const TIER_ORDER = ['RESUS', 'CRITICAL', 'EMERGENCY', 'URGENT', 'STANDARD', 'SELF_CARE'];

// ── Sub-components ────────────────────────────────────────────

function StatCard({ label, value, sub, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 text-center">
      <p className="text-3xl font-bold" style={{ color: color || '#f9fafb' }}>{value}</p>
      <p className="text-xs text-gray-400 mt-1">{label}</p>
      {sub && <p className="text-[10px] text-gray-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function QueueRow({ patient, rank, onClick }) {
  const color = TIER_COLORS[patient.code] || '#6b7280';
  const bandWidth = patient.score_max - patient.score_min;

  return (
    <div
      onClick={() => onClick(patient)}
      className="px-5 py-4 flex items-center gap-4 hover:bg-gray-800/50
                 cursor-pointer transition-all group animate-fade-in"
    >
      {/* rank */}
      <div className="w-7 text-center text-gray-600 font-mono text-sm shrink-0">
        #{rank}
      </div>

      {/* color dot */}
      <div
        className="w-3 h-3 rounded-full shrink-0 shadow"
        style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}80` }}
      />

      {/* patient info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-white text-sm font-medium truncate">{patient.patient_name}</p>
          {patient.human_review && (
            <span className="text-[9px] bg-fuchsia-500/20 text-fuchsia-300
                             border border-fuchsia-500/40 px-1.5 py-0.5 rounded-full shrink-0">
              REVIEW NEEDED
            </span>
          )}
        </div>
        <p className="text-gray-500 text-[11px] truncate mt-0.5">
          {patient.top_consideration}
        </p>
      </div>

      {/* band */}
      <div className="hidden md:block w-28">
        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
          <span>{patient.score_min}</span>
          <span>{patient.score_max}</span>
        </div>
        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              marginLeft: `${patient.score_min}%`,
              width: `${Math.max(bandWidth, 2)}%`,
              background: `linear-gradient(90deg, ${color}80, ${color})`,
            }}
          />
        </div>
        <p className="text-[9px] text-gray-600 text-center mt-0.5">
          {patient.confidence}% conf.
        </p>
      </div>

      {/* routing badge */}
      <div
        className="text-xs font-bold px-3 py-1 rounded-full border shrink-0"
        style={{
          color,
          borderColor: `${color}50`,
          backgroundColor: `${color}15`,
        }}
      >
        {patient.code}
      </div>

      {/* target */}
      <div className="hidden lg:block text-right shrink-0 w-36">
        <p className="text-[11px] text-gray-300">{patient.target}</p>
        <p className="text-[10px] text-gray-600">{patient.questions_asked}Q asked</p>
      </div>

      {/* arrow */}
      <div className="text-gray-700 group-hover:text-gray-400 transition-colors text-sm">
        ›
      </div>
    </div>
  );
}

function PatientModal({ patient, onClose, onOverride }) {
  const [overrideCode, setOverrideCode] = useState('');
  const [reason, setReason] = useState('');
  const [clinicianId, setClinicianId] = useState('');
  const [overriding, setOverriding] = useState(false);
  const [overrideDone, setOverrideDone] = useState(false);

  if (!patient) return null;
  const color = TIER_COLORS[patient.code] || '#6b7280';

  const handleOverride = async () => {
    if (!overrideCode || !reason.trim() || !clinicianId.trim()) return;
    setOverriding(true);
    try {
      await fetch(`${API}/api/session/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: patient.session_id,
          new_routing_code: overrideCode,
          clinician_id: clinicianId,
          reason,
        }),
      });
      setOverrideDone(true);
      if (onOverride) onOverride();
    } catch (e) {
      console.error(e);
    }
    setOverriding(false);
  };

  return (
    <div
      className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center
                 justify-center z-50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-lg
                   max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <h3 className="text-white font-bold">{patient.patient_name}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white text-xl transition-colors w-8 h-8
                       flex items-center justify-center rounded-lg hover:bg-gray-800"
          >
            ×
          </button>
        </div>

        {/* body */}
        <div className="p-5 space-y-4">

          {/* routing info */}
          <div
            className="rounded-xl p-4 border"
            style={{ borderColor: `${color}40`, backgroundColor: `${color}10` }}
          >
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs text-gray-400 mb-1">Current Routing</p>
                <p className="text-lg font-bold" style={{ color }}>{patient.label}</p>
                <p className="text-xs text-gray-300 mt-1">{patient.target}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400 mb-1">Risk Band</p>
                <p className="text-lg font-mono font-bold text-white">
                  {patient.score_min}–{patient.score_max}
                </p>
                <p className="text-[10px] text-gray-500">{patient.confidence}% confidence</p>
              </div>
            </div>
          </div>

          {/* top consideration */}
          <div className="bg-gray-800/50 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 mb-1">Top Differential Consideration</p>
            <p className="text-sm text-gray-200">{patient.top_consideration}</p>
            <p className="text-[10px] text-gray-600 mt-2">
              For clinician review only — not a diagnosis.
            </p>
          </div>

          {/* session info */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {[
              ['Questions Asked', `${patient.questions_asked}`],
              ['Human Review', patient.human_review ? '⚠ Required' : '✓ Not needed'],
              ['Session ID', patient.session_id?.slice(0, 8) + '…'],
              ['Arrived', new Date(patient.created_at).toLocaleTimeString()],
            ].map(([k, v]) => (
              <div key={k} className="bg-gray-800/40 rounded-lg p-3">
                <p className="text-gray-500">{k}</p>
                <p className="text-white font-medium mt-0.5">{v}</p>
              </div>
            ))}
          </div>

          {/* clinician override */}
          {!overrideDone ? (
            <div className="border border-gray-700 rounded-xl p-4">
              <h4 className="text-white text-sm font-semibold mb-3">
                👨‍⚕️ Clinician Override
              </h4>
              <div className="space-y-2">
                <input
                  placeholder="Clinician ID / Name"
                  value={clinicianId}
                  onChange={e => setClinicianId(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3
                             py-2 text-xs text-white placeholder-gray-600 focus:outline-none
                             focus:border-red-500"
                />
                <select
                  value={overrideCode}
                  onChange={e => setOverrideCode(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3
                             py-2 text-xs text-white focus:outline-none focus:border-red-500"
                >
                  <option value="">Select new routing tier…</option>
                  {TIER_ORDER.map(code => (
                    <option key={code} value={code}>{code}</option>
                  ))}
                </select>
                <textarea
                  placeholder="Clinical reason for override (required)"
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  rows={2}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3
                             py-2 text-xs text-white placeholder-gray-600 focus:outline-none
                             focus:border-red-500 resize-none"
                />
                <button
                  onClick={handleOverride}
                  disabled={overriding || !overrideCode || !reason.trim() || !clinicianId.trim()}
                  className="w-full bg-red-600 hover:bg-red-700 disabled:opacity-40
                             text-white text-xs font-semibold py-2 rounded-lg transition-all"
                >
                  {overriding ? 'Submitting…' : 'Submit Override'}
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-green-500/10 border border-green-500/40 rounded-xl p-4 text-center">
              <p className="text-green-300 font-semibold text-sm">✅ Override recorded</p>
              <p className="text-gray-400 text-xs mt-1">Queue will refresh automatically.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main AdminPage ────────────────────────────────────────────

export default function AdminPage() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [filterTier, setFilterTier] = useState('ALL');
  const [searchText, setSearchText] = useState('');

  const fetchQueue = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/queue`);
      if (!res.ok) throw new Error('Network error');
      const data = await res.json();
      setQueue(data.queue || []);
      setLastRefresh(new Date());
    } catch (e) {
      console.error('Queue fetch error:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  // Derived stats
  const stats = {
    total: queue.length,
    needsReview: queue.filter(q => q.human_review).length,
    critical: queue.filter(q => ['RESUS', 'CRITICAL'].includes(q.code)).length,
    avgConfidence: queue.length
      ? Math.round(queue.reduce((a, q) => a + (q.confidence || 0), 0) / queue.length)
      : 0,
  };

  // Filtered + searched queue
  const displayed = queue
    .filter(p => filterTier === 'ALL' || p.code === filterTier)
    .filter(p => !searchText || p.patient_name.toLowerCase().includes(searchText.toLowerCase()));

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">

      {/* page header */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-white">Doctor Dashboard</h2>
          <p className="text-gray-400 text-sm mt-0.5">
            Real-time priority queue — sorted by acuity
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <p className="text-[11px] text-gray-600">
              Last updated {lastRefresh.toLocaleTimeString()}
            </p>
          )}
          <div className="flex items-center gap-2 bg-gray-900 border border-gray-800
                          rounded-xl px-3 py-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-400">Auto-refresh 5s</span>
          </div>
          <button
            onClick={fetchQueue}
            className="bg-gray-800 hover:bg-gray-700 text-white text-xs font-medium
                       px-3 py-2 rounded-xl transition-all"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Patients"      value={stats.total}         color="#f9fafb" />
        <StatCard label="Need Human Review"   value={stats.needsReview}   color="#a855f7" sub="escalated" />
        <StatCard label="Critical / RESUS"    value={stats.critical}      color="#ef4444" sub="immediate attention" />
        <StatCard label="Avg Confidence"      value={`${stats.avgConfidence}%`} color="#22c55e" sub="routing certainty" />
      </div>

      {/* per-tier counts */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-6">
        {TIER_ORDER.map(code => {
          const count = queue.filter(p => p.code === code).length;
          const color = TIER_COLORS[code];
          const active = filterTier === code;
          return (
            <button
              key={code}
              onClick={() => setFilterTier(active ? 'ALL' : code)}
              className="rounded-xl p-3 text-center border transition-all hover:scale-105"
              style={{
                borderColor: active ? color : `${color}30`,
                backgroundColor: active ? `${color}20` : 'transparent',
              }}
            >
              <p className="text-xl font-bold" style={{ color }}>{count}</p>
              <p className="text-[9px] text-gray-500 mt-0.5">{code}</p>
            </button>
          );
        })}
      </div>

      {/* search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by patient name…"
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          className="w-full md:w-72 bg-gray-900 border border-gray-800 rounded-xl
                     px-4 py-2 text-sm text-white placeholder-gray-600
                     focus:outline-none focus:border-red-500"
        />
      </div>

      {/* queue table */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-white font-semibold text-sm">
            Patient Queue
            <span className="ml-2 text-gray-500 font-normal">({displayed.length} shown)</span>
          </h3>
          {filterTier !== 'ALL' && (
            <button
              onClick={() => setFilterTier('ALL')}
              className="text-[11px] text-gray-400 hover:text-white"
            >
              ✕ Clear filter
            </button>
          )}
        </div>

        {loading ? (
          <div className="py-16 text-center">
            <div className="inline-block w-8 h-8 border-2 border-gray-700 border-t-red-500
                            rounded-full animate-spin mb-3" />
            <p className="text-gray-500 text-sm">Loading queue…</p>
          </div>
        ) : displayed.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-4xl mb-3">🏥</p>
            <p className="text-gray-400 text-sm">
              {queue.length === 0
                ? 'Queue is empty. Complete a triage session to see patients here.'
                : 'No patients match the current filter.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800/60">
            {displayed.map((patient, i) => (
              <QueueRow
                key={patient.session_id}
                patient={patient}
                rank={i + 1}
                onClick={setSelected}
              />
            ))}
          </div>
        )}

        {displayed.length > 0 && (
          <div className="px-5 py-3 border-t border-gray-800 text-[10px] text-gray-600">
            Sorted by acuity tier then arrival time · Click a row for details and override
          </div>
        )}
      </div>

      {/* disclaimer */}
      <div className="mt-6 bg-amber-500/10 border border-amber-500/30 rounded-xl
                      px-4 py-3 text-[11px] text-amber-300 text-center">
        ⚕️ This dashboard is simulated decision support only.
        All routing decisions require confirmation by a qualified clinician.
      </div>

      {/* modal */}
      {selected && (
        <PatientModal
          patient={selected}
          onClose={() => setSelected(null)}
          onOverride={() => { fetchQueue(); setSelected(null); }}
        />
      )}
    </div>
  );
}