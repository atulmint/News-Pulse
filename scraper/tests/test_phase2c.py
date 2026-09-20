"""
Phase 2C unit tests: PostgreSQL repository persistence, source upserting, article deduplication, and error isolation.
All unit tests use mocked database connections and cursors.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.config.feeds import FeedSource
from src.database.repository import ArticleRepository
from src.normalization.normalizer import NormalizedArticle
from src.utils.hashing import sha256_hash

_TEST_SOURCE = FeedSource(
    name="Test Source",
    feed_url="https://example.com/feed.xml",
    home_url="https://example.com",
)


def _make_article(
    url: str = "https://example.com/article-1",
    guid: str | None = "guid-001",
    content: str | None = "Extracted body text for unit test verification.",
    title: str = "Sample Article Headline",
) -> NormalizedArticle:
    chash = sha256_hash(content) if content else None
    return NormalizedArticle(
        source_name="Test Source",
        source_feed_url="https://example.com/feed.xml",
        title=title,
        url=url,
        summary="Brief summary excerpt",
        guid=guid,
        published_at=None,
        content=content,
        content_hash=chash,
        cluster_id=None,
    )


class TestSourceUpsert:
    def test_ensure_source_inserts_new_source(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = ArticleRepository()
        source_id, is_new = repo.ensure_source(mock_conn, _TEST_SOURCE)

        assert is_new is True
        assert isinstance(source_id, str)
        assert len(source_id) > 0
        mock_cursor.execute.assert_called()
        # Verify SELECT and INSERT called
        assert mock_cursor.execute.call_count == 2
        insert_args = mock_cursor.execute.call_args_list[1][0]
        assert "INSERT INTO sources" in insert_args[0]
        assert insert_args[1][1] == _TEST_SOURCE.name
        assert insert_args[1][2] == _TEST_SOURCE.feed_url

    def test_ensure_source_reuses_existing_source(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("existing-uuid-1234",)

        repo = ArticleRepository()
        source_id, is_new = repo.ensure_source(mock_conn, _TEST_SOURCE)

        assert is_new is False
        assert source_id == "existing-uuid-1234"
        assert mock_cursor.execute.call_count == 1


class TestArticleDeduplication:
    def test_save_article_inserts_new_article(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = ArticleRepository()
        article = _make_article()
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "inserted"
        # Check that cluster_id is NULL in INSERT query
        insert_args = mock_cursor.execute.call_args_list[1][0]
        sql_query = insert_args[0]
        params = insert_args[1]

        assert "INSERT INTO articles" in sql_query
        assert "NULL" in sql_query  # cluster_id = NULL
        assert params[1] == "src-123"
        assert params[2] == article.title
        assert params[3] == article.url

    def test_save_article_duplicate_guid_skipped(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("existing-art-id", "Existing content body")

        repo = ArticleRepository()
        article = _make_article(guid="guid-dup")
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "duplicate"

    def test_save_article_duplicate_url_skipped(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("existing-art-id", "Existing content body")

        repo = ArticleRepository()
        article = _make_article(guid=None, url="https://example.com/duplicate")
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "duplicate"

    def test_existing_content_not_overwritten_by_null(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        # DB already has content
        mock_cursor.fetchone.return_value = ("art-100", "Existing good body text")

        repo = ArticleRepository()
        # New extraction failed (content is None)
        article = _make_article(content=None)
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "duplicate"
        # Ensure UPDATE query was NOT executed
        for call in mock_cursor.execute.call_args_list:
            assert "UPDATE articles" not in call[0][0]

    def test_updates_content_if_previously_null(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        # DB previously had no content (content is None)
        mock_cursor.fetchone.return_value = ("art-100", None)

        repo = ArticleRepository()
        article = _make_article(content="Newly extracted article content body.")
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "updated"
        update_call = mock_cursor.execute.call_args_list[1][0]
        assert "UPDATE articles SET content =" in update_call[0]

    def test_different_sources_can_share_content_hash(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = ArticleRepository()
        shared_text = "Syndicated article text published by multiple outlets."

        art_src1 = _make_article(url="https://source1.com/story", content=shared_text)
        art_src2 = _make_article(url="https://source2.com/story", content=shared_text)

        status1 = repo.save_article(mock_conn, "src-1", art_src1)
        status2 = repo.save_article(mock_conn, "src-2", art_src2)

        assert status1 == "inserted"
        assert status2 == "inserted"

    def test_nullable_guid_does_not_cause_global_dedup(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = ArticleRepository()
        art1 = _make_article(url="https://example.com/a1", guid=None)
        art2 = _make_article(url="https://example.com/a2", guid=None)

        status1 = repo.save_article(mock_conn, "src-1", art1)
        status2 = repo.save_article(mock_conn, "src-1", art2)

        assert status1 == "inserted"
        assert status2 == "inserted"

    def test_parameterized_sql_used_for_queries(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = ArticleRepository()
        article = _make_article(title="SQL' Injection Test --")
        repo.save_article(mock_conn, "src-123", article)

        for call in mock_cursor.execute.call_args_list:
            sql, params = call[0]
            assert isinstance(params, tuple)
            assert "SQL' Injection Test --" not in sql  # Title must be in params, not formatted SQL

    def test_single_article_failure_returns_failed_status(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB Disk I/O error")

        repo = ArticleRepository()
        article = _make_article()
        status = repo.save_article(mock_conn, "src-123", article)

        assert status == "failed"
