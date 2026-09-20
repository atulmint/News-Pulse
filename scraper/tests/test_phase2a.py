"""
Phase 2A unit tests: RSS normalization and feed fetch failure handling.
All tests use fixture data — no live HTTP calls.
"""
from __future__ import annotations

import types
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.config.feeds import FeedSource
from src.feeds.fetcher import _parse_and_normalize
from src.normalization.normalizer import normalize_entry


def _entry(**kwargs) -> types.SimpleNamespace:
    defaults = {
        "title": "",
        "link": "",
        "id": None,
        "summary": "",
        "content": [],
        "published_parsed": None,
        "published": "",
        "updated": "",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


SOURCE = FeedSource(
    name="Test Source",
    feed_url="https://example.com/feed.xml",
    home_url="https://example.com",
)


class TestNormalizeEntry:
    def test_basic_rss_entry(self):
        entry = _entry(
            title="Test Headline",
            link="https://example.com/article",
            id="guid-001",
            summary="Short description.",
            published_parsed=(2024, 3, 15, 10, 0, 0, 4, 75, 0),
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.title == "Test Headline"
        assert article.url == "https://example.com/article"
        assert article.guid == "guid-001"
        assert article.summary == "Short description."
        assert article.published_at == datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)

    def test_content_encoded_preferred_over_description(self):
        entry = _entry(
            title="Article",
            link="https://example.com/article",
            content=[{"value": "<p>Full body text.</p>", "type": "text/html"}],
            summary="Short summary only.",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.summary == "Full body text."

    def test_description_fallback_when_no_content(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a",
            summary="<p>Description text.</p>",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.summary == "Description text."

    def test_published_string_fallback(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a",
            published="Mon, 18 Mar 2024 09:30:00 +0000",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.published_at is not None
        assert article.published_at.year == 2024
        assert article.published_at.month == 3
        assert article.published_at.day == 18
        assert article.published_at.tzinfo is not None

    def test_published_string_without_timezone_is_naive(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a",
            published="2024-03-18 09:30:00",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.published_at is not None
        assert article.published_at.year == 2024
        assert article.published_at.tzinfo is None

    def test_no_published_date_returns_none(self):
        entry = _entry(title="Article", link="https://example.com/a")
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.published_at is None

    def test_malformed_date_returns_none(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a",
            published="not-a-date-at-all",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.published_at is None

    def test_missing_guid_is_none(self):
        entry = _entry(title="Article", link="https://example.com/a", id=None)
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.guid is None

    def test_html_stripped_from_summary(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a",
            summary="<p>Clean <b>text</b> with <a href='x'>a link</a>.</p>",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert "<" not in article.summary
        assert "Clean" in article.summary
        assert "text" in article.summary

    def test_no_title_returns_none(self):
        assert normalize_entry(SOURCE.name, SOURCE.feed_url, _entry(title="", link="https://example.com/a")) is None

    def test_no_link_returns_none(self):
        assert normalize_entry(SOURCE.name, SOURCE.feed_url, _entry(title="Article", link="")) is None

    def test_url_query_stripped(self):
        entry = _entry(
            title="Article",
            link="https://example.com/a?utm_source=rss&utm_medium=feed",
        )
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert "?" not in article.url
        assert article.url == "https://example.com/a"

    def test_later_phase_fields_are_none(self):
        entry = _entry(title="A", link="https://example.com/a")
        article = normalize_entry(SOURCE.name, SOURCE.feed_url, entry)

        assert article is not None
        assert article.content is None
        assert article.content_hash is None
        assert article.cluster_id is None


class TestFetcherFailureHandling:
    def test_http_failure_returns_error_result(self):
        import httpx

        with patch("src.feeds.fetcher._fetch_raw", side_effect=httpx.ConnectError("refused")):
            from src.feeds.fetcher import fetch_and_normalize
            result = fetch_and_normalize(SOURCE)

        assert not result.ok
        assert result.articles == []

    def test_one_bad_feed_does_not_stop_another(self):
        import httpx

        bad_source = FeedSource("Bad", "https://bad.example/feed", "https://bad.example")
        good_source = FeedSource("Good", "https://good.example/feed", "https://good.example")

        good_rss = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>Good Article</title>
            <link>https://good.example/article</link>
            <description>OK</description>
          </item>
        </channel></rss>"""

        def fake_fetch(url: str) -> bytes:
            if "bad" in url:
                raise httpx.ConnectError("refused")
            return good_rss

        with patch("src.feeds.fetcher._fetch_raw", side_effect=fake_fetch):
            from src.feeds.fetcher import fetch_all
            results = fetch_all([bad_source, good_source])

        assert len(results) == 2
        bad_result, good_result = results
        assert not bad_result.ok
        assert good_result.ok
        assert len(good_result.articles) == 1
        assert good_result.articles[0].title == "Good Article"

    def test_valid_raw_rss_is_parsed(self):
        raw_rss = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>Test Article</title>
            <link>https://example.com/test</link>
            <description>Testing.</description>
          </item>
        </channel></rss>"""

        result = _parse_and_normalize(SOURCE, raw_rss)

        assert result.ok
        assert len(result.articles) == 1
        assert result.articles[0].title == "Test Article"

    def test_completely_unparseable_raw_bytes(self):
        result = _parse_and_normalize(SOURCE, b"this is not xml at all")
        # feedparser is permissive — no exception should propagate.
        assert isinstance(result.articles, list)
