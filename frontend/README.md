# News Pulse — Frontend

Next.js 14 frontend for News Pulse using the App Router and Tailwind CSS.

## Project layout

```
frontend/
|-- src/
|   |-- app/           # Next.js App Router pages and layouts
|   |-- components/    # Reusable UI components
|   |   |-- ui/        # Primitive UI elements (buttons, cards, etc.)
|   |-- features/      # Feature-oriented modules
|   |   |-- timeline/  # Visual timeline feature
|   |   |-- clusters/  # Cluster explorer feature
|   |   |-- ingestion/ # Ingestion control panel feature
|   |-- lib/           # Shared utilities (API client, helpers)
|   |-- types/         # Shared TypeScript type definitions
|-- public/            # Static assets
```

## Setup

```bash
cp .env.example .env.local   # fill in NEXT_PUBLIC_API_URL
npm install
npm run dev
```

## Features (Phase 4)

- **Timeline view** — visual timeline of article clusters by date
- **Cluster explorer** — browse articles within a topic cluster
- **Ingestion panel** — trigger the Python pipeline and watch progress
