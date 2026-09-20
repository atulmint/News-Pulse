# News Pulse — Backend API

NestJS REST API for News Pulse.

## Project layout

```
backend/
|-- src/
|   |-- modules/
|   |   |-- articles/    # GET /articles, GET /articles/:id
|   |   |-- clusters/    # GET /clusters, GET /clusters/:id
|   |   |-- timeline/    # GET /timeline
|   |   |-- ingestion/   # POST /ingestion/run, GET /ingestion/jobs
|   |-- common/          # Health check, shared guards/filters
|   |-- config/          # App configuration
|   |-- database/        # PrismaService, DatabaseModule
|-- prisma/
|   |-- schema.prisma    # Database schema
|   |-- migrations/      # Prisma migrations (generated in Phase 3)
|-- test/                # e2e tests (Phase 3)
```

## Setup

```bash
cp .env.example .env   # fill in DATABASE_URL
npm install
npx prisma generate    # generate Prisma client
```

## Running

```bash
npm run start:dev
```

## API endpoints (Phase 3)

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /articles | List articles (paginated) |
| GET | /articles/:id | Single article |
| GET | /clusters | List clusters |
| GET | /clusters/:id | Single cluster with articles |
| GET | /timeline | Timeline data |
| POST | /ingestion/run | Trigger ingestion pipeline |
| GET | /ingestion/jobs | List ingestion jobs |
| GET | /ingestion/jobs/:id | Single ingestion job |
