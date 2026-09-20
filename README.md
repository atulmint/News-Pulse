# News Pulse

A full-stack news aggregation and topic-clustering system. It pulls live articles from multiple RSS feeds, extracts their content, deduplicates across repeated runs, groups related articles into topic clusters, and presents the result as an interactive visual timeline.

---

## Architecture

```
RSS Sources
    |
Python Ingestion Pipeline  (scraper/)
    |-- RSS Fetcher
    |-- Normalizer
    |-- Article Extractor
    |-- Deduplication
    |-- Topic Clustering
    |-- Database Persistence
           |
      PostgreSQL
           ^
      NestJS REST API  (backend/)
           |
      Next.js Frontend  (frontend/)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 · TypeScript · React 19 · Tailwind CSS 4 |
| Backend API | Node.js · NestJS · TypeScript · Prisma ORM |
| Database | PostgreSQL |
| Ingestion pipeline | Python 3 · feedparser · httpx · trafilatura · scikit-learn |

---

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | **FOUNDATION READY** | Directory structure, dependency manifests, env templates, Prisma schema draft, module scaffolds |
| Phase 2 | NOT IMPLEMENTED | Python ingestion pipeline (RSS fetch, normalize, extract, deduplicate, cluster, persist) |
| Phase 3 | NOT IMPLEMENTED | NestJS REST API endpoints |
| Phase 4 | NOT IMPLEMENTED | Next.js frontend (timeline, cluster explorer, ingestion panel) |
| Phase 5 | NOT IMPLEMENTED | Integration testing, deployment, demo video |

---

## API Contract

The following endpoints are required by the assessment specification.
They will be implemented in Phase 3.

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /clusters | List all clusters |
| GET | /clusters/:id | Single cluster with articles |
| GET | /timeline | Chronological timeline data |
| POST | /ingest/trigger | Trigger an ingestion run |
| GET | /ingest/status/:jobId | Poll ingestion job status |

---

## RSS Sources

Three verified public feeds are configured for the initial implementation:

- BBC World News — `https://feeds.bbci.co.uk/news/world/rss.xml`
- NPR News — `https://feeds.npr.org/1001/rss.xml`
- The Guardian — `https://www.theguardian.com/world/rss`

---

## Quick Start

> Requires all phases to be implemented first.

```bash
# 1. Start PostgreSQL

# 2. Backend
cd backend
cp .env.example .env
npm install
npm run start:dev

# 3. Ingestion pipeline
cd scraper
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main

# 4. Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```
