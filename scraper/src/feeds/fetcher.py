from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import feedparser
import httpx

from src.config.feeds import FeedSource
from src.config.settings import settings
from src.normalization.normalizer import NormalizedArticle, normalize_entry
from src.utils.logger import get_logger

logger = get_logger(__name__)

_HEADERS = {
    "User-Agent": "NewsPulse/1.0 (RSS aggregator; contact: admin@newspulse.example)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
}


@dataclass
class FeedResult:
    source: FeedSource
    articles: list[NormalizedArticle]
    skipped: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def fetch_and_normalize(source: FeedSource) -> FeedResult:
    try:
        raw = _fetch_raw(source.feed_url)
    except Exception as exc:
        logger.error("Failed to fetch %s (%s): %s", source.name, source.feed_url, exc)
        return FeedResult(source=source, articles=[], skipped=0, error=str(exc))

    return _parse_and_normalize(source, raw)


def fetch_all(sources: list[FeedSource]) -> list[FeedResult]:
    results = []
    for source in sources:
        results.append(fetch_and_normalize(source))
    return results


# ── internals ────────────────────────────────────────────────────────────────

def _fetch_raw(url: str) -> bytes:
    with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
        response = client.get(url, headers=_HEADERS)
        response.raise_for_status()
        return response.content


def _parse_and_normalize(source: FeedSource, raw: bytes) -> FeedResult:
    feed = feedparser.parse(raw)

    # feedparser signals a hard parse failure via bozo + bozo_exception.
    if feed.bozo and not feed.entries:
        exc = getattr(feed, "bozo_exception", "unknown parse error")
        logger.error("Could not parse feed %s: %s", source.name, exc)
        return FeedResult(source=source, articles=[], skipped=0, error=str(exc))

    if feed.bozo:
        # Bozo but has entries — common for slightly malformed feeds; continue.
        logger.warning("Feed %s is not well-formed but yielded entries", source.name)

    articles: list[NormalizedArticle] = []
    skipped = 0

    for entry in feed.entries:
        article = normalize_entry(source.name, source.feed_url, entry)
        if article is not None:
            articles.append(article)
        else:
            skipped += 1

    logger.info(
        "%-20s  fetched=%d  normalized=%d  skipped=%d",
        source.name,
        len(feed.entries),
        len(articles),
        skipped,
    )
    return FeedResult(source=source, articles=articles, skipped=skipped)
