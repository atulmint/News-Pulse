# News Pulse — Architecture

## Overview

Three-tier system: a Python ingestion pipeline writes processed data to PostgreSQL; a NestJS API reads from that database and exposes REST endpoints; a Next.js frontend consumes the API.

---

## Tier 1 — Python Ingestion Pipeline (`scraper/`)

Runs as a standalone process triggered on demand via the API or directly from the command line.

| Module | Responsibility |
|--------|----------------|
| RSS Fetcher | Downloads and parses RSS/Atom feeds with feedparser |
| Normalizer | Maps inconsistent feed fields to a canonical article schema |
| Article Extractor | Fetches each article URL and extracts body text with trafilatura |
| Deduplication | Skips articles already in the database (URL + content hash check) |
| Topic Clustering | Groups articles into clusters using TF-IDF + cosine similarity |
| DB Persistence | Writes sources, articles, clusters, and ingestion job records to PostgreSQL |

### Data flow

```
RSS Feed URLs (config)
    |
RSS Fetcher     -> raw feed entries
    |
Normalizer      -> canonical Article objects
    |
Article Extractor -> articles with body text
    |
Deduplication check -> new articles only
    |
Topic Clustering -> clustered article groups
    |
DB Persistence  -> PostgreSQL
```

---

## Tier 2 — NestJS REST API (`backend/`)

Stateless HTTP server. Reads from PostgreSQL via Prisma. Manages ingestion job lifecycle so the frontend can poll progress.

### Required endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /clusters | List all clusters |
| GET | /clusters/:id | Single cluster with its articles |
| GET | /timeline | Clusters ordered chronologically |
| POST | /ingest/trigger | Start a new ingestion run |
| GET | /ingest/status/:jobId | Poll job status and stats |

---

## Tier 3 — Next.js Frontend (`frontend/`)

App Router, React 19, Tailwind CSS 4.

| Feature | Description |
|---------|-------------|
| Timeline | Clusters on a time axis; each cluster spans earliest to latest article date |
| Cluster detail | Headline, source, published time, original link for each article |
| Source filter | Filter the timeline by news source |
| Ingestion panel | Trigger a run and poll status until complete |

---

## Database Schema

Managed by Prisma migrations (`backend/prisma/`). The Python pipeline uses psycopg2 to write to the same schema — it does not maintain a separate ORM model layer. Prisma schema is the single source of truth for table structure.

```
sources
  id          UUID PK
  name        TEXT
  feed_url    TEXT UNIQUE
  home_url    TEXT
  created_at  TIMESTAMP

articles
  id           UUID PK
  source_id    UUID FK -> sources
  cluster_id   UUID FK -> clusters  (nullable)
  title        TEXT
  url          TEXT UNIQUE
  published_at TIMESTAMP
  content      TEXT
  summary      TEXT
  content_hash TEXT          -- SHA-256 for cross-source deduplication
  created_at   TIMESTAMP

clusters
  id                   UUID PK
  label                TEXT
  representative_title TEXT  -- display label derived from most central article
  created_at           TIMESTAMP
  updated_at           TIMESTAMP
  -- article count is derived via _count, not stored as a mutable column

ingestion_jobs
  id               UUID PK
  status           ENUM (PENDING | RUNNING | COMPLETED | FAILED)
  articles_found   INT
  articles_new     INT
  clusters_updated INT
  error_message    TEXT
  started_at       TIMESTAMP
  completed_at     TIMESTAMP
  created_at       TIMESTAMP
```

---

## Key Design Decisions

**No message queue.** The API triggers the Python pipeline via subprocess. A queue is unnecessary complexity at this scale.

**Single PostgreSQL instance.** The pipeline and the API share one database. Prisma handles connection pooling on the Node side; psycopg2 on the Python side.

**Prisma as the schema owner.** The Prisma schema and its migrations are the authoritative definition of the database structure. Python reads and writes using raw psycopg2 queries against the same tables — no duplicate ORM model layer in Python.

**article_count not stored.** Cluster article counts are derived from the articles relation at query time (`_count`). Storing them would require keeping a denormalised counter in sync.

**Trafilatura first.** Handles the majority of article extraction. BeautifulSoup is the fallback for pages where trafilatura returns nothing.

**TF-IDF + cosine similarity for clustering.** Simple, dependency-light, no LLM or external API required. Threshold parameter is tunable in configuration.
