import React from 'react';

/**
 * DecisionTimeline — shows the sequence of agent decisions as a vertical timeline.
 *
 * Props:
 *   timeline   Array of { event, time, icon, score? }
 *   compact    bool — smaller version for sidebars
 */

const SCORE_COLOR = (s) => {
  if (!s && s !== 0) return '#6b7280';
  if (s >= 80) return '#a855f7';
  if (s >= 62) return '#ef4444';
  if (s >= 45) return '#f97316';
  if (s >= 28) return '#eab308';
  if (s >= 12) return '#22c55e';
  return '#16a34a';
};

function ScoreBar({ score }) {
  if (score === undefined || score === null) return null;
  const color = SCORE_COLOR(score);
  return (
    <div className="mt-1.5 flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-mono shrink-0" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

export default function DecisionTimeline({ timeline = [], compact = false }) {
  if (timeline.length === 0) {
    return (
      <div>
        <h3 className={`font-semibold text-white mb-3 ${compact ? 'text-xs' : 'text-sm'}`}>
          📋 Decision Timeline
        </h3>
        <p className="text-[11px] text-gray-600">
          Timeline will populate as the assessment progresses.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className={`font-semibold text-white mb-4 ${compact ? 'text-xs' : 'text-sm'}`}>
        📋 Decision Timeline
        <span className="ml-2 text-gray-600 font-normal text-[10px]">
          {timeline.length} event{timeline.length !== 1 ? 's' : ''}
        </span>
      </h3>

      <div className="relative">
        {/* vertical connecting line */}
        {timeline.length > 1 && (
          <div
            className="absolute left-3.5 top-7 bottom-0 w-px bg-gray-800"
            style={{ height: `calc(100% - 28px)` }}
          />
        )}

        <div className="space-y-4">
          {timeline.map((item, i) => {
            const isLast = i === timeline.length - 1;
            return (
              <div key={i} className="flex items-start gap-3 animate-fade-in">

                {/* icon circle */}
                <div
                  className={`relative z-10 w-7 h-7 rounded-full flex items-center
                               justify-center shrink-0 text-sm border
                               ${isLast
                                 ? 'bg-gray-900 border-gray-600'
                                 : 'bg-gray-950 border-gray-800'}`}
                >
                  {item.icon}
                </div>

                {/* content */}
                <div className="flex-1 pb-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p
                      className={`text-gray-200 leading-snug ${
                        compact ? 'text-[11px]' : 'text-xs'
                      } ${isLast ? 'font-semibold text-white' : ''}`}
                    >
                      {item.event}
                    </p>
                    <span className="text-[10px] text-gray-600 shrink-0 font-mono">
                      {item.time}
                    </span>
                  </div>

                  {/* score bar */}
                  {!compact && <ScoreBar score={item.score} />}

                  {/* sub-text */}
                  {item.sub && (
                    <p className="text-[10px] text-gray-500 mt-0.5 italic">{item.sub}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}