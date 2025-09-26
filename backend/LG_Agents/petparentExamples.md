
# Pet Parent State Examples — 10 Complete Samples

Each section contains a single **PetParentState** JSON block (validated by `petparent_state.PetParentState`).  
You can load them with the provided `petprofile_loader.py` which extracts all ```json``` blocks, validates, and returns objects.

---

## Example P-101 — Golden Retriever Puppy — Austin, TX
```json
{
  "version": "1.0",
  "pet_id": "P-101",
  "user_id": "U-101",
  "pet": {
    "species": "dog",
    "breed": "Golden Retriever",
    "age_months": 8,
    "weight_lb": 42.3,
    "location_zip": "78701",
    "habits": ["chewer", "crate-trained"]
  },
  "chat_history": [
    {"msg_id": "m101-1", "role": "user", "content": "We just adopted a Golden Retriever puppy. What should we buy first?"},
    {"msg_id": "m101-2", "role": "assistant", "content": "I'd suggest a starter bundle with puppy food, a bed, bowl, and training pads."},
    {"msg_id": "m101-3", "role": "user", "content": "Let's keep it affordable. Any discounts?"},
    {"msg_id": "m101-4", "role": "assistant", "content": "You qualify for a cart threshold discount and a puppy combo bonus."}
  ],
  "interactions": [
    {"event_id": "e101-1", "type": "viewed_packages", "attributes": {"bundles": ["basic", "premium"]}},
    {"event_id": "e101-2", "type": "selected_bundle", "attributes": {"bundle_id": "basic-1"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10101",
      "location_zip": "78701",
      "status": "completed",
      "discounts": 5.00,
      "items": [
        {"sku": "FOO-PUP-LG-15", "name": "Puppy Kibble Large Breed 15lb", "qty": 1, "unit_price": 39.99, "category": "food"},
        {"sku": "BOWL-SS", "name": "Stainless Steel Bowl", "qty": 2, "unit_price": 8.99, "category": "bowl"},
        {"sku": "PADS-50", "name": "Training Pads (50ct)", "qty": 1, "unit_price": 24.99, "category": "training"}
      ]
    }
  ]
}
```

## Example P-102 — French Bulldog Adult — Miami, FL
```json
{
  "version": "1.0",
  "pet_id": "P-102",
  "user_id": "U-102",
  "pet": {
    "species": "dog",
    "breed": "French Bulldog",
    "age_months": 24,
    "weight_lb": 25.0,
    "location_zip": "33130",
    "habits": ["shedder", "sensitive-skin"]
  },
  "chat_history": [
    {"msg_id": "m102-1", "role": "user", "content": "Looking for food and a gentle shampoo for my Frenchie."},
    {"msg_id": "m102-2", "role": "assistant", "content": "Adult kibble and an oatmeal shampoo would fit well."},
    {"msg_id": "m102-3", "role": "user", "content": "Add a small bed too."},
    {"msg_id": "m102-4", "role": "assistant", "content": "Added. I'll check local availability next."}
  ],
  "interactions": [
    {"event_id": "e102-1", "type": "checked_inventory", "attributes": {"zip": "33130"}},
    {"event_id": "e102-2", "type": "modified_item", "attributes": {"sku": "BED-S", "qty": 1}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10201",
      "location_zip": "33130",
      "status": "completed",
      "discounts": 3.50,
      "items": [
        {"sku": "FOO-ADULT-15", "name": "Adult Kibble 15lb", "qty": 1, "unit_price": 34.99, "category": "food"},
        {"sku": "SHAM-OAT-16", "name": "Gentle Oatmeal Dog Shampoo 16oz", "qty": 1, "unit_price": 12.99, "category": "shampoo"},
        {"sku": "BED-S", "name": "Plush Dog Bed (Small)", "qty": 1, "unit_price": 29.99, "category": "bed"}
      ]
    }
  ]
}
```

