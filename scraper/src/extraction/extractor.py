from __future__ import annotations

import re
from typing import Any

import httpx
import trafilatura
from bs4 import BeautifulSoup

from src.config.settings import settings
from src.normalization.normalizer import NormalizedArticle
from src.utils.hashing import sha256_hash
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Minimum character length for an article body to be considered valid content.
MIN_CONTENT_LENGTH = 100

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_NOISY_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "iframe"}
_WHITESPACE = re.compile(r"[ \t]+")
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def extract_article_content(
    url: str,
    client: httpx.Client | None = None,
    timeout: int = settings.http_timeout_seconds,
) -> str | None:
    """Fetch HTML for a given URL and extract clean text using Trafilatura or BeautifulSoup fallback."""
    html_content = _fetch_page_html(url, client=client, timeout=timeout)
    if not html_content:
        return None

    # 1. Primary extraction strategy: Trafilatura
    content = _extract_with_trafilatura(html_content)
    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content

    # 2. Fallback extraction strategy: BeautifulSoup
    content = _extract_with_beautifulsoup(html_content)
    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content

    logger.warning("Extraction result below quality threshold (%d chars) for URL: %s", len(content or ""), url)
    return None


def enrich_article(
    article: NormalizedArticle,
    client: httpx.Client | None = None,
) -> NormalizedArticle:
    """Attempt article content extraction and attach content and content_hash to NormalizedArticle."""
    try:
        content = extract_article_content(article.url, client=client)
        if content:
            article.content = content
            article.content_hash = sha256_hash(content)
        else:
            article.content = None
            article.content_hash = None
            logger.warning(
                "Article extraction failed for %s (%s): %s",
                article.source_name, article.title, article.url,
            )
    except Exception as exc:
        logger.error(
            "Unexpected error extracting article content for %s (%s): %s",
            article.source_name, article.url, exc,
        )
        article.content = None
        article.content_hash = None

    return article


def enrich_articles(
    articles: list[NormalizedArticle],
    client: httpx.Client | None = None,
) -> list[NormalizedArticle]:
    """Enrich a list of normalized articles with extracted content. Continues on single article failure."""
    enriched = []
    own_client = False
    if client is None:
        client = httpx.Client(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": _DEFAULT_USER_AGENT},
        )
        own_client = True

    try:
        for article in articles:
            enriched.append(enrich_article(article, client=client))
    finally:
        if own_client:
            client.close()

    return enriched


def _fetch_page_html(
    url: str,
    client: httpx.Client | None = None,
    timeout: int = settings.http_timeout_seconds,
) -> str | None:
    headers = {
        "User-Agent": _DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        if client is not None:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as http_client:
            response = http_client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP error %s for URL: %s", exc.response.status_code, url)
        return None
    except httpx.RequestError as exc:
        logger.warning("Request error fetching URL %s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("Failed to fetch HTML for URL %s: %s", url, exc)
        return None


def _extract_with_trafilatura(html: str) -> str | None:
    try:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            fast=True,
        )
        if extracted:
            return _clean_text(extracted)
    except Exception as exc:
        logger.debug("Trafilatura extraction failed: %s", exc)
    return None


def _extract_with_beautifulsoup(html: str) -> str | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(_NOISY_TAGS):
            tag.decompose()

        # Look for semantic content containers
        containers = (
            soup.find_all("article")
            or soup.find_all("main")
            or soup.find_all(attrs={"class": re.compile(r"content|article|story|post", re.I)})
            or soup.find_all(attrs={"id": re.compile(r"content|article|story|post", re.I)})
        )

        text = ""
        if containers:
            best_container = max(containers, key=lambda c: len(c.get_text()))
            text = best_container.get_text(separator="\n\n")
        elif soup.body:
            text = soup.body.get_text(separator="\n\n")
        else:
            text = soup.get_text(separator="\n\n")

        cleaned = _clean_text(text)
        return cleaned if cleaned else None
    except Exception as exc:
        logger.debug("BeautifulSoup fallback extraction failed: %s", exc)
        return None


def _clean_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line_str = _WHITESPACE.sub(" ", line).strip()
        if line_str:
            lines.append(line_str)
    raw_joined = "\n\n".join(lines)
    return _MULTIPLE_NEWLINES.sub("\n\n", raw_joined).strip()
