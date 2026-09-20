'use client';

interface SourceFilterProps {
  availableSources: string[];
  selectedSource: string;
  onSelectSource: (source: string) => void;
  totalClustersCount: number;
}

export default function SourceFilter({
  availableSources,
  selectedSource,
  onSelectSource,
  totalClustersCount,
}: SourceFilterProps) {
  const sources = ['All Sources', ...availableSources];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-gray-900 p-4 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
          Filter by Source
        </span>
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
          {totalClustersCount} {totalClustersCount === 1 ? 'cluster' : 'clusters'}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {sources.map((src) => {
          const isActive = selectedSource === src;
          return (
            <button
              key={src}
              onClick={() => onSelectSource(src)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                  : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              {src}
            </button>
          );
        })}

        {selectedSource !== 'All Sources' && (
          <button
            onClick={() => onSelectSource('All Sources')}
            className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline px-2 py-1"
          >
            Reset Filter
          </button>
        )}
      </div>
    </div>
  );
}
