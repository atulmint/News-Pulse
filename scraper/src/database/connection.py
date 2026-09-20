from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import psycopg2

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_connection(db_url: str | None = None) -> psycopg2.extensions.connection:
    """Create a new PostgreSQL database connection using psycopg2."""
    target_url = db_url or settings.database_url
    if not target_url:
        raise ValueError("DATABASE_URL is not set in environment or settings.")
    try:
        conn = psycopg2.connect(target_url)
        return conn
    except Exception as exc:
        logger.error("Failed to connect to PostgreSQL database: %s", exc)
        raise


@contextmanager
def get_db_transaction(db_url: str | None = None) -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager providing a database connection with auto-commit/rollback transaction management."""
    conn = get_connection(db_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
