"""
Phase 2B unit tests: Article page extraction, fallback strategies, quality checks, content hashing, and failure resilience.
All unit tests use mocked HTTP responses and fixtures — no live network requests.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.extraction.extractor import (
    MIN_CONTENT_LENGTH,
    enrich_article,
    enrich_articles,
    extract_article_content,
)
from src.normalization.normalizer import NormalizedArticle
from src.utils.hashing import sha256_hash

_SAMPLE_URL = "https://example.com/news/article-1"
_LONG_TEXT_PARAGRAPH = (
    "This is a comprehensive news report discussing significant updates and developments "
    "across various sectors. The investigation highlights key findings, historical data, and "
    "expert commentary to provide a full analysis of the situation."
)


def _make_article(url: str = _SAMPLE_URL, title: str = "Test Headline") -> NormalizedArticle:
    return NormalizedArticle(
        source_name="Test Publisher",
        source_feed_url="https://example.com/feed.xml",
        title=title,
        url=url,
        summary="Brief summary of the article.",
        guid="guid-123",
        published_at=None,
    )


class TestExtractorUnit:
    def test_successful_trafilatura_extraction(self):
        html = f"<html><body><article><p>{_LONG_TEXT_PARAGRAPH}</p></article></body></html>"
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)

        assert content is not None
        assert len(content) >= MIN_CONTENT_LENGTH
        assert "comprehensive news report" in content

    def test_trafilatura_returns_none_triggers_beautifulsoup_fallback(self):
        html = (
            "<html><body>"
            "<nav><a href='/'>Home</a></nav>"
            f"<main><p>{_LONG_TEXT_PARAGRAPH}</p></main>"
            "</body></html>"
        )
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        with patch("src.extraction.extractor.trafilatura.extract", return_value=None):
            content = extract_article_content(_SAMPLE_URL, client=mock_client)

        assert content is not None
        assert len(content) >= MIN_CONTENT_LENGTH
        assert "comprehensive news report" in content
        assert "Home" not in content

    def test_empty_html_returns_none(self):
        html = "<html><body></body></html>"
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is None

    def test_short_unusable_content_below_threshold_returns_none(self):
        html = "<html><body><p>Too short.</p></body></html>"
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is None

    def test_http_404_error_returns_none(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(status_code=404)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is None

    def test_http_500_error_returns_none(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(status_code=500)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is None

    def test_network_timeout_failure_returns_none(self):
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is None

    def test_malformed_html_handling(self):
        html = f"<div><p>{_LONG_TEXT_PARAGRAPH}<div><span>unclosed tags"
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        content = extract_article_content(_SAMPLE_URL, client=mock_client)
        assert content is not None
        assert "comprehensive news report" in content

    def test_html_strips_scripts_styles_and_nav(self):
        html = (
            "<html><head><style>body { color: red; }</style></head><body>"
            "<script>var tracker = 123;</script>"
            "<nav><a href='/'>Menu link</a></nav>"
            f"<article><p>{_LONG_TEXT_PARAGRAPH}</p></article>"
            "<footer>Copyright 2026</footer>"
            "</body></html>"
        )
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        with patch("src.extraction.extractor.trafilatura.extract", return_value=None):
            content = extract_article_content(_SAMPLE_URL, client=mock_client)

        assert content is not None
        assert "var tracker" not in content
        assert "color: red" not in content
        assert "Menu link" not in content
        assert "Copyright 2026" not in content
        assert "comprehensive news report" in content


class TestHashDeterminism:
    def test_same_content_produces_identical_hash(self):
        text = "Extracted news article body content for testing determinism."
        hash1 = sha256_hash(text)
        hash2 = sha256_hash(text)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_different_content_produces_different_hash(self):
        text1 = "Extracted news article body content A."
        text2 = "Extracted news article body content B."
        assert sha256_hash(text1) != sha256_hash(text2)


class TestPipelineEnrichmentAndResilience:
    def test_enrich_article_success(self):
        article = _make_article()
        html = f"<html><body><article><p>{_LONG_TEXT_PARAGRAPH}</p></article></body></html>"
        mock_response = MagicMock(status_code=200, text=html)
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        enriched = enrich_article(article, client=mock_client)

        assert enriched.content is not None
        assert enriched.content_hash == sha256_hash(enriched.content)
        assert enriched.cluster_id is None

    def test_enrich_article_failure_leaves_fields_none(self):
        article = _make_article()
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        enriched = enrich_article(article, client=mock_client)

        assert enriched.content is None
        assert enriched.content_hash is None
        assert enriched.cluster_id is None
        assert enriched.title == "Test Headline"  # Metadata preserved

    def test_enrich_articles_one_failure_does_not_stop_others(self):
        art1 = _make_article("https://example.com/1", "Article 1")
        art2 = _make_article("https://example.com/2", "Article 2")
        art3 = _make_article("https://example.com/3", "Article 3")

        html_good = f"<html><body><article><p>{_LONG_TEXT_PARAGRAPH}</p></article></body></html>"

        def mock_get(url, **kwargs):
            if "2" in url:
                resp = MagicMock(status_code=500)
                resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "500 Server Error", request=MagicMock(), response=resp
                )
                return resp
            return MagicMock(status_code=200, text=html_good)

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = mock_get

        results = enrich_articles([art1, art2, art3], client=mock_client)

        assert len(results) == 3
        assert results[0].content is not None
        assert results[0].content_hash is not None

        assert results[1].content is None
        assert results[1].content_hash is None

        assert results[2].content is not None
        assert results[2].content_hash is not None
