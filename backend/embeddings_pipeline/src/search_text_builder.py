"""
Search text construction module.

Builds deterministic search_text for each product using specific field order.
"""

import pandas as pd
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


class SearchTextBuilder:
    """Builds structured search text for product embeddings."""
    
    def __init__(self, max_length: int = 2000):
        """
        Initialize search text builder.
        
        Args:
            max_length: Maximum length for search text (truncate if longer)
        """
        self.max_length = max_length
    
    def build_search_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build search_text for each product following the specified format.
        
        Format order:
        1. Name: {PRODUCT_NAME}
        2. Brand: {PRODUCT_PURCHASE_BRAND}
        3. Species: dog/cat/dog,cat
        4. Category: {LEVEL1} > {LEVEL2} > {LEVEL3} ({CATEGORY_LIST})
        5. Merch: {CLASS1} | {CLASS2} | {CLASS3}
        6. Lifestage: {LIFESTAGE}. Breed-size: {BREED_SIZE}
        7. Food-form: {FOOD_FORM}. Special-diet: {SPECIAL_DIET}
        8. Parent: {PARENT_NAME}
        9. Flags: rx_required:{RX} consumable:{CONSUMABLE} food:{FOOD}
        10. Long description: {DESCRIPTION}
        
        Args:
            df: DataFrame with product data and species flags
            
        Returns:
            DataFrame with search_text column added
        """
        logger.info(f"Building search text for {len(df):,} products...")
        
        df = df.copy()
        search_texts = []
        
        for idx, row in df.iterrows():
            search_text = self._build_single_search_text(row)
            search_texts.append(search_text)
            
            # Log progress every 10k rows
            if (idx + 1) % 10000 == 0:
                logger.info(f"Processed {idx + 1:,} search texts...")
        
        df['search_text'] = search_texts
        
        logger.info("Search text construction complete")
        self._log_sample_texts(df)
        
        return df
    
    def _build_single_search_text(self, row: pd.Series) -> str:
        """Build search text for a single product row."""
        parts = []
        
        # 1. Product Name
        if self._has_value(row, 'PRODUCT_NAME'):
            parts.append(str(row['PRODUCT_NAME']).strip())
        
        # 2. Brand
        if self._has_value(row, 'PRODUCT_PURCHASE_BRAND'):
            parts.append(f"Brand: {row['PRODUCT_PURCHASE_BRAND']}.")
        
        # 3. Species (from flags)
        species_part = self._build_species_text(row)
        if species_part:
            parts.append(species_part)
        
        # 4. Category chain
        category_part = self._build_category_text(row)
        if category_part:
            parts.append(category_part)
        
        # 5. Merch classifications
        merch_part = self._build_merch_text(row)
        if merch_part:
            parts.append(merch_part)
        
        # 6. Fit attributes (Lifestage and Breed-size)
        fit_part = self._build_fit_text(row)
        if fit_part:
            parts.append(fit_part)
        
        # 7. Food attributes
        food_part = self._build_food_text(row)
        if food_part:
            parts.append(food_part)
        
        # 8. Parent product
        if self._has_value(row, 'PARENT_PRODUCT_NAME'):
            parts.append(f"Parent: {row['PARENT_PRODUCT_NAME']}.")
        
        # 9. Flags
        flags_part = self._build_flags_text(row)
        if flags_part:
            parts.append(flags_part)
        
        # 10. Long description (last)
        desc_part = self._build_description_text(row)
        if desc_part:
            parts.append(desc_part)
        
        # Join all parts with spaces
        search_text = ' '.join(parts)
        
        # Normalize and truncate
        search_text = self._normalize_text(search_text)
        if len(search_text) > self.max_length:
            search_text = search_text[:self.max_length].rsplit(' ', 1)[0] + '...'
        
        return search_text
    
    def _build_species_text(self, row: pd.Series) -> str:
        """Build species part: 'Species: dog.' or 'Species: cat.' or 'Species: dog, cat.'"""
        species = []
        if row.get('SPECIES_DOG_FLAG', False):
            species.append('dog')
        if row.get('SPECIES_CAT_FLAG', False):
            species.append('cat')
        
        if species:
            return f"Species: {', '.join(species)}."
        return ""
    
    def _build_category_text(self, row: pd.Series) -> str:
        """Build category part: 'Category: Level1 > Level2 > Level3 (List).'"""
        levels = []
        for level in ['PRODUCT_CATEGORY_LEVEL1', 'PRODUCT_CATEGORY_LEVEL2', 'PRODUCT_CATEGORY_LEVEL3']:
            if self._has_value(row, level):
                levels.append(str(row[level]).strip())
        
        if not levels:
            return ""
        
        category_chain = ' > '.join(levels)
        
        # Add category list if available
        if self._has_value(row, 'PRODUCT_CATEGORY_LIST'):
            category_list = str(row['PRODUCT_CATEGORY_LIST']).strip()
            return f"Category: {category_chain} ({category_list})."
        else:
            return f"Category: {category_chain}."
    
    def _build_merch_text(self, row: pd.Series) -> str:
        """Build merch part: 'Merch: Class1 | Class2 | Class3.'"""
        merch_classes = []
        for field in ['PRODUCT_MERCH_CLASSIFICATION1', 'PRODUCT_MERCH_CLASSIFICATION2', 'PRODUCT_MERCH_CLASSIFICATION3']:
            if self._has_value(row, field):
                merch_classes.append(str(row[field]).strip())
        
        if merch_classes:
            return f"Merch: {' | '.join(merch_classes)}."
        return ""
    
    def _build_fit_text(self, row: pd.Series) -> str:
        """Build fit part: 'Lifestage: Adult. Breed-size: Large.'"""
        parts = []
        
        if self._has_value(row, 'PRODUCT_LIFESTAGE'):
            parts.append(f"Lifestage: {row['PRODUCT_LIFESTAGE']}")
        
        if self._has_value(row, 'BREED_SIZE'):
            parts.append(f"Breed-size: {row['BREED_SIZE']}")
        
        if parts:
            return '. '.join(parts) + '.'
        return ""
    
    def _build_food_text(self, row: pd.Series) -> str:
        """Build food part: 'Food-form: Dry. Special-diet: Grain-Free.'"""
        parts = []
        
        if self._has_value(row, 'PRODUCT_ATTR_FOOD_FORM'):
            parts.append(f"Food-form: {row['PRODUCT_ATTR_FOOD_FORM']}")
        
        if self._has_value(row, 'PRODUCT_ATTR_SPECIAL_DIET'):
            parts.append(f"Special-diet: {row['PRODUCT_ATTR_SPECIAL_DIET']}")
        
        if parts:
            return '. '.join(parts) + '.'
        return ""
    
    def _build_flags_text(self, row: pd.Series) -> str:
        """Build flags part: 'Flags: rx_required:true consumable:false food:true.'"""
        flags = []
        
        # Convert flag values to lowercase booleans
        for flag_field, flag_name in [
            ('PRODUCT_RX_REQUIRED_FLAG', 'rx_required'),
            ('PRODUCT_IS_CONSUMABLE_FLAG', 'consumable'),
            ('PRODUCT_IS_FOOD_FLAG', 'food')
        ]:
            if flag_field in row:
                flag_value = str(row[flag_field]).lower()
                # Convert various representations to boolean
                bool_value = flag_value in ['true', '1', 'yes', 't']
                flags.append(f"{flag_name}:{str(bool_value).lower()}")
        
        if flags:
            return f"Flags: {' '.join(flags)}."
        return ""
    
    def _build_description_text(self, row: pd.Series) -> str:
        """Build description part: 'Long description: {description}'"""
        # Use PRODUCT_DESCRIPTION_LONG as the primary field
        if self._has_value(row, 'PRODUCT_DESCRIPTION_LONG'):
            desc = str(row['PRODUCT_DESCRIPTION_LONG']).strip()
            if desc:
                return f"Long description: {desc}"
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
        logger.info("Sample search texts:")
        logger.info("=" * 80)
        
        sample_df = df.sample(min(sample_size, len(df)))
        
        for idx, row in sample_df.iterrows():
            logger.info(f"Product: {row.get('PRODUCT_PART_NUMBER', 'Unknown')}")
            logger.info(f"Text: {row['search_text'][:200]}...")
            logger.info("-" * 40)
