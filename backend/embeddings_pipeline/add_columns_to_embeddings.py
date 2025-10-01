#!/usr/bin/env python3
"""
Add Additional Columns to Existing Embeddings

This script adds PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG and PARENT_PRODUCT_PART_NUMBER
to the existing catalog_embeds.jsonl file without regenerating embeddings.

Usage:
    python add_columns_to_embeddings.py
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_existing_embeddings(embeddings_path: str) -> Dict[str, Dict]:
    """Load existing embeddings into a dictionary keyed by product_part_number."""
    logger.info(f"Loading existing embeddings from: {embeddings_path}")
    
    embeddings_dict = {}
    
    with open(embeddings_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    record = json.loads(line)
                    product_id = record['product_part_number']
                    embeddings_dict[product_id] = record
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                except KeyError as e:
                    logger.warning(f"Missing product_part_number on line {line_num}: {e}")
    
    logger.info(f"Loaded {len(embeddings_dict):,} embedding records")
    return embeddings_dict


def load_csv_data(csv_path: str) -> pd.DataFrame:
    """Load CSV data with the additional columns."""
    logger.info(f"Loading CSV data from: {csv_path}")
    
    # Load only the columns we need
    required_cols = ['PRODUCT_PART_NUMBER', 'PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG', 'PARENT_PRODUCT_PART_NUMBER']
    
    try:
        df = pd.read_csv(csv_path, usecols=required_cols, dtype=str)
        logger.info(f"Loaded {len(df):,} CSV records")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise


def merge_and_save(embeddings_dict: Dict[str, Dict], csv_df: pd.DataFrame, output_path: str):
    """Merge embeddings with CSV data and save to new file."""
    logger.info("Merging embeddings with CSV data...")
    
    # Create lookup dictionary from CSV
    csv_dict = {}
    for _, row in csv_df.iterrows():
        product_id = str(row['PRODUCT_PART_NUMBER'])
        csv_dict[product_id] = {
            'autoship_eligible': bool(pd.notna(row['PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG']) and 
                                    str(row['PRODUCT_AUTOSHIP_SAVE_ELIGIBLE_FLAG']).lower() in ['true', '1', 'yes']),
            'parent_product_part_number': str(row['PARENT_PRODUCT_PART_NUMBER']) if pd.notna(row['PARENT_PRODUCT_PART_NUMBER']) else None
        }
    
    logger.info(f"Created lookup for {len(csv_dict):,} CSV records")
    
    # Merge and save
    matched_count = 0
    unmatched_count = 0
    
    with open(output_path, 'w') as f:
        for product_id, embedding_record in embeddings_dict.items():
            # Start with existing embedding record
            enhanced_record = embedding_record.copy()
            
            # Add new fields if product exists in CSV
            if product_id in csv_dict:
                csv_data = csv_dict[product_id]
                enhanced_record['product_autoship_save_eligible_flag'] = csv_data['autoship_eligible']
                enhanced_record['parent_product_part_number'] = csv_data['parent_product_part_number']
                matched_count += 1
            else:
                # Set defaults for unmatched products
                enhanced_record['product_autoship_save_eligible_flag'] = False
                enhanced_record['parent_product_part_number'] = None
                unmatched_count += 1
            
            # Write enhanced record
            f.write(json.dumps(enhanced_record, ensure_ascii=False) + '\n')
    
    logger.info(f"Merge complete:")
    logger.info(f"  ✅ Matched products: {matched_count:,}")
    logger.info(f"  ⚠️  Unmatched products: {unmatched_count:,}")
    logger.info(f"  📁 Output saved: {output_path}")


def main():
    """Main function."""
    # File paths
    embeddings_path = "artifacts/catalog_embeds.jsonl"
    csv_path = "../../product embeddings table.csv"
    output_path = "artifacts/catalog_embeds_2.jsonl"
    
    # Validate input files
    if not Path(embeddings_path).exists():
        logger.error(f"Embeddings file not found: {embeddings_path}")
        return
    
    if not Path(csv_path).exists():
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    try:
        # Load data
        embeddings_dict = load_existing_embeddings(embeddings_path)
        csv_df = load_csv_data(csv_path)
        
        # Merge and save
        merge_and_save(embeddings_dict, csv_df, output_path)
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("🎉 COLUMN ADDITION COMPLETE!")
        logger.info("="*60)
        logger.info(f"📁 Input: {embeddings_path}")
        logger.info(f"📁 Output: {output_path}")
        logger.info("📊 Added columns:")
        logger.info("   - product_autoship_save_eligible_flag (boolean)")
        logger.info("   - parent_product_part_number (string)")
        logger.info("✅ Ready to use with recommendation engine!")
        
    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
        raise


if __name__ == "__main__":
    main()
