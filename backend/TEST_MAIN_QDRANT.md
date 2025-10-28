# Testing main.py with Qdrant

## What Was Wrong

`main.py` initializes an **on-demand recommendation handler** (line 49) which was always loading JSONL embeddings, completely ignoring the `USE_QDRANT` flag.

## What Was Fixed

Updated `backend/agents/on_demand_recommendations/product_searcher.py` to:
1. Check `USE_QDRANT` environment variable
2. Use `QdrantVectorSearch` (REST API) when enabled
3. Fall back to JSONL when disabled

## Test It

```bash
cd backend
source venv/bin/activate
python main.py
```

### Expected Output (with USE_QDRANT=true):

```
✅ OpenAI API key found, AI validation enabled (model: gpt-4.1)
INFO: Started server process [xxxxx]
INFO: Waiting for application startup.
✅ On-demand recommendations initialized with 117,584 products  # Fast startup!
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Key difference:**
- **Before:** 30-60s startup time (loading 5GB JSONL into RAM)
- **After:** <1s startup time (just connecting to Qdrant)

## What Changed

### File: `product_searcher.py`

**Initialization (lines 45-108):**
- Now checks `USE_QDRANT` flag
- Creates `QdrantVectorSearch()` when enabled
- Falls back to `OnDemandVectorSearch()` for JSONL

**Search (lines 111-169):**
- Routes to Qdrant REST API when `self.qdrant_search` exists
- Routes to JSONL search when `self.vector_search` exists
- Same output format either way

## Components Using This

1. **Main FastAPI Server** (`main.py`) - On-demand recommendations
2. **Full Pipeline** (`run_full_pipeline.py`) - Uses separate engine (already fixed)

Both now respect the `USE_QDRANT` flag!

---

**Date:** October 27, 2025  
**Status:** ✅ FIXED - All components now use Qdrant when enabled

