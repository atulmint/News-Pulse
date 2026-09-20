'use client';

interface EmptyStateProps {
  selectedSource?: string;
  onResetFilter?: () => void;
  onRefresh?: () => void;
}

export default function EmptyState({
  selectedSource,
  onResetFilter,
  onRefresh,
}: EmptyStateProps) {
  const isFiltered = selectedSource && selectedSource !== 'All Sources';

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-12 text-center shadow-sm">
      <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-100 dark:border-indigo-900 flex items-center justify-center mx-auto mb-4 text-indigo-600 dark:text-indigo-400">
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      </div>

      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
        {isFiltered ? `No clusters found for "${selectedSource}"` : 'No Timeline Data Available'}
      </h3>

      <p className="text-xs text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
        {isFiltered
          ? 'There are currently no topic clusters generated for this specific news source. Try selecting another source or reset filters.'
          : 'The ingestion system has not processed any news clusters yet. Trigger a news refresh to fetch live RSS feeds and compute story clusters.'}
      </p>

      <div className="flex items-center justify-center space-x-3">
        {isFiltered && onResetFilter && (
          <button
            onClick={onResetFilter}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 transition-colors"
          >
            Show All Sources
          </button>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-sm shadow-indigo-500/20"
          >
            Fetch Live News
          </button>
        )}
      </div>
    </div>
  );
}
