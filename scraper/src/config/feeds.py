from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    name: str
    feed_url: str
    home_url: str


FEED_SOURCES: list[FeedSource] = [
    FeedSource(
        name="BBC World News",
        feed_url="https://feeds.bbci.co.uk/news/world/rss.xml",
        home_url="https://www.bbc.com/news",
    ),
    FeedSource(
        name="NPR News",
        feed_url="https://feeds.npr.org/1001/rss.xml",
        home_url="https://www.npr.org",
    ),
    FeedSource(
        name="The Guardian",
        feed_url="https://www.theguardian.com/world/rss",
        home_url="https://www.theguardian.com",
    ),
]
