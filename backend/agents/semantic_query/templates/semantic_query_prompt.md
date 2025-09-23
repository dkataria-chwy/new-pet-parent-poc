Compose multi-slot retrieval queries for pet products.

- Use only the data below. Do not invent any facts or numbers.
- If an attribute is missing, omit it.
- Keep the provided filters.pc1.
- Maintain MUSTS (species, lifestage, size/variant, allergens) in every slot.
- Use your pet-care domain knowledge non-exhaustively to anticipate what this pet typically needs this month (for its age/breed size/living context), and add any other justified needs beyond the examples, as long as they map to allowed families.
- Weather: use alerts first; if none apply, use the 7-day forecast and the thresholds from the system message to decide whether to add cooling (heat) or winter_gear (freeze).
- Calendar: use events only if within the event window or days_to_event ≤ 14 and confidence ≥ 0.6. Map slot_triggers_seed as described in the system message.

### Inputs

#### pet_profile
{{pet_profile_json}}

#### user_profile (optional)
{{user_profile_json}}

#### order_history (optional)
{{order_history_json}}

#### weather_context
{{weather_json}}

#### calendar_context
{{calendar_json}}

#### catalog_hard_filters
{{catalog_filters_json}}

### Constraints

- 1–8 slots.
- Specify both top_family (department) and family (intent) per slot.
- Families allowed for family: see schema enum.
- embedding_query = 200–400 chars; grounded; include variant cues + lifestage + allergens (brand preferences only as preferences).
- bm25_query = literal tokens with boolean ops; include negatives as needed (e.g., NOT rawhide).
- filters must include pc1 exactly as provided.
- Do not reference MC1–4 or PC2/PC3 unless provided by the caller.
- If weather/calendar do not qualify, skip those slots.

### Output

Respond with JSON only conforming to the schema (the caller validates).