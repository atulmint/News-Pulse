import hashlib


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalise_url(url: str) -> str:
    """Strip query strings and trailing slashes for deduplication comparison."""
    return url.rstrip("/").split("?")[0]
