"""
Storage loader for product embeddings and metadata.
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class EmbeddingStorageLoader:
    """Loads and partitions product embeddings for fast species-based search."""
    
    def __init__(self, embeddings_path: str = "backend/embeddings_pipeline/artifacts/catalog_embeds.jsonl"):
        """
        Initialize storage loader.
        
        Args:
            embeddings_path: Path to catalog embeddings JSONL file
        """
        self.embeddings_path = Path(embeddings_path)
        self.full_df = None
        self.dog_df = None
        self.cat_df = None
        self.dog_embeddings = None
        self.cat_embeddings = None
        
    def load_and_partition(self) -> Dict[str, any]:
        """
        Load embeddings and partition by species for faster search.
        
        Returns:
            Dict with loaded data and statistics
        """
        logger.info(f"Loading embeddings from: {self.embeddings_path}")
        
        if not self.embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {self.embeddings_path}")
        
        # Load JSONL file
        data = []
        with open(self.embeddings_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        
        self.full_df = pd.DataFrame(data)
        logger.info(f"Loaded {len(self.full_df):,} total products")
        
        # Partition by species
        self.dog_df = self.full_df[self.full_df['species_dog_flag'] == True].copy()
        self.cat_df = self.full_df[self.full_df['species_cat_flag'] == True].copy()
        
        # Convert embeddings to numpy arrays for faster search
        self.dog_embeddings = np.vstack(self.dog_df['embedding'].values).astype(np.float32)
        self.cat_embeddings = np.vstack(self.cat_df['embedding'].values).astype(np.float32)
        
        stats = {
            'total_products': len(self.full_df),
            'dog_products': len(self.dog_df),
            'cat_products': len(self.cat_df),
            'embedding_dim': len(self.full_df.iloc[0]['embedding']),
            'dog_matrix_shape': self.dog_embeddings.shape,
            'cat_matrix_shape': self.cat_embeddings.shape
        }
        
        logger.info(f"Partitioned embeddings:")
        logger.info(f"  🐕 Dog products: {stats['dog_products']:,}")
        logger.info(f"  🐱 Cat products: {stats['cat_products']:,}")
        logger.info(f"  📊 Embedding dimension: {stats['embedding_dim']}")
        
        return stats
    
    def get_species_data(self, species: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Get DataFrame and embedding matrix for a specific species.
        
        Args:
            species: "Dog" or "Cat"
            
        Returns:
            Tuple of (dataframe, embedding_matrix)
        """
        if species.lower() == "dog":
            return self.dog_df, self.dog_embeddings
        elif species.lower() == "cat":
            return self.cat_df, self.cat_embeddings
        else:
            raise ValueError(f"Unknown species: {species}. Use 'Dog' or 'Cat'")
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Get product details by SKU.
        
        Args:
            sku: Product part number
            
        Returns:
            Product dict or None if not found
        """
        matches = self.full_df[self.full_df['product_part_number'] == sku]
        if len(matches) > 0:
            return matches.iloc[0].to_dict()
        return None
