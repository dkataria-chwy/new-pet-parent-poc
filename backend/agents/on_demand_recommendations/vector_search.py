"""
On-demand specific vector search with full product name handling.
Separate from the main vector search to avoid impacting Stage 1/2 pipelines.
"""

import logging
import numpy as np
import pandas as pd
import openai
import os
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class OnDemandVectorSearch:
    """
    Vector search specifically optimized for on-demand recommendations.
    Key differences from main vector search:
    - Preserves full product names (no truncation)
    - Optimized for single-query searches
    - Enhanced deduplication by parentSKU
    """
    
    def __init__(self, storage_loader):
        """Initialize with embedding storage loader."""
        self.storage_loader = storage_loader
        self.client = self._initialize_openai_client()
        self._load_embeddings()
    
    def _load_embeddings(self):
        """Load embeddings data."""
        try:
            # Use the correct method from EmbeddingStorageLoader
            stats = self.storage_loader.load_and_partition()
            logger.info(f"✅ Loaded {stats['total_products']:,} product embeddings for on-demand search")
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings: {e}")
            raise
    
    def search_products(self, 
                       embedding_query: str, 
                       species: str, 
                       top_k: int = 20,
                       brand_preferences: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for products using embedding query.
        
        Args:
            embedding_query: The search query string
            species: Pet species for filtering ("dog" or "cat")
            top_k: Number of results to return
            brand_preferences: List of preferred brands (not used in on-demand to avoid bias)
            
        Returns:
            List of product dictionaries with full names and metadata
        """
        try:
            # Step 1: Build enhanced query (same logic as original vector search)
            enhanced_query = self._build_enhanced_query(embedding_query, species)
            
            # Step 2: Get species-specific data (pre-filtered)
            species_filtered_df, filtered_embeddings = self.storage_loader.get_species_data(species.capitalize())
            
            if species_filtered_df.empty:
                logger.warning(f"No products found for species: {species}")
                return []
            
            # Step 3: Generate query embedding using OpenAI
            query_vector = self._embed_query(enhanced_query)
            if query_vector is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Step 4: Cosine similarity search
            query_matrix = query_vector.reshape(1, -1)
            similarities = cosine_similarity(query_matrix, filtered_embeddings)[0]
            
            # Step 4: Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get extra for deduplication
            
            # Step 5: Build results with full product names
            results = []
            for rank, idx in enumerate(top_indices, 1):
                product_row = species_filtered_df.iloc[idx]
                
                # Use product_name column directly (added to embeddings file)
                product_name = product_row.get('product_name', None)
                
                # Fallback to extracting from search_text if product_name is missing
                if not product_name or pd.isna(product_name):
                    product_name = self._extract_full_product_name(product_row['search_text'])
                
                result = {
                    'rank': rank,
                    'sku': product_row['product_part_number'],
                    'parentSKU': product_row.get('parent_product_part_number', ''),
                    'name': product_name,
                    'similarity': float(similarities[idx]),
                    'product_link': product_row.get('product_link', '') or '',  # Ensure it's never None
                    'product_price_current': product_row.get('product_price_current', None),
                    'autoship_eligible': bool(product_row.get('product_autoship_save_eligible_flag', False)),
                    'base_similarity': float(similarities[idx]),  # Same as similarity in JSONL (no brand boost)
                    'brand_boosted': False,  # JSONL doesn't do brand boosting
                    'search_text': product_row['search_text'],
                    'species_flags': {
                        'dog': product_row['species_dog_flag'],
                        'cat': product_row['species_cat_flag']
                    }
                }
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} products for enhanced query: '{enhanced_query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def _build_enhanced_query(self, base_query: str, species: str) -> str:
        """
        Build enhanced query by adding missing essential terms.
        Same logic as original vector search to ensure consistency.
        
        Args:
            base_query: Original embedding query
            species: Pet species
            
        Returns:
            Enhanced query string
        """
        base_query_lower = base_query.lower()
        terms_to_add = []
        
        # Essential terms that should be present
        essential_terms = [species.lower()]
        
        # Add missing essential terms
        for term in essential_terms:
            if term not in base_query_lower:
                terms_to_add.append(term)
        
        # Add missing terms to query
        if terms_to_add:
            enhanced_query = base_query + ";" + ";".join(terms_to_add)
            logger.info(f"Enhanced query with missing terms: {terms_to_add}")
            return enhanced_query
        
        return base_query
    
    def _initialize_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client for query embedding."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return openai.OpenAI(api_key=api_key)
    
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
                input=query_text,
                dimensions=3072  # Match Qdrant embedding dimensions
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    def _filter_by_species(self, df: pd.DataFrame, species: str) -> pd.DataFrame:
        """Filter products by species."""
        species_col = f'species_{species.lower()}_flag'
        
        if species_col not in df.columns:
            logger.warning(f"Species column {species_col} not found")
            return df
        
        filtered_df = df[df[species_col] == 1].copy()
        logger.info(f"🔍 Species filtering ({species}): {len(df)} → {len(filtered_df)} products")
        
        return filtered_df
    
    def _extract_full_product_name(self, search_text: str) -> str:
        """
        Extract full product name without truncation.
        Optimized for on-demand recommendations to preserve complete names.
        """
        if not search_text:
            return "Unknown Product"
        
        # Method 1: Split on " Brand:" if present (most reliable)
        if ' Brand:' in search_text:
            product_name = search_text.split(' Brand:')[0].strip()
            return product_name
        
        # Method 2: Look for common patterns to extract name
        # Remove trailing periods and common suffixes
        product_name = search_text.strip()
        
        # Remove trailing period if present
        if product_name.endswith('.'):
            product_name = product_name[:-1].strip()
        
        # If the name is still very long, try to find a reasonable cutoff
        # but preserve the full product name as much as possible
        if len(product_name) > 200:
            # Look for sentence boundaries but keep the full product description
            sentences = product_name.split('. ')
            if len(sentences) > 1:
                # Take first sentence if it's substantial
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 20:
                    product_name = first_sentence
        
        return product_name
    
    def format_results(self, 
                      products: List[Dict[str, Any]], 
                      rationale: str, 
                      embedding_query: str) -> Dict[str, Any]:
        """Format search results for API response."""
        return {
            "timestamp": pd.Timestamp.now().isoformat(),
            "query_used": embedding_query,
            "rationale": rationale,
            "total_products": len(products),
            "products": products
        }
