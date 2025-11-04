# Qdrant Vector Database Migration Guide

This document explains how to migrate from JSONL in-memory vector search to Qdrant cloud vector database.

---

## 📊 Why Migrate to Qdrant?

### Current Setup (JSONL)
- **Size:** 117K products, 4.78GB embeddings
- **Memory:** ~4.78GB RAM required (entire dataset in memory)
- **Search Speed:** ~100-200ms per query (cosine similarity on 117K vectors)
- **Scaling:** Limited by available RAM

### With Qdrant
- **Memory:** ~50-100MB RAM (client only, vectors stored in Qdrant cloud)
- **Search Speed:** ~20-50ms per query (HNSW index, optimized for speed)
- **Scaling:** Handles millions of vectors easily
- **Cost:** $25-100/month (Qdrant cloud pricing)

### ROI Analysis
**Memory Savings:** 4.68GB (98% reduction)  
**Speed Improvement:** 2-4x faster  
**Monthly Cost:** ~$50-75 (Qdrant cloud)  

✅ **Recommendation:** Strongly recommended for production deployment

---

## 🚀 Migration Steps

### Step 1: Install Qdrant Client

Already completed! The `qdrant-client` package is added to `requirements.txt`.

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Qdrant Credentials

Already configured in `.env`:

```bash
# Qdrant Vector Database
QDRANT_URL=https://316ef286-2111-4907-b620-c8f3fc693dad.us-east-1-1.aws.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.wIT9J0VEOBalnVKY3IiJA92VqsOGpYUYDbj_kpaxLEg
QDRANT_CLUSTER_ID=316ef286-2111-4907-b620-c8f3fc693dad
USE_QDRANT=false
```

**Note:** `USE_QDRANT` is set to `false` by default. This allows you to test the migration without affecting existing functionality.

### Step 3: Run Migration Script

Migrate the 117K embeddings to Qdrant cloud:

```bash
cd backend/embeddings_pipeline
python migrate_to_qdrant.py
```

**What it does:**
- Creates a new collection `chewy_products_117k` in Qdrant
- Uploads all 117K embeddings in optimized batches (500 vectors per batch)
- Includes all metadata (product name, species, category, price, etc.)
- Optimized HNSW index settings for fast search

**Expected output:**
```
🚀 Starting Qdrant migration for 117K products...
✅ Connected to Qdrant at https://...
📦 Creating collection: chewy_products_117k
✅ Created optimized collection: chewy_products_117k
📂 Loading embeddings from: .../catalog_embeds.jsonl
📊 Total products to migrate: 117000
Migrating vectors: 100%|████████████████| 117000/117000 [05:30<00:00, 354.00it/s]
✅ Migration complete! Uploaded 117000 vectors
⏳ Waiting for indexing to complete...
🎉 Final stats:
   - Vectors indexed: 117000
   - Collection status: green
✅ All vectors successfully migrated and indexed!
```

**Time:** ~5-10 minutes depending on network speed

### Step 4: Test Both Implementations

Verify that Qdrant returns similar results to JSONL:

```bash
cd backend/agents/product_recommendations
python test_qdrant_migration.py
```

**What it does:**
- Runs the same test query against both JSONL and Qdrant
- Compares top 10 results for SKU overlap
- Compares similarity scores for matching products
- Saves detailed comparison to `qdrant_comparison_results.json`

**Expected output:**
```
🧪 Testing JSONL vs Qdrant Vector Search Implementations
================================================================================
📁 Testing JSONL Implementation
   ✅ Loaded 117000 products
   ✅ Found 20 products
   
🚀 Testing Qdrant Implementation
   ✅ Found 20 products
   
📊 Comparison Analysis
   Top 10 SKU Overlap: 8/10 (80%)
   ✅ PASS: 80% overlap - implementations are consistent!
```

**Acceptance criteria:** ≥70% overlap in top 10 results

### Step 5: Enable Qdrant (when ready)

Once migration is verified, enable Qdrant in production:

```bash
# In .env file, change:
USE_QDRANT=true
```

Restart your backend server to apply changes.

---

## 🔧 Technical Details

### Architecture

**Before (JSONL):**
```
User Request → Recommendation Engine → EmbeddingStorageLoader (loads 4.78GB into RAM)
                                    → SpeciesAwareVectorSearch (NumPy cosine similarity)
                                    → Filter & Rank → Response
```

**After (Qdrant):**
```
User Request → Recommendation Engine → QdrantVectorSearch (connects to Qdrant cloud)
                                    → Qdrant HNSW Index (fast similarity search)
                                    → Filter & Rank → Response
```

### Feature Flag Implementation

The system uses the `USE_QDRANT` environment variable to switch between implementations:

- **`USE_QDRANT=false`** (default): Uses JSONL in-memory search
- **`USE_QDRANT=true`**: Uses Qdrant cloud vector database

