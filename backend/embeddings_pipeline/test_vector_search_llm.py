#!/usr/bin/env python3
"""
LLM-Aware Test and Demo Script for Vector Search Engine

This mirrors test_search.py but routes queries through the LLM Query Processor:
- Uses LLM to extract positive_terms, exclusions, brand preferences, target species
- Searches with positive_terms (negatives removed)
- Post-filters results to enforce exclusions

Usage:
    python test_search_llm.py

Requirements:
    - Pre-generated embeddings at artifacts/catalog_embeds.jsonl
    - OpenAI API key in .env (for LLM parsing and query embeddings)
"""

import sys
import os
from pathlib import Path
import re
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vector_search import VectorSearchEngine
from storage_manager import EmbeddingStorageManager
from llm_query_processor import LLMQueryProcessor
from openai import OpenAI
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration flag: Switch between LLM-based and rule-based exclusions
# 
# False (default): Uses rule-based filtering with hardcoded patterns
#   - Fast, deterministic, free
#   - Limited to exact word matches and predefined "X-free" patterns
#   - May miss "poultry" → "chicken" relationships
#
# True: Uses LLM-powered intelligent filtering  
#   - Understands ingredient categories (poultry=chicken/turkey/duck)
#   - Handles complex negations and context
#   - Costs ~$0.001 per product filtered
#
USE_LLM_EXCLUSIONS = True  # Set to True to enable LLM-powered exclusions


def load_search_engine():
    """Load the vector search engine with pre-generated embeddings."""
    logger.info("📁 Loading pre-generated embeddings...")
    
    # Check if embeddings exist
    embeddings_path = Path("artifacts/catalog_embeds.jsonl")
    if not embeddings_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {embeddings_path}\n"
            "Please run the pipeline first: python run_pipeline.py 'path/to/catalog.csv'"
        )
    
    # Load embeddings
    storage = EmbeddingStorageManager()
    df = storage.load_embeddings()
    
    # Initialize search engine
    logger.info("🔧 Initializing vector search engine...")
    search_engine = VectorSearchEngine()
    search_engine.load_embeddings(df)
    
    # Show stats
    stats = search_engine.get_search_stats()
    logger.info(f"✅ Search engine ready!")
    logger.info(f"   📊 Total products: {stats['total_products']:,}")
    logger.info(f"   🐕 Dog products: {stats['dog_products']:,}")
    logger.info(f"   🐱 Cat products: {stats['cat_products']:,}")
    logger.info(f"   💾 Index size: {stats['index_size_mb']:.1f} MB")
    
    return search_engine


def build_species_filter(example_species: str | None, target_species: str | None) -> str | None:
    """Respect example's species if provided; otherwise map LLM target species."""
    if example_species:
        return example_species
    if not target_species:
        return None
    ts = target_species.lower()
    if ts in ("dog", "cat"):
        return ts
    return None  # both/unknown


def apply_exclusions(results, exclusions, search_engine: VectorSearchEngine):
    """Filter out results that contain excluded ingredients (smart context-aware filtering)."""
    if not exclusions:
        return results
    filtered = []
    lower_exclusions = [e.lower() for e in exclusions if isinstance(e, str) and e]
    for r in results:
        try:
            prod_id = r['product_part_number']
            idx = search_engine.product_ids.index(prod_id)
            full_text = str(search_engine.embeddings_df.iloc[idx].get('search_text', '')).lower()
            
            should_exclude = False
            for exclusion in lower_exclusions:
                # Skip if the exclusion appears in negative contexts (good for user)
                if any(phrase in full_text for phrase in [
                    f"no {exclusion}", f"without {exclusion}", f"{exclusion}-free", 
                    f"free of {exclusion}", f"excludes {exclusion}"
                ]):
                    continue  # This is actually a good match
                
                # Check if exclusion appears as ingredient (bad for user)
                # Use word boundaries to avoid partial matches
                if re.search(rf'\b{re.escape(exclusion)}\b', full_text):
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered.append(r)
        except Exception:
            # If any lookup fails, keep the item rather than over-filter
            filtered.append(r)
    return filtered


def llm_exclusion_filter(product_description: str, exclusions: List[str]) -> bool:
    """
    Use LLM to determine if a product should be excluded based on user's exclusions.
    Returns True if product should be EXCLUDED.
    """
    if not exclusions:
        return False
    
    prompt = f"""User wants to AVOID: {', '.join(exclusions)}

Product: "{product_description}"

Guidelines:
- If the product CONTAINS what the user wants to avoid → Exclude (YES)
- If the product is explicitly formulated WITHOUT what the user wants to avoid → Keep (NO)
- Consider ingredient categories and related terms (poultry includes chicken/turkey/duck, grains include wheat/corn/rice, etc.)
- Look for positive language indicating absence (free, without, excludes, etc.)

Should this product be excluded from search results?
Answer: YES or NO"""

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper for filtering
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().upper()
        should_exclude = answer.startswith("YES")
        
        # Log the LLM's decision for debugging
        decision = "EXCLUDE" if should_exclude else "KEEP"
        logger.info(f"🧠 LLM Decision: {decision} - {answer}")
        
        return should_exclude
        
    except Exception as e:
        logger.warning(f"LLM filtering failed: {e}, keeping product")
        return False  # If LLM fails, don't exclude (safer)


