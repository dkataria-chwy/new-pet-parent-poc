"""
Data loading and species normalization module.

Handles CSV loading and species flag derivation for Dog/Cat products.
"""

import pandas as pd
import logging
from typing import Tuple, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ProductDataLoader:
    """Handles loading and preprocessing of product catalog data."""
    
    def __init__(self):
        self.df = None
        self.total_rows = 0
        self.kept_rows = 0
    
    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load the product catalog CSV file.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Loaded DataFrame
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Loading CSV from: {csv_path}")
        
        # Load CSV with proper encoding and error handling
        try:
            self.df = pd.read_csv(
                csv_path,
                dtype=str,  # Load all as strings initially
                na_values=['', 'NULL', 'null', 'None'],
                keep_default_na=False
            )
            self.total_rows = len(self.df)
            logger.info(f"Loaded {self.total_rows:,} rows with {len(self.df.columns)} columns")
            
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise
    
    def derive_species_flags(self) -> pd.DataFrame:
        """
        Derive SPECIES_DOG_FLAG and SPECIES_CAT_FLAG based on category and attributes.
        
        Species logic:
        - SPECIES_DOG_FLAG = (PRODUCT_CATEGORY_LEVEL1='DOG') OR ('Dog' in PRODUCT_ATTR_PET_TYPE)
        - SPECIES_CAT_FLAG = (PRODUCT_CATEGORY_LEVEL1='CAT') OR ('Cat' in PRODUCT_ATTR_PET_TYPE)
        
        Returns:
            DataFrame with species flags added
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        logger.info("Deriving species flags...")
        
        # Initialize flags
        self.df['SPECIES_DOG_FLAG'] = False
        self.df['SPECIES_CAT_FLAG'] = False
        
        # Helper function to check pet type attributes
        def check_pet_type(pet_type_str: str, target_species: str) -> bool:
            """Check if target species is in comma-separated pet type string."""
            if pd.isna(pet_type_str) or pet_type_str == '':
                return False
            
            # Split by comma, strip whitespace, check case-insensitive
            pet_types = [pt.strip().lower() for pt in str(pet_type_str).split(',')]
            return target_species.lower() in pet_types
        
        # Derive DOG flag
        category_dog = self.df['PRODUCT_CATEGORY_LEVEL1'].str.upper() == 'DOG'
        attr_dog = self.df['PRODUCT_ATTR_PET_TYPE'].apply(
            lambda x: check_pet_type(x, 'Dog')
        )
        self.df['SPECIES_DOG_FLAG'] = category_dog | attr_dog
        
        # Derive CAT flag  
        category_cat = self.df['PRODUCT_CATEGORY_LEVEL1'].str.upper() == 'CAT'
        attr_cat = self.df['PRODUCT_ATTR_PET_TYPE'].apply(
            lambda x: check_pet_type(x, 'Cat')
        )
        self.df['SPECIES_CAT_FLAG'] = category_cat | attr_cat
        
        # Filter to dog/cat products only
        dog_cat_mask = self.df['SPECIES_DOG_FLAG'] | self.df['SPECIES_CAT_FLAG']
        self.df = self.df[dog_cat_mask].copy()
        self.kept_rows = len(self.df)
        
        logger.info(f"Species filtering: {self.total_rows:,} → {self.kept_rows:,} rows")
        logger.info(f"Dog products: {self.df['SPECIES_DOG_FLAG'].sum():,}")
        logger.info(f"Cat products: {self.df['SPECIES_CAT_FLAG'].sum():,}")
        logger.info(f"Both dog+cat: {(self.df['SPECIES_DOG_FLAG'] & self.df['SPECIES_CAT_FLAG']).sum():,}")
        
        return self.df
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'total_rows': self.total_rows,
            'kept_rows': self.kept_rows,
            'dog_products': self.df['SPECIES_DOG_FLAG'].sum() if self.df is not None else 0,
            'cat_products': self.df['SPECIES_CAT_FLAG'].sum() if self.df is not None else 0,
            'columns': list(self.df.columns) if self.df is not None else []
        }
