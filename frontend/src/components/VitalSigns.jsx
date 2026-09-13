import React, { useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const FIELDS = [
  {
    key: 'heart_rate',
    label: 'Heart Rate',
    unit: 'bpm',
    placeholder: '60–100',
    icon: '❤️',
    ranges: { critLo: 40, lo: 60, hi: 100, critHi: 130 },
  },
  {
    key: 'systolic_bp',
    label: 'Systolic BP',
    unit: 'mmHg',
    placeholder: '90–140',
    icon: '🩺',
    ranges: { critLo: 80, lo: 90, hi: 140, critHi: 180 },
  },
  {
    key: 'diastolic_bp',
    label: 'Diastolic BP',
    unit: 'mmHg',
    placeholder: '60–90',
    icon: '🩺',
    ranges: { lo: 60, hi: 90 },
  },
  {
    key: 'spo2',
    label: 'SpO₂',
    unit: '%',
    placeholder: '95–100',
    icon: '🫁',
    ranges: { critLo: 90, lo: 94, hi: 100 },
  },
  {
    key: 'resp_rate',
    label: 'Resp Rate',
    unit: '/min',
    placeholder: '12–20',
    icon: '🌬️',
    ranges: { critLo: 8, lo: 12, hi: 20, critHi: 25 },
  },
  {
    key: 'temperature',
    label: 'Temperature',
    unit: '°C',
    placeholder: '36.1–37.5',
    icon: '🌡️',
    ranges: { critLo: 35.0, lo: 36.1, hi: 37.5, critHi: 39.5 },
    step: 0.1,
  },
];

function getStatus(value, ranges) {
  const v = parseFloat(value);
  if (isNaN(v)) return null;
  if ((ranges.critLo !== undefined && v <= ranges.critLo) ||
      (ranges.critHi !== undefined && v >= ranges.critHi)) return 'CRITICAL';
  if ((ranges.lo !== undefined && v < ranges.lo) ||
      (ranges.hi !== undefined && v > ranges.hi)) return 'WARNING';
  return 'NORMAL';
}

const STATUS_STYLES = {
  CRITICAL: {
    border: 'border-red-500',
    bg: 'bg-red-500/10',
    badge: 'bg-red-500/20 text-red-300',
    dot: '🔴',
    text: 'text-red-400',
  },
  WARNING: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-500/10',
    badge: 'bg-yellow-500/20 text-yellow-300',
    dot: '🟡',
    text: 'text-yellow-400',
  },
  NORMAL: {
    border: 'border-green-500/60',
    bg: 'bg-green-500/5',
    badge: 'bg-green-500/20 text-green-300',
    dot: '🟢',
    text: 'text-green-400',
  },
};

/**
 * VitalSigns component — collects vital signs, colour-codes them, and POSTs to backend.
 *
 * Props:
 *   sessionId   (string)   required — session UUID
 *   onUpdate    (fn)       optional — called with API response on successful submit
 *   compact     (bool)     optional — smaller layout for sidebars
 */
