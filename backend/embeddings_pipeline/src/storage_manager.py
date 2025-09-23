"""
Storage management module.

Handles saving and loading embeddings to/from JSONL format.
"""

import json
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EmbeddingStorageManager:
    """Manages storage of embeddings in JSONL format."""
    
    def __init__(self, artifacts_dir: str = "./artifacts"):
        """
        Initialize storage manager.
        
        Args:
            artifacts_dir: Directory to store artifacts
        """
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        self.jsonl_path = self.artifacts_dir / "catalog_embeds.jsonl"
    
    def save_embeddings(self, df: pd.DataFrame) -> str:
        """
        Save embeddings DataFrame to JSONL format.
        
        Expected DataFrame columns:
        - PRODUCT_PART_NUMBER: Product identifier
        - search_text: Constructed search text
        - embedding: List of floats (3072 dimensions)
        - SPECIES_DOG_FLAG: Boolean
        - SPECIES_CAT_FLAG: Boolean
        - embedded_at: ISO timestamp
        
        Args:
            df: DataFrame with embeddings
            
        Returns:
            Path to saved JSONL file
        """
        required_columns = [
            'PRODUCT_PART_NUMBER', 'search_text', 'embedding',
            'SPECIES_DOG_FLAG', 'SPECIES_CAT_FLAG', 'embedded_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        logger.info(f"Saving {len(df):,} embeddings to {self.jsonl_path}")
        
        # Write JSONL file
        with open(self.jsonl_path, 'w', encoding='utf-8') as f:
            for idx, row in df.iterrows():
                record = {
                    "product_part_number": str(row['PRODUCT_PART_NUMBER']),
                    "search_text": str(row['search_text']),
                    "embedding": row['embedding'],  # List of floats
                    "species_dog_flag": bool(row['SPECIES_DOG_FLAG']),
                    "species_cat_flag": bool(row['SPECIES_CAT_FLAG']),
                    "embedded_at": str(row['embedded_at'])
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                
                # Log progress every 10k records
                if (idx + 1) % 10000 == 0:
                    logger.info(f"Saved {idx + 1:,} records...")
        
        # Log file info
        file_size_mb = self.jsonl_path.stat().st_size / (1024 * 1024)
        logger.info(f"Saved embeddings to: {self.jsonl_path}")
        logger.info(f"File size: {file_size_mb:.1f} MB")
        
        return str(self.jsonl_path)
    
    def load_embeddings(self, jsonl_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load embeddings from JSONL file.
        
        Args:
            jsonl_path: Path to JSONL file (uses default if None)
            
        Returns:
            DataFrame with embeddings
        """
        if jsonl_path is None:
            jsonl_path = self.jsonl_path
        else:
            jsonl_path = Path(jsonl_path)
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        logger.info(f"Loading embeddings from: {jsonl_path}")
        
        records = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                    
                    # Log progress every 10k records
                    if line_num % 10000 == 0:
                        logger.info(f"Loaded {line_num:,} records...")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    continue
        
        df = pd.DataFrame(records)
        logger.info(f"Loaded {len(df):,} embeddings with {len(df.columns)} columns")
        
        return df
    
    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Save processing metadata.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Path to saved metadata file
        """
        metadata_path = self.artifacts_dir / "embedding_metadata.json"
        
        # Add timestamp
        metadata['generated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata to: {metadata_path}")
        return str(metadata_path)
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load processing metadata."""
        metadata_path = self.artifacts_dir / "embedding_metadata.json"
        
        if not metadata_path.exists():
            return {}
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about stored files."""
        info = {
            'artifacts_dir': str(self.artifacts_dir),
            'jsonl_exists': self.jsonl_path.exists(),
            'metadata_exists': (self.artifacts_dir / "embedding_metadata.json").exists()
        }
        
        if info['jsonl_exists']:
            stat = self.jsonl_path.stat()
            info['jsonl_size_mb'] = stat.st_size / (1024 * 1024)
            info['jsonl_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Count lines quickly
            with open(self.jsonl_path, 'r') as f:
                info['jsonl_record_count'] = sum(1 for _ in f)
        
        return info
    
    def validate_jsonl_integrity(self, jsonl_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate JSONL file integrity.
        
        Args:
            jsonl_path: Path to JSONL file (uses default if None)
            
        Returns:
            Validation results
        """
        if jsonl_path is None:
            jsonl_path = self.jsonl_path
        else:
            jsonl_path = Path(jsonl_path)
        
        if not jsonl_path.exists():
            return {'valid': False, 'error': 'File does not exist'}
        
        logger.info(f"Validating JSONL integrity: {jsonl_path}")
        
        validation_results = {
            'valid': True,
            'total_lines': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'missing_fields': [],
            'embedding_dimensions': [],
            'sample_records': []
        }
        
        required_fields = [
            'product_part_number', 'search_text', 'embedding',
            'species_dog_flag', 'species_cat_flag', 'embedded_at'
        ]
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                validation_results['total_lines'] += 1
                
                try:
                    record = json.loads(line.strip())
                    
                    # Check required fields
                    missing = [field for field in required_fields if field not in record]
                    if missing:
                        validation_results['missing_fields'].extend(missing)
                        validation_results['invalid_records'] += 1
                        continue
                    
                    # Check embedding dimension
                    if isinstance(record['embedding'], list):
                        dim = len(record['embedding'])
                        validation_results['embedding_dimensions'].append(dim)
                    
                    validation_results['valid_records'] += 1
                    
                    # Store sample records (first 3)
                    if len(validation_results['sample_records']) < 3:
                        sample = {k: v for k, v in record.items() if k != 'embedding'}
                        sample['embedding_length'] = len(record['embedding']) if isinstance(record['embedding'], list) else 0
                        validation_results['sample_records'].append(sample)
                    
                except json.JSONDecodeError:
                    validation_results['invalid_records'] += 1
        
        # Summary statistics
        validation_results['missing_fields'] = list(set(validation_results['missing_fields']))
        if validation_results['embedding_dimensions']:
            unique_dims = list(set(validation_results['embedding_dimensions']))
            validation_results['unique_embedding_dimensions'] = unique_dims
            validation_results['correct_dimension_count'] = sum(1 for d in validation_results['embedding_dimensions'] if d == 3072)
        
        validation_results['valid'] = (
            validation_results['invalid_records'] == 0 and
            not validation_results['missing_fields']
        )
        
        logger.info(f"Validation complete: {validation_results['valid_records']:,} valid, {validation_results['invalid_records']:,} invalid")
        
        return validation_results
