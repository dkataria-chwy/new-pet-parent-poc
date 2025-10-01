#!/usr/bin/env python3
"""
Product Embeddings Pipeline - CLI Entry Point

Usage:
    python run_pipeline.py "path/to/product_catalog.csv"
    
Example:
    python run_pipeline.py "../product embeddings table.csv"
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv("../../.env")

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import EmbeddingsPipeline, setup_logging
import logging

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python run_pipeline.py <csv_path>")
        print("Example: python run_pipeline.py '../product embeddings table.csv'")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    # Setup logging
    setup_logging("INFO")
    
    # Validate CSV path
    if not Path(csv_path).exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    logger.info(f"Starting embeddings pipeline for: {csv_path}")
    
    # Initialize pipeline with production settings
    pipeline = EmbeddingsPipeline(
        artifacts_dir="./artifacts",
        batch_size=100,  # Efficient batch size for OpenAI API
        max_text_length=3000  # Good balance of detail vs token usage
    )
    
    # Run the complete pipeline
    results = pipeline.run_full_pipeline(csv_path)
    
    if results['success']:
        logger.info("\n" + "="*60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"⏱️  Duration: {results['duration_seconds']:.1f} seconds")
        logger.info(f"📁 Output: {results['jsonl_path']}")
        logger.info(f"📊 Records: {results['pipeline_stats']['data_stats']['kept_rows']:,}")
        logger.info(f"💰 Cost: ${results['pipeline_stats']['api_usage']['estimated_cost_usd']:.2f}")
        
        # Create and demo search engine
        logger.info("\n" + "="*60)
        logger.info("🔍 CREATING SEARCH DEMO")
        logger.info("="*60)
        
        try:
            search_engine = pipeline.create_search_demo()
            
            # Run demonstration searches
            demo_queries = [
                "large-breed puppy growth food with DHA and controlled calcium",
                "durable chew toy for strong chewer",
                "grain-free salmon dog food for adult dogs",
                "interactive puzzle toy for mental stimulation",
                "calming treats for anxiety and stress"
            ]
            
            for query in demo_queries:
                logger.info(f"\n🔎 Query: '{query}'")
                results = search_engine.search(query, top_k=3, species_filter='dog')
                
                for result in results:
                    logger.info(f"   {result['rank']}. Product {result['product_part_number']} (similarity: {result['similarity']:.3f})")
                    logger.info(f"      {result['search_text_preview']}")
            
            logger.info("\n✅ Search demo completed successfully!")
            logger.info("💡 You can now use the search engine programmatically:")
            logger.info("   from src.vector_search import VectorSearchEngine")
            logger.info("   search_engine = VectorSearchEngine()")
            logger.info("   search_engine.load_embeddings(df)")
            logger.info("   results = search_engine.search('your query here')")
            
        except Exception as e:
            logger.warning(f"Search demo failed: {e}")
    
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ PIPELINE FAILED!")
        logger.error("="*60)
        logger.error(f"Error: {results['error']}")
        logger.error(f"Duration: {results['duration_seconds']:.1f} seconds")
        sys.exit(1)


if __name__ == "__main__":
    main()
