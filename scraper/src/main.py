import logging

from src.config.feeds import FEED_SOURCES
from src.config.settings import settings
from src.database.connection import get_db_transaction
from src.database.repository import ArticleRepository, IngestionStats
from src.extraction.extractor import enrich_articles
from src.feeds.fetcher import fetch_all
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_rss_ingestion() -> IngestionStats:
    logging.basicConfig(level=settings.log_level)

    logger.info("Starting RSS ingestion cycle...")
    results = fetch_all(FEED_SOURCES)

    stats = IngestionStats(feeds_processed=len(results))
    repo = ArticleRepository()

    # 1. Enrich articles with extracted page content
    for result in results:
        if not result.ok or not result.articles:
            continue

        stats.articles_seen += len(result.articles)
        enrich_articles(result.articles)

        failed_extractions = sum(1 for a in result.articles if a.content is None)
        stats.articles_extraction_failed += failed_extractions

    # 2. Persist to PostgreSQL database
    if settings.database_url:
        try:
            with get_db_transaction() as conn:
                for result in results:
                    if not result.ok or not result.articles:
                        continue

                    source_id, is_new = repo.ensure_source(conn, result.source)
                    if is_new:
                        stats.sources_created += 1

                    for article in result.articles:
                        status = repo.save_article(conn, source_id, article)
                        if status == "inserted":
                            stats.articles_inserted += 1
                        elif status in ("duplicate", "updated"):
                            stats.articles_skipped_duplicate += 1
                        else:
                            stats.articles_failed += 1
        except Exception as exc:
            logger.error("Database persistence failed: %s", exc)
    else:
        logger.warning("DATABASE_URL not set; skipping database persistence step.")

    # 3. Topic Clustering Pass
    num_clusters, num_assigned = run_topic_clustering()

    logger.info(
        "Phase 2D Ingestion & Clustering Summary:\n"
        "  Feeds Processed:           %d\n"
        "  Sources Created:           %d\n"
        "  Articles Seen:             %d\n"
        "  Extraction Failed:         %d\n"
        "  Articles Persisted (New):  %d\n"
        "  Articles Skipped (Dup):    %d\n"
        "  Articles Failed:           %d\n"
        "  Topic Clusters Created:    %d\n"
        "  Articles Clustered:        %d",
        stats.feeds_processed,
        stats.sources_created,
        stats.articles_seen,
        stats.articles_extraction_failed,
        stats.articles_inserted,
        stats.articles_skipped_duplicate,
        stats.articles_failed,
        num_clusters,
        num_assigned,
    )
    return stats


def run_topic_clustering() -> tuple[int, int]:
    """Execute topic clustering pass on all stored database articles."""
    from src.clustering.clusterer import perform_clustering

    if not settings.database_url:
        logger.warning("DATABASE_URL not set; skipping topic clustering.")
        return 0, 0

    repo = ArticleRepository()
    try:
        with get_db_transaction() as conn:
            raw_articles = repo.get_all_articles(conn)
            clusters = perform_clustering(raw_articles)
            num_clusters, num_assigned = repo.save_clusters(conn, clusters)
            return num_clusters, num_assigned
    except Exception as exc:
        logger.error("Topic clustering pass failed: %s", exc)
        return 0, 0


if __name__ == "__main__":
    run_rss_ingestion()