def apply_llm_exclusions(results, exclusions, search_engine: VectorSearchEngine):
    """Apply LLM-powered smart exclusions"""
    if not exclusions:
        return results
    
    logger.info(f"🧠 Applying LLM-powered exclusions: {exclusions}")
    
    filtered = []
    excluded_count = 0
    
    for r in results:
        try:
            prod_id = r['product_part_number']
            idx = search_engine.product_ids.index(prod_id)
            full_text = str(search_engine.embeddings_df.iloc[idx].get('search_text', ''))
            
            # Show which product we're evaluating
            product_preview = full_text[:100] + "..." if len(full_text) > 100 else full_text
            logger.info(f"🤖 Evaluating Product {prod_id}: {product_preview}")
            
            should_exclude = llm_exclusion_filter(full_text, exclusions)
            
            if should_exclude:
                excluded_count += 1
                logger.info(f"❌ EXCLUDED: Product {prod_id}")
            else:
                filtered.append(r)
                logger.info(f"✅ KEPT: Product {prod_id}")
                
        except Exception as e:
            logger.warning(f"Error processing product {prod_id}: {e}")
            filtered.append(r)  # Keep if error
    
    logger.info(f"📊 Excluded {excluded_count}/{len(results)} products")
    return filtered


def apply_smart_exclusions(results, exclusions, search_engine: VectorSearchEngine):
    """
    Apply exclusions using either LLM-based or rule-based filtering.
    Controlled by the USE_LLM_EXCLUSIONS global flag.
    """
    if USE_LLM_EXCLUSIONS:
        logger.info("🧠 Using LLM-based exclusion filtering")
        return apply_llm_exclusions(results, exclusions, search_engine)
    else:
        logger.info("📋 Using rule-based exclusion filtering")
        return apply_exclusions(results, exclusions, search_engine)

