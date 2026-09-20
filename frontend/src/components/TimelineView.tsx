'use client';

import { useMemo, useState } from 'react';
import { TimelineEntry } from '../types';
import { formatDate, formatTimeSpan } from '../lib/api';

interface TimelineViewProps {
  entries: TimelineEntry[];
  selectedClusterId: string | null;
  onSelectCluster: (clusterId: string) => void;
}

interface TrackEntry {
  entry: TimelineEntry;
  leftPercent: number;
  widthPercent: number;
}

export default function TimelineView({
  entries,
  selectedClusterId,
  onSelectCluster,
}: TimelineViewProps) {
  const [hoveredClusterId, setHoveredClusterId] = useState<string | null>(null);

  // Calculate time bounds and track layouts
  const { minMs, maxMs, tracks, timeTicks } = useMemo(() => {
    if (entries.length === 0) {
      return { minMs: Date.now(), maxMs: Date.now() + 3600000, tracks: [], timeTicks: [] };
    }

    let min = Infinity;
    let max = -Infinity;

    entries.forEach((e) => {
      const s = new Date(e.startTime).getTime();
      const end = new Date(e.endTime).getTime();
      if (!isNaN(s) && s < min) min = s;
      if (!isNaN(end) && end > max) max = end;
    });

    // Ensure min and max are valid and have a reasonable span
    if (min === Infinity || max === -Infinity) {
      min = Date.now() - 3600000;
      max = Date.now();
    }

    // Add 1 hour buffer before and after if span is small
    const buffer = Math.max((max - min) * 0.05, 3600000); // at least 1 hr
    const adjustedMin = min - buffer;
    const adjustedMax = max + buffer;
    const totalSpanMs = adjustedMax - adjustedMin;

    // Generate 5 evenly spaced time axis ticks
    const ticks: { label: string; percent: number }[] = [];
    const tickCount = 5;
    for (let i = 0; i < tickCount; i++) {
      const tickMs = adjustedMin + (totalSpanMs * i) / (tickCount - 1);
      ticks.push({
        label: formatDate(new Date(tickMs)),
        percent: (i / (tickCount - 1)) * 100,
      });
    }

    // Sort entries chronologically by startTime
    const sorted = [...entries].sort(
      (a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
    );

    // Track allocation for overlapping blocks
    const allocatedTracks: TrackEntry[][] = [];

    sorted.forEach((entry) => {
      const startMs = new Date(entry.startTime).getTime();
      const endMs = new Date(entry.endTime).getTime();

      let leftPercent = ((startMs - adjustedMin) / totalSpanMs) * 100;
      let widthPercent = ((endMs - startMs) / totalSpanMs) * 100;

      // Minimum visual width for readability (min 12%)
      if (widthPercent < 12) {
        widthPercent = 12;
      }
      // Ensure leftPercent + widthPercent <= 100%
      if (leftPercent + widthPercent > 100) {
        leftPercent = 100 - widthPercent;
      }

      const trackItem: TrackEntry = { entry, leftPercent, widthPercent };

      // Find suitable track
      let placed = false;
      for (const track of allocatedTracks) {
        const lastInTrack = track[track.length - 1];
        const lastEndMs = new Date(lastInTrack.entry.endTime).getTime();

        // Check if there's enough visual separation in percentage space
        const lastRightPercent = lastInTrack.leftPercent + lastInTrack.widthPercent;
        if (leftPercent >= lastRightPercent + 2 || startMs >= lastEndMs + 300000) {
          track.push(trackItem);
          placed = true;
          break;
        }
      }

      if (!placed) {
        allocatedTracks.push([trackItem]);
      }
    });

    return {
      minMs: adjustedMin,
      maxMs: adjustedMax,
      tracks: allocatedTracks,
      timeTicks: ticks,
    };
  }, [entries]);

  const clusterAccents = [
    {
      bg: 'bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/80',
      border: 'border-indigo-300 dark:border-indigo-700',
      accent: 'bg-indigo-600',
      badge: 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300',
      glow: 'shadow-indigo-500/10',
    },
    {
      bg: 'bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:hover:bg-emerald-900/80',
      border: 'border-emerald-300 dark:border-emerald-700',
      accent: 'bg-emerald-600',
      badge: 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300',
      glow: 'shadow-emerald-500/10',
    },
    {
      bg: 'bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/60 dark:hover:bg-amber-900/80',
      border: 'border-amber-300 dark:border-amber-700',
      accent: 'bg-amber-600',
      badge: 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300',
      glow: 'shadow-amber-500/10',
    },
    {
      bg: 'bg-violet-50 hover:bg-violet-100 dark:bg-violet-950/60 dark:hover:bg-violet-900/80',
      border: 'border-violet-300 dark:border-violet-700',
      accent: 'bg-violet-600',
      badge: 'bg-violet-100 dark:bg-violet-900 text-violet-700 dark:text-violet-300',
      glow: 'shadow-violet-500/10',
    },
    {
      bg: 'bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900/80',
      border: 'border-sky-300 dark:border-sky-700',
      accent: 'bg-sky-600',
      badge: 'bg-sky-100 dark:bg-sky-900 text-sky-700 dark:text-sky-300',
      glow: 'shadow-sky-500/10',
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>Temporal News Timeline</span>
            <span className="text-xs font-normal text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2.5 py-0.5 rounded-full border border-gray-200 dark:border-gray-700">
              Interactive Time Axis
            </span>
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Story clusters positioned by publication timeframe. Click a block to inspect full coverage.
          </p>
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
            <span>Cluster Block</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-6 h-1 rounded bg-gradient-to-r from-indigo-500 to-emerald-500"></span>
            <span>Time Span</span>
          </div>
        </div>
      </div>

      {/* Main Timeline Scrollable Container */}
      <div className="overflow-x-auto pb-4 pt-2 relative">
        <div className="min-w-[700px] relative">
          {/* Visual Time Grid Background Lines */}
          <div className="absolute inset-0 top-8 bottom-8 flex justify-between pointer-events-none">
            {timeTicks.map((tick, idx) => (
              <div
                key={idx}
                className="border-l border-dashed border-gray-200 dark:border-gray-800 h-full relative"
                style={{ left: `${tick.percent}%` }}
              />
            ))}
          </div>

          {/* Top Time Axis Ticks */}
          <div className="relative h-8 border-b border-gray-200 dark:border-gray-800 mb-6 text-xs text-gray-400 font-mono">
            {timeTicks.map((tick, idx) => (
              <div
                key={idx}
                className="absolute transform -translate-x-1/2 whitespace-nowrap text-[10px] sm:text-xs font-medium"
                style={{ left: `${tick.percent}%` }}
              >
                {tick.label}
              </div>
            ))}
          </div>

          {/* Tracks / Blocks Layer */}
          <div className="space-y-4 py-2 relative z-10">
            {tracks.map((track, trackIdx) => (
              <div key={trackIdx} className="relative h-16 w-full">
                {track.map(({ entry, leftPercent, widthPercent }, idx) => {
                  const isSelected = selectedClusterId === entry.clusterId;
                  const isHovered = hoveredClusterId === entry.clusterId;
                  const theme = clusterAccents[(trackIdx * 3 + idx) % clusterAccents.length];

                  return (
                    <div
                      key={entry.clusterId}
                      onClick={() => onSelectCluster(entry.clusterId)}
                      onMouseEnter={() => setHoveredClusterId(entry.clusterId)}
                      onMouseLeave={() => setHoveredClusterId(null)}
                      tabIndex={0}
                      role="button"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          onSelectCluster(entry.clusterId);
                        }
                      }}
                      style={{
                        left: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                      }}
                      className={`absolute top-0 bottom-0 rounded-xl border transition-all duration-200 cursor-pointer p-2.5 flex flex-col justify-between group focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        theme.bg
                      } ${theme.border} ${theme.glow} ${
                        isSelected
                          ? 'ring-2 ring-indigo-600 dark:ring-indigo-400 shadow-md scale-[1.02] z-20'
                          : isHovered
                          ? 'shadow-md scale-[1.01] z-20'
                          : 'z-10'
                      }`}
                    >
                      {/* Top Bar inside Block */}
                      <div className="flex items-center justify-between gap-1 overflow-hidden">
                        <div className="flex items-center space-x-1.5 min-w-0">
                          <span
                            className={`w-2 h-2 rounded-full flex-shrink-0 ${theme.accent}`}
                          />
                          <h3 className="text-xs font-bold text-gray-900 dark:text-white truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                            {entry.label}
                          </h3>
                        </div>
                        <span
                          className={`flex-shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold ${theme.badge}`}
                        >
                          {entry.articleCount} {entry.articleCount === 1 ? 'article' : 'articles'}
                        </span>
                      </div>

                      {/* Bottom Info inside Block */}
                      <div className="flex items-center justify-between text-[10px] text-gray-500 dark:text-gray-400 font-mono mt-1">
                        <span className="truncate">
                          {formatTimeSpan(entry.startTime, entry.endTime)}
                        </span>
                        <span className="hidden sm:inline-block font-sans text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                          Inspect ↗
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Bottom Time Axis Ticks */}
          <div className="relative h-8 border-t border-gray-200 dark:border-gray-800 mt-6 text-xs text-gray-400 font-mono">
            {timeTicks.map((tick, idx) => (
              <div
                key={idx}
                className="absolute top-2 transform -translate-x-1/2 whitespace-nowrap text-[10px] sm:text-xs font-medium"
                style={{ left: `${tick.percent}%` }}
              >
                {tick.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
