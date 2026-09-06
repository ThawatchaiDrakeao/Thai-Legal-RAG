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
