"""
Vector search with species pre-filtering and cosine similarity.
"""

import numpy as np
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
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results with brand boosting
        results = []
        brand_bias = slot.get("brand_bias", [])
        
        for rank, idx in enumerate(top_indices, 1):
            product_row = df.iloc[idx]
            
            # Extract product name from search_text (everything before " Brand:")
            search_text = product_row['search_text']
            if ' Brand:' in search_text:
                product_name = search_text.split(' Brand:')[0].strip()
            else:
                # Fallback: split on first period if Brand: not found
                product_name = search_text.split('.')[0].strip()
            
            # Apply brand boosting
            base_similarity = float(similarities[idx])
            boosted_similarity = self._apply_brand_boost(search_text, brand_bias, base_similarity)
            
            result = {
                'rank': rank,
                'sku': product_row['product_part_number'],
                'name': product_name,
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
        
        # Re-sort by boosted similarity if any boosts were applied
        if any(r['brand_boosted'] for r in results):
            results.sort(key=lambda x: x['similarity'], reverse=True)
            # Update ranks after re-sorting
            for i, result in enumerate(results, 1):
                result['rank'] = i
            logger.info(f"Applied brand boosting - results re-ranked")
        
        logger.info(f"Found {len(results)} products before filtering")
        return results, query_text
