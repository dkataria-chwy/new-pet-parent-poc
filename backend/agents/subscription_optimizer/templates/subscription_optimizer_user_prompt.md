Analyze the recommended products below and create an intelligent subscription vs. one-time purchase strategy for THIS specific pet.

Apply your pet care expertise and the decision framework from your system instructions to determine which products should be auto-shipped (subscription) and which should be one-time purchases.

---

## Inputs

### Pet Profile
{{pet_profile_json}}

### Journey Stage
- **Month**: {{month_idx}}
- **Journey ID**: {{journey_id}}
- **Context**: {{journey_context}}

### Order History
{{order_history_json}}

### Weather Context
{{weather_json}}

### Calendar Context
{{calendar_json}}

### Recommended Products
{{recommended_products_json}}

---

## Task

1. **Analyze consumption patterns** - Calculate monthly depletion rates based on THIS pet's characteristics (weight, activity, chew strength, etc.)
2. **Check order history FIRST**:
   - Journey Month 1 = cold start (recommend setup essentials)
   - Journey Month 2+ = avoid re-recommending durables already purchased, continue consumables subscriptions
3. **Consider journey stage** - Journey Month 1-2 needs more setup items; Month 3+ prioritize consumables but don't ignore durables/grooming if needed
4. **Apply seasonal logic** - Weather/calendar-triggered items are typically one-time purchases
5. **Ensure variety** - Mix product categories (food, treats, waste, grooming, toys, gear, etc.)
6. **Write personalized notes** - Use pet's name and specific details for EVERY product

**Output:**
- **15 Subscription Products** (high-frequency consumables with predictable monthly depletion)
- **15 One-Time Products** (durables, seasonal items, setup essentials)
- **Overall Strategy** (brief explanation tailored to THIS pet at THIS journey stage)

Return your analysis as JSON conforming to the schema provided.
