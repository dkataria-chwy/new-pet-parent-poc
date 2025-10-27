# Breed-Specific Product Recommendation Ontology

**Purpose:** Capture breed-specific care needs and product requirements that LLMs miss without structured knowledge, enabling smarter, more preventive product recommendations.

---

## 📊 ONTOLOGY STRUCTURE (All paths → Products)

### **Core Relationship Types:**

**1. Genetic Risk → Prevention Products (Food, Supplements)**
- Golden Retriever (60% cancer at age 6) → 🍖 Antioxidant-Rich Senior Dog Food, 💊 High-Potency Omega-3 Fish Oil, 💊 Advanced Hip & Joint Supplement with Glucosamine & Chondroitin
- Cavalier (60% MVD at age 5) → 🍖 Low-Sodium Heart-Healthy Dog Food Formula, 💊 Taurine Supplement for Canine Heart Health, 🦴 Low-Sodium Training Treats
- German Shepherd (45% hip dysplasia) → 🍖 Large Breed Dog Food with Joint Support, 💊 Hip & Joint Supplement for Large Breeds (start age 8mo)

**2. Anatomy → Required Care Products (Grooming/Care)**
- Basset ears (extreme length) → 🧴 Enzymatic Ear Cleaning Solution for Dogs (2-3x/week), 🧼 Dog Ear Wipes Bulk Pack, 🧴 Ear Drying Powder for Moisture Control
- Shar Pei folds → 🧼 Medicated Wrinkle & Skin Fold Wipes (daily), 🧴 Antifungal Powder for Dog Skin Folds, 🧴 Probiotic Skin & Coat Spray
- Bulldog tail pocket → 🧼 Tail Pocket Cleaning Wipes for Bulldogs (daily), 🧴 Grooming Powder for Skin Folds

**3. Climate Thresholds → Safety Products (Accessories, Toys)**
- Bulldog >75°F = heatstroke → 🛏️ Gel-Infused Cooling Mat for Dogs, 🦺 Evaporative Cooling Vest for Flat-Faced Breeds, 🧊 Silicone Frozen Treat Molds, 🎾 Indoor Puzzle Toy for Mental Stimulation
- Chihuahua <50°F = hypothermia → 🦺 Insulated Dog Sweater for Small Breeds, 👢 Waterproof Paw Boots for Snow & Ice, 🛏️ Self-Warming Heated Dog Bed
- Husky in hot climate → 🏊 Portable Kiddie Pool for Dogs, 🧊 Silicone Frozen Treat Molds, 🎾 Interactive Indoor Exercise Toy, 🦺 Cooling Bandana with Ice Pack Insert

**4. Fatal Contraindications → Alternative Products (Accessories)**
- Bulldog + Collar = tracheal collapse → ❌ NEVER collar | ✅ 🦺 No-Pull Front-Clip Harness for Medium Dogs (ONLY)
- German Shepherd + Exercise post-meal = bloat → 🍽️ Slow Feeder Dog Bowl Anti-Gulping, 🍽️ Elevated Feeder Stand for Large Breeds, 🎾 Low-Intensity Puzzle Toy
- Beef allergy → ❌ AVOID beef products | ✅ 🍖 Fish-Based Grain-Free Dog Food, 🦴 Duck & Venison Novel Protein Treats, 🦴 Sweet Potato Dehydrated Chews

**5. Catastrophic Combos → Product Bundles (Food + Grooming)**
- Food allergy + skin folds = systemic infection → 🍖 Hypoallergenic Limited-Ingredient Dog Food, 🧼 Medicated Chlorhexidine Wipes 2x/daily, 🧴 Antifungal Powder for Skin Folds, 🦺 Soft Inflatable E-Collar
- Hot weather + flat face → 🦺 Evaporative Cooling Vest for Bulldogs, 🍽️ Elevated Water Bowl with No-Spill Design, 🧊 Silicone Frozen Treat Molds, 🛏️ Gel-Infused Cooling Mat

**6. Age-Triggered Milestones → New Products (Food, Supplements)**
- Golden age 5-6 → 🍖 Senior Wellness Dog Food Formula, 💊 High-Dose Glucosamine & Chondroitin, 💊 Omega-3 Fish Oil, 💊 Antioxidant Complex Supplement
- Cavalier age 12mo → 🍖 Low-Sodium Heart-Healthy Dog Food, 💊 Taurine Supplement for Heart Health, 🦴 Low-Sodium Training Treats
- Chihuahua age 2-3 → 🦴 Daily Dental Chews for Small Dogs, 🧴 Dental Water Additive for Plaque Control, 🍖 Dental Health Formula Small Breed Food

