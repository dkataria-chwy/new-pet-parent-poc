# Qdrant Performance Fix

## Problem

After migrating to Qdrant, searches were timing out at 60 seconds, making the system **25 minutes slower** than JSONL for a full pipeline run.

### Root Cause

The `qdrant-client` Python library uses `httpx` internally, which had persistent connection timeout issues with our Qdrant Cloud cluster:
- REST API (`requests` library): ✅ 0.24s response time
- Python client (`httpx`): ❌ 60s timeout

## Solution

Switched to using **Qdrant's REST API directly** with the `requests` library, bypassing the problematic Python client.

### Implementation

**File:** `backend/agents/product_recommendations/qdrant_vector_search_rest.py`

Key changes:
1. Use `requests.Session()` instead of `QdrantClient()`
2. Direct POST to `/collections/{collection}/points/search` endpoint
3. Manual JSON payload construction

### Additional Fix: Payload Indexes

Qdrant requires explicit indexes for filtered fields:

```bash
python backend/create_qdrant_indexes.py
```

Creates indexes for:
- `species_dog_flag` (bool)
- `species_cat_flag` (bool)

**Note:** Only needs to be run once per collection.

## Performance Results

### Before (Python Client with httpx):
```
- Per-slot search: 60s (timeout)
- 2 slots: 120s+
- Status: ❌ UNUSABLE
```

### After (REST API with requests):
```
- Initialization: 0.26s (vs 30-60s for JSONL)
- Per-slot search: 0.54s (embedding + search)
- 2 slots: 1.34s total
- Status: ✅ 22x FASTER than before
```

## How to Test

```bash
cd backend
source venv/bin/activate
python test_full_pipeline_qdrant.py
```

Expected output:
- Init time: <1s
- Per-slot: 0.5-0.7s
- Results: Relevant products with >60% similarity

## Files Modified

1. **New:** `qdrant_vector_search_rest.py` - REST API implementation
2. **Modified:** `recommendation_engine.py` - Import REST version
3. **Tool:** `create_qdrant_indexes.py` - One-time index creation
4. **Test:** `test_full_pipeline_qdrant.py` - Validation script

## Why REST API Over Python Client?

Both are officially supported by Qdrant:
- **Python Client**: Better for most use cases, has rich features
- **REST API**: Lower-level, but more reliable when httpx has issues

For our specific Qdrant Cloud cluster, REST API is the right choice.

## Migration Notes

The REST implementation is a **drop-in replacement**:
- ✅ Same input format (slots)
- ✅ Same output format (products with similarity scores)
- ✅ Same filtering logic (species, brands, etc.)
- ✅ No changes needed in consuming code

---

**Date:** October 27, 2025  
**Status:** ✅ RESOLVED - Qdrant now faster than JSONL

