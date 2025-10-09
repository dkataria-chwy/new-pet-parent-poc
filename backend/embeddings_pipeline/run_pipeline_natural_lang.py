"""
Natural Language Embeddings Pipeline Runner

Same as run_pipeline.py but uses NaturalLanguageSearchTextBuilder
instead of SearchTextBuilder. Everything else is identical.

Output: artifacts/catalog_embeds_natural_lang.jsonl
"""

import sys
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_loader import ProductDataLoader
from search_text_builder_natural import NaturalLanguageSearchTextBuilder  # ← ONLY CHANGE
from embedding_generator import EmbeddingGenerator
from storage_manager import EmbeddingStorageManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_extra_columns(df_embeddings: pd.DataFrame, df_original: pd.DataFrame) -> pd.DataFrame:
    """
    Add product_autoship_save_eligible_flag, parent_product_part_number, and product_link
    from original CSV to embeddings DataFrame.
    
    Logic copied from add_columns_to_embeddings.py
    """
    df = df_embeddings.copy()
    
    # Create lookup from original CSV
    lookup = {}
    for _, row in df_original.iterrows():
        product_part_number = str(row['PRODUCT_PART_NUMBER'])
        
        # Build product_link: https://www.chewy.com/{PDPSLUG}/dp/{PRODUCT_ID}
        product_link = None
        if pd.notna(row.get('PDPSLUG')) and pd.notna(row.get('PRODUCT_ID')):
            pdpslug = str(row['PDPSLUG']).strip()
            product_id = str(row['PRODUCT_ID']).strip()
            if pdpslug and product_id:
                product_link = f"https://www.chewy.com/{pdpslug}/dp/{product_id}"
        
        lookup[product_part_number] = {
            'autoship_eligible': bool(pd.notna(row.get('PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG')) and 
                                    str(row['PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG']).lower() in ['true', '1', 'yes']),
            'parent_product_part_number': str(row['PARENT_PRODUCT_PART_NUMBER']) if pd.notna(row.get('PARENT_PRODUCT_PART_NUMBER')) else None,
            'product_link': product_link
        }
    
    # Add columns to embeddings DataFrame
    df['product_autoship_save_eligible_flag'] = df['PRODUCT_PART_NUMBER'].apply(
        lambda x: lookup.get(str(x), {}).get('autoship_eligible', False)
    )
    df['parent_product_part_number'] = df['PRODUCT_PART_NUMBER'].apply(
        lambda x: lookup.get(str(x), {}).get('parent_product_part_number', None)
    )
    df['product_link'] = df['PRODUCT_PART_NUMBER'].apply(
        lambda x: lookup.get(str(x), {}).get('product_link', None)
    )
    
    return df


def save_embeddings_with_extra_columns(df: pd.DataFrame, output_path: str):
    """
    Save embeddings to JSONL with ALL columns (including the 3 extra ones).
    Format matches existing catalog_embeds.jsonl exactly.
    """
    logger.info(f"Saving {len(df):,} embeddings to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, row in df.iterrows():
            record = {
                "product_part_number": str(row['PRODUCT_PART_NUMBER']),
                "search_text": str(row['search_text']),
                "embedding": row['embedding'],  # List of floats
                "species_dog_flag": bool(row['SPECIES_DOG_FLAG']),
                "species_cat_flag": bool(row['SPECIES_CAT_FLAG']),
                "embedded_at": str(row['embedded_at']),
                # Extra columns added (same as existing catalog_embeds.jsonl)
                "product_autoship_save_eligible_flag": bool(row['product_autoship_save_eligible_flag']),
                "parent_product_part_number": row['parent_product_part_number'],
                "product_link": row['product_link']
            }
            
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            # Log progress every 10k records
            if (idx + 1) % 10000 == 0:
                logger.info(f"Saved {idx + 1:,} records...")
    
    logger.info(f"✅ Saved all {len(df):,} records")


def main(csv_path: str):
    """
    Run the complete natural language embeddings pipeline.
    Uses NaturalLanguageSearchTextBuilder instead of SearchTextBuilder.
    """
    logger.info("=" * 80)
    logger.info("NATURAL LANGUAGE EMBEDDINGS PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now()}")
    
    # Step 1: Load data
    logger.info("\n📊 Step 1: Loading product data...")
    loader = ProductDataLoader()
    df = loader.load_csv(csv_path)
    loader.derive_species_flags()
    df = loader.df
    
    logger.info(f"✅ Loaded {len(df):,} products")
    
    # Step 2: Build natural language search text
    logger.info("\n📝 Step 2: Building natural language search text...")
    search_builder = NaturalLanguageSearchTextBuilder()  # ← ONLY CHANGE
    df = search_builder.build_search_text(df)
    
    logger.info(f"✅ Built search text for {len(df):,} products")
    
    # Step 3: Generate embeddings
    logger.info("\n🧠 Step 3: Generating embeddings...")
    embedding_gen = EmbeddingGenerator()
    df_with_embeddings = embedding_gen.generate_embeddings(df)
    
    logger.info(f"✅ Generated {len(df_with_embeddings):,} embeddings")
    
    # Step 4: Add extra columns (autoship, parent_sku, product_link)
    logger.info("\n🔗 Step 4: Adding extra columns from CSV...")
    df_with_embeddings = add_extra_columns(df_with_embeddings, loader.df)
    
    logger.info(f"✅ Added product_autoship_save_eligible_flag, parent_product_part_number, product_link")
    
    # Step 5: Save embeddings with ALL columns
    logger.info("\n💾 Step 5: Saving embeddings with all columns...")
    output_file = Path(__file__).parent / "artifacts" / "catalog_embeds_natural_lang.jsonl"
    save_embeddings_with_extra_columns(df_with_embeddings, str(output_file))
    
    logger.info(f"✅ Saved embeddings to: {output_file.name}")
    logger.info(f"   File size: {output_file.stat().st_size / (1024**3):.2f} GB")
    
    # Done
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE! ✅")
    logger.info("=" * 80)
    logger.info(f"Finished at: {datetime.now()}")
    logger.info(f"\nOutput: artifacts/catalog_embeds_natural_lang.jsonl")
    logger.info(f"Total products: {len(df_with_embeddings):,}")
    logger.info("\n✅ Natural language embeddings ready to use!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python run_pipeline_natural_lang.py <path_to_csv>")
        print("Example: python run_pipeline_natural_lang.py '../product embeddings table.csv'")
        print("\nThis will create: artifacts/catalog_embeds_natural_lang.jsonl")
        print("Cost: ~$27, Time: ~60 minutes\n")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    main(csv_path)

