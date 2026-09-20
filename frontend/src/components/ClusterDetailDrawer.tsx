'use client';

import { useEffect, useState } from 'react';
import { ClusterDetail } from '../types';
import { fetchClusterDetail, formatDate, formatTimeSpan } from '../lib/api';

interface ClusterDetailDrawerProps {
  clusterId: string | null;
  onClose: () => void;
}

export default function ClusterDetailDrawer({
  clusterId,
  onClose,
}: ClusterDetailDrawerProps) {
  const [detail, setDetail] = useState<ClusterDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clusterId) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchClusterDetail(clusterId)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load cluster details');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [clusterId]);

  // Handle ESC key listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!clusterId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm transition-opacity duration-300 animate-fade-in"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-800 flex flex-col transform transition-transform duration-300 ease-in-out">
          {/* Drawer Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-950/50 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Topic Cluster
                </span>
                {detail && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                    {detail.articleCount} {detail.articleCount === 1 ? 'article' : 'articles'}
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {loading ? (
                  <span className="inline-block w-48 h-6 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
                ) : (
                  detail?.label ?? 'Cluster Details'
                )}
              </h2>
              {detail && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-mono">
                  {formatTimeSpan(detail.startTime, detail.endTime)}
                </p>
              )}
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Close panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Drawer Body / Articles Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {loading && (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 rounded-2xl border border-gray-200 dark:border-gray-800 animate-pulse space-y-3">
                    <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                    <div className="h-12 bg-gray-100 dark:bg-gray-800/50 rounded" />
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-center space-y-3">
                <p className="text-sm font-semibold text-rose-700 dark:text-rose-400">{error}</p>
                <button
                  onClick={() => {
                    setLoading(true);
                    setError(null);
                    fetchClusterDetail(clusterId).then(setDetail).catch(err => setError(err.message)).finally(() => setLoading(false));
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700 transition-colors"
                >
                  Retry Loading
                </button>
              </div>
            )}

            {!loading && !error && detail && (
              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                  Chronological Article Coverage ({detail.articles.length})
                </h3>

                {detail.articles.map((article) => (
                  <div
                    key={article.id}
                    className="group bg-gray-50/70 dark:bg-gray-850/50 hover:bg-white dark:hover:bg-gray-800 p-5 rounded-2xl border border-gray-200/80 dark:border-gray-800 transition-all shadow-sm hover:shadow-md"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                        {article.source}
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
                        {formatDate(article.publishedTime)}
                      </span>
                    </div>

                    <h4 className="text-base font-semibold text-gray-900 dark:text-white leading-snug mb-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {article.title}
                    </h4>

                    {article.summary && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3 mb-4 leading-relaxed">
                        {article.summary}
                      </p>
                    )}

                    <div className="flex items-center justify-between pt-2 border-t border-gray-200/60 dark:border-gray-700/60">
                      <span className="text-[11px] text-gray-400 dark:text-gray-500">
                        Original Publisher
                      </span>
                      <a
                        href={article.originalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 transition-colors"
                      >
                        <span>Read Original Article</span>
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