**7. Progressive Conditions → Early Intervention (Food, Accessories)**
- Obesity → Arthritis → 🍖 Weight Management Low-Calorie Dog Food, 🍽️ Automatic Portion Control Smart Feeder, 💊 Glucosamine & Chondroitin Supplement (start early), 🛏️ Orthopedic Memory Foam Bed
- Dental disease → Gum problems → 🦴 Dental Chews with Tartar Control, 🍖 Dental Health Formula Dog Food, 🎾 Rope Toy for Dental Cleaning

**8. Treatment Bundles (Synergies) (Supplements + Food)**
- Joint health bundle → 💊 Glucosamine & Chondroitin + 💊 Omega-3 Fish Oil + 🍖 Joint Support Dog Food Formula (recommend together)
- Fold care bundle → 🧼 Medicated Wrinkle Wipes + 🧴 Antifungal Powder for Skin Folds + 🧴 Probiotic Skin Spray (mandatory set)
- Skin health bundle → 🍖 Omega-Rich Salmon & Sweet Potato Food + 💊 Fish Oil Supplement + 🧼 Oatmeal & Aloe Soothing Shampoo

**9. Allergen Risks → Safe Product Lists (Food, Treats)**
- Shar Pei 40% chicken/beef allergy → 🍖 Limited-Ingredient Fish & Sweet Potato Dog Food, 🦴 Novel Protein Duck & Kangaroo Treats, 💊 Probiotic Digestive Health Supplement
- German Shepherd common allergens → 🍖 Lamb & Brown Rice Dog Food Formula, 🦴 Fish-Based Training Treats, 🍖 Grain-Free Salmon Dog Food

**10. Environment × Anatomy → Protocol Upgrades (Grooming)**
- Floppy ears + rainy climate → 🧴 Enzymatic Ear Cleaning Solution (upgrade to 2x/week), 🧼 Dog Ear Wipes Bulk Pack (200 count), 🧴 Ear Drying Powder with Boric Acid
- Skin folds + humid climate → 🧼 Medicated Wrinkle Wipes Double Pack (200 count), 🧴 Antifungal Powder Extra Strength, 🧴 Moisture-Wicking Wrinkle Spray

---

## 🔍 EXAMPLE: Golden Retriever, Age 6, Rainy Climate

**LLM Output:** "Ear cleaning, joint supplement, grooming"

**KG-Enhanced Output:** 
- **60% cancer risk at this exact age** → 💊 High-Potency Omega-3 Fish Oil with EPA & DHA, 🍖 Antioxidant-Rich Senior Dog Food with Superfoods, 💊 Antioxidant Complex with Vitamins C & E
- **60% hip dysplasia** → 💊 High-Dose Glucosamine & Chondroitin (2x strength), 🍖 Large Breed Joint Support Dog Food Formula, 🛏️ Orthopedic Memory Foam Bed for Large Breeds
- **Floppy ears + rainy climate** → 🧴 Enzymatic Ear Cleaning Solution for Dogs (upgrade to 2x/week protocol), 🧼 Dog Ear Wipes Bulk Pack (200 count), 🧴 Ear Drying Powder for Moisture Control

**Product Categories Covered:**
- 🍖 **Food:** Antioxidant-Rich Senior Dog Food, Large Breed Joint Support Formula
- 💊 **Supplements:** High-Potency Omega-3, High-Dose Glucosamine & Chondroitin, Antioxidant Complex
- 🧴 **Grooming:** Enzymatic Ear Cleaning Solution, Ear Drying Powder
- 🧼 **Care Products:** Dog Ear Wipes Bulk Pack (200 count)
- 🛏️ **Accessories:** Orthopedic Memory Foam Bed for Large Breeds

**What LLM Misses:**
- ❌ Specific prevalence rates (60% vs. "can have") → Enables confident, early recommendations
- ❌ Age-triggered onset (72 months = prevention starts NOW) → Timing for product upgrades
- ❌ Climate-adjusted protocols (2x/week vs. weekly) → Need bulk sizes (200 count vs. 50)
- ❌ Product specificity (enzymatic solution + drying powder vs. basic wipes)

---

## 📈 LLM vs. KG: What Actually Gets Missed (Impacts Product Recs)

