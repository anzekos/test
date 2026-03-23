# Implementation Plan — Backend Bug Fixes

## Changes Made

### vector_store.py
- **Dummy embedding fallback**: When `OPENAI_API_KEY` is missing, `embed_text()` returns a deterministic 1536-dim vector derived from SHA-512 hash of the input text. Server no longer crashes without the key.
- **`collection_count(name)`**: Returns the number of points stored in a given Qdrant collection.
- **`upsert_batch(collection_name, items)`**: Batch-upserts a list of `{id, content, metadata}` dicts in a single Qdrant call.

### pirs_rag.py
- Moved `_ensure_index()` out of `__init__` into a lazy guard inside `retrieve()`. Runs once on first query, not on import.

### mfiles_rag.py
- Same lazy `_ensure_index()` pattern as `pirs_rag.py`.

### mfiles_client.py
- `fetch_documents()` now actually fetches objects from `/objects`, lists files from `/objects/0/{id}/{version}/files`, downloads content from `.../files/{file_id}/content`, and extracts plain text.
- Falls back to mock documents on any connection error (instead of returning `[]`).

## New Files
| File | Purpose |
|------|---------|
| `ingest_pirs.py` | Standalone script to populate `pirs_collection` |
| `test_rag.py` | Pytest smoke tests for the full RAG pipeline |
| `implementation_plan.md` | This file |
| `walkthrough.md` | Post-implementation walkthrough |

## Stack
FastAPI · Qdrant (local file-based) · OpenAI text-embedding-3-small
