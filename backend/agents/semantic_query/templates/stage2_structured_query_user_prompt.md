Generate search queries for each need identified in Stage 1 structured analysis.

Apply the query composition rules from your system instructions to create optimal embedding and BM25 queries for THIS specific pet.

## Inputs

### stage1_needs
{{stage1_needs_json}}

### pet_profile
{{pet_profile_json}}

### user_profile
{{user_profile_json}}

### product_taxonomy
```json
{
  "top_family_options": {{top_family_taxonomy}},
  "family_options": {{family_taxonomy}}
}
```

**Use taxonomy for product categories**: Include top_family and family names naturally in embedding_query (e.g., "dry kibble", "VOHC chews", "cooling gear").

## Task

**For EACH need in stage1_needs (do not skip any):**
1. Copy `bucket` field unchanged from Stage 1
2. Use your judgement to match top_family/family to product_taxonomy (or keep Stage 1 value if you cannot match)
3. Generate `embedding_query`: Write as natural language - ideally start with species+lifestage, add product category, extract key attributes from Stage 1 description as natural phrases, include brands (from pet_profile if any)
4. Generate `bm25_query`: Extract key terms from embedding_query, add allergen NOTs from negatives
5. Set `top_k` (typically 3-15, adjust for specificity and category)
6. Copy `rationale` and `negatives` exactly as provided

Return a complete query set as JSON conforming to the schema.