## Example P-103 — Domestic Shorthair Kitten — San Francisco, CA
```json
{
  "version": "1.0",
  "pet_id": "P-103",
  "user_id": "U-103",
  "pet": {
    "species": "cat",
    "breed": "Domestic Shorthair",
    "age_months": 5,
    "weight_lb": 4.2,
    "location_zip": "94110",
    "habits": ["indoor", "litter-trained"]
  },
  "chat_history": [
    {"msg_id": "m103-1", "role": "user", "content": "New kitten! Need essentials."},
    {"msg_id": "m103-2", "role": "assistant", "content": "Litter, kitten food, bowls, and a cozy bed are a great start."},
    {"msg_id": "m103-3", "role": "user", "content": "Let's start with food and a bowl."}
  ],
  "interactions": [
    {"event_id": "e103-1", "type": "viewed_packages", "attributes": {"bundles": ["basic"]}},
    {"event_id": "e103-2", "type": "abandoned_cart", "attributes": {"reason": "compare_prices"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10301",
      "location_zip": "94110",
      "status": "completed",
      "discounts": 0.00,
      "items": [
        {"sku": "FOO-PUP-SM-5", "name": "Puppy Kibble Small Breed 5lb", "qty": 1, "unit_price": 19.99, "category": "food"},
        {"sku": "BOWL-SS", "name": "Stainless Steel Bowl", "qty": 1, "unit_price": 8.99, "category": "bowl"}
      ]
    }
  ]
}
```

## Example P-104 — German Shepherd Adult — New York, NY
```json
{
  "version": "1.0",
  "pet_id": "P-104",
  "user_id": "U-104",
  "pet": {
    "species": "dog",
    "breed": "German Shepherd",
    "age_months": 72,
    "weight_lb": 78.5,
    "location_zip": "10001",
    "habits": ["high-energy", "shedder"]
  },
  "chat_history": [
    {"msg_id": "m104-1", "role": "user", "content": "Need a durable large bed and adult food."},
    {"msg_id": "m104-2", "role": "assistant", "content": "Recommending a large plush bed and 15lb adult kibble."},
    {"msg_id": "m104-3", "role": "user", "content": "Add a chew toy too."}
  ],
  "interactions": [
    {"event_id": "e104-1", "type": "modified_item", "attributes": {"sku": "TOY-CHEW", "action": "add"}},
    {"event_id": "e104-2", "type": "applied_discount", "attributes": {"type": "threshold_10"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10401",
      "location_zip": "10001",
      "status": "completed",
      "discounts": 12.00,
      "items": [
        {"sku": "FOO-ADULT-15", "name": "Adult Kibble 15lb", "qty": 2, "unit_price": 34.99, "category": "food"},
        {"sku": "BED-L", "name": "Plush Dog Bed (Large)", "qty": 1, "unit_price": 69.99, "category": "bed"},
        {"sku": "TOY-CHEW", "name": "Durable Chew Toy", "qty": 1, "unit_price": 11.99, "category": "toy"}
      ]
    }
  ]
}
```

## Example P-105 — Maine Coon Adult — Chicago, IL
```json
{
  "version": "1.0",
  "pet_id": "P-105",
  "user_id": "U-105",
  "pet": {
    "species": "cat",
    "breed": "Maine Coon",
    "age_months": 36,
    "weight_lb": 17.8,
    "location_zip": "60607",
    "habits": ["indoor", "long-hair"]
  },
  "chat_history": [
    {"msg_id": "m105-1", "role": "user", "content": "My Maine Coon needs a bigger bed and adult food."},
    {"msg_id": "m105-2", "role": "assistant", "content": "Adding a medium bed and adult kibble; want grooming supplies too?"},
    {"msg_id": "m105-3", "role": "user", "content": "Yes, include shampoo."}
  ],
  "interactions": [
    {"event_id": "e105-1", "type": "selected_bundle", "attributes": {"bundle_id": "premium-1"}},
    {"event_id": "e105-2", "type": "checked_inventory", "attributes": {"zip": "60607"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10501",
      "location_zip": "60607",
      "status": "completed",
      "discounts": 7.00,
      "items": [
        {"sku": "FOO-ADULT-15", "name": "Adult Kibble 15lb", "qty": 1, "unit_price": 34.99, "category": "food"},
        {"sku": "BED-M", "name": "Plush Dog Bed (Medium)", "qty": 1, "unit_price": 49.99, "category": "bed"},
        {"sku": "SHAM-OAT-16", "name": "Gentle Oatmeal Dog Shampoo 16oz", "qty": 1, "unit_price": 12.99, "category": "shampoo"}
      ]
    }
  ]
}
```

