"""
Vector search using Qdrant Cloud via REST API (bypasses httpx timeout issues).

This implementation uses the requests library directly to avoid httpx connection
timeouts that occur with the qdrant-client Python library.
"""

import requests
import openai
import os
import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class QdrantVectorSearch:
    """Vector search engine using Qdrant Cloud via REST API."""
    
    def __init__(self, collection_name: str = "chewy_products_117k"):
        """
        Initialize Qdrant vector search with REST API.
        
        Args:
            collection_name: Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables are required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'api-key': self.qdrant_api_key,
            'Content-Type': 'application/json'
        })
        
        self.openai_client = self._initialize_openai_client()
        
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
                value = must.split(":", 1)[1].strip()
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
    
    def _embed_query(self, query_text: str) -> List[float]:
        """
        Embed query using OpenAI.
        
        Args:
            query_text: Query text to embed
            
        Returns:
            Query embedding vector
        """
        response = self.openai_client.embeddings.create(
            input=query_text,
            model="text-embedding-3-large",
            dimensions=3072
        )
        return response.data[0].embedding
    
    def _apply_brand_boost(self, search_text: str, brand_bias: List[str], base_similarity: float) -> float:
        """
        Apply brand boosting to similarity scores.
        
        Args:
            search_text: Product search text
            brand_bias: List of preferred brands
            base_similarity: Original similarity score
            
        Returns:
            Boosted similarity score
        """
        if not brand_bias:
            return base_similarity
        
        search_text_lower = search_text.lower()
        
        for brand in brand_bias:
            brand_lower = brand.lower()
            if brand_lower in search_text_lower:
                boosted = base_similarity * 1.15
                logger.debug(f"Brand boost applied for '{brand}': {base_similarity:.4f} -> {boosted:.4f}")
                return min(boosted, 1.0)
        
        return base_similarity
    
    def search_slot(self, slot: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        """
        Search for products matching a single slot using Qdrant REST API.
        
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
        
        # Embed the query
        query_vector = self._embed_query(query_text)
        
        # Build filter for species
        filter_conditions = []
        
        if species:
            if species.lower() == "dog":
                filter_conditions.append({
                    "key": "species_dog_flag",
                    "match": {"value": True}
                })
            elif species.lower() == "cat":
                filter_conditions.append({
                    "key": "species_cat_flag",
                    "match": {"value": True}
                })
        
        # Build search request
        search_request = {
            "vector": query_vector,
            "limit": min(top_k * 5, 500),  # Request more for deduplication
            "with_payload": True,
            "score_threshold": 0.0
        }
        
        if filter_conditions:
            search_request["filter"] = {"must": filter_conditions}
        
        # Execute search via REST API
        try:
            response = self.session.post(
                f"{self.qdrant_url}/collections/{self.collection_name}/points/search",
                json=search_request,
                timeout=10  # Should be sub-second
            )
            response.raise_for_status()
            
            search_results = response.json()["result"]
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            logger.error(f"Search request was: {search_request}")
            return [], query_text
        
        if not search_results:
            logger.warning(f"No products found for species: {species}")
            return [], query_text
        
        # Process results and remove duplicate parent SKUs
        seen_parent_skus = set()
        results = []
        brand_bias = slot.get("brand_bias", [])
        
        for hit in search_results:
            payload = hit["payload"]
            parent_sku = payload.get('parent_product_part_number', '')
            
            # Skip if we've already seen this parent SKU
            if parent_sku and parent_sku != "" and parent_sku in seen_parent_skus:
                continue
            
            # Track this parent SKU
            if parent_sku and parent_sku != "":
                seen_parent_skus.add(parent_sku)
            
            # Get product name
            product_name = payload.get('product_name', '')
            
            # Fallback to extracting from search_text if product_name is missing
            if not product_name:
                search_text = payload.get('search_text', '')
                if ' Brand:' in search_text:
                    product_name = search_text.split(' Brand:')[0].strip()
                else:
                    product_name = search_text.split('.')[0].strip()
            
            search_text = payload.get('search_text', '')
            
            # Apply brand boosting
            base_similarity = float(hit["score"])
            boosted_similarity = self._apply_brand_boost(search_text, brand_bias, base_similarity)
            
            result = {
                'rank': len(results) + 1,
                'sku': payload.get('product_part_number', ''),
                'parentSKU': parent_sku,
                'name': product_name,
                'product_link': payload.get('product_link', ''),
                'product_price_current': payload.get('product_price_current', None),
                'autoship_eligible': bool(payload.get('product_autoship_save_eligible_flag', False)),
                'similarity': boosted_similarity,
                'base_similarity': base_similarity,
                'brand_boosted': boosted_similarity != base_similarity,
                'search_text': search_text,
                'species_flags': {
                    'dog': payload.get('species_dog_flag', False),
                    'cat': payload.get('species_cat_flag', False)
                }
            }
            results.append(result)
            
            # Stop once we have enough unique parent SKUs
            if len(results) >= top_k:
                break
        
        logger.info(f"Adaptive search: requested {top_k} unique products, found {len(results)} (scanned {len(search_results)} candidates)")
        
        return results, query_text

