'use client';

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 rounded-2xl p-8 text-center max-w-xl mx-auto my-8">
      <div className="w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-900/60 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto mb-3">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <h3 className="text-base font-bold text-rose-900 dark:text-rose-200 mb-1">
        Unable to Load News Timeline
      </h3>

      <p className="text-xs text-rose-700 dark:text-rose-400 mb-6 max-w-md mx-auto">
        {message}
      </p>

      <button
        onClick={onRetry}
        className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white transition-colors shadow-sm shadow-rose-500/20 focus:outline-none focus:ring-2 focus:ring-rose-500"
      >
        Try Again
      </button>
    </div>
  );
}