export default function VitalSigns({ sessionId, onUpdate, compact = false }) {
  const [values, setValues] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [updatedRisk, setUpdatedRisk] = useState(null);

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: val }));
    setSubmitted(false);
  };

  const handleSubmit = async () => {
    const hasAny = FIELDS.some(f => values[f.key] !== undefined && values[f.key] !== '');
    if (!hasAny) { setError('Please enter at least one vital sign.'); return; }

    setLoading(true);
    setError(null);

    const payload = { session_id: sessionId };
    FIELDS.forEach(f => {
      if (values[f.key] !== undefined && values[f.key] !== '') {
        payload[f.key] = parseFloat(values[f.key]);
      }
    });

    try {
      const res = await fetch(`${API}/api/session/vitals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setSubmitted(true);
      setUpdatedRisk(data.risk);
      if (onUpdate) onUpdate(data);
    } catch (e) {
      setError(e.message || 'Failed to submit vitals.');
    }
    setLoading(false);
  };

  const allStatuses = FIELDS
    .map(f => getStatus(values[f.key], f.ranges))
    .filter(Boolean);
  const hasCritical = allStatuses.includes('CRITICAL');
  const hasWarning = allStatuses.includes('WARNING');

  return (
    <div className={`bg-gray-900 border ${hasCritical ? 'border-red-500/60' : hasWarning ? 'border-yellow-500/40' : 'border-gray-800'} rounded-2xl overflow-hidden`}>
      {/* header */}
      <div className={`px-4 py-3 flex items-center justify-between border-b border-gray-800 ${hasCritical ? 'bg-red-500/10' : ''}`}>
        <div className="flex items-center gap-2">
          <span className="text-base">📊</span>
          <span className="text-white font-semibold text-sm">Vital Signs</span>
        </div>
        {hasCritical && (
          <span className="text-[10px] font-bold text-red-300 bg-red-500/20 px-2 py-0.5 rounded-full animate-pulse">
            ⚠ CRITICAL VALUE
          </span>
        )}
        {!hasCritical && hasWarning && (
          <span className="text-[10px] font-bold text-yellow-300 bg-yellow-500/20 px-2 py-0.5 rounded-full">
            ⚠ ABNORMAL
          </span>
        )}
      </div>

      {/* fields */}
      <div className={`p-4 ${compact ? 'space-y-2' : 'space-y-3'}`}>
        {FIELDS.map(field => {
          const status = getStatus(values[field.key], field.ranges);
          const styles = status ? STATUS_STYLES[status] : null;

          return (
            <div key={field.key}>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[11px] text-gray-400 flex items-center gap-1">
                  <span>{field.icon}</span>
                  <span>{field.label}</span>
                  <span className="text-gray-600">({field.unit})</span>
                </label>
                {status && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${styles.badge}`}>
                    {styles.dot} {status}
                  </span>
                )}
              </div>
              <div className={`flex items-center border rounded-xl overflow-hidden transition-all ${styles ? `${styles.border} ${styles.bg}` : 'border-gray-700 bg-gray-800/50'}`}>
                <input
                  type="number"
                  value={values[field.key] ?? ''}
                  onChange={e => handleChange(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  step={field.step ?? 1}
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none"
                />
                <span className={`text-[10px] px-2 ${styles ? styles.text : 'text-gray-600'}`}>
                  {field.unit}
                </span>
              </div>

              {/* reference range bar */}
              {values[field.key] && field.ranges.lo && field.ranges.hi && (() => {
                const v = parseFloat(values[field.key]);
                const rangeMin = field.ranges.critLo ?? field.ranges.lo;
                const rangeMax = field.ranges.critHi ?? field.ranges.hi;
                const pct = Math.min(Math.max((v - rangeMin) / (rangeMax - rangeMin) * 100, 0), 100);
                const normalLoPct = ((field.ranges.lo - rangeMin) / (rangeMax - rangeMin)) * 100;
                const normalHiPct = ((field.ranges.hi - rangeMin) / (rangeMax - rangeMin)) * 100;
                return (
                  <div className="mt-1 relative h-1 bg-gray-700 rounded-full overflow-visible">
                    {/* normal zone */}
                    <div className="absolute h-full bg-green-500/20 rounded-full"
                         style={{ left: `${normalLoPct}%`, width: `${normalHiPct - normalLoPct}%` }} />
                    {/* pointer */}
                    <div className="absolute top-1/2 w-2 h-2 rounded-full -translate-y-1/2 -translate-x-1/2 transition-all duration-300 shadow"
                         style={{ left: `${pct}%`, backgroundColor: styles?.border?.replace('border-', '') || '#6b7280' }} />
                  </div>
                );
              })()}
            </div>
          );
        })}

        {/* error */}
        {error && (
          <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-lg p-2">
            {error}
          </p>
        )}

        {/* submit */}
        <button
          onClick={handleSubmit}
          disabled={loading || submitted}
          className={`mt-2 w-full py-2.5 rounded-xl text-sm font-semibold transition-all ${
            submitted
              ? 'bg-green-600/80 text-white cursor-default'
              : loading
              ? 'bg-gray-700 text-gray-400 cursor-wait'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {submitted ? '✅ Vitals Submitted & Reassessment Triggered'
                     : loading ? 'Submitting…'
                     : 'Submit Vitals & Trigger Reassessment'}
        </button>

        {/* result preview */}
        {submitted && updatedRisk && (
          <div className="mt-2 bg-gray-800/50 border border-gray-700 rounded-xl p-3 text-xs">
            <p className="text-gray-400 mb-1">Updated risk after vitals:</p>
            <div className="flex justify-between">
              <span className="text-gray-300">Band</span>
              <span className="font-mono text-white">
                {updatedRisk.score_min} – {updatedRisk.score_max}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Routing</span>
              <span style={{ color: updatedRisk.tier_max?.color }}>
                {updatedRisk.tier_max?.code}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Confidence</span>
              <span className="text-white">{updatedRisk.confidence_pct}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}