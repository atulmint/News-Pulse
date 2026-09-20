'use client';

import { useCallback, useEffect, useState } from 'react';
import Header from '../components/Header';
import SourceFilter from '../components/SourceFilter';
import TimelineView from '../components/TimelineView';
import ClusterDetailDrawer from '../components/ClusterDetailDrawer';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { TimelineEntry } from '../types';
import { fetchTimeline } from '../lib/api';

const KNOWN_SOURCES = ['BBC World News', 'NPR News', 'The Guardian'];

export default function HomePage() {
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('All Sources');
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTimelineData = useCallback(async (source?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTimeline(source);
      setTimeline(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load timeline';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTimelineData(selectedSource);
  }, [selectedSource, loadTimelineData]);

  const handleRefreshSuccess = () => {
    loadTimelineData(selectedSource);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 flex flex-col font-sans transition-colors">
      {/* Top Navigation Header */}
      <Header onRefreshSuccess={handleRefreshSuccess} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Source Filter Controls */}
        <SourceFilter
          availableSources={KNOWN_SOURCES}
          selectedSource={selectedSource}
          onSelectSource={(src) => setSelectedSource(src)}
          totalClustersCount={timeline.length}
        />

        {/* Dynamic Content Views */}
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={() => loadTimelineData(selectedSource)}
          />
        ) : timeline.length === 0 ? (
          <EmptyState
            selectedSource={selectedSource}
            onResetFilter={() => setSelectedSource('All Sources')}
            onRefresh={handleRefreshSuccess}
          />
        ) : (
          <TimelineView
            entries={timeline}
            selectedClusterId={selectedClusterId}
            onSelectCluster={(id) => setSelectedClusterId(id)}
          />
        )}
      </main>

      {/* Cluster Detail Drawer Modal */}
      <ClusterDetailDrawer
        clusterId={selectedClusterId}
        onClose={() => setSelectedClusterId(null)}
      />

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-6 text-center text-xs text-gray-400 dark:text-gray-500">
        <p>News Pulse Ingestion Engine & Temporal Clustering Dashboard — Phase 2F</p>
      </footer>
    </div>
  );
}
