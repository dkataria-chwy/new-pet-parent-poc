#!/usr/bin/env python3
"""
Test and Demo Script for Vector Search Engine

This script demonstrates how to use the pre-generated embeddings for semantic search.
It's completely independent from the embedding creation pipeline.

Usage:
    python test_search.py

Requirements:
    - Pre-generated embeddings at artifacts/catalog_embeds.jsonl
    - OpenAI API key in .env (for generating query embeddings)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vector_search import VectorSearchEngine
from storage_manager import EmbeddingStorageManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def run_example_searches(search_engine):
    """Run example searches to demonstrate the capabilities."""
    
    logger.info("\n" + "="*80)
    logger.info("🔍 EXAMPLE SEARCHES - Chewy Concierge Recommendation Queries")
    logger.info("="*80)
    
    # Example queries that your recommendation system might generate
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
        {
            "name": "Senior Dog Care",
            "query": "Senior large dog joint support; low-fat easy digest food; orthopedic bed for comfort; gentle chew toys for sensitive teeth; supplements for mobility",
            "species": "dog", 
            "top_k": 6
        },
        {
            "name": "Summer/Heat Wave Products",
            "query": "Summer cooling products; heat wave relief mat; elevated water bowl; frozen treat molds; shade shelter for yard dogs",
            "species": "dog",
            "top_k": 5
        },
        {
            "name": "Sensitive Stomach Solutions",
            "query": "Sensitive stomach formula; limited ingredient diet; probiotics for digestive health; hypoallergenic treats; grain-free options",
            "species": "dog",
            "top_k": 5
        },
        {
            "name": "Kitten Starter Kit",
            "query": "Month 1 kitten starter; growth food with DHA; soft kitten toys; kitten training treats; scratching post",
            "species": "cat",
            "top_k": 5
        },
        {
            "name": "High-Energy Working Dog",
            "query": "High-energy working dog nutrition; endurance supplements; durable outdoor toys; training rewards; recovery nutrition",
            "species": "dog",
            "top_k": 5
        }
    ]
    
    for i, example in enumerate(example_queries, 1):
        logger.info(f"\n🎯 Example {i}: {example['name']}")
        logger.info(f"Query: \"{example['query']}\"")
        logger.info(f"Species: {example['species']} | Top-K: {example['top_k']}")
        logger.info("-" * 60)
        
        try:
            results = search_engine.search(
                query_text=example["query"],
                top_k=example["top_k"], 
                species_filter=example["species"]
            )
            
            if results:
                for result in results:
                    logger.info(f"  {result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"     {result['search_text_preview']}")
                    logger.info(f"     Species: {'🐕' if result['species_flags']['dog'] else ''}{'🐱' if result['species_flags']['cat'] else ''}")
            else:
                logger.warning("  No results found!")
                
        except Exception as e:
            logger.error(f"  Search failed: {e}")


def run_interactive_search(search_engine):
    """Run interactive search where user can input custom queries."""
    
    logger.info("\n" + "="*80)
    logger.info("💬 INTERACTIVE SEARCH MODE")
    logger.info("="*80)
    logger.info("Enter your own search queries! (type 'quit' to exit)")
    logger.info("Examples:")
    logger.info("  - 'puppy food with DHA'")
    logger.info("  - 'durable chew toy for strong chewer'") 
    logger.info("  - 'calming treats for anxiety'")
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
                top_k = max(1, min(top_k, 20))  # Limit between 1-20
            except ValueError:
                top_k = 5
            
            # Run search
            logger.info(f"\n🔍 Searching: '{query}' (species: {species or 'both'}, top-{top_k})")
            logger.info("-" * 40)
            
            results = search_engine.search(
                query_text=query,
                top_k=top_k,
                species_filter=species
            )
            
            if results:
                for result in results:
                    logger.info(f"{result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"   {result['search_text_preview']}")
                    species_icons = ('🐕' if result['species_flags']['dog'] else '') + ('🐱' if result['species_flags']['cat'] else '')
                    logger.info(f"   Species: {species_icons}")
                    logger.info("")
            else:
                logger.warning("No results found!")
                
        except KeyboardInterrupt:
            logger.info("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Search error: {e}")


def test_similar_products(search_engine):
    """Test finding similar products to a given product."""
    
    logger.info("\n" + "="*80)
    logger.info("🔗 SIMILAR PRODUCTS TEST")
    logger.info("="*80)
    
    # Test with a known product (using first few from our data)
    test_products = ["49744", "49743", "64330", "90881"]  # From our search results
    
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
            break  # Stop testing if product not found


def main():
    """Main function to run all tests and demos."""
    
    logger.info("🚀 VECTOR SEARCH ENGINE - TEST & DEMO")
    logger.info("="*80)
    
    try:
        # Load search engine
        search_engine = load_search_engine()
        
        # Run example searches (automated)
        run_example_searches(search_engine)
        
        # Test similar products 
        test_similar_products(search_engine)
        
        # Ask user if they want interactive mode
        logger.info("\n" + "="*80)
        response = input("🤔 Would you like to try interactive search? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            run_interactive_search(search_engine)
        else:
            logger.info("✅ Demo completed! Vector search engine is ready for integration.")
            
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        logger.info("💡 Make sure to run the embedding pipeline first!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
