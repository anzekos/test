# Walkthrough — Backend Bug Fixes

## Summary
Fixed 4 backend Python files and added 4 new files to the `backend/` directory.

## Bug Fixes

### 1. vector_store.py — Dummy Embedding Fallback
- **Problem**: Server crashed on startup if `OPENAI_API_KEY` was not set.
- **Fix**: Added `_dummy_embedding()` that produces a deterministic 1536-dim vector from SHA-512 hash. `embed_text()` uses it automatically when no API key is present.
- **Added**: `collection_count(name)` and `upsert_batch(collection_name, items)` helper methods.

### 2. pirs_rag.py — Lazy Index Init
- **Problem**: `_ensure_index()` ran in `__init__`, triggering embedding calls on module import.
- **Fix**: Moved to lazy call inside `retrieve()` guarded by `_indexed` flag. Runs once on first query.

### 3. mfiles_rag.py — Lazy Index Init
- **Problem**: Same eager `_ensure_index()` issue.
- **Fix**: Same lazy pattern with `_indexed` flag.

### 4. mfiles_client.py — Real Document Fetch
- **Problem**: `fetch_documents()` returned `[]` when authenticated.
- **Fix**: Walks `/objects` → `/objects/0/{id}/{version}/files` → `.../content`, extracts plain text. Returns mock documents if the server is unreachable (instead of empty list).

## New Files
| File | Purpose |
|------|---------|
| `ingest_pirs.py` | Standalone ingestion script for pirs_collection |
| `test_rag.py` | Pytest smoke tests (dummy embedding, upsert, search, lazy init) |
| `implementation_plan.md` | Change summary for the backend |
| `walkthrough.md` | This file |

## Verification
Run the smoke tests:
```bash
cd backend
python -m pytest test_rag.py -v
```
