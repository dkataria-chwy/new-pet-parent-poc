# Natural Language Embeddings

## What Changed?

**Only 2 files added** to generate natural language embeddings:

1. **`src/search_text_builder_natural.py`** - Generates natural flowing text instead of structured "Brand: X. Species: Y." format
2. **`run_pipeline_natural_lang.py`** - Uses the natural language builder, everything else is identical

## Output

- **File**: `artifacts/catalog_embeds_natural_lang.jsonl`
- **Columns**: Exact same 9 columns as existing `catalog_embeds.jsonl`:
  - `product_part_number`
  - `search_text` ← **ONLY DIFFERENCE** (natural language format)
  - `embedding`
  - `species_dog_flag`
  - `species_cat_flag`
  - `embedded_at`
  - `product_autoship_save_eligible_flag`
  - `parent_product_part_number`
  - `product_link`

## Search Text Format Comparison

### Old (Structured Format)
```
Diamond Naturals Large Breed Puppy Formula Brand: Diamond Naturals. Species: Dog. 
Lifestage: Puppy. Breed Size: Large. Food Form: Dry Kibble. Special Diet: None. 
Description: Formulated for large breed puppies with DHA for brain development...
```

### New (Natural Language Format)
```
Diamond Naturals Large Breed Puppy Formula for dog, puppy, large breed, dry food. 
Formulated for large breed puppies with DHA for brain development, includes 
glucosamine for joint support. Available in multiple sizes. No prescription required. 
Consumable product. Food product. Health & wellness supplement for dogs.
```

## Why Natural Language?

- **Better semantic understanding** - Embeddings capture meaning more accurately
- **Higher similarity scores** - Initial tests showed +10% improvement (0.65 → 0.72)
- **More natural queries** - Works better with conversational search queries

## How to Run

```bash
cd backend/embeddings_pipeline
source ../venv/bin/activate
export $(cat ../../.env | xargs)

python run_pipeline_natural_lang.py "../../product embeddings table.csv"
```

**Cost**: ~$17 | **Time**: ~60 minutes | **Output**: `artifacts/catalog_embeds_natural_lang.jsonl`

## How to Use

To switch from structured to natural language embeddings:

1. Replace `catalog_embeds.jsonl` with `catalog_embeds_natural_lang.jsonl`
2. Restart backend
3. Done! All search/recommendations will use natural language embeddings

## No Impact on Existing Pipeline

- Old pipeline still works: `run_pipeline.py` + `search_text_builder.py`
- New pipeline is separate: `run_pipeline_natural_lang.py` + `search_text_builder_natural.py`
- You can run comparison tests without breaking anything