## Example P-106 — Labrador Retriever Adolescent — Seattle, WA
```json
{
  "version": "1.0",
  "pet_id": "P-106",
  "user_id": "U-106",
  "pet": {
    "species": "dog",
    "breed": "Labrador Retriever",
    "age_months": 10,
    "weight_lb": 55.0,
    "location_zip": "98109",
    "habits": ["chewer", "high-energy"]
  },
  "chat_history": [
    {"msg_id": "m106-1", "role": "user", "content": "Puppy Lab—need food and a durable bed."},
    {"msg_id": "m106-2", "role": "assistant", "content": "Large-breed puppy food and a large bed recommended."},
    {"msg_id": "m106-3", "role": "user", "content": "Add a chew toy."},
    {"msg_id": "m106-4", "role": "assistant", "content": "Added. You also qualify for a combo discount."}
  ],
  "interactions": [
    {"event_id": "e106-1", "type": "applied_discount", "attributes": {"type": "puppy_combo"}},
    {"event_id": "e106-2", "type": "started_checkout", "attributes": {}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10601",
      "location_zip": "98109",
      "status": "completed",
      "discounts": 8.00,
      "items": [
        {"sku": "FOO-PUP-LG-15", "name": "Puppy Kibble Large Breed 15lb", "qty": 1, "unit_price": 39.99, "category": "food"},
        {"sku": "BED-L", "name": "Plush Dog Bed (Large)", "qty": 1, "unit_price": 69.99, "category": "bed"},
        {"sku": "TOY-CHEW", "name": "Durable Chew Toy", "qty": 1, "unit_price": 11.99, "category": "toy"}
      ]
    }
  ]
}
```

## Example P-107 — Siamese Senior — Boston, MA
```json
{
  "version": "1.0",
  "pet_id": "P-107",
  "user_id": "U-107",
  "pet": {
    "species": "cat",
    "breed": "Siamese",
    "age_months": 96,
    "weight_lb": 10.5,
    "location_zip": "02116",
    "habits": ["indoor", "vocal"]
  },
  "chat_history": [
    {"msg_id": "m107-1", "role": "user", "content": "Senior cat—looking for gentle food and a warm bed."},
    {"msg_id": "m107-2", "role": "assistant", "content": "Adult kibble should suit; adding a small plush bed."},
    {"msg_id": "m107-3", "role": "user", "content": "Also need a new bowl."}
  ],
  "interactions": [
    {"event_id": "e107-1", "type": "viewed_packages", "attributes": {"bundles": ["basic"]}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10701",
      "location_zip": "02116",
      "status": "completed",
      "discounts": 2.50,
      "items": [
        {"sku": "FOO-ADULT-15", "name": "Adult Kibble 15lb", "qty": 1, "unit_price": 34.99, "category": "food"},
        {"sku": "BED-S", "name": "Plush Dog Bed (Small)", "qty": 1, "unit_price": 29.99, "category": "bed"},
        {"sku": "BOWL-SS", "name": "Stainless Steel Bowl", "qty": 1, "unit_price": 8.99, "category": "bowl"}
      ]
    }
  ]
}
```

## Example P-108 — Australian Shepherd Young Adult — Denver, CO
```json
{
  "version": "1.0",
  "pet_id": "P-108",
  "user_id": "U-108",
  "pet": {
    "species": "dog",
    "breed": "Australian Shepherd",
    "age_months": 14,
    "weight_lb": 38.0,
    "location_zip": "80205",
    "habits": ["high-energy", "herding-instinct"]
  },
  "chat_history": [
    {"msg_id": "m108-1", "role": "user", "content": "Need sturdy toys and adult food for my Aussie."},
    {"msg_id": "m108-2", "role": "assistant", "content": "Suggesting adult kibble, chew toy, and a medium bed."},
    {"msg_id": "m108-3", "role": "user", "content": "Proceed with those."}
  ],
  "interactions": [
    {"event_id": "e108-1", "type": "selected_bundle", "attributes": {"bundle_id": "premium-1"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10801",
      "location_zip": "80205",
      "status": "completed",
      "discounts": 6.00,
      "items": [
        {"sku": "FOO-ADULT-15", "name": "Adult Kibble 15lb", "qty": 1, "unit_price": 34.99, "category": "food"},
        {"sku": "BED-M", "name": "Plush Dog Bed (Medium)", "qty": 1, "unit_price": 49.99, "category": "bed"},
        {"sku": "TOY-CHEW", "name": "Durable Chew Toy", "qty": 2, "unit_price": 11.99, "category": "toy"}
      ]
    }
  ]
}
```

