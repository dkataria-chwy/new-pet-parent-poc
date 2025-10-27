"""
Main embeddings pipeline orchestrator.

Coordinates all steps of the embedding generation process.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from data_loader import ProductDataLoader
from search_text_builder import SearchTextBuilder
from embedding_generator import EmbeddingGenerator
from storage_manager import EmbeddingStorageManager

logger = logging.getLogger(__name__)


class EmbeddingsPipeline:
    """Main pipeline for generating product embeddings."""
    
    def __init__(self, 
                 artifacts_dir: str = "./artifacts",
                 batch_size: int = 100,
                 max_text_length: int = 2000):
        """
        Initialize the embeddings pipeline.
        
        Args:
            artifacts_dir: Directory to store output artifacts
            batch_size: Batch size for embedding generation
            max_text_length: Maximum length for search text
        """
        self.artifacts_dir = artifacts_dir
        
        # Initialize components
        self.data_loader = ProductDataLoader()
        self.text_builder = SearchTextBuilder(max_length=max_text_length)
        self.embedding_generator = EmbeddingGenerator(batch_size=batch_size)
        self.storage_manager = EmbeddingStorageManager(artifacts_dir=artifacts_dir)
        
        # Pipeline state
        self.df = None
        self.pipeline_stats = {}
        
    def run_full_pipeline(self, csv_path: str) -> Dict[str, Any]:
        """
        Run the complete embeddings generation pipeline.
        
        Args:
            csv_path: Path to the product catalog CSV
            
        Returns:
            Pipeline execution results
        """
        logger.info("=" * 80)
        logger.info("STARTING EMBEDDINGS PIPELINE")
        logger.info("=" * 80)
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Load CSV and derive species flags
            logger.info("Step 1: Loading CSV and deriving species flags...")
            self.df = self.data_loader.load_csv(csv_path)
            self.df = self.data_loader.derive_species_flags()
            
            # Step 2: Build search text
            logger.info("Step 2: Building search text...")
            self.df = self.text_builder.build_search_text(self.df)
            
            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings...")
            cost_estimate = self.embedding_generator.estimate_cost(
                num_texts=len(self.df),
                avg_tokens_per_text=150  # Conservative estimate
            )
            logger.info(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}")
            
            # Ask for confirmation before proceeding with expensive operation
            if cost_estimate['estimated_cost_usd'] > 10.0:
                logger.warning(f"High cost estimate: ${cost_estimate['estimated_cost_usd']:.2f}")
                logger.warning("Consider running on a smaller subset first")
            
            self.df = self.embedding_generator.generate_embeddings(self.df)
            
            # Step 4: Validate embeddings
            logger.info("Step 4: Validating embeddings...")
            validation_results = self.embedding_generator.validate_embeddings(self.df)
            
            # Step 5: Save to JSONL
            logger.info("Step 5: Saving embeddings...")
            jsonl_path = self.storage_manager.save_embeddings(self.df)
            
            # Step 6: Save metadata
            metadata = self._collect_pipeline_metadata(start_time, validation_results, cost_estimate)
            metadata_path = self.storage_manager.save_metadata(metadata)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Output: {jsonl_path}")
            logger.info("=" * 80)
            
            return {
                'success': True,
                'duration_seconds': duration,
                'jsonl_path': jsonl_path,
                'metadata_path': metadata_path,
                'pipeline_stats': metadata
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
            }
    
    def _collect_pipeline_metadata(self, 
                                 start_time: datetime,
                                 validation_results: Dict[str, Any],
                                 cost_estimate: Dict[str, Any]) -> Dict[str, Any]:
        """Collect comprehensive pipeline metadata."""
        return {
            'pipeline_version': '1.0.0',
            'execution_time': {
                'started_at': start_time.isoformat() + 'Z',
                'completed_at': datetime.utcnow().isoformat() + 'Z'
            },
            'data_stats': self.data_loader.get_stats(),
            'embedding_config': {
                'model': self.embedding_generator.model,
                'batch_size': self.embedding_generator.batch_size,
                'max_text_length': self.text_builder.max_length
            },
            'api_usage': {
                'total_requests': self.embedding_generator.total_requests,
                'failed_requests': self.embedding_generator.failed_requests,
                'total_tokens': self.embedding_generator.total_tokens,
                'estimated_cost_usd': cost_estimate['estimated_cost_usd']
            },
            'validation_results': validation_results,
            'output_files': {
                'jsonl_path': str(self.storage_manager.jsonl_path),
                'artifacts_dir': str(self.storage_manager.artifacts_dir)
            }
        }
    


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('embeddings_pipeline.log')
        ]
    )


def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate product embeddings pipeline')
    parser.add_argument('csv_path', help='Path to product catalog CSV file')
    parser.add_argument('--artifacts-dir', default='./artifacts', help='Output directory for artifacts')
    parser.add_argument('--batch-size', type=int, default=100, help='Embedding batch size')
    parser.add_argument('--max-text-length', type=int, default=2000, help='Maximum search text length')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run pipeline
    pipeline = EmbeddingsPipeline(
        artifacts_dir=args.artifacts_dir,
        batch_size=args.batch_size,
        max_text_length=args.max_text_length
    )
    
    results = pipeline.run_full_pipeline(args.csv_path)
    
    if results['success']:
        logger.info("Pipeline completed successfully!")
        
        # Create search demo
        search_engine = pipeline.create_search_demo()
        
        # Run sample searches
        logger.info("\n" + "="*50)
        logger.info("SAMPLE SEARCHES")
        logger.info("="*50)
        
        sample_queries = [
            "large-breed puppy growth food with DHA and controlled calcium",
            "durable teething chew for strong chewer",
            "VOHC dental starter for puppy",
            "cooling mat for heat wave",
            "calming chews for fireworks noise"
        ]
        
        for query in sample_queries:
            logger.info(f"\nQuery: {query}")
            results = search_engine.search(query, top_k=3, species_filter='dog')
            for result in results:
                logger.info(f"  {result['rank']}. {result['product_part_number']} (sim: {result['similarity']:.3f})")
                logger.info(f"     {result['search_text_preview']}")
    else:
        logger.error("Pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