| What LLMs Miss | Example | Why It Matters for Products |
|----------------|---------|----------------------------|
| **Prevalence rates** | "60% of Cavaliers" vs. "can have" | Urgency: Recommend heart-healthy products at age 1, not "eventually" |
| **Onset ages** | "72 months" vs. "as they age" | Timing: Start joint supplements at 8mo, not waiting until symptoms |
| **Care timing windows** | "3-12mo" vs. "when needed" | Critical: Eye care products become essential during this window |
| **Temp thresholds** | ">75°F" vs. "hot weather" | Safety: Recommend cooling products at specific temps |
| **Care frequencies** | "2-3x/week" vs. "regularly" | Volume: Need to recommend bulk/larger sizes for frequent use |
| **Rare breed traits** | FSF, extreme folds, tracheal sensitivity | Product gaps: LLM would miss specialized care products entirely |
| **Equipment safety** | "Harness ONLY" vs. "harness better" | Critical: Must exclude collar products, not just suggest alternatives |
| **Compounding factors** | "Allergy + folds = intensive care" | Bundles: Need to recommend complete care protocol, not isolated products |

---

## 🔥 VET-SPECIFIC BREED CONDITIONS → OTC PRODUCTS

**Cavalier King Charles Spaniel - Mitral Valve Disease (MVD)**
```cypher
(:Cavalier) -[:PRONE_TO {prevalence: 0.60, onset_age: 60}]-> (:MVD)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS]-> 
    💊 Taurine Supplement 500-1000mg for Canine Heart Health (start age 12mo)
    💊 CoQ10 Heart Support Supplement for Dogs
    💊 Omega-3 Fish Oil for Cardiac & Cardiovascular Support
    🍖 Low-Sodium Heart-Healthy Dog Food Formula
    🦴 Low-Sodium Training Treats for Heart Health
```

**Golden Retriever - Cancer & Hip Dysplasia**
```cypher
(:Golden) -[:PRONE_TO {prevalence: 0.60, onset_age: 72}]-> (:Cancer)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS]-> 
    💊 High-Potency Omega-3 Fish Oil with EPA & DHA for Senior Dogs
    💊 Antioxidant Complex with Vitamins C & E for Immune Support
    🍖 Antioxidant-Rich Senior Dog Food with Superfoods
    
(:Golden) -[:PRONE_TO {prevalence: 0.60, onset_age: 72}]-> (:HipDysplasia)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS {start_age: 8}]-> 
    💊 Advanced Hip & Joint Supplement with Glucosamine & Chondroitin (start age 8mo)
    💊 MSM Joint Support Supplement for Large Breed Dogs
    🍖 Large Breed Adult Dog Food with Joint Support Formula
    🛏️ Orthopedic Memory Foam Dog Bed for Large Breeds (age 5+)
```

**Shar Pei - Familial Shar Pei Fever (FSF) & Skin Folds**
```cypher
(:SharPei) -[:PRONE_TO {prevalence: 0.23, onset_age: 4-18}]-> (:FSF)
  -[:RECOMMEND_MONITORING_PRODUCTS]-> 
    🌡️ Digital Pet Thermometer for Fever Monitoring
    🍖 Omega-Rich Anti-Inflammatory Dog Food Formula
    💊 Probiotic Digestive Health Supplement for Dogs
    💊 Omega-3 Fish Oil Anti-Inflammatory Supplement
    
(:SharPei) -[:ANATOMICAL_TRAIT]-> (:ExtremeFolds)
  -[:RECOMMEND_CARE_PRODUCTS {frequency: "daily", duration: "10min"}]-> 
    🧼 Medicated Wrinkle & Skin Fold Wipes with Chlorhexidine
    🧴 Antifungal Powder for Dog Skin Folds
    🧴 Probiotic Skin & Coat Spray for Wrinkle Care
    🍖 Limited-Ingredient Dog Food for Sensitive Skin (40% allergen risk)
```

**German Shepherd - Hip Dysplasia & Degenerative Myelopathy (DM)**
```cypher
(:GermanShepherd) -[:PRONE_TO {prevalence: 0.45, onset_age: 24}]-> (:HipDysplasia)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS {start_age: 8}]-> 
    💊 Hip & Joint Supplement with Glucosamine & Chondroitin for Large Breeds (start age 8mo)
    💊 Omega-3 Fish Oil for Joint Health & Mobility
    🍖 Large Breed Adult Dog Food with Glucosamine & Joint Support
    🛏️ Orthopedic Memory Foam Bed for Large & Giant Breeds
    
(:GermanShepherd) -[:PRONE_TO {prevalence: 0.08, onset_age: 96}]-> (:DM)
  -[:RECOMMEND_SUPPORTIVE_PRODUCTS]-> 
    💊 B-Complex Vitamin Supplement for Neurological Health
    💊 Vitamin E Antioxidant Supplement for Dogs
    🍖 Senior Dog Food with Neurological Support Formula (age 7+)
```