## Example P-109 — Dachshund Puppy — Phoenix, AZ
```json
{
  "version": "1.0",
  "pet_id": "P-109",
  "user_id": "U-109",
  "pet": {
    "species": "dog",
    "breed": "Dachshund",
    "age_months": 6,
    "weight_lb": 11.2,
    "location_zip": "85004",
    "habits": ["burrower", "chewer"]
  },
  "chat_history": [
    {"msg_id": "m109-1", "role": "user", "content": "Mini Dachshund puppy—need food and training pads."},
    {"msg_id": "m109-2", "role": "assistant", "content": "Small-breed puppy food and pads added; want a small bed too?"},
    {"msg_id": "m109-3", "role": "user", "content": "Yes, add small bed."}
  ],
  "interactions": [
    {"event_id": "e109-1", "type": "modified_item", "attributes": {"sku": "BED-S", "qty": 1}},
    {"event_id": "e109-2", "type": "applied_discount", "attributes": {"type": "puppy_combo"}}
  ],
  "purchase_history": [
    {
      "order_id": "O-10901",
      "location_zip": "85004",
      "status": "completed",
      "discounts": 4.00,
      "items": [
        {"sku": "FOO-PUP-SM-5", "name": "Puppy Kibble Small Breed 5lb", "qty": 1, "unit_price": 19.99, "category": "food"},
        {"sku": "PADS-50", "name": "Training Pads (50ct)", "qty": 1, "unit_price": 24.99, "category": "training"},
        {"sku": "BED-S", "name": "Plush Dog Bed (Small)", "qty": 1, "unit_price": 29.99, "category": "bed"}
      ]
    }
  ]
}
```

## Example P-110 — Ragdoll Kitten — Dallas, TX
```json
{
  "version": "1.0",
  "pet_id": "P-110",
  "user_id": "U-110",
  "pet": {
    "species": "cat",
    "breed": "Ragdoll",
    "age_months": 3,
    "weight_lb": 3.5,
    "location_zip": "75201",
    "habits": ["indoor", "litter-trained"]
  },
  "chat_history": [
    {"msg_id": "m110-1", "role": "user", "content": "Ragdoll kitten—need basics."},
    {"msg_id": "m110-2", "role": "assistant", "content": "Start with kitten food and a bowl; want a small bed as well?"},
    {"msg_id": "m110-3", "role": "user", "content": "Yes, add the bed."}
  ],
  "interactions": [
    {"event_id": "e110-1", "type": "viewed_packages", "attributes": {"bundles": ["basic"]}}
  ],
  "purchase_history": [
    {
      "order_id": "O-11001",
      "location_zip": "75201",
      "status": "completed",
      "discounts": 0.00,
      "items": [
        {"sku": "FOO-PUP-SM-5", "name": "Puppy Kibble Small Breed 5lb", "qty": 1, "unit_price": 19.99, "category": "food"},
        {"sku": "BOWL-SS", "name": "Stainless Steel Bowl", "qty": 1, "unit_price": 8.99, "category": "bowl"},
        {"sku": "BED-S", "name": "Plush Dog Bed (Small)", "qty": 1, "unit_price": 29.99, "category": "bed"}
      ]
    }
  ]
}
```

---

### Usage
Use `petprofile_loader.py` to parse this file and build `PetParentState` objects:

```bash
python petprofile_loader.py ./petparentExamples.md
python petprofile_loader.py ./petparentExamples.md --pet-id P-104
python petprofile_loader.py ./petparentExamples.md --out petparent_states.jsonl
```
