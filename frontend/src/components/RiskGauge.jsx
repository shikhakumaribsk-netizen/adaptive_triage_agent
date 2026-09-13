import React, { useEffect, useState } from 'react';

const TIERS = [
  { lo: 0,  hi: 12,  label: 'SELF CARE',  color: '#16a34a' },
  { lo: 12, hi: 28,  label: 'STANDARD',   color: '#22c55e' },
  { lo: 28, hi: 45,  label: 'URGENT',     color: '#eab308' },
  { lo: 45, hi: 62,  label: 'EMERGENCY',  color: '#f97316' },
  { lo: 62, hi: 80,  label: 'CRITICAL',   color: '#ef4444' },
  { lo: 80, hi: 100, label: 'RESUS',      color: '#a855f7' },
];

function getTier(score) {
  return TIERS.find(t => score >= t.lo && score < t.hi) || TIERS[TIERS.length - 1];
}

/**
 * RiskGauge — animated SVG semi-circle gauge showing point score.
 *
 * Props:
 *   score       (number)  0-100  point estimate
 *   scoreMin    (number)  0-100  lower bound of band (optional)
 *   scoreMax    (number)  0-100  upper bound of band (optional)
 *   size        (number)  SVG width/height in px, default 200
 *   showBand    (bool)    show the uncertainty arc, default true
 *   showLabel   (bool)    show tier label text, default true
 */
export default function RiskGauge({
  score = 0,
  scoreMin,
  scoreMax,
  size = 200,
  showBand = true,
  showLabel = true,
}) {
  const [animScore, setAnimScore] = useState(0);

  // animate on mount and on score change
  useEffect(() => {
    let frame;
    const start = animScore;
    const end = score;
    const duration = 600;
    const startTime = performance.now();

    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimScore(Math.round(start + (end - start) * eased));
      if (progress < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [score]); // eslint-disable-line react-hooks/exhaustive-deps

  const tier = getTier(animScore);
  const cx = size / 2;
  const cy = size * 0.55;
  const r = size * 0.38;
  const strokeW = size * 0.09;

  // semi-circle from 180° to 0° (left to right)
  // angle: 180° = score 0, 0° = score 100
  const scoreToAngle = (s) => 180 - (s / 100) * 180; // degrees

  const polarToXY = (angleDeg, radius) => {
    const rad = (angleDeg * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy - radius * Math.sin(rad),
    };
  };

  const arcPath = (startDeg, endDeg, radius) => {
    const s = polarToXY(startDeg, radius);
    const e = polarToXY(endDeg, radius);
    const largeArc = Math.abs(startDeg - endDeg) > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${largeArc} 0 ${e.x} ${e.y}`;
  };

  // build tier background arcs
  const tierArcs = TIERS.map((t) => ({
    ...t,
    path: arcPath(
      scoreToAngle(t.lo),
      scoreToAngle(Math.min(t.hi, 100)),
      r
    ),
  }));

  // score needle angle
  const needleAngle = scoreToAngle(animScore);
  const needleTip = polarToXY(needleAngle, r * 0.82);
  const needleBase1 = polarToXY(needleAngle + 90, r * 0.07);
  const needleBase2 = polarToXY(needleAngle - 90, r * 0.07);

  // band arc (uncertainty)
  const minAngle = scoreToAngle(scoreMin ?? animScore);
  const maxAngle = scoreToAngle(scoreMax ?? animScore);
  const bandPath = arcPath(minAngle, maxAngle, r);

  return (
    <div className="flex flex-col items-center select-none">
      <svg
        width={size}
        height={size * 0.65}
        viewBox={`0 0 ${size} ${size * 0.65}`}
        overflow="visible"
      >
        {/* tier background arcs */}
        {tierArcs.map((t) => (
          <path
            key={t.label}
            d={t.path}
            fill="none"
            stroke={t.color}
            strokeWidth={strokeW}
            strokeLinecap="butt"
            opacity={0.18}
          />
        ))}

        {/* active score arc */}
        <path
          d={arcPath(180, scoreToAngle(animScore), r)}
          fill="none"
          stroke={tier.color}
          strokeWidth={strokeW * 0.55}
          strokeLinecap="round"
          style={{ transition: 'stroke 0.5s' }}
        />

        {/* uncertainty band arc */}
        {showBand && scoreMin !== undefined && scoreMax !== undefined && scoreMin !== scoreMax && (
          <path
            d={bandPath}
            fill="none"
            stroke="#ffffff"
            strokeWidth={strokeW * 0.22}
            strokeLinecap="round"
            strokeDasharray="4 3"
            opacity={0.45}
          />
        )}

        {/* needle */}
        <polygon
          points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
          fill={tier.color}
          opacity={0.9}
          style={{ transition: 'fill 0.5s' }}
        />

        {/* hub */}
        <circle cx={cx} cy={cy} r={size * 0.04} fill={tier.color} opacity={0.9} />

        {/* score text */}
        <text
          x={cx}
          y={cy - r * 0.28}
          textAnchor="middle"
          fill="white"
          fontSize={size * 0.16}
          fontWeight="bold"
          fontFamily="monospace"
        >
          {animScore}
        </text>
        <text
          x={cx}
          y={cy - r * 0.05}
          textAnchor="middle"
          fill="#9ca3af"
          fontSize={size * 0.065}
          fontFamily="sans-serif"
        >
          / 100
        </text>

        {/* min/max labels */}
        {showBand && scoreMin !== undefined && scoreMax !== undefined && (
          <>
            <text x={cx - r - strokeW / 2} y={cy + size * 0.06}
                  textAnchor="middle" fill="#6b7280" fontSize={size * 0.055}>
              {scoreMin}
            </text>
            <text x={cx + r + strokeW / 2} y={cy + size * 0.06}
                  textAnchor="middle" fill="#6b7280" fontSize={size * 0.055}>
              {scoreMax}
            </text>
          </>
        )}
      </svg>

      {/* tier label badge */}
      {showLabel && (
        <div
          className="mt-1 px-4 py-1 rounded-full text-xs font-bold tracking-wider border"
          style={{
            color: tier.color,
            borderColor: `${tier.color}50`,
            backgroundColor: `${tier.color}15`,
          }}
        >
          {tier.label}
        </div>
      )}

      {/* band explanation */}
      {showBand && scoreMin !== undefined && scoreMax !== undefined && scoreMin !== scoreMax && (
        <p className="mt-1 text-[10px] text-gray-500 text-center">
          band {scoreMin} – {scoreMax} &nbsp;·&nbsp; dashed arc = uncertainty
        </p>
      )}
    </div>
  );
}