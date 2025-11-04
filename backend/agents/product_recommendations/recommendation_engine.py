"""
Main product recommendation engine that processes LLM slots and returns recommendations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Try relative imports first (when imported as module), fall back to absolute (when run directly)
try:
    from .storage_loader import EmbeddingStorageLoader
    from .vector_search import SpeciesAwareVectorSearch
    from .qdrant_vector_search_rest import QdrantVectorSearch  # Using REST API for reliability
    from .filters import ProductFilters
except ImportError:
    from agents.product_recommendations.storage_loader import EmbeddingStorageLoader
    from agents.product_recommendations.vector_search import SpeciesAwareVectorSearch
    from agents.product_recommendations.qdrant_vector_search_rest import QdrantVectorSearch  # Using REST API for reliability
    from agents.product_recommendations.filters import ProductFilters

logger = logging.getLogger(__name__)


class ProductRecommendationEngine:
    """Main engine for processing LLM slots and generating product recommendations."""
    
    def __init__(self, embeddings_path: str = None):
        """
        Initialize recommendation engine.
        
        Args:
            embeddings_path: Path to catalog embeddings file
        """
        if embeddings_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            embeddings_path = project_root / "backend/embeddings_pipeline/artifacts/catalog_embeds.jsonl"
        
        self.storage_loader = EmbeddingStorageLoader(str(embeddings_path))
        self.vector_search = None
        self.filters = ProductFilters()
        self.is_initialized = False
    
    def initialize(self) -> Dict[str, Any]:
        """
        Load embeddings and initialize search components.
        
        Returns:
            Initialization statistics
        """
        logger.info("Initializing Product Recommendation Engine...")
        
        # Check if we should use Qdrant
        use_qdrant = os.getenv("USE_QDRANT", "false").lower() == "true"
        
        if use_qdrant:
            logger.info("🚀 Using Qdrant vector database")
            self.vector_search = QdrantVectorSearch()
            
            # Try to get collection stats from Qdrant using REST API
            try:
                response = self.vector_search.session.get(
                    f"{self.vector_search.qdrant_url}/collections/{self.vector_search.collection_name}"
                )
                response.raise_for_status()
                collection_info = response.json()["result"]
                total_products = collection_info["points_count"]
                stats = {
                    "mode": "qdrant",
                    "total_products": total_products,
                    "message": f"Using Qdrant cloud vector database ({total_products:,} products)"
                }
            except Exception as e:
                logger.warning(f"Could not get Qdrant collection stats: {e}")
                stats = {"mode": "qdrant", "message": "Using Qdrant cloud vector database"}
        else:
            logger.info("📁 Using JSONL in-memory vector search")
            # Load and partition embeddings
            stats = self.storage_loader.load_and_partition()
            
            # Initialize vector search
            self.vector_search = SpeciesAwareVectorSearch(self.storage_loader)
            stats["mode"] = "jsonl"
        
        self.is_initialized = True
        logger.info("✅ Product Recommendation Engine ready!")
        
        return stats
    
    def process_llm_output(self, llm_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process LLM output with multiple slots and generate product recommendations.
        
        Args:
            llm_output: LLM-generated JSON with slots
            
        Returns:
            Compact recommendation results
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized. Call initialize() first.")
        
        slots = llm_output.get("slots", [])
        if not slots:
            raise ValueError("No slots found in LLM output")
        
        logger.info(f"Processing {len(slots)} slots...")
        
        # Process each slot
        slot_results = []
        all_unique_products = {}  # sku -> {name, max_similarity}
        
        for i, slot in enumerate(slots, 1):
            logger.info(f"\n--- Processing Slot {i}/{len(slots)}: {slot.get('slot_id', 'unknown')} ---")
            
            try:
                slot_products, actual_query = self._process_single_slot(slot)
                
                if slot_products:
                    # Store slot results with rationale, count, and actual query used
                    slot_result = {
                        "slot_id": slot.get("slot_id", f"slot_{i}"),
                        "top_family": slot.get("top_family", "Unknown"),
                        "rationale": slot.get("rationale", ""),
                        "count": len(slot_products),
                        "actual_query": actual_query,
                        "products": slot_products
                    }
                    slot_results.append(slot_result)
                    
                    # Track for global deduplication
                    for product in slot_products:
                        sku = product["sku"]
                        if sku not in all_unique_products or product["similarity"] > all_unique_products[sku]["similarity"]:
                            all_unique_products[sku] = {
                                "name": product["name"],
                                "similarity": product["similarity"]
                            }
                
            except Exception as e:
                logger.error(f"Failed to process slot {slot.get('slot_id', i)}: {e}")
                continue
        
        # Build final output
        result = self._build_output(llm_output, slot_results, all_unique_products)
        
        logger.info(f"\n✅ Processing complete!")
        logger.info(f"   📊 Slots processed: {len(slot_results)}/{len(slots)}")
        logger.info(f"   🎯 Unique products: {len(all_unique_products)}")
        
        return result
    
    def _process_single_slot(self, slot: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        """
        Process a single slot through the full pipeline.
        
        Args:
            slot: LLM slot configuration
            
        Returns:
            Tuple of (recommended products for this slot, actual query used)
        """
        # 1. Vector search with species pre-filtering
        results, actual_query = self.vector_search.search_slot(slot)
        
        if not results:
            logger.warning(f"No products found in vector search for slot: {slot.get('slot_id', 'unknown')}")
            return [], actual_query
        
        # 2. Apply rule-based musts filtering (DISABLED for now)
        # musts = slot.get("musts", [])
        # results = self.filters.apply_musts_filter(results, musts)
        # 
        # if not results:
        #     logger.warning(f"No products remaining after musts filtering")
        #     return []
        
        logger.info(f"Musts filtering disabled - keeping all {len(results)} products")
        
        # 3. Apply LLM-based negatives filtering
        negatives = slot.get("negatives", [])
        results = self.filters.apply_negatives_filter(results, negatives)
        
        if not results:
            logger.warning(f"No products remaining after negatives filtering")
            return []
        
        # 4. Sort by similarity descending and clean up results
        results_sorted = sorted(results, key=lambda x: x["similarity"], reverse=True)
        
        # Note: Parent SKU deduplication now happens in vector_search.py during adaptive search
        
        clean_results = []
        for rank, product in enumerate(results_sorted, 1):
            clean_product = {
                "rank": rank,
                "sku": product["sku"],
                "parentSKU": product.get("parentSKU", ""),
                "name": product["name"],
                "product_link": product.get("product_link", ""),
                "product_price_current": product.get("product_price_current", None),
                "autoship_eligible": product.get("autoship_eligible", False),
                "similarity": round(product["similarity"], 4)
            }
            clean_results.append(clean_product)
        
        logger.info(f"Final results for slot: {len(clean_results)} products")
        return clean_results, actual_query
    
    def _build_output(self, llm_output: Dict[str, Any], slot_results: List[Dict], all_unique_products: Dict) -> Dict[str, Any]:
        """
        Build final compact output format.
        
        Args:
            llm_output: Original LLM output
            slot_results: Results per slot
            all_unique_products: Deduplicated products across all slots
            
        Returns:
            Final recommendation output
        """
        # Extract metadata from LLM output filename pattern or content
        pet_id = "unknown"
        month = 0
        
        # Try to extract from common patterns in the data
        if "pet_id" in llm_output:
            pet_id = llm_output["pet_id"]
        if "month" in llm_output:
            month = llm_output["month"]
        
        # Build all_products list
        all_products = [
            {
                "sku": sku,
                "name": data["name"]
            }
            for sku, data in all_unique_products.items()
        ]
        
        return {
            "pet_id": pet_id,
            "month": month,
            "timestamp": datetime.now().isoformat(),
            "processed_slots": len(slot_results),
            "total_unique_products": len(all_products),
            "results": slot_results,
            "all_products": all_products
        }
    
    def process_file(self, llm_output_file: str) -> Dict[str, Any]:
        """
        Process LLM output from a JSON file.
        
        Args:
            llm_output_file: Path to LLM output JSON file
            
        Returns:
            Recommendation results
        """
        file_path = Path(llm_output_file)
        
        # If relative path, make it relative to the current working directory first,
        # then try relative to backend directory if that doesn't work
        if not file_path.is_absolute():
            # First try: relative to current working directory
            if file_path.exists():
                pass  # Use as-is
            else:
                # Second try: relative to backend directory
                backend_root = Path(__file__).parent.parent.parent  # Go up to backend/
                file_path = backend_root / llm_output_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"LLM output file not found: {file_path}")
        
        # Load LLM output
        with open(file_path, 'r') as f:
            llm_output = json.load(f)
        
        # Extract pet_id and month from filename if not in data
        # Expected pattern: model_output_{pet_id}_month{N}_timestamp.json
        filename = file_path.stem
        parts = filename.split('_')
        
        if len(parts) >= 3 and not llm_output.get("pet_id"):
            try:
                llm_output["pet_id"] = parts[2]  # Extract pet_id
            except:
                pass
        
        if "month" in filename and not llm_output.get("month"):
            try:
                # Extract month number from filename
                for part in parts:
                    if part.startswith("month"):
                        llm_output["month"] = int(part.replace("month", ""))
                        break
            except:
                pass
        
        return self.process_llm_output(llm_output)
