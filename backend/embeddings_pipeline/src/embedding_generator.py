"""
Embedding generation module.

Handles OpenAI API calls to generate embeddings for product search texts.
"""

import openai
import pandas as pd
import numpy as np
import logging
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
from tqdm import tqdm

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using OpenAI's text-embedding-3-large model."""
    
    def __init__(self, 
                 model: str = "text-embedding-3-large",
                 batch_size: int = 100,
                 max_retries: int = 3,
                 delay_between_batches: float = 1.0):
        """
        Initialize embedding generator.
        
        Args:
            model: OpenAI embedding model to use
            batch_size: Number of texts to embed per API call
            max_retries: Maximum number of retries for failed requests
            delay_between_batches: Delay in seconds between batch requests
        """
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.delay_between_batches = delay_between_batches
        
        # Initialize OpenAI client
        self.client = self._initialize_client()
        
        # Track stats
        self.total_tokens = 0
        self.total_requests = 0
        self.failed_requests = 0
    
    def _initialize_client(self) -> openai.OpenAI:
        """Initialize OpenAI client with API key."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
        
        logger.info(f"Initializing OpenAI client with model: {self.model}")
        return openai.OpenAI(api_key=api_key)
    
    def generate_embeddings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate embeddings for all search texts in the DataFrame.
        
        Args:
            df: DataFrame with 'search_text' column
            
        Returns:
            DataFrame with 'embedding' and 'embedded_at' columns added
        """
        if 'search_text' not in df.columns:
            raise ValueError("DataFrame must have 'search_text' column")
        
        logger.info(f"Generating embeddings for {len(df):,} products...")
        
        # Extract search texts
        search_texts = df['search_text'].tolist()
        
        # Generate embeddings in batches
        all_embeddings = self._embed_texts_batched(search_texts)
        
        # Add embeddings to DataFrame
        df = df.copy()
        df['embedding'] = all_embeddings
        df['embedded_at'] = datetime.utcnow().isoformat() + 'Z'
        
        logger.info(f"Embedding generation complete!")
        logger.info(f"Total API requests: {self.total_requests}")
        logger.info(f"Failed requests: {self.failed_requests}")
        logger.info(f"Total tokens processed: {self.total_tokens:,}")
        
        return df
    
    def _embed_texts_batched(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts in batches.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        logger.info(f"Processing {total_batches} batches of size {self.batch_size}")
        
        with tqdm(total=len(texts), desc="Generating embeddings") as pbar:
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = self._embed_single_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                pbar.update(len(batch_texts))
                
                # Rate limiting delay
                if i + self.batch_size < len(texts):  # Don't delay after last batch
                    time.sleep(self.delay_between_batches)
        
        return all_embeddings
    
    def _embed_single_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a single batch of texts.
        
        Args:
            texts: Batch of texts to embed
            
        Returns:
            List of embedding vectors for the batch
        """
        for attempt in range(self.max_retries):
            try:
                self.total_requests += 1
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float"
                )
                
                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                
                # Track token usage
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens += response.usage.total_tokens
                
                return embeddings
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries - 1:
                    self.failed_requests += 1
                    logger.error(f"Failed to embed batch after {self.max_retries} attempts: {e}")
                    # Return zero vectors as fallback
                    return [[0.0] * 3072 for _ in texts]
                
                # Exponential backoff
                time.sleep(2 ** attempt)
    
    def validate_embeddings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate generated embeddings.
        
        Args:
            df: DataFrame with embeddings
            
        Returns:
            Validation results
        """
        if 'embedding' not in df.columns:
            raise ValueError("DataFrame must have 'embedding' column")
        
        logger.info("Validating embeddings...")
        
        embeddings = df['embedding'].tolist()
        
        # Check dimensions
        dimensions = [len(emb) for emb in embeddings if emb]
        expected_dim = 3072
        
        validation_results = {
            'total_embeddings': len(embeddings),
            'non_null_embeddings': len([e for e in embeddings if e]),
            'expected_dimension': expected_dim,
            'actual_dimensions': list(set(dimensions)),
            'correct_dimension_count': sum(1 for d in dimensions if d == expected_dim),
            'zero_embeddings': sum(1 for emb in embeddings if emb and all(v == 0.0 for v in emb)),
            'embedding_stats': self._compute_embedding_stats(embeddings)
        }
        
        # Log validation results
        logger.info(f"Validation results:")
        logger.info(f"  Total embeddings: {validation_results['total_embeddings']:,}")
        logger.info(f"  Non-null embeddings: {validation_results['non_null_embeddings']:,}")
        logger.info(f"  Correct dimension ({expected_dim}): {validation_results['correct_dimension_count']:,}")
        logger.info(f"  Zero embeddings: {validation_results['zero_embeddings']:,}")
        
        if validation_results['actual_dimensions'] != [expected_dim]:
            logger.warning(f"Unexpected dimensions found: {validation_results['actual_dimensions']}")
        
        return validation_results
    
    def _compute_embedding_stats(self, embeddings: List[List[float]]) -> Dict[str, float]:
        """Compute basic statistics for embeddings."""
        if not embeddings or not embeddings[0]:
            return {}
        
        # Convert to numpy array for easier computation
        valid_embeddings = [emb for emb in embeddings if emb and len(emb) == 3072]
        if not valid_embeddings:
            return {}
        
        emb_array = np.array(valid_embeddings)
        
        return {
            'mean_norm': float(np.mean(np.linalg.norm(emb_array, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(emb_array, axis=1))),
            'mean_value': float(np.mean(emb_array)),
            'std_value': float(np.std(emb_array))
        }
    
    def estimate_cost(self, num_texts: int, avg_tokens_per_text: int = 100) -> Dict[str, float]:
        """
        Estimate the cost of embedding generation.
        
        Args:
            num_texts: Number of texts to embed
            avg_tokens_per_text: Average tokens per text
            
        Returns:
            Cost estimation
        """
        # text-embedding-3-large pricing (as of 2024)
        cost_per_1k_tokens = 0.00013  # $0.00013 per 1K tokens
        
        total_tokens = num_texts * avg_tokens_per_text
        estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens
        
        return {
            'num_texts': num_texts,
            'estimated_tokens': total_tokens,
            'cost_per_1k_tokens': cost_per_1k_tokens,
            'estimated_cost_usd': estimated_cost
        }
