"""
Vector search and retrieval module.

Provides semantic search capabilities using cosine similarity.
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Tuple, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import openai
import os

logger = logging.getLogger(__name__)


class VectorSearchEngine:
    """Provides semantic search over product embeddings."""
    
    def __init__(self, 
                 model: str = "text-embedding-3-large",
                 embeddings_df: Optional[pd.DataFrame] = None):
        """
        Initialize vector search engine.
        
        Args:
            model: OpenAI embedding model for query embedding
            embeddings_df: Pre-loaded DataFrame with embeddings
        """
        self.model = model
        self.embeddings_df = embeddings_df
        self.embeddings_matrix = None
        self.product_ids = None
        
        # Initialize OpenAI client for query embedding
        self.client = self._initialize_client()
        
        if embeddings_df is not None:
            self._prepare_search_index()
    
    def _initialize_client(self) -> openai.OpenAI:
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return openai.OpenAI(api_key=api_key)
    
    def load_embeddings(self, embeddings_df: pd.DataFrame) -> None:
        """
        Load embeddings DataFrame and prepare search index.
        
        Args:
            embeddings_df: DataFrame with embeddings
        """
        required_columns = ['product_part_number', 'embedding', 'species_dog_flag', 'species_cat_flag']
        missing_columns = [col for col in required_columns if col not in embeddings_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        self.embeddings_df = embeddings_df
        self._prepare_search_index()
        
        logger.info(f"Loaded {len(self.embeddings_df):,} product embeddings")
    
    def _prepare_search_index(self) -> None:
        """Prepare the search index from embeddings DataFrame."""
        if self.embeddings_df is None:
            raise ValueError("No embeddings loaded")
        
        # Extract embeddings and convert to numpy matrix
        embeddings_list = self.embeddings_df['embedding'].tolist()
        self.embeddings_matrix = np.array(embeddings_list)
        
        # Store product IDs for lookup
        self.product_ids = self.embeddings_df['product_part_number'].tolist()
        
        logger.info(f"Prepared search index: {self.embeddings_matrix.shape}")
    
    def embed_query(self, query_text: str) -> List[float]:
        """
        Generate embedding for a query string.
        
        Args:
            query_text: Query string to embed
            
        Returns:
            Query embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[query_text],
                encoding_format="float"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    def search(self, 
               query_text: str,
               top_k: int = 10,
               species_filter: Optional[str] = None,
               min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform semantic search over product embeddings.
        
        Args:
            query_text: Natural language search query
            top_k: Number of top results to return
            species_filter: Filter by species ('dog', 'cat', or None for both)
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of search results with similarity scores
        """
        if self.embeddings_matrix is None:
            raise ValueError("No search index prepared. Call load_embeddings() first.")
        
        logger.info(f"Searching for: '{query_text}' (top_k={top_k}, species={species_filter})")
        
        # Embed the query
        query_embedding = self.embed_query(query_text)
        query_vector = np.array([query_embedding])
        
        # Apply species filter if specified
        search_mask = self._get_species_mask(species_filter)
        
        if search_mask is not None:
            filtered_embeddings = self.embeddings_matrix[search_mask]
            filtered_indices = np.where(search_mask)[0]
        else:
            filtered_embeddings = self.embeddings_matrix
            filtered_indices = np.arange(len(self.embeddings_matrix))
        
        # Compute cosine similarities
        similarities = cosine_similarity(query_vector, filtered_embeddings)[0]
        
        # Apply minimum similarity filter
        valid_mask = similarities >= min_similarity
        similarities = similarities[valid_mask]
        filtered_indices = filtered_indices[valid_mask]
        
        # Get top-k results
        if len(similarities) == 0:
            logger.warning("No results found above similarity threshold")
            return []
        
        # Sort by similarity (descending)
        sorted_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for i, sorted_idx in enumerate(sorted_indices):
            original_idx = filtered_indices[sorted_idx]
            similarity = similarities[sorted_idx]
            
            result = {
                'rank': i + 1,
                'product_part_number': self.product_ids[original_idx],
                'similarity': float(similarity),
                'search_text_preview': self._get_text_preview(original_idx),
                'species_flags': {
                    'dog': bool(self.embeddings_df.iloc[original_idx]['species_dog_flag']),
                    'cat': bool(self.embeddings_df.iloc[original_idx]['species_cat_flag'])
                }
            }
            results.append(result)
        
        logger.info(f"Found {len(results)} results (similarity range: {results[0]['similarity']:.3f} - {results[-1]['similarity']:.3f})")
        
        return results
    
    def _get_species_mask(self, species_filter: Optional[str]) -> Optional[np.ndarray]:
        """Get boolean mask for species filtering."""
        if species_filter is None:
            return None
        
        if species_filter.lower() == 'dog':
            return self.embeddings_df['species_dog_flag'].values
        elif species_filter.lower() == 'cat':
            return self.embeddings_df['species_cat_flag'].values
        else:
            raise ValueError(f"Invalid species filter: {species_filter}. Use 'dog', 'cat', or None.")
    
    def _get_text_preview(self, index: int, max_chars: int = 120) -> str:
        """Get preview of search text for a result."""
        if 'search_text' in self.embeddings_df.columns:
            text = self.embeddings_df.iloc[index]['search_text']
            if len(text) <= max_chars:
                return text
            else:
                return text[:max_chars] + '...'
        return ""
    
    def search_similar_products(self, 
                              product_part_number: str,
                              top_k: int = 10,
                              exclude_self: bool = True) -> List[Dict[str, Any]]:
        """
        Find products similar to a given product.
        
        Args:
            product_part_number: Product to find similar products for
            top_k: Number of similar products to return
            exclude_self: Whether to exclude the input product from results
            
        Returns:
            List of similar products with similarity scores
        """
        # Find the product in our index
        if product_part_number not in self.product_ids:
            raise ValueError(f"Product {product_part_number} not found in index")
        
        product_idx = self.product_ids.index(product_part_number)
        product_embedding = self.embeddings_matrix[product_idx:product_idx+1]
        
        # Compute similarities with all products
        similarities = cosine_similarity(product_embedding, self.embeddings_matrix)[0]
        
        # Sort by similarity (descending)
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Exclude self if requested
        if exclude_self:
            sorted_indices = sorted_indices[sorted_indices != product_idx]
        
        # Get top-k results
        results = []
        for i, idx in enumerate(sorted_indices[:top_k]):
            similarity = similarities[idx]
            
            result = {
                'rank': i + 1,
                'product_part_number': self.product_ids[idx],
                'similarity': float(similarity),
                'search_text_preview': self._get_text_preview(idx),
                'species_flags': {
                    'dog': bool(self.embeddings_df.iloc[idx]['species_dog_flag']),
                    'cat': bool(self.embeddings_df.iloc[idx]['species_cat_flag'])
                }
            }
            results.append(result)
        
        logger.info(f"Found {len(results)} similar products to {product_part_number}")
        
        return results
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index."""
        if self.embeddings_df is None:
            return {}
        
        return {
            'total_products': len(self.embeddings_df),
            'dog_products': self.embeddings_df['species_dog_flag'].sum(),
            'cat_products': self.embeddings_df['species_cat_flag'].sum(),
            'both_species': (self.embeddings_df['species_dog_flag'] & self.embeddings_df['species_cat_flag']).sum(),
            'embedding_dimension': self.embeddings_matrix.shape[1] if self.embeddings_matrix is not None else 0,
            'index_size_mb': self.embeddings_matrix.nbytes / (1024 * 1024) if self.embeddings_matrix is not None else 0
        }
