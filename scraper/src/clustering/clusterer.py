from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Centralized similarity threshold and text truncation limit
CLUSTER_SIMILARITY_THRESHOLD = 0.25
MAX_CONTENT_CHARS = 1000


@dataclass
class RawArticleData:
    id: str
    title: str
    summary: str | None = None
    content: str | None = None
    source_id: str | None = None
    url: str | None = None


@dataclass
class GeneratedCluster:
    id: str
    label: str
    representative_title: str
    article_ids: list[str] = field(default_factory=list)


def prepare_clustering_text(title: str, summary: str | None, content: str | None) -> str:
    """Combine title, summary, and truncated content into a normalized text string."""
    parts = [title or ""]
    if summary:
        parts.append(summary)
    if content:
        parts.append(content[:MAX_CONTENT_CHARS])
    raw_text = " ".join(parts)
    cleaned = re.sub(r"[^\w\s]", " ", raw_text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def perform_clustering(
    articles: list[RawArticleData],
    similarity_threshold: float = CLUSTER_SIMILARITY_THRESHOLD,
) -> list[GeneratedCluster]:
    """
    Groups related articles into topic clusters using TF-IDF + Cosine Similarity + Connected Components.
    Returns a list of GeneratedCluster objects containing assigned article IDs.
    """
    if len(articles) < 2:
        logger.info("Fewer than 2 articles provided; skipping clustering.")
        return []

    # 1. Prepare text corpus
    corpus = [
        prepare_clustering_text(a.title, a.summary, a.content)
        for a in articles
    ]

    valid_indices = [i for i, text in enumerate(corpus) if len(text) >= 10]
    if len(valid_indices) < 2:
        logger.info("Insufficient valid article text for clustering.")
        return []

    valid_articles = [articles[i] for i in valid_indices]
    valid_corpus = [corpus[i] for i in valid_indices]

    # 2. Vectorize using TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,
        sublinear_tf=True,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(valid_corpus)
    except Exception as exc:
        logger.error("TF-IDF vectorization failed: %s", exc)
        return []

    # 3. Pairwise cosine similarity matrix
    sim_matrix = cosine_similarity(tfidf_matrix)

    # 4. Connected Components grouping
    n = len(valid_articles)
    visited = [False] * n
    clusters: list[GeneratedCluster] = []

    feature_names = vectorizer.get_feature_names_out()

    for i in range(n):
        if visited[i]:
            continue

        component_indices = []
        queue = [i]
        visited[i] = True

        while queue:
            curr = queue.pop(0)
            component_indices.append(curr)

            for j in range(n):
                if not visited[j] and sim_matrix[curr, j] >= similarity_threshold:
                    visited[j] = True
                    queue.append(j)

        # Only create a cluster if 2 or more articles are grouped together
        if len(component_indices) >= 2:
            cluster_id = str(uuid.uuid4())
            comp_articles = [valid_articles[idx] for idx in component_indices]
            comp_tfidf = tfidf_matrix[component_indices]

            label = _generate_cluster_label(comp_tfidf, feature_names)
            rep_title = _find_representative_title(comp_articles, sim_matrix, component_indices)

            clusters.append(
                GeneratedCluster(
                    id=cluster_id,
                    label=label,
                    representative_title=rep_title,
                    article_ids=[a.id for a in comp_articles],
                )
            )

    logger.info("Clustering complete: generated %d clusters across %d articles.", len(clusters), len(articles))
    return clusters


def _generate_cluster_label(comp_tfidf: Any, feature_names: np.ndarray) -> str:
    """Generate a clean, deterministic, non-redundant cluster label from top TF-IDF terms."""
    try:
        summed_weights = np.asarray(comp_tfidf.sum(axis=0)).flatten()
        top_indices = summed_weights.argsort()[::-1]

        selected_terms: list[str] = []
        seen_words: set[str] = set()

        for idx in top_indices:
            raw_term = feature_names[idx].strip()
            term_words = [w.lower() for w in raw_term.split()]

            # Skip numeric tokens or words shorter than 3 chars
            if any(w.isdigit() or len(w) < 3 for w in term_words):
                continue

            # Avoid adding terms that overlap with already selected word tokens
            if any(w in seen_words for w in term_words):
                continue

            selected_terms.append(raw_term.title())
            seen_words.update(term_words)

            if len(selected_terms) >= 3:
                break

        if selected_terms:
            return " ".join(selected_terms)
    except Exception as exc:
        logger.debug("Cluster label generation error: %s", exc)

    return "General News"


def _find_representative_title(
    comp_articles: list[RawArticleData],
    sim_matrix: np.ndarray,
    component_indices: list[int],
) -> str:
    """Find the title of the article closest to the centroid of the cluster."""
    if len(comp_articles) == 1:
        return comp_articles[0].title

    sub_matrix = sim_matrix[np.ix_(component_indices, component_indices)]
    avg_similarities = sub_matrix.mean(axis=1)
    best_local_idx = int(np.argmax(avg_similarities))

    return comp_articles[best_local_idx].title
