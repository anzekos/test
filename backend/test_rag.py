"""
test_rag.py — Smoke tests for the RAG pipeline.

Usage:
    cd backend
    python -m pytest test_rag.py -v
"""
import os
import sys
import shutil
import tempfile
import pytest

# Brez OpenAI in brez sidecarja — testi delujejo s dummy embeddingom
os.environ.pop("OPENAI_API_KEY", None)
_TEST_QDRANT_DIR = tempfile.mkdtemp(prefix="qdrant_test_")
os.environ["QDRANT_PATH"] = _TEST_QDRANT_DIR

sys.path.insert(0, os.path.dirname(__file__))


# Patch sidecar _wait_for_sidecar da ne čaka 30s v testih
import unittest.mock as mock

with mock.patch("vector_store.VectorStore._wait_for_sidecar"):
    from vector_store import VectorStore


@pytest.fixture(scope="module")
def store():
    with mock.patch.object(VectorStore, "_wait_for_sidecar"):
        s = VectorStore()
    yield s
    try:
        shutil.rmtree(_TEST_QDRANT_DIR, ignore_errors=True)
    except Exception:
        pass


# ---------- vector_store tests ----------

def test_dummy_embedding_length(store):
    """Dummy embedding mora vrniti 1024-dim list (multilingual-e5-large)."""
    # Patch sidecar da vrne napako → padec na dummy
    with mock.patch("requests.post", side_effect=Exception("no sidecar")):
        vec = store.embed_text("hello world")
    assert isinstance(vec, list)
    assert len(vec) == 1024  # FIX: bilo 1536, zdaj pravilno 1024


def test_dummy_embedding_deterministic(store):
    """Isti tekst mora vedno vrniti isti vektor."""
    with mock.patch("requests.post", side_effect=Exception("no sidecar")):
        a = store.embed_text("test determinism")
        b = store.embed_text("test determinism")
    assert a == b


def test_dummy_embedding_differs_for_different_text(store):
    """Različni teksti morajo dati različne vektorje."""
    with mock.patch("requests.post", side_effect=Exception("no sidecar")):
        a = store.embed_text("alpha")
        b = store.embed_text("beta")
    assert a != b


def test_upsert_and_search(store):
    """Upsert dokumenta in preveri da ga iskanje najde."""
    with mock.patch("requests.post", side_effect=Exception("no sidecar")):
        store.upsert_document(
            "pirs_collection",
            "test_doc_1",
            "Pogodba o zaposlitvi mora biti v pisni obliki.",
            {"source": "test", "section": "1"},
        )
        results = store.search("pirs_collection", "pogodba zaposlitev")
    assert len(results) >= 1
    assert "content" in results[0]


def test_upsert_batch_and_count(store):
    """Batch upsert in preveri collection_count."""
    items = [
        {"id": "batch_1", "content": "Dokument ena.", "metadata": {"src": "b1"}},
        {"id": "batch_2", "content": "Dokument dva.", "metadata": {"src": "b2"}},
        {"id": "batch_3", "content": "Dokument tri.", "metadata": {"src": "b3"}},
    ]
    with mock.patch("requests.post", side_effect=Exception("no sidecar")):
        store.upsert_batch("mfiles_collection", items)
    count = store.collection_count("mfiles_collection")
    assert count >= 3


# ---------- lazy-init tests ----------

def test_pirs_retriever_lazy_init():
    """PIRSRetriever._indexed mora biti False takoj po konstrukciji."""
    from pirs_rag import PIRSRetriever
    r = PIRSRetriever()
    assert r._indexed is False


def test_mfiles_retriever_lazy_init():
    """MFilesRetriever._indexed mora biti False takoj po konstrukciji."""
    from mfiles_rag import MFilesRetriever
    r = MFilesRetriever()
    assert r._indexed is False