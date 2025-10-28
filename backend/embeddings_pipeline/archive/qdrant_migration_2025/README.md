# Qdrant Migration Scripts Archive (October 2025)

This folder contains the one-time scripts used to migrate 117,584 product embeddings from JSONL to Qdrant Cloud.

## Migration Completed: October 27, 2025

✅ **Status:** Successfully migrated all 117,584 products  
✅ **Collection:** `chewy_products_117k`  
✅ **Qdrant Cluster:** US-East-1  
✅ **Data Integrity:** 100% verified

---

## Files in this Archive:

### 1. `migrate_to_qdrant_rest.py` ✅ **SUCCESSFUL**
- **Purpose:** Final successful migration script using REST API
- **Why it worked:** Used `requests` library directly, bypassing httpx timeout issues
- **Result:** Migrated all 117,584 products in ~9 minutes 40 seconds
- **Keep for:** Future re-migrations or updates

### 2. `migrate_to_qdrant.py` ❌ **FAILED**
- **Purpose:** Initial migration attempt using Qdrant Python client
- **Why it failed:** httpx connection timeout issues with cloud cluster
- **Keep for:** Reference/learning

### 3. `test_qdrant_connection.py` 🔍 **TESTING**
- **Purpose:** One-time connection test to verify Qdrant credentials
- **Keep for:** Future troubleshooting if connection issues arise

---

## Production Code (Still Active):

These files are **NOT** archived and are actively used:

- `backend/agents/product_recommendations/qdrant_vector_search.py` - Production vector search class
- `backend/QDRANT_MIGRATION.md` - Complete migration documentation

---

## If You Need to Re-Migrate:

Use `migrate_to_qdrant_rest.py`:

```bash
cd backend/embeddings_pipeline/archive/qdrant_migration_2025
cp migrate_to_qdrant_rest.py ../../
cd ../../
python migrate_to_qdrant_rest.py
```

---

## Deleted Scripts (No Longer Needed):

These were one-time debugging scripts, now deleted:
- `diagnose_network.py` - Network diagnostics for timeout issues
- `test_qdrant_migration.py` - Verification test comparing Qdrant vs JSONL results

---

**Note:** The production system now uses Qdrant automatically when `USE_QDRANT=true` in `.env`

