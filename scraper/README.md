# News Pulse — Scraper

Python ingestion pipeline for News Pulse.

## Responsibilities

1. Fetch articles from configured RSS/Atom feeds.
2. Normalize inconsistent feed data to a canonical schema.
3. Fetch each article page and extract the main body text.
4. Deduplicate articles across repeated ingestion runs.
5. Cluster related articles by topic.
6. Persist results to PostgreSQL.

## Project layout

`
scraper/
|-- src/
|   |-- config/         # Feed list, runtime settings
|   |-- feeds/          # RSS fetching and parsing
|   |-- normalization/  # Canonical article schema + field mapping
|   |-- extraction/     # Article body extraction (trafilatura / BS4)
|   |-- deduplication/  # Duplicate detection logic
|   |-- clustering/     # TF-IDF + cosine similarity clustering
|   |-- database/       # PostgreSQL session + repository layer
|   |-- utils/          # Shared helpers (logging, hashing, dates)
|   |-- main.py         # Pipeline entry-point
|-- tests/              # pytest unit and integration tests
|-- requirements.txt
|-- .env.example
`

## Setup

`ash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL
`

## Running the pipeline

`ash
python -m src.main
`

## Running tests

`ash
pytest tests/
`
