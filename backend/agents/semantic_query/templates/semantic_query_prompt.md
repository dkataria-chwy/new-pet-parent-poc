Compose multi-slot retrieval queries for pet products.

- Use only the data below. Do not invent any facts or numbers.
- If an attribute is missing, omit it.
- Keep the provided filters.pc1.
- Maintain MUSTS (species, lifestage, size/variant, allergens) in every slot.
- Use your pet‑care knowledge to pick ALL relevant semantic product types and variations this pet needs this month. Generate comprehensive coverage.
- Calendar: use events only if within window or days_to_event ≤ 14 and confidence ≥ 0.6.
- Embedding focus: each embedding_query is a semicolon‑separated facet bag; include only facets that add signal; avoid contradictions.
- Brand preferences (if any): list in brand_bias and optionally add as a soft OR at the end of bm25_query. Only put brand in embedding_query if inputs mark it a must.

### Inputs

#### pet_profile
{{pet_profile_json}}

#### user_profile (optional)
{{user_profile_json}}

#### order_history (optional)
<!-- {{order_history_json}} -->

#### weather_context
{{weather_json}}

#### calendar_context
{{calendar_json}}

#### catalog_hard_filters
{{catalog_filters_json}}

#### Available Categories (prefer these, but custom values allowed for important pet needs)

**top_family options:**
{{top_family_enums}}

**family options:**
{{family_enums}}

### Constraints

- Produce as many slots as you think are truly relevant for this pet now…
- Specify both top_family (department) and family (intent) per slot.
- embedding_query = facet-bag format, max 300 chars; semicolon-separated facets only; focus on relevant semantic signals for this pet.
- bm25_query = literal tokens with boolean ops; include negatives as needed (e.g., NOT rawhide).
- filters must include pc1 exactly as provided.

### Output

Respond with JSON only conforming to the schema (the caller validates).