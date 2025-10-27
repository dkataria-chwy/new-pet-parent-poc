"""
Vector search with species pre-filtering and cosine similarity.
"""

import numpy as np
import pandas as pd
import openai
import os
import logging
import re
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SpeciesAwareVectorSearch:
    """Vector search engine with species pre-filtering for performance."""
    
    def __init__(self, storage_loader):
        """
        Initialize vector search engine.
        
        Args:
            storage_loader: EmbeddingStorageLoader instance
        """
        self.storage_loader = storage_loader
        self.client = self._initialize_openai_client()
        
    def _initialize_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client for query embedding."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return openai.OpenAI(api_key=api_key)
    
    def _build_enhanced_query(self, slot: Dict[str, Any]) -> str:
        """
        Build enhanced query by adding missing musts values and brand bias.
        
        Args:
            slot: LLM slot with embedding_query, musts, and brand_bias
            
        Returns:
            Enhanced query string
        """
        base_query = slot.get("embedding_query", "")
        musts = slot.get("musts", [])
        brand_bias = slot.get("brand_bias", [])
        
        query_lower = base_query.lower()
        terms_to_add = []
        
        # 1. Add missing musts values
        for must in musts:
            if ":" in must:
                # Extract value from "key: value" format
                value = must.split(":", 1)[1].strip()
                # Check if value is already in query (handle variations like "small-medium" vs "small medium")
                value_variations = [
                    value.lower(),
                    value.lower().replace("-", " "),
                    value.lower().replace(" ", "-")
                ]
                
                if not any(variation in query_lower for variation in value_variations):
                    terms_to_add.append(value)
        
        # 2. Add missing brands
        for brand in brand_bias:
            if brand.lower() not in query_lower:
                terms_to_add.append(brand)
        
        # Build enhanced query
        if terms_to_add:
            enhanced_query = base_query + ";" + ";".join(terms_to_add)
            logger.info(f"Enhanced query with missing terms: {terms_to_add}")
            return enhanced_query
        
        return base_query
    
    def _apply_brand_boost(self, search_text: str, brand_bias: List[str], base_similarity: float) -> float:
        """
        Apply brand boosting to similarity score.
        
        Args:
            search_text: Product search text
            brand_bias: List of preferred brands
            base_similarity: Original cosine similarity score
            
        Returns:
            Boosted similarity score
        """
        if not brand_bias:
            return base_similarity
        
        search_text_lower = search_text.lower()
        boost_applied = False
        
        for brand in brand_bias:
            brand_lower = brand.lower()
            
            # Check for brand matches in different contexts
            brand_patterns = [
                f"brand: {brand_lower}",  # "Brand: Mars"
                f"{brand_lower} ",        # "Mars Petcare"
                f" {brand_lower} ",       # " Mars "
                f"{brand_lower}.",        # "Mars."
            ]
            
            if any(pattern in search_text_lower for pattern in brand_patterns):
                # Apply boost: 15% increase to similarity score
                boosted_score = min(base_similarity * 1.15, 1.0)  # Cap at 1.0
                logger.debug(f"Brand boost applied: {brand} ({base_similarity:.4f} → {boosted_score:.4f})")
                return boosted_score
        
        return base_similarity
    
    def _embed_query(self, query_text: str) -> np.ndarray:
        """
        Convert query text to embedding vector.
        
        Args:
            query_text: Query string to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-large",
                input=query_text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    def search_slot(self, slot: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        """
        Search for products matching a single slot.
        
        Args:
            slot: LLM slot with embedding_query, filters, top_k, etc.
            
        Returns:
            Tuple of (matching products with similarity scores, actual query used)
        """
        # Build enhanced query with brand bias
        query_text = self._build_enhanced_query(slot)
        species = slot.get("filters", {}).get("pc1", "")
        top_k = slot.get("top_k", 50)
        
        logger.info(f"Searching slot: {slot.get('slot_id', 'unknown')}")
        logger.info(f"Query: '{query_text}'")
        logger.info(f"Species: {species}, Top-K: {top_k}")
        
        # Get species-specific data (pre-filtering)
        try:
            df, embeddings_matrix = self.storage_loader.get_species_data(species)
        except ValueError as e:
            logger.error(f"Invalid species filter: {e}")
            return [], query_text
        
        if len(df) == 0:
            logger.warning(f"No products found for species: {species}")
            return [], query_text
        
        # Embed the query
        query_vector = self._embed_query(query_text)
        query_matrix = query_vector.reshape(1, -1)
        
        # Cosine similarity search
        similarities = cosine_similarity(query_matrix, embeddings_matrix)[0]
        
        # Adaptive search: fetch enough products to get top_k unique parent SKUs
        # Start with 2x top_k to account for duplicates, expand if needed
        search_size = min(top_k * 2, len(similarities))
        max_search_size = min(top_k * 5, len(similarities))  # Cap at 5x or total products
        
        seen_parent_skus = set()
        results = []
        brand_bias = slot.get("brand_bias", [])
        
        # Get all indices sorted by similarity
        all_indices = np.argsort(similarities)[::-1]
        
        # Iterate through products until we have enough unique parent SKUs
        for idx in all_indices[:max_search_size]:
            product_row = df.iloc[idx]
            parent_sku = product_row.get('parent_product_part_number', '')
            
            # Skip if we've already seen this parent SKU
            if parent_sku and parent_sku != "" and parent_sku in seen_parent_skus:
                continue
            
            # Track this parent SKU
            if parent_sku and parent_sku != "":
                seen_parent_skus.add(parent_sku)
            
            # Use product_name column from embeddings (added via add_columns_to_embeddings.py)
            product_name = product_row.get('product_name', None)
            
            # Fallback to extracting from search_text if product_name is missing
            if not product_name or pd.isna(product_name):
                search_text = product_row['search_text']
                if ' Brand:' in search_text:
                    product_name = search_text.split(' Brand:')[0].strip()
                else:
                    # Fallback: split on first period if Brand: not found
                    product_name = search_text.split('.')[0].strip()
            
            # Extract additional product fields from embeddings
            product_link = product_row.get('product_link', '')
            product_price = product_row.get('product_price_current', None)
            # Convert numpy bool to Python bool for JSON serialization
            autoship_eligible = bool(product_row.get('product_autoship_save_eligible_flag', False))
            
            search_text = product_row['search_text']
            
            # Apply brand boosting
            base_similarity = float(similarities[idx])
            boosted_similarity = self._apply_brand_boost(search_text, brand_bias, base_similarity)
            
            result = {
                'rank': len(results) + 1,  # Rank based on order added
                'sku': product_row['product_part_number'],
                'parentSKU': parent_sku,
                'name': product_name,
                'product_link': product_link,
                'product_price_current': product_price,
                'autoship_eligible': autoship_eligible,
                'similarity': boosted_similarity,
                'base_similarity': base_similarity,  # Keep original for debugging
                'brand_boosted': boosted_similarity != base_similarity,
                'search_text': search_text,  # For filtering
                'species_flags': {
                    'dog': product_row['species_dog_flag'],
                    'cat': product_row['species_cat_flag']
                }
            }
            results.append(result)
            
            # Stop once we have enough unique parent SKUs
            if len(results) >= top_k:
                break
        
        logger.info(f"Adaptive search: requested {top_k} unique products, found {len(results)} (scanned {min(len(all_indices), max_search_size)} candidates)")
        
        # Re-sort by boosted similarity if any boosts were applied
        if any(r['brand_boosted'] for r in results):
            results.sort(key=lambda x: x['similarity'], reverse=True)
            # Update ranks after re-sorting
            for i, result in enumerate(results, 1):
                result['rank'] = i
            logger.info(f"Applied brand boosting - results re-ranked")
        
        logger.info(f"Found {len(results)} products before filtering")
        return results, query_text
