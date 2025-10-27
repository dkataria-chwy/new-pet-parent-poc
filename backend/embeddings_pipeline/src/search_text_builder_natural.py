"""
Natural Language Search Text Builder

Same as search_text_builder.py but generates natural, flowing text
instead of structured "Brand: X. Species: Y." format.

Use this instead of SearchTextBuilder when you want natural language embeddings.
"""

import pandas as pd
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class NaturalLanguageSearchTextBuilder:
    """Builds natural language search text for product embeddings."""
    
    def __init__(self, max_length: int = 3000):
        """
        Initialize natural language search text builder.
        
        Args:
            max_length: Maximum length for search text (truncate if longer)
        """
        self.max_length = max_length
    
    def build_search_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build natural language search_text for each product.
        
        Format: Flowing natural language without structured labels
        Example:
        "Diamond Naturals Large Breed Puppy Formula for dog, puppy, large breed, dry food.
        Formulated for large breed puppies with DHA for brain development..."
        
        Args:
            df: DataFrame with product data and species flags
            
        Returns:
            DataFrame with search_text column added
        """
        logger.info(f"Building natural language search text for {len(df):,} products...")
        
        df = df.copy()
        search_texts = []
        
        for idx, row in df.iterrows():
            search_text = self._build_single_search_text(row)
            search_texts.append(search_text)
            
            # Log progress every 10k rows
            if (idx + 1) % 10000 == 0:
                logger.info(f"Processed {idx + 1:,} search texts...")
        
        df['search_text'] = search_texts
        
        logger.info("Natural language search text construction complete")
        self._log_sample_texts(df)
        
        return df
    
    def _build_single_search_text(self, row: pd.Series) -> str:
        """Build natural language search text for a single product."""
        parts = []
        
        # Start with product name with integrated attributes
        intro = self._build_intro(row)
        if intro:
            parts.append(intro)
        
        # Add description (main semantic content)
        desc = self._extract_description(row)
        if desc:
            parts.append(desc)
        
        # Add key attributes naturally
        attributes = self._build_attributes(row)
        if attributes:
            parts.append(attributes)
        
        # Add category context
        category_context = self._build_category_context(row)
        if category_context:
            parts.append(category_context)
        
        # Join all parts
        search_text = ' '.join(parts)
        
        # Normalize and truncate
        search_text = self._normalize_text(search_text)
        if len(search_text) > self.max_length:
            search_text = search_text[:self.max_length].rsplit(' ', 1)[0] + '...'
        
        return search_text
    
    def _build_intro(self, row: pd.Series) -> str:
        """Build natural intro: 'Brand Name Product for species, lifestage, size'"""
        parts = []
        
        # Brand + Product Name
        if self._has_value(row, 'PRODUCT_PURCHASE_BRAND'):
            parts.append(row['PRODUCT_PURCHASE_BRAND'])
        
        if self._has_value(row, 'PRODUCT_NAME'):
            name = str(row['PRODUCT_NAME']).strip()
            # Don't repeat brand if it's already in the name
            if parts and parts[0].lower() not in name.lower():
                parts.append(name)
            elif not parts:
                parts.append(name)
        
        intro = ' '.join(parts) if parts else ""
        
        # Add species, lifestage, breed-size naturally
        qualifiers = []
        
        # Species
        species = self._get_species(row)
        if species:
            qualifiers.append(species)
        
        # Lifestage
        if self._has_value(row, 'PRODUCT_LIFESTAGE'):
            lifestage = str(row['PRODUCT_LIFESTAGE']).strip().lower()
            qualifiers.append(lifestage)
        
        # Breed size
        if self._has_value(row, 'BREED_SIZE'):
            breed_size = str(row['BREED_SIZE']).strip().lower()
            if species == 'dog':
                qualifiers.append(f"{breed_size} breed")
            else:
                qualifiers.append(breed_size)
        
        # Food form
        if self._has_value(row, 'PRODUCT_ATTR_FOOD_FORM'):
            food_form = str(row['PRODUCT_ATTR_FOOD_FORM']).strip().lower()
            qualifiers.append(food_form)
        
        # Special diet
        if self._has_value(row, 'PRODUCT_ATTR_SPECIAL_DIET'):
            diet = str(row['PRODUCT_ATTR_SPECIAL_DIET']).strip().lower()
            qualifiers.append(diet)
        
        # Combine intro with qualifiers
        if intro and qualifiers:
            return f"{intro} for {', '.join(qualifiers)}."
        elif intro:
            return f"{intro}."
        return ""
    
    def _extract_description(self, row: pd.Series) -> str:
        """Extract and clean product description."""
        if self._has_value(row, 'PRODUCT_DESCRIPTION_LONG'):
            desc = str(row['PRODUCT_DESCRIPTION_LONG']).strip()
            # Remove promotional junk
            desc = re.sub(r'\*\*.*?\*\*', '', desc)  # Remove **bold** markers
            desc = re.sub(r'SHOP NOW|BUY NOW|LIMITED TIME', '', desc, flags=re.IGNORECASE)
            desc = self._normalize_text(desc)
            return desc
        return ""
    
    def _build_attributes(self, row: pd.Series) -> str:
        """Build natural attributes: 'Available in X sizes. Requires prescription. Consumable product.'"""
        attrs = []
        
        # Parent product info (indicates multiple sizes/variants)
        if self._has_value(row, 'PARENT_PRODUCT_NAME'):
            attrs.append("Available in multiple sizes")
        
        # Prescription required
        if row.get('PRODUCT_RX_REQUIRED_FLAG') in [True, 'TRUE', 'True', 'true', '1', 'yes', 't']:
            attrs.append("Prescription required")
        else:
            attrs.append("No prescription required")
        
        # Consumable
        if row.get('PRODUCT_IS_CONSUMABLE_FLAG') in [True, 'TRUE', 'True', 'true', '1', 'yes', 't']:
            attrs.append("Consumable product")
        
        # Food flag
        if row.get('PRODUCT_IS_FOOD_FLAG') in [True, 'TRUE', 'True', 'true', '1', 'yes', 't']:
            attrs.append("Food product")
        
        if attrs:
            return '. '.join(attrs) + '.'
        return ""
    
    def _build_category_context(self, row: pd.Series) -> str:
        """Build category context naturally: 'Health & wellness supplement for dogs.'"""
        parts = []
        
        # Add category levels if available (e.g., "Pet Supplies > Dog > Food")
        category_levels = []
        for field in ['PRODUCT_CATEGORY_LEVEL1', 'PRODUCT_CATEGORY_LEVEL2', 'PRODUCT_CATEGORY_LEVEL3']:
            if self._has_value(row, field):
                val = str(row[field]).strip().lower()
                if val:
                    category_levels.append(val)
        
        if category_levels:
            parts.append(' > '.join(category_levels))
        
        # Add category list if available
        if self._has_value(row, 'PRODUCT_CATEGORY_LIST'):
            cat_list = str(row['PRODUCT_CATEGORY_LIST']).strip()
            parts.append(cat_list)
        
        # Add merch classifications
        merch = []
        for field in ['PRODUCT_MERCH_CLASSIFICATION1', 'PRODUCT_MERCH_CLASSIFICATION2', 'PRODUCT_MERCH_CLASSIFICATION3']:
            if self._has_value(row, field):
                val = str(row[field]).strip().lower()
                if val not in merch:  # Avoid duplicates
                    merch.append(val)
        
        if merch:
            species = self._get_species(row)
            if species:
                parts.append(f"{' '.join(merch)} for {species}s")
            else:
                parts.append(' '.join(merch))
        
        if parts:
            return '. '.join(parts) + '.'
        return ""
    
    def _get_species(self, row: pd.Series) -> str:
        """Get species as natural text: 'dog', 'cat', or 'dog and cat'"""
        species = []
        if row.get('SPECIES_DOG_FLAG', False):
            species.append('dog')
        if row.get('SPECIES_CAT_FLAG', False):
            species.append('cat')
        
        if len(species) == 2:
            return 'dog and cat'
        elif len(species) == 1:
            return species[0]
        return ""
    
    def _has_value(self, row: pd.Series, field: str) -> bool:
        """Check if field exists and has a non-empty value."""
        return (field in row and 
                pd.notna(row[field]) and 
                str(row[field]).strip() != '' and
                str(row[field]).strip().lower() not in ['null', 'none', 'n/a'])
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: UTF-8, collapse whitespace."""
        # Ensure UTF-8 encoding
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Collapse multiple whitespace into single spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _log_sample_texts(self, df: pd.DataFrame, sample_size: int = 5) -> None:
        """Log sample search texts for QA."""
        logger.info("Sample natural language search texts:")
        logger.info("=" * 80)
        
        sample_df = df.sample(min(sample_size, len(df)))
        
        for idx, row in sample_df.iterrows():
            logger.info(f"Product: {row.get('PRODUCT_PART_NUMBER', 'Unknown')}")
            logger.info(f"Text: {row['search_text'][:300]}...")
            logger.info("-" * 40)

