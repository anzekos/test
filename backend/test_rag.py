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

# Force dummy embeddings for tests (no OpenAI key needed)
os.environ.pop("OPENAI_API_KEY", None)
# Use a temporary Qdrant path so tests don't pollute the real DB
_TEST_QDRANT_DIR = tempfile.mkdtemp(prefix="qdrant_test_")
os.environ["QDRANT_PATH"] = _TEST_QDRANT_DIR

# Ensure backend/ is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import after env setup so singletons pick up test config
from vector_store import VectorStore  # noqa: E402


@pytest.fixture(scope="module")
def store():
    """Create a fresh VectorStore for the test session."""
    s = VectorStore()
    yield s
    # Cleanup
    try:
        shutil.rmtree(_TEST_QDRANT_DIR, ignore_errors=True)
    except Exception:
        pass


# ---------- vector_store tests ----------

def test_dummy_embedding_length(store):
    """Dummy embedding should return a 1536-dim list."""
    vec = store.embed_text("hello world")
    assert isinstance(vec, list)
    assert len(vec) == 1536


def test_dummy_embedding_deterministic(store):
    """Same input text must produce the exact same embedding."""
    a = store.embed_text("test determinism")
    b = store.embed_text("test determinism")
    assert a == b


def test_dummy_embedding_differs_for_different_text(store):
    """Different inputs should produce different embeddings."""
    a = store.embed_text("alpha")
    b = store.embed_text("beta")
    assert a != b


def test_upsert_and_search(store):
    """Upsert a document and verify it can be found via search."""
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
    """Batch upsert several docs then verify collection_count."""
    items = [
        {"id": "batch_1", "content": "Dokument ena.", "metadata": {"src": "b1"}},
        {"id": "batch_2", "content": "Dokument dva.", "metadata": {"src": "b2"}},
        {"id": "batch_3", "content": "Dokument tri.", "metadata": {"src": "b3"}},
    ]
    store.upsert_batch("mfiles_collection", items)
    count = store.collection_count("mfiles_collection")
    assert count >= 3


# ---------- lazy-init tests ----------

def test_pirs_retriever_lazy_init():
    """PIRSRetriever._indexed should be False right after construction."""
    from pirs_rag import PIRSRetriever

    r = PIRSRetriever()
    assert r._indexed is False


def test_mfiles_retriever_lazy_init():
    """MFilesRetriever._indexed should be False right after construction."""
    from mfiles_rag import MFilesRetriever

    r = MFilesRetriever()
    assert r._indexed is False
