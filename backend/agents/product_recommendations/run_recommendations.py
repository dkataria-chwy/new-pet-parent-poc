#!/usr/bin/env python3
"""
Product Recommendations CLI

Usage:
    python run_recommendations.py <llm_output_file.json>
    
Example:
    python run_recommendations.py ../../outputs/model_output_1c4083d7_month14_20250925_193526.json
"""

import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from recommendation_engine import ProductRecommendationEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python run_recommendations.py <llm_output_file.json>")
        print("Example: python run_recommendations.py backend/outputs/model_output_1c4083d7_month14_20250925_193526.json")
        sys.exit(1)
    
    llm_output_file = sys.argv[1]
    
    logger.info("🚀 PRODUCT RECOMMENDATION ENGINE")
    logger.info("=" * 60)
    logger.info(f"📁 Input file: {llm_output_file}")
    
    try:
        # Initialize engine
        engine = ProductRecommendationEngine()
        
        logger.info("\n📊 Initializing engine...")
        stats = engine.initialize()
        
        logger.info(f"✅ Loaded {stats['total_products']:,} products")
        logger.info(f"   🐕 Dog products: {stats['dog_products']:,}")
        logger.info(f"   🐱 Cat products: {stats['cat_products']:,}")
        
        # Process LLM output
        logger.info(f"\n🔍 Processing LLM output...")
        results = engine.process_file(llm_output_file)
        
        # Generate output filename - ensure it's relative to project root
        input_path = Path(llm_output_file)
        if not input_path.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            input_path = project_root / llm_output_file
        
        # Generate output filename with current timestamp (replace existing timestamp)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract base name without existing timestamp
        stem = input_path.stem  # e.g., "model_output_1c4083d7_month11_20250929_154326"
        parts = stem.split('_')
        
        # Remove the last two parts if they look like timestamp (YYYYMMDD_HHMMSS)
        if len(parts) >= 2 and len(parts[-1]) == 6 and len(parts[-2]) == 8:
            base_parts = parts[:-2]  # Remove timestamp parts
        else:
            base_parts = parts
        
        # Build clean filename
        base_name = '_'.join(base_parts).replace("model_output", "recommendations")
        output_filename = f"{base_name}_{timestamp}.json"
        
        # Always save to backend/outputs/ directory
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = project_root / "backend" / "outputs" / output_filename
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 PROCESSING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"📊 Pet ID: {results['pet_id']}")
        logger.info(f"📅 Month: {results['month']}")
        logger.info(f"🎯 Slots processed: {results['processed_slots']}")
        logger.info(f"🛍️  Unique products: {results['total_unique_products']}")
        logger.info(f"💾 Output saved: {output_path}")
        
        # Show sample results
        if results['results']:
            logger.info(f"\n📋 Sample results:")
            first_slot = results['results'][0]
            logger.info(f"   Slot: {first_slot['slot_id']} ({first_slot['top_family']})")
            
            for product in first_slot['products'][:3]:  # Show first 3
                logger.info(f"     {product['rank']}. {product['sku']} - {product['name'][:50]}... (sim: {product['similarity']})")
            
            if len(first_slot['products']) > 3:
                logger.info(f"     ... and {len(first_slot['products']) - 3} more products")
        
        logger.info(f"\n✅ Recommendations ready! Check: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
