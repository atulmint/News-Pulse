import {
  ClusterDetail,
  ClusterSummary,
  JobStatusResponse,
  TimelineEntry,
  TriggerJobResponse,
} from '../types';

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001';

export async function fetchTimeline(sourceFilter?: string): Promise<TimelineEntry[]> {
  const url = new URL(`${API_BASE_URL}/timeline`);
  if (sourceFilter && sourceFilter !== 'All Sources') {
    url.searchParams.set('source', sourceFilter);
  }

  const res = await fetch(url.toString(), { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch timeline (${res.status} ${res.statusText})`);
  }

  const data = await res.json();
  return data.timeline ?? [];
}

export async function fetchClusters(sourceFilter?: string): Promise<ClusterSummary[]> {
  const url = new URL(`${API_BASE_URL}/clusters`);
  if (sourceFilter && sourceFilter !== 'All Sources') {
    url.searchParams.set('source', sourceFilter);
  }

  const res = await fetch(url.toString(), { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch clusters (${res.status} ${res.statusText})`);
  }

  const data = await res.json();
  return data.clusters ?? [];
}

export async function fetchClusterDetail(clusterId: string): Promise<ClusterDetail> {
  const res = await fetch(`${API_BASE_URL}/clusters/${encodeURIComponent(clusterId)}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error(`Cluster not found (404)`);
    }
    throw new Error(`Failed to fetch cluster details (${res.status})`);
  }

  return res.json();
}

export async function triggerIngestion(): Promise<TriggerJobResponse> {
  const res = await fetch(`${API_BASE_URL}/ingest/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!res.ok) {
    throw new Error(`Failed to trigger ingestion (${res.status})`);
  }

  return res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/ingest/status/${encodeURIComponent(jobId)}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch job status (${res.status})`);
  }

  return res.json();
}

export function formatDate(dateString: string | Date | null | undefined): string {
  if (!dateString) return 'Unknown date';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'Unknown date';
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return 'Unknown date';
  }
}

export function formatTimeSpan(startTime: string, endTime: string): string {
  const start = new Date(startTime);
  const end = new Date(endTime);
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return '';

  const formatShort = (d: Date) =>
    d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

  if (start.toDateString() === end.toDateString()) {
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}, ${formatShort(start)} – ${formatShort(end)}`;
  }

  return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
}
