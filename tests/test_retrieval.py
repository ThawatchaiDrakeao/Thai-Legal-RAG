import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from query import INDEX_PATH, META_PATH, load, search


@pytest.fixture(scope="module")
def retrieval_resources():
    index, meta, model = load()
    return index, meta, model


def test_index_and_metadata_have_same_length(retrieval_resources):
    index, meta, _ = retrieval_resources
    assert INDEX_PATH.exists()
    assert META_PATH.exists()
    assert index.ntotal == len(meta)


def test_thai_query_returns_relevant_top_result(retrieval_resources):
    index, meta, model = retrieval_resources
    results = search("มาตรา 1 กล่าวถึงอะไร", index, meta, model, top_k=3)

    assert results
    assert results[0]["score"] > 0.5
    assert results[0]["source"]


def test_exact_match_with_full_sentence_and_prefixed_article_id():
    """Regression test: article_id like 'มาตรา 420' (not a bare number) must
    still match via exact article-number extraction, even in a long sentence."""
    from src.query import load, search

    index, meta, model = load()
    results = search(
        "มาตรา 420 แห่งประมวลกฎหมายแพ่งและพาณิชย์กล่าวถึงเรื่องอะไร",
        index, meta, model, top_k=3,
    )
    assert results[0]["exact_match"] is True
    assert results[0]["article_number"] == 420
