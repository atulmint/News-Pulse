"""
Phase 2D unit tests: Topic clustering using TF-IDF, Cosine Similarity, Connected Components, and label generation.
All tests use synthetic dataset objects — no live web or production database dependencies.
"""
from __future__ import annotations

import pytest

from src.clustering.clusterer import (
    CLUSTER_SIMILARITY_THRESHOLD,
    RawArticleData,
    perform_clustering,
    prepare_clustering_text,
)


def _art(
    id: str,
    title: str,
    summary: str | None = None,
    content: str | None = None,
    source_id: str = "src-default",
) -> RawArticleData:
    return RawArticleData(
        id=id,
        title=title,
        summary=summary,
        content=content,
        source_id=source_id,
        url=f"https://example.com/article-{id}",
    )


class TestTopicClusteringUnit:
    def test_two_similar_articles_form_same_cluster(self):
        art1 = _art(
            "1",
            "Ukraine and Russia peace talks resume in Geneva",
            summary="Delegates from Ukraine and Russia hold negotiations for ceasefire.",
            content="Official peace discussions between Ukraine and Russia continued in Switzerland.",
        )
        art2 = _art(
            "2",
            "Geneva hosts new round of Ukraine Russia peace negotiations",
            summary="Delegations meet in Geneva to negotiate ceasefire in Ukraine Russia conflict.",
            content="Peace talks involving Ukraine and Russia delegations began today in Geneva.",
        )
        clusters = perform_clustering([art1, art2], similarity_threshold=0.20)

        assert len(clusters) == 1
        assert set(clusters[0].article_ids) == {"1", "2"}
        assert len(clusters[0].label) > 0

    def test_unrelated_articles_remain_separate(self):
        art1 = _art(
            "1",
            "Ukraine and Russia peace talks resume in Geneva",
            content="Delegates from Ukraine and Russia hold negotiations for ceasefire.",
        )
        art2 = _art(
            "2",
            "James Webb Space Telescope discovers ancient galaxy cluster",
            content="Astronomers observe distant cosmic formations using infrared imaging technology.",
        )
        clusters = perform_clustering([art1, art2], similarity_threshold=0.25)

        assert len(clusters) == 0  # Unrelated articles remain unclustered

    def test_different_sources_form_same_cluster(self):
        bbc_art = _art("bbc-1", "Federal Reserve interest rate decisions update", source_id="bbc")
        npr_art = _art("npr-1", "Federal Reserve interest rate decisions announcement", source_id="npr")

        clusters = perform_clustering([bbc_art, npr_art], similarity_threshold=0.25)

        assert len(clusters) == 1
        assert set(clusters[0].article_ids) == {"bbc-1", "npr-1"}

    def test_source_name_does_not_influence_similarity(self):
        # Two articles with completely different content but different sources
        art1 = _art("1", "Climate change agreement signed in Paris", source_id="BBC World News")
        art2 = _art("2", "Global semiconductor manufacturing market expands", source_id="BBC World News")

        clusters = perform_clustering([art1, art2], similarity_threshold=0.25)
        assert len(clusters) == 0

    def test_empty_or_insufficient_text_handled_safely(self):
        art1 = _art("1", "", summary=None, content=None)
        art2 = _art("2", "a", summary="b", content="c")

        clusters = perform_clustering([art1, art2])
        assert clusters == []

    def test_single_article_dataset_returns_empty(self):
        art1 = _art("1", "Single article title headline")
        clusters = perform_clustering([art1])
        assert clusters == []

    def test_empty_dataset_returns_empty(self):
        clusters = perform_clustering([])
        assert clusters == []

    def test_deterministic_cluster_labels(self):
        art1 = _art("1", "Federal Reserve cuts interest rates again")
        art2 = _art("2", "Federal Reserve interest rate cuts boost stocks")

        c1 = perform_clustering([art1, art2], similarity_threshold=0.20)
        c2 = perform_clustering([art1, art2], similarity_threshold=0.20)

        assert len(c1) == 1
        assert len(c2) == 1
        assert c1[0].label == c2[0].label
        assert "Federal" in c1[0].label or "Reserve" in c1[0].label or "Rate" in c1[0].label

    def test_rerunning_clustering_produces_stable_assignments(self):
        art1 = _art(
            "1",
            "Oil prices rise following OPEC supply reductions",
            summary="Oil prices rise as OPEC cuts crude production across international markets.",
        )
        art2 = _art(
            "2",
            "OPEC crude oil supply cuts drive energy market prices up",
            summary="Energy markets react as OPEC reduces oil production quotas worldwide.",
        )
        art3 = _art(
            "3",
            "Unrelated technology news about artificial intelligence chips",
            summary="Semiconductor manufacturers launch next-gen AI hardware acceleration chips.",
        )

        dataset = [art1, art2, art3]

        c1 = perform_clustering(dataset, similarity_threshold=0.20)
        c2 = perform_clustering(dataset, similarity_threshold=0.20)

        assert len(c1) == len(c2) == 1
        assert set(c1[0].article_ids) == set(c2[0].article_ids) == {"1", "2"}

    def test_prepare_clustering_text_truncates_long_content(self):
        long_body = "x " * 2000
        text = prepare_clustering_text("Title", "Summary", long_body)

        assert "title" in text
        assert "summary" in text
        assert len(text) < 3000

    def test_cluster_label_eliminates_redundant_and_duplicate_words(self):
        from src.clustering.clusterer import _generate_cluster_label
        import numpy as np

        # Mock TF-IDF matrix with feature names containing unigram and bigram overlap
        feature_names = np.array(["sheeran", "macklemore", "ed sheeran", "concert"])
        comp_tfidf = np.array([
            [1.0, 0.8, 0.9, 0.5],
            [0.9, 0.7, 0.8, 0.4],
        ])

        label = _generate_cluster_label(comp_tfidf, feature_names)

        # "Sheeran" should appear only ONCE in the label
        words_in_label = [w.lower() for w in label.split()]
        assert words_in_label.count("sheeran") == 1
        assert "Macklemore" in label
        assert len(words_in_label) <= 4
