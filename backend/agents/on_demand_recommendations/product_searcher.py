"""
Product Search Module for On-Demand Recommendations

Handles vector search using enhanced embedding queries to find relevant products.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from product_recommendations.storage_loader import EmbeddingStorageLoader
from product_recommendations.qdrant_vector_search_rest import QdrantVectorSearch

# Import the on-demand vector search (for JSONL fallback)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from vector_search import OnDemandVectorSearch

logger = logging.getLogger(__name__)


class OnDemandProductSearcher:
    """Searches for products using enhanced embedding queries."""
    
    def __init__(self):
        """Initialize the product searcher with on-demand vector search."""
        # Set correct embeddings path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        embeddings_path = project_root / "backend/embeddings_pipeline/artifacts/catalog_embeds.jsonl"
        
        self.storage_loader = EmbeddingStorageLoader(str(embeddings_path))
        self.vector_search = None
        self.qdrant_search = None  # For Qdrant mode
        self.is_initialized = False
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the on-demand vector search.
        
        Returns:
            Initialization statistics
        """
        if not self.is_initialized:
            logger.info("Initializing on-demand product searcher...")
            
            # Check if we should use Qdrant
            use_qdrant = os.getenv("USE_QDRANT", "false").lower() == "true"
            
            if use_qdrant:
                logger.info("🚀 Using Qdrant vector database for on-demand search")
                # Use Qdrant REST implementation
                # Note: OnDemandVectorSearch will be set to None, we'll use QdrantVectorSearch directly
                self.qdrant_search = QdrantVectorSearch()
                self.vector_search = None  # Mark as not using JSONL
                
                # Get stats from Qdrant
                try:
                    import requests
                    session = requests.Session()
                    session.headers.update({'api-key': os.getenv('QDRANT_API_KEY')})
                    response = session.get(
                        f"{os.getenv('QDRANT_URL')}/collections/chewy_products_117k"
                    )
                    response.raise_for_status()
                    collection_info = response.json()["result"]
                    total_products = collection_info["points_count"]
                except Exception as e:
                    logger.warning(f"Could not get Qdrant stats: {e}")
                    total_products = 117584  # Fallback
                
                self.is_initialized = True
                logger.info("✅ On-demand product searcher ready with Qdrant!")
                
                return {
                    "total_products": total_products,
                    "search_type": "qdrant",
                    "status": "initialized"
                }
            else:
                logger.info("📁 Using JSONL in-memory vector search for on-demand")
                # Use JSONL-based search
                self.vector_search = OnDemandVectorSearch(self.storage_loader)
                self.qdrant_search = None
                self.is_initialized = True
                logger.info("✅ On-demand product searcher ready with JSONL!")
                
                # Return stats in the format expected by main.py
                # Get the stats from storage_loader which should have total_products
                if hasattr(self.storage_loader, 'full_df') and self.storage_loader.full_df is not None:
                    total_products = len(self.storage_loader.full_df)
                else:
                    total_products = 0  # Fallback
                    
                return {
                    "total_products": total_products,
                    "search_type": "on_demand_vector_search",
                    "status": "initialized"
                }
        return {"total_products": 0}
    
    def search_products(self, 
                       embedding_query: str, 
                       species: str, 
                       top_k: int = 20,
                       brand_preferences: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for products using the enhanced embedding query.
        
        Args:
            embedding_query: The LLM-generated embedding query with facets
            species: Pet species for filtering ("Dog" or "Cat")
            top_k: Number of products to return
            brand_preferences: List of preferred brands (not used to avoid bias)
            
        Returns:
            List of product recommendations with SKU, parentSKU, name, similarity
        """
        if not self.is_initialized:
            raise ValueError("Product searcher not initialized. Call initialize() first.")
        
        logger.info(f"🔍 On-demand search with query: '{embedding_query}'")
        logger.info(f"Species: {species}, Top-K: {top_k}")
        
        try:
            if self.qdrant_search:
                # Use Qdrant REST API
                logger.info("Using Qdrant for search")
                
                # Create a slot in the format expected by Qdrant search
                slot = {
                    "slot_id": "on_demand",
                    "embedding_query": embedding_query,
                    "filters": {"pc1": species.lower()},
                    "top_k": top_k,
                    "brand_bias": brand_preferences or []
                }
                
                # Search using Qdrant
                results, _ = self.qdrant_search.search_slot(slot)
                
                logger.info(f"✅ Found {len(results)} products from Qdrant")
                return results
                
            else:
                # Use JSONL-based search (original behavior)
                logger.info("Using JSONL for search")
                results = self.vector_search.search_products(
                    embedding_query=embedding_query,
                    species=species,
                    top_k=top_k,
                    brand_preferences=brand_preferences  # Passed but not used internally
                )
                
                logger.info(f"✅ Found {len(results)} products from JSONL")
                return results
            
        except Exception as e:
            logger.error(f"❌ On-demand product search failed: {e}")
            raise
    
    def format_results(self, 
                      products: List[Dict[str, Any]], 
                      rationale: str,
                      embedding_query: str) -> Dict[str, Any]:
        """
        Format the search results for API response.
        
        Args:
            products: List of product recommendations
            rationale: Personalized rationale from LLM
            embedding_query: The embedding query used for search
            
        Returns:
            Formatted response dictionary
        """
        from datetime import datetime
        
        return {
            "timestamp": datetime.now().isoformat(),
            "query_used": embedding_query,
            "rationale": rationale,
            "total_products": len(products),
            "products": products
        }


def main():
    """Test function for on-demand product searcher."""
    searcher = OnDemandProductSearcher()
    
    try:
        # Initialize
        stats = searcher.initialize()
        print(f"📊 Initialized: {stats}")
        
        # Test search
        test_query = "dog; puppy; teething; chew-toys; medium-breed; durable; safe; winter; indoor"
        test_species = "dog"
        test_brands = ["KONG", "Nylabone"]
        
        results = searcher.search_products(
            embedding_query=test_query,
            species=test_species,
            top_k=10,
            brand_preferences=test_brands
        )
        
        print(f"\n🎉 Search Results ({len(results)} products):")
        for i, product in enumerate(results[:3], 1):  # Show first 3
            print(f"{i}. {product['sku']} (Parent: {product['parentSKU']}) - {product['name'][:80]}... (sim: {product['similarity']:.4f})")
        
        # Test formatting
        test_rationale = "These chew toys are perfect for Max's teething phase..."
        formatted = searcher.format_results(results, test_rationale, test_query)
        
        print(f"\n📋 Formatted Response:")
        print(f"Total Products: {formatted['total_products']}")
        print(f"Rationale: {formatted['rationale'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
