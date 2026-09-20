import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # None when DATABASE_URL is not set; validated at connection time.
    database_url: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    http_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_SECONDS", "15"))
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()

