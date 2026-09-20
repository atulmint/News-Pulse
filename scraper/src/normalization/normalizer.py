from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from src.utils.hashing import normalise_url
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NormalizedArticle:
    source_name: str
    source_feed_url: str
    title: str
    url: str
    summary: str          # cleaned plain-text excerpt from the feed
    guid: str | None
    published_at: datetime | None
    # Fields populated by later phases — kept here so the schema is stable.
    content: str | None = field(default=None)
    content_hash: str | None = field(default=None)
    cluster_id: str | None = field(default=None)


def normalize_entry(source_name: str, source_feed_url: str, entry: Any) -> NormalizedArticle | None:
    title = _extract_title(entry)
    if not title:
        logger.warning("Skipping entry with no title from %s", source_name)
        return None

    url = _extract_url(entry)
    if not url:
        logger.warning("Skipping entry with no link from %s: %r", source_name, title)
        return None

    return NormalizedArticle(
        source_name=source_name,
        source_feed_url=source_feed_url,
        title=title,
        url=normalise_url(url),
        summary=_extract_summary(entry),
        guid=_extract_guid(entry),
        published_at=_extract_published(entry, source_name, title),
    )


# ── field extraction ──────────────────────────────────────────────────────────

def _extract_title(entry: Any) -> str:
    raw = getattr(entry, "title", "") or ""
    return _strip_html(raw).strip()


def _extract_url(entry: Any) -> str:
    link = getattr(entry, "link", "") or ""
    return link.strip()


def _extract_guid(entry: Any) -> str | None:
    guid = getattr(entry, "id", None)
    return guid.strip() if isinstance(guid, str) else None


def _extract_summary(entry: Any) -> str:
    # content:encoded > description/summary — in that order of preference.
    content_list = getattr(entry, "content", None) or []
    if content_list:
        raw = content_list[0].get("value", "") if isinstance(content_list[0], dict) else ""
        if raw:
            return _strip_html(raw).strip()

    for attr in ("summary", "description"):
        raw = getattr(entry, attr, "") or ""
        if raw:
            return _strip_html(raw).strip()

    return ""


def _extract_published(entry: Any, source_name: str, title: str) -> datetime | None:
    # feedparser pre-parses dates into published_parsed (time.struct_time, UTC).
    # Prefer that to avoid re-parsing ambiguous strings.
    parsed_struct = getattr(entry, "published_parsed", None)
    if parsed_struct is not None:
        try:
            return datetime(*parsed_struct[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    for attr in ("published", "updated", "pubDate"):
        raw = getattr(entry, attr, "") or ""
        if raw:
            return _parse_date_string(raw, source_name, title)

    return None


def _parse_date_string(raw: str, source_name: str, title: str) -> datetime | None:
    try:
        dt = dateutil_parser.parse(raw)
        return dt
    except Exception as exc:
        logger.warning(
            "Could not parse date %r for %r (%s): %s",
            raw, title, source_name, exc,
        )
        return None


# ── HTML cleaning ─────────────────────────────────────────────────────────────

_WHITESPACE = re.compile(r"[ \t]+")
_NEWLINES = re.compile(r"\n{3,}")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    if "<" not in text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ")
    clean = _WHITESPACE.sub(" ", clean)
    clean = _NEWLINES.sub("\n\n", clean)
    return clean.strip()
