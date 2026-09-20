from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import psycopg2

from src.config.feeds import FeedSource
from src.normalization.normalizer import NormalizedArticle
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IngestionStats:
    feeds_processed: int = 0
    articles_seen: int = 0
    articles_inserted: int = 0
    articles_skipped_duplicate: int = 0
    articles_extraction_failed: int = 0
    articles_failed: int = 0
    sources_created: int = 0


class ArticleRepository:
    def ensure_source(self, conn: Any, source: FeedSource) -> tuple[str, bool]:
        """Look up existing source by feed_url or insert a new source. Returns (source_id, is_new)."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM sources WHERE feed_url = %s LIMIT 1;",
                (source.feed_url,),
            )
            row = cur.fetchone()
            if row:
                source_id = row[0] if isinstance(row, (list, tuple)) else row["id"]
                return source_id, False

            new_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO sources (id, name, feed_url, home_url, created_at)
                VALUES (%s, %s, %s, %s, NOW());
                """,
                (new_id, source.name, source.feed_url, source.home_url),
            )
            return new_id, True

    def save_article(self, conn: Any, source_id: str, article: NormalizedArticle) -> str:
        """
        Idempotently insert an article or update missing content.
        Returns status string: 'inserted', 'duplicate', 'updated', or 'failed'.
        """
        try:
            with conn.cursor() as cur:
                existing_id = None
                existing_content = None

                if article.guid:
                    cur.execute(
                        "SELECT id, content FROM articles WHERE (source_id = %s AND guid = %s) OR url = %s LIMIT 1;",
                        (source_id, article.guid, article.url),
                    )
                else:
                    cur.execute(
                        "SELECT id, content FROM articles WHERE url = %s LIMIT 1;",
                        (article.url,),
                    )

                row = cur.fetchone()
                if row:
                    existing_id = row[0] if isinstance(row, (list, tuple)) else row["id"]
                    existing_content = row[1] if isinstance(row, (list, tuple)) else row["content"]

                if existing_id:
                    # Do not overwrite existing content with NULL if extraction failed
                    if existing_content is None and article.content is not None:
                        cur.execute(
                            "UPDATE articles SET content = %s, content_hash = %s WHERE id = %s;",
                            (article.content, article.content_hash, existing_id),
                        )
                        return "updated"
                    return "duplicate"

                new_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO articles (
                        id, source_id, cluster_id, title, url, guid,
                        published_at, content, summary, content_hash, created_at
                    ) VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NOW());
                    """,
                    (
                        new_id,
                        source_id,
                        article.title,
                        article.url,
                        article.guid,
                        article.published_at,
                        article.content,
                        article.summary,
                        article.content_hash,
                    ),
                )
                return "inserted"
        except psycopg2.IntegrityError as exc:
            if hasattr(conn, "rollback"):
                conn.rollback()
            logger.warning("Duplicate key integrity catch for %s: %s", article.url, exc)
            return "duplicate"
        except Exception as exc:
            if hasattr(conn, "rollback"):
                conn.rollback()
            logger.error("Failed to persist article %s (%s): %s", article.title, article.url, exc)
            return "failed"

    def get_all_articles(self, conn: Any) -> list[RawArticleData]:
        """Fetch all stored articles from database for topic clustering."""
        from src.clustering.clusterer import RawArticleData

        with conn.cursor() as cur:
            cur.execute("SELECT id, title, summary, content, source_id, url FROM articles;")
            rows = cur.fetchall()
            articles = []
            for r in rows:
                articles.append(
                    RawArticleData(
                        id=r[0],
                        title=r[1],
                        summary=r[2],
                        content=r[3],
                        source_id=r[4],
                        url=r[5],
                    )
                )
            return articles

    def save_clusters(self, conn: Any, clusters: list[Any]) -> tuple[int, int]:
        """
        Atomically clear old clusters and persist new generated clusters.
        Returns (num_clusters_created, num_articles_assigned).
        """
        with conn.cursor() as cur:
            cur.execute("UPDATE articles SET cluster_id = NULL;")
            cur.execute("DELETE FROM clusters;")

            total_assigned = 0
            for cluster in clusters:
                cur.execute(
                    """
                    INSERT INTO clusters (id, label, representative_title, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW());
                    """,
                    (cluster.id, cluster.label, cluster.representative_title),
                )

                if cluster.article_ids:
                    cur.execute(
                        "UPDATE articles SET cluster_id = %s WHERE id IN %s;",
                        (cluster.id, tuple(cluster.article_ids)),
                    )
                    total_assigned += len(cluster.article_ids)

            return len(clusters), total_assigned
