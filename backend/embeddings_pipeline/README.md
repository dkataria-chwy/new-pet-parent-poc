# Product Embeddings Pipeline

A modular system for generating semantic embeddings from the Chewy product catalog, designed for the Chewy Concierge Recommender system.

## 🎯 Overview

This pipeline transforms product catalog data into semantic embeddings that enable intelligent product recommendations through vector similarity search. It follows the approach outlined in the "Chewy Concierge Recommender" specification.

## 📋 Features

- **Species-aware processing**: Automatically identifies and filters Dog/Cat products
- **Structured search text**: Deterministic text construction for consistent embeddings  
- **Batch processing**: Efficient OpenAI API usage with rate limiting
- **JSONL storage**: Simple, inspectable output format
- **Vector search**: Built-in semantic search capabilities
- **Cost estimation**: Transparent API cost tracking

## 🏗️ Architecture

```
📁 embeddings_pipeline/
├── 📁 src/                    # Core modules
│   ├── data_loader.py         # CSV loading & species normalization
│   ├── search_text_builder.py # Deterministic text construction
│   ├── embedding_generator.py # OpenAI API integration
│   ├── storage_manager.py     # JSONL persistence
│   ├── vector_search.py       # Semantic search engine
│   └── pipeline.py           # Main orchestrator
├── 📁 artifacts/             # Output directory
├── run_pipeline.py           # CLI entry point for creation
├── test_search.py            # CLI entry point for testing/demo
└── requirements.txt          # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend/embeddings_pipeline
source ../venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

Ensure OPENAI_API_KEY is set in the project root `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Generate Embeddings (One-Time)

```bash
python run_pipeline.py "../product embeddings table.csv"
```

### 4. Test Vector Search

```bash
python test_search.py
```

## 📊 Pipeline Steps

### Step 1: Data Loading & Species Normalization
- Loads product CSV with UTF-8 encoding
- Derives `SPECIES_DOG_FLAG` and `SPECIES_CAT_FLAG` from:
  - `PRODUCT_CATEGORY_LEVEL1` (primary species field)
  - `PRODUCT_ATTR_PET_TYPE` (multi-valued field)
- Filters to Dog/Cat products only

### Step 2: Search Text Construction
Builds deterministic search text using this exact format:
```
{PRODUCT_NAME}. 
Brand: {PRODUCT_PURCHASE_BRAND}. 
Species: dog/cat/dog,cat. 
Category: {LEVEL1} > {LEVEL2} > {LEVEL3} ({CATEGORY_LIST}). 
Merch: {CLASS1} | {CLASS2} | {CLASS3}. 
Lifestage: {LIFESTAGE}. Breed-size: {BREED_SIZE}. 
Food-form: {FOOD_FORM}. Special-diet: {SPECIAL_DIET}. 
Parent: {PARENT_PRODUCT_NAME}. 
Flags: rx_required:false consumable:true food:true. 
Long description: {PRODUCT_DESCRIPTION_LONG}
```

### Step 3: Embedding Generation
- Uses OpenAI `text-embedding-3-large` (3072 dimensions)
- Batch processing with rate limiting
- Automatic retry logic with exponential backoff
- Cost estimation and tracking

### Step 4: Storage & Validation
- Saves to `./artifacts/catalog_embeds.jsonl`
- Each line: `{"product_part_number": "...", "search_text": "...", "embedding": [...], ...}`
- Validates embedding dimensions and integrity
- Generates comprehensive metadata

## 🔍 Vector Search API

### Basic Search
```python
from src.vector_search import VectorSearchEngine
from src.storage_manager import EmbeddingStorageManager

# Load embeddings
storage = EmbeddingStorageManager()
df = storage.load_embeddings()

# Initialize search engine  
search_engine = VectorSearchEngine()
search_engine.load_embeddings(df)

# Search
results = search_engine.search(
    query_text="puppy food with DHA",
    top_k=10,
    species_filter='dog',  # 'dog', 'cat', or None
    min_similarity=0.7
)
```

### Similar Product Search
```python
similar = search_engine.search_similar_products(
    product_part_number="1234567",
    top_k=10,
    exclude_self=True
)
```

## 📈 Output Format

### JSONL Structure
```json
{
  "product_part_number": "1234567",
  "search_text": "Iams Proactive Health Minichunks Dry Dog Food...",
  "embedding": [-0.01234, 0.00321, 0.01987, ...],
  "species_dog_flag": true,
  "species_cat_flag": false,
  "embedded_at": "2025-09-16T12:00:00Z"
}
```

### Search Results
```python
[
  {
    "rank": 1,
    "product_part_number": "1234567",
    "similarity": 0.892,
    "search_text_preview": "Iams Proactive Health Large Breed Puppy...",
    "species_flags": {"dog": true, "cat": false}
  }
]
```

## 💰 Cost Information

For the full catalog (117,584 products):
- **Model**: text-embedding-3-large @ $0.00013 per 1K tokens
- **Actual cost**: ~$17.15 (13.2M tokens processed)
- **Processing time**: ~57 minutes
- **Output**: 4.7GB JSONL file

## 🧪 Testing & Demo

Use `test_search.py` to:
- Test semantic search with example queries
- Try interactive search mode
- Find similar products
- Validate search functionality

Example test queries:
- "Month 1 large-breed puppy starter; growth food with DHA"
- "Senior large dog joint support; low-fat easy digest food"
- "Summer cooling products; heat wave relief mat"

## 🔄 Integration with Recommender System

This pipeline produces the foundation for the Chewy Concierge Recommender:

1. **LLM Query Generation**: The recommendation system generates semantic queries
2. **Vector Retrieval**: Search engine finds top candidates using cosine similarity
3. **LLM Selection**: Final product selection and explanation generation

```python
# Your recommendation system workflow:
query = "Month 1 large-breed puppy; growth food with DHA; durable teething chew"
candidates = search_engine.search(query, top_k=50, species_filter='dog')
final_recs = llm_planner.select_and_explain(candidates, pet_profile, context)
```

## 📝 File Outputs

- `artifacts/catalog_embeds.jsonl` - Main embeddings file (4.7GB)
- `artifacts/embedding_metadata.json` - Pipeline metadata
- `embeddings_pipeline.log` - Execution log

## 🛠️ Troubleshooting

### Common Issues

1. **"No OPENAI_API_KEY found"**: Ensure API key is set in root `.env` file
2. **Memory issues**: The search index uses ~2.8GB RAM for 117K products
3. **File not found**: Ensure `catalog_embeds.jsonl` exists before testing search

### Re-running Pipeline

To regenerate embeddings:
1. Delete `artifacts/catalog_embeds.jsonl`
2. Run `python run_pipeline.py "path/to/catalog.csv"`
3. Wait ~60 minutes and pay ~$17 in API costs

---

**Generated by**: Chewy Product Embeddings Pipeline v1.0.0  
**Compatible with**: OpenAI text-embedding-3-large  
**Output format**: JSONL (3072-dimensional embeddings)