**No code changes required** - it's a drop-in replacement!

```python
# In recommendation_engine.py
use_qdrant = os.getenv("USE_QDRANT", "false").lower() == "true"

if use_qdrant:
    self.vector_search = QdrantVectorSearch()  # Qdrant implementation
else:
    self.vector_search = SpeciesAwareVectorSearch(storage_loader)  # JSONL implementation
```

### Key Files

| File | Purpose |
|------|---------|
| `embeddings_pipeline/migrate_to_qdrant.py` | Migration script (JSONL → Qdrant) |
| `agents/product_recommendations/qdrant_vector_search.py` | Qdrant implementation |
| `agents/product_recommendations/vector_search.py` | Original JSONL implementation |
| `agents/product_recommendations/recommendation_engine.py` | Feature flag logic |
| `agents/product_recommendations/test_qdrant_migration.py` | Verification test |

### Qdrant Collection Schema

**Collection Name:** `chewy_products_117k`

**Vector Config:**
- **Size:** 1536 (OpenAI `text-embedding-3-large`)
- **Distance:** Cosine similarity
- **Index:** HNSW (m=16, ef_construct=100)

**Metadata Fields:**
```json
{
  "product_id": "string",
  "product_name": "string",
  "description": "string",
  "species": "string",
  "species_dog_flag": "boolean",
  "species_cat_flag": "boolean",
  "category": "string",
  "subcategory": "string",
  "price": "float",
  "brand": "string",
  "product_part_number": "string",
  "parent_product_part_number": "string",
  "search_text": "string",
  "product_link": "string",
  "image_url": "string",
  "product_autoship_save_eligible_flag": "boolean"
}
```

---

## 🧪 Testing Strategy

### 1. Migration Verification
Run `test_qdrant_migration.py` to verify:
- ✅ Qdrant connection works
- ✅ Same query returns similar top results (≥70% overlap)
- ✅ Similarity scores are comparable

### 2. A/B Testing (Recommended)
Enable Qdrant for a subset of users:
1. Keep `USE_QDRANT=false` in production
2. Enable `USE_QDRANT=true` for internal testing
3. Compare recommendation quality and performance
4. Roll out to all users once validated

### 3. Performance Benchmarking
```bash
# Compare search speed
cd backend/agents/product_recommendations
python benchmark_search_speed.py  # JSONL (if script exists)
USE_QDRANT=true python benchmark_search_speed.py  # Qdrant
```

---

## 🔄 Rollback Plan

If issues arise with Qdrant, rollback is instant:

```bash
# In .env file, change:
USE_QDRANT=false
```

Restart backend server. The system will revert to JSONL in-memory search.

**No data loss** - original JSONL files remain untouched.

---

## 📈 Monitoring

### Key Metrics to Track

1. **Search Speed**
   - JSONL: ~100-200ms
   - Qdrant: ~20-50ms (target)

2. **Memory Usage**
   - JSONL: ~4.78GB
   - Qdrant: ~50-100MB (target)

3. **Search Quality**
   - Compare top 10 SKU overlap (target: ≥70%)
   - Monitor user feedback and conversion rates

4. **Error Rate**
   - Qdrant connection failures
   - Timeout errors (increase timeout if needed)

### Troubleshooting

**Issue:** Qdrant connection timeout  
**Fix:** Increase timeout in `qdrant_vector_search.py`:
```python
self.client = QdrantClient(url=url, api_key=api_key, timeout=60)  # Increase from 30 to 60
```

**Issue:** Results differ significantly from JSONL  
**Fix:** Check if migration completed successfully. Re-run `migrate_to_qdrant.py` if needed.

**Issue:** Slow search performance  
**Fix:** Check Qdrant cloud plan and consider upgrading for better performance.

---

## 💰 Cost Analysis

### Qdrant Cloud Pricing (Estimated)

**Current Dataset:**
- 117K vectors × 1536 dimensions × 4 bytes = ~720MB vector data
- Add ~280MB for metadata → ~1GB total storage

**Recommended Plan:** Standard Cluster  
- **Cost:** ~$50-75/month
- **Performance:** <50ms search latency
- **Storage:** 1GB vectors + metadata

**ROI:**
- **Memory savings:** 4.68GB (can downsize server)
- **Speed improvement:** 2-4x faster search
- **Scalability:** Room to grow to 500K+ products

✅ **Worth it** if this leads to better recommendations and user experience

---

## 🎯 Next Steps

1. ✅ Run migration: `python migrate_to_qdrant.py`
2. ✅ Test both implementations: `python test_qdrant_migration.py`
3. ⏳ Enable Qdrant for internal testing: `USE_QDRANT=true`
4. ⏳ Monitor performance and quality metrics
5. ⏳ Roll out to production once validated

---

## 📚 Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

**Questions?** Check the test output in `qdrant_comparison_results.json` or contact the dev team.

