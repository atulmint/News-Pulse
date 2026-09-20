export interface ClusterSummary {
  id: string;
  label: string;
  articleCount: number;
  startTime: string;
  endTime: string;
}

export interface ArticleDetail {
  id: string;
  title: string;
  source: string;
  publishedTime: string;
  originalUrl: string;
  summary: string | null;
}

export interface ClusterDetail extends ClusterSummary {
  articles: ArticleDetail[];
}

export interface TimelineEntry {
  clusterId: string;
  label: string;
  startTime: string;
  endTime: string;
  articleCount: number;
  intensity: number;
}

export interface TriggerJobResponse {
  jobId: string;
  status: string;
}

export interface JobStatusResponse {
  jobId: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  startedAt: string | null;
  completedAt: string | null;
  articlesProcessed: number;
  articlesCreated: number;
  error: string | null;
}