def run_example_searches(search_engine, processor: LLMQueryProcessor):
    """Run example searches, but route through LLM parsing first."""
    logger.info("\n" + "="*80)
    logger.info("🔍 EXAMPLE SEARCHES (LLM-processed)")
    logger.info("="*80)
    
    example_queries = [
        {
            "name": "Puppy Starter Kit",
            "query": "Month 1 large-breed puppy starter; growth food with DHA and controlled calcium; durable teething chew for strong chewer; puppy training treats; VOHC dental starter",
            "species": "dog",
            "top_k": 8
        },
        {
            "name": "Adult Dog Maintenance", 
            "query": "Adult medium dog maintenance; grain-free salmon food; interactive puzzle toy for mental stimulation; dental chews for tartar control",
            "species": "dog",
            "top_k": 6
        },
        # {
        #     "name": "Senior Dog Care",
        #     "query": "Senior large dog joint support; low-fat easy digest food; orthopedic bed for comfort; gentle chew toys for sensitive teeth; supplements for mobility",
        #     "species": "dog", 
        #     "top_k": 6
        # },
        # {
        #     "name": "Summer/Heat Wave Products",
        #     "query": "Summer cooling products; heat wave relief mat; elevated water bowl; frozen treat molds; shade shelter for yard dogs",
        #     "species": "dog",
        #     "top_k": 5
        # },
        # {
        #     "name": "Sensitive Stomach Solutions",
        #     "query": "Sensitive stomach formula; limited ingredient diet; probiotics for digestive health; hypoallergenic treats; grain-free options",
        #     "species": "dog",
        #     "top_k": 5
        # },
        # {
        #     "name": "Kitten Starter Kit",
        #     "query": "Month 1 kitten starter; growth food with DHA; soft kitten toys; kitten training treats; scratching post",
        #     "species": "cat",
        #     "top_k": 5
        # },
        # {
        #     "name": "High-Energy Working Dog",
        #     "query": "High-energy working dog nutrition; endurance supplements; durable outdoor toys; training rewards; recovery nutrition",
        #     "species": "dog",
        #     "top_k": 5
        # }
    ]
    
    for i, example in enumerate(example_queries, 1):
        logger.info(f"\n🎯 Example {i}: {example['name']}")
        logger.info(f"Query: \"{example['query']}\"")
        logger.info(f"Species: {example['species']} | Top-K: {example['top_k']}")
        logger.info("-" * 60)
        
        try:
            analysis = processor.process_query(example["query"])
            positive = analysis.get("positive_terms") or example["query"]
            exclusions = analysis.get("exclusions", [])
            species_filter = build_species_filter(example.get("species"), analysis.get("target_species"))
            
            logger.info(f"🧠 LLM positive terms: '{positive}'")
            if exclusions:
                logger.info(f"🚫 Exclusions: {exclusions}")
            
            results = search_engine.search(
                query_text=positive,
                top_k=example["top_k"],
                species_filter=species_filter
            )
            
            filtered = apply_smart_exclusions(results, exclusions, search_engine)
            removed = len(results) - len(filtered)
            if removed > 0:
                logger.info(f"🧹 Removed {removed} results due to exclusions")
            
            if filtered:
                for result in filtered:
                    logger.info(f"  {result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"     {result['search_text_preview']}")
                    logger.info(f"     Species: {'🐕' if result['species_flags']['dog'] else ''}{'🐱' if result['species_flags']['cat'] else ''}")
            else:
                logger.warning("  No results after applying exclusions!")
                
        except Exception as e:
            logger.error(f"  Search failed: {e}")


def run_interactive_search(search_engine, processor: LLMQueryProcessor):
    """Run interactive search where user input is parsed by LLM first."""
    logger.info("\n" + "="*80)
    logger.info("💬 INTERACTIVE SEARCH MODE (LLM)")
    logger.info("="*80)
    logger.info("Enter your own search queries! (type 'quit' to exit)")
    logger.info("Examples:")
    logger.info("  - 'chicken and sweet potato dry dog food nature\'s recipe, no pumpkin'")
    logger.info("  - 'puppy food without corn or soy'")
    logger.info("-" * 60)
    
    while True:
        try:
            # Get user input
            query = input("\n🔍 Enter search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                logger.info("👋 Goodbye!")
                break
                
            if not query:
                continue
            
            # Get species filter
            species = input("🐾 Species filter (dog/cat/both): ").strip().lower()
            if species not in ['dog', 'cat', 'both']:
                species = None
            elif species == 'both':
                species = None
            
            # Get top-k
            try:
                top_k = int(input("📊 Number of results (default 5): ") or "5")
                top_k = max(1, min(top_k, 20))
            except ValueError:
                top_k = 5
            
            # LLM parse
            analysis = processor.process_query(query)
            positive = analysis.get("positive_terms") or query
            exclusions = analysis.get("exclusions", [])
            if not species:
                species = build_species_filter(None, analysis.get("target_species"))
            
            logger.info(f"\n🧠 Positive terms: '{positive}'")
            if exclusions:
                logger.info(f"🚫 Exclusions: {exclusions}")
            logger.info(f"🔎 Searching (species: {species or 'both'}, top-{top_k})")
            logger.info("-" * 40)
            
            results = search_engine.search(
                query_text=positive,
                top_k=top_k,
                species_filter=species
            )
            
            filtered = apply_smart_exclusions(results, exclusions, search_engine)
            
            if filtered:
                for result in filtered:
                    logger.info(f"{result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"   {result['search_text_preview']}")
                    species_icons = ('🐕' if result['species_flags']['dog'] else '') + ('🐱' if result['species_flags']['cat'] else '')
                    logger.info(f"   Species: {species_icons}")
                    logger.info("")
            else:
                logger.warning("No results after applying exclusions!")
                
        except KeyboardInterrupt:
            logger.info("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Search error: {e}")


def test_similar_products(search_engine):
    """Test finding similar products to a given product (unchanged)."""
    logger.info("\n" + "="*80)
    logger.info("🔗 SIMILAR PRODUCTS TEST")
    logger.info("="*80)
    
    test_products = ["49744", "49743", "64330", "90881"]
    
    for product_id in test_products:
        try:
            logger.info(f"\n🎯 Finding products similar to: {product_id}")
            similar = search_engine.search_similar_products(
                product_part_number=product_id,
                top_k=3,
                exclude_self=True
            )
            
            if similar:
                for result in similar:
                    logger.info(f"  {result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"     {result['search_text_preview']}")
            else:
                logger.warning(f"  No similar products found for {product_id}")
                
        except Exception as e:
            logger.warning(f"  Similar products test failed for {product_id}: {e}")
            break


def main():
    """Main function to run all tests and demos (LLM-aware)."""
    logger.info("🚀 VECTOR SEARCH ENGINE - LLM-AWARE TEST & DEMO")
    logger.info("="*80)
    
    # Log which exclusion method is being used
    exclusion_method = "LLM-powered" if USE_LLM_EXCLUSIONS else "Rule-based"
    logger.info(f"🔧 Exclusion filtering mode: {exclusion_method}")
    
    try:
        # Load search engine
        search_engine = load_search_engine()
        # Init LLM processor (defaults to gpt-5-2025-08-07 with fallbacks)
        processor = LLMQueryProcessor()
        
        # Run example searches (automated)
        run_example_searches(search_engine, processor)
        
        # Test similar products
        test_similar_products(search_engine)
        
        # Ask user if they want interactive mode
        logger.info("\n" + "="*80)
        response = input("🤔 Would you like to try interactive LLM search? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            run_interactive_search(search_engine, processor)
        else:
            logger.info("✅ Demo completed! LLM-aware vector search is ready.")
            
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        logger.info("💡 Make sure to run the embedding pipeline first!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
