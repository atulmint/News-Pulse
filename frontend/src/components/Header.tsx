'use client';

import { useState, useEffect, useRef } from 'react';
import { triggerIngestion, fetchJobStatus } from '../lib/api';

interface HeaderProps {
  onRefreshSuccess: () => void;
}

export default function Header({ onRefreshSuccess }: HeaderProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const pollingTimer = useRef<NodeJS.Timeout | null>(null);

  const handleRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    setRefreshError(null);
    setJobStatus('PENDING');

    try {
      const res = await triggerIngestion();
      setJobId(res.jobId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to trigger ingestion';
      setRefreshError(msg);
      setIsRefreshing(false);
      setJobStatus(null);
    }
  };

  useEffect(() => {
    if (!jobId || !isRefreshing) return;

    pollingTimer.current = setInterval(async () => {
      try {
        const statusRes = await fetchJobStatus(jobId);
        setJobStatus(statusRes.status);

        if (statusRes.status === 'COMPLETED') {
          if (pollingTimer.current) clearInterval(pollingTimer.current);
          setIsRefreshing(false);
          setJobId(null);
          onRefreshSuccess();
        } else if (statusRes.status === 'FAILED') {
          if (pollingTimer.current) clearInterval(pollingTimer.current);
          setIsRefreshing(false);
          setRefreshError(statusRes.error ?? 'Ingestion job failed');
          setJobId(null);
        }
      } catch (err: unknown) {
        if (pollingTimer.current) clearInterval(pollingTimer.current);
        setIsRefreshing(false);
        const msg = err instanceof Error ? err.message : 'Polling failed';
        setRefreshError(msg);
        setJobId(null);
      }
    }, 1500);

    return () => {
      if (pollingTimer.current) clearInterval(pollingTimer.current);
    };
  }, [jobId, isRefreshing, onRefreshSuccess]);

  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md sticky top-0 z-30 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white font-black text-xl">
              N
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
                  News Pulse
                </h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-1.5"></span>
                  Live Engine
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Real-time RSS news aggregation & TF-IDF topic cluster timeline
              </p>
            </div>
          </div>

          {/* Action / Refresh Status */}
          <div className="flex items-center space-x-3">
            {refreshError && (
              <span className="text-xs font-medium text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 px-3 py-1.5 rounded-lg max-w-xs truncate">
                ⚠️ {refreshError}
              </span>
            )}

            {isRefreshing && (
              <div className="flex items-center space-x-2 text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800 px-3 py-1.5 rounded-lg">
                <svg
                  className="animate-spin h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span>{jobStatus === 'RUNNING' ? 'Running Ingestion & Clustering...' : 'Initializing Job...'}</span>
              </div>
            )}

            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                isRefreshing
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-500/20 active:scale-95'
              }`}
            >
              <svg
                className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>{isRefreshing ? 'Updating News...' : 'Refresh News'}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
