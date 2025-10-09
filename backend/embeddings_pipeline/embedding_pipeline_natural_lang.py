"""
Natural Language Embeddings Pipeline

Generates embeddings with natural language search text format
while preserving ALL existing columns from the original pipeline.

Output: artifacts/catalog_embeds_natural_lang.jsonl
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_loader import ProductDataLoader
from embedding_generator import EmbeddingGenerator
from storage_manager import EmbeddingStorageManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NaturalLanguageSearchTextBuilder:
    """
    Builds natural language search text for product embeddings.
    Uses the same column structure as the original pipeline but
    rewrites search_text in a more natural, flowing format.
    """
    
    def __init__(self, max_length: int = 2000):
        self.max_length = max_length
    
    def build_search_text_for_product(self, row: dict) -> str:
        """
        Build natural language search text for a single product.
        
        Args:
            row: Product data dictionary
            
        Returns:
            Natural language search text string
        """
        parts = []
        
        # 1. Start with brand + product name + key attributes
        intro = self._build_intro(row)
        if intro:
            parts.append(intro)
        
        # 2. Add the main product description
        desc = self._extract_description(row)
        if desc:
            parts.append(desc)
        
        # 3. Add product attributes naturally
        attributes = self._build_attributes(row)
        if attributes:
            parts.append(attributes)
        
        # 4. Add category context
        category_context = self._build_category_context(row)
        if category_context:
            parts.append(category_context)
        
        # Join and normalize
        search_text = ' '.join(parts)
        search_text = self._normalize_text(search_text)
        
        # Truncate if needed
        if len(search_text) > self.max_length:
            search_text = search_text[:self.max_length].rsplit(' ', 1)[0] + '...'
        
        return search_text
    
    def _build_intro(self, row: dict) -> str:
        """Build natural intro: 'Brand Name Product for species, lifestage, size'"""
        parts = []
        
        # Brand + Product Name
        if self._has_value(row, 'PRODUCT_PURCHASE_BRAND'):
            parts.append(row['PRODUCT_PURCHASE_BRAND'])
        
        if self._has_value(row, 'PRODUCT_NAME'):
            name = str(row['PRODUCT_NAME']).strip()
            # Don't repeat brand if already in name
            if parts and parts[0].lower() not in name.lower():
                parts.append(name)
            elif not parts:
                parts.append(name)
        
        intro = ' '.join(parts) if parts else ""
        
        # Add qualifiers (species, lifestage, breed-size, food form, diet)
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
        
        # Combine
        if intro and qualifiers:
            return f"{intro} for {', '.join(qualifiers)}."
        elif intro:
            return f"{intro}."
        return ""
    
    def _extract_description(self, row: dict) -> str:
        """Extract and clean product description"""
        if self._has_value(row, 'PRODUCT_DESCRIPTION_LONG'):
            desc = str(row['PRODUCT_DESCRIPTION_LONG']).strip()
            # Remove promotional markers
            import re
            desc = re.sub(r'\*\*.*?\*\*', '', desc)
            desc = re.sub(r'SHOP NOW|BUY NOW|LIMITED TIME', '', desc, flags=re.IGNORECASE)
            desc = self._normalize_text(desc)
            return desc
        return ""
    
    def _build_attributes(self, row: dict) -> str:
        """Build product attributes naturally"""
        attrs = []
        
        # Multiple sizes/variants
        if self._has_value(row, 'PARENT_PRODUCT_NAME'):
            attrs.append("Available in multiple sizes")
        
        # Prescription
        if row.get('PRODUCT_RX_REQUIRED_FLAG') in [True, 'true', '1', 'yes', 't', 'True']:
            attrs.append("Prescription required")
        else:
            attrs.append("No prescription required")
        
        # Consumable
        if row.get('PRODUCT_IS_CONSUMABLE_FLAG') in [True, 'true', '1', 'yes', 't', 'True']:
            attrs.append("Consumable product")
        
        # Food
        if row.get('PRODUCT_IS_FOOD_FLAG') in [True, 'true', '1', 'yes', 't', 'True']:
            attrs.append("Food product")
        
        if attrs:
            return '. '.join(attrs) + '.'
        return ""
    
    def _build_category_context(self, row: dict) -> str:
        """Build category context naturally"""
        parts = []
        
        # Use merch classifications
        merch = []
        for field in ['PRODUCT_MERCH_CLASSIFICATION1', 'PRODUCT_MERCH_CLASSIFICATION2', 'PRODUCT_MERCH_CLASSIFICATION3']:
            if self._has_value(row, field):
                val = str(row[field]).strip().lower()
                if val not in merch:
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
    
    def _get_species(self, row: dict) -> str:
        """Get species as natural text"""
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
    
    def _has_value(self, row: dict, field: str) -> bool:
        """Check if field has non-empty value"""
        import pandas as pd
        return (field in row and 
                pd.notna(row[field]) and 
                str(row[field]).strip() != '' and
                str(row[field]).strip().lower() not in ['null', 'none', 'n/a'])
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: UTF-8, collapse whitespace"""
        import re
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def run_natural_language_pipeline(csv_path: str):
    """
    Run the complete natural language embeddings pipeline.
    
    Preserves ALL columns from the original pipeline:
    - product_part_number
    - search_text (NEW: natural language format)
    - embedding
    - species_dog_flag
    - species_cat_flag
    - embedded_at
    - product_autoship_save_eligible_flag
    - parent_product_part_number
    - product_link
    
    Args:
        csv_path: Path to product CSV file
    """
    logger.info("=" * 80)
    logger.info("NATURAL LANGUAGE EMBEDDINGS PIPELINE")
    logger.info("=" * 80)
    
    # Step 1: Load and prepare data
    logger.info("\n1. Loading product data...")
    loader = ProductDataLoader()
    df = loader.load_csv(csv_path)
    loader.derive_species_flags()
    df = loader.df
    
    logger.info(f"Loaded {len(df):,} products")
    
    # Step 2: Build natural language search text
    logger.info("\n2. Building natural language search text...")
    search_builder = NaturalLanguageSearchTextBuilder()
    
    search_texts = []
    for idx, row in df.iterrows():
        search_text = search_builder.build_search_text_for_product(row.to_dict())
        search_texts.append(search_text)
        
        if (idx + 1) % 10000 == 0:
            logger.info(f"  Processed {idx + 1:,} search texts...")
    
    df['search_text'] = search_texts
    logger.info(f"  ✅ Search text construction complete")
    
    # Log samples
    logger.info("\n  Sample natural language search texts:")
    for idx in range(min(3, len(df))):
        logger.info(f"  SKU {df.iloc[idx]['PRODUCT_PART_NUMBER']}: {df.iloc[idx]['search_text'][:200]}...")
    
    # Step 3: Generate embeddings
    logger.info("\n3. Generating embeddings...")
    embedding_gen = EmbeddingGenerator()
    df_with_embeddings = embedding_gen.generate_embeddings(df)
    
    logger.info(f"  ✅ Generated {len(df_with_embeddings):,} embeddings")
    
    # Step 4: Prepare output with ALL required columns
    logger.info("\n4. Preparing output with all columns...")
    
    output_records = []
    for idx, row in df_with_embeddings.iterrows():
        record = {
            # Core fields
            "product_part_number": str(row['PRODUCT_PART_NUMBER']),
            "search_text": row['search_text'],
            "embedding": row['embedding'],
            
            # Species flags
            "species_dog_flag": bool(row.get('SPECIES_DOG_FLAG', False)),
            "species_cat_flag": bool(row.get('SPECIES_CAT_FLAG', False)),
            
            # Timestamp
            "embedded_at": datetime.now(timezone.utc).isoformat(),
            
            # Additional fields
            "product_autoship_save_eligible_flag": bool(row.get('PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG', False)),
            "parent_product_part_number": str(row.get('PARENT_PRODUCT_PART_NUMBER', '')) if row.get('PARENT_PRODUCT_PART_NUMBER') else None,
            "product_link": row.get('product_link', '') or ''
        }
        output_records.append(record)
    
    logger.info(f"  ✅ Prepared {len(output_records):,} records")
    
    # Step 5: Save to JSONL
    output_file = Path(__file__).parent / "artifacts" / "catalog_embeds_natural_lang.jsonl"
    logger.info(f"\n5. Saving to {output_file.name}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in output_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    logger.info(f"  ✅ Saved {len(output_records):,} records")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE! ✅")
    logger.info("=" * 80)
    logger.info(f"\nOutput file: {output_file}")
    logger.info(f"Total products: {len(output_records):,}")
    logger.info(f"File size: {output_file.stat().st_size / (1024**3):.2f} GB")
    logger.info("\n✅ Natural language embeddings ready for use!")
    logger.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python embedding_pipeline_natural_lang.py <path_to_csv>")
        print("Example: python embedding_pipeline_natural_lang.py '../product embeddings table.csv'")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    run_natural_language_pipeline(csv_path)