**Chihuahua - Dental Disease & Tracheal Collapse**
```cypher
(:Chihuahua) -[:PRONE_TO {prevalence: 0.80, onset_age: 36}]-> (:DentalDisease)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS {start_age: 12}]-> 
    🦴 Daily Dental Chews for Small Dogs & Toy Breeds (age 1+)
    🍖 Dental Health Formula Dog Food for Small Breeds
    🧴 Dental Water Additive for Fresh Breath & Plaque Control
    🎾 Dental Rope Toy for Teeth Cleaning & Gum Health
    
(:Chihuahua) -[:PRONE_TO {prevalence: 0.30}]-> (:TracheaCollapse)
  -[:RECOMMEND_SAFE_PRODUCTS]-> 
    🦺 Soft Mesh Harness for Small Dogs (NEVER use collar)
    💊 Omega-3 Supplement for Respiratory & Airway Support
    🧴 HEPA Air Purifier for Pet Allergens & Irritants
```

**Bulldog - Brachycephalic Obstructive Airway Syndrome (BOAS)**
```cypher
(:Bulldog) -[:ANATOMICAL_TRAIT]-> (:FlatFace + :BOAS)
  -[:RECOMMEND_SUPPORTIVE_PRODUCTS]-> 
    🛏️ Gel-Infused Cooling Mat for Dogs (overheating risk)
    🦺 Evaporative Cooling Vest for Bulldogs & Flat-Faced Breeds (use >72°F)
    🍽️ Elevated Slow Feeder Bowl to Reduce Gulping & Choking
    🍖 Weight Management Dog Food for Bulldogs (obesity worsens BOAS)
    💊 Omega-3 Fish Oil for Inflammation & Respiratory Support
    🧊 Silicone Frozen Treat Molds for Dogs
```

**Basset Hound - Chronic Ear Infections**
```cypher
(:BassetHound) -[:ANATOMICAL_TRAIT]-> (:ExtremeLongEars)
  -[:PRONE_TO {prevalence: 0.65}]-> (:ChronicEarInfections)
  -[:RECOMMEND_PREVENTIVE_PRODUCTS {frequency: "2-3x/week"}]-> 
    🧴 Enzymatic Ear Cleaning Solution for Dogs
    🧼 Dog Ear Wipes Bulk Pack (100 count)
    🧴 Ear Drying Powder for Moisture Control
    💊 Omega-3 Fish Oil Anti-Inflammatory Supplement
    🍖 Omega-Rich Dog Food for Skin & Coat Health
```

---

## 🎯 THE DIFFERENCE (Product Recommendations)

**Without KG:**
> "Golden Retrievers need: food, treats, brush, ear cleaner, joint supplement."

**With KG:**
> "Mario is 6. Based on breed-specific care needs (60% of Goldens develop joint/health issues at this age), here are his personalized products: 
> - 🍖 Antioxidant-Rich Senior Dog Food with Superfoods + 💊 High-Potency Omega-3 Fish Oil with EPA & DHA (preventive care)
> - 💊 High-Dose Glucosamine & Chondroitin (2x strength) + 🍖 Large Breed Joint Support Formula + 🛏️ Orthopedic Memory Foam Bed for Large Breeds (60% develop joint issues)
> - 🧴 Enzymatic Ear Cleaning Solution for Dogs 2x/week + 🧴 Ear Drying Powder for Moisture Control (rainy climate + floppy ears need more frequent care)"

**Value:**
- ✅ Specific prevalence (60% vs. "some") → Earlier, more confident recommendations
- ✅ Exact ages (8mo vs. "older") → Time product upgrades precisely
- ✅ Protocol detail (2x/week vs. "regularly") → Recommend bulk/larger sizes
- ✅ Multi-product bundles at age-triggered milestones → Complete care solutions

---

## 📊 NEXT STEP: Build JSON Prototype

**Start with top 5 high-impact breeds:**
- Golden Retriever (cancer, hip dysplasia, ear care)
- Shar Pei (FSF, entropion, fold care, allergens)
- Cavalier (MVD, echocardiogram milestones)
- Bulldog (BOAS, heatstroke thresholds, collar contraindication)
- Chihuahua (dental, hypothermia, tracheal collapse)

**Implementation:** Pass breed-specific JSON to Stage 1 LLM as structured context alongside the current prompt.