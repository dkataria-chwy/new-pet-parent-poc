#!/usr/bin/env python3
"""
Stage 2 Structured Product Recommendations CLI
Converts Stage 2 structured query output to recommendations using the existing recommendation engine.
Maintains bucket information (essentials/nice_to_haves/enrichment).

Usage:
    python run_stage2_structured_recommendations.py <stage2_structured_output_file.json>
    
Example:
    python run_stage2_structured_recommendations.py stage2_structured_queries_1c4083d7_month2_20251001_205537.json
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

# Add current directory and backend to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))  # product_recommendations dir
sys.path.insert(0, str(Path(__file__).parent.parent))  # agents dir  
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # backend dir

from recommendation_engine import ProductRecommendationEngine
import database

def get_pet_info_from_journey(journey_id):
    """Get pet_id and species from journey_id by querying the database."""
    try:
        journey = database.db.get_journey(journey_id)
        if journey:
            pet = database.db.get_pet(journey.petId)
            if pet:
                return {
                    "pet_id": journey.petId,
                    "species": pet.species.lower() if pet.species else "dog"  # default to dog
                }
            else:
                logger.warning(f"Pet {journey.petId} not found in database")
                return {"pet_id": journey.petId, "species": "dog"}
        else:
            logger.warning(f"Journey {journey_id} not found in database, using journey_id as pet_id")
            return {"pet_id": journey_id, "species": "dog"}
    except Exception as e:
        logger.warning(f"Failed to get pet info from journey {journey_id}: {e}, using journey_id as pet_id")
        return {"pet_id": journey_id, "species": "dog"}

def convert_stage2_structured_to_llm_format(stage2_data):
    """
    Convert Stage 2 structured query format to original LLM output format.
    Maintains bucket information for later organization.
    
    Stage 2 structured format: {"total_queries": N, "queries": [...], "metadata": {...}}
    LLM format: {"pet_id": "...", "month": N, "slots": [...]}
    """
    # Extract metadata
    metadata = stage2_data.get("metadata", {})
    journey_id = metadata.get("journey_id", "unknown")
    month_idx = metadata.get("month_idx", 0)
    
    # Get actual pet_id and species from journey
    pet_info = get_pet_info_from_journey(journey_id)
    pet_id = pet_info["pet_id"]
    species = pet_info["species"]
    
    # Convert queries to slots (preserving bucket info and rationale)
    slots = []
    for i, query in enumerate(stage2_data.get("queries", [])):
        slot = {
            "slot_id": i + 1,
            "bucket": query.get("bucket", "enrichment"),  # Maintain bucket info
            "top_family": query.get("top_family", ""),
            "family": query.get("family", ""),
            "embedding_query": query.get("embedding_query", ""),
            "bm25_query": query.get("bm25_query", ""),
            "top_k": query.get("top_k", 10),
            "rationale": query.get("rationale", ""),  # Include rationale from Stage 2
            "negatives": query.get("negatives", []),
            "musts": [f"species:{species}"],  # Add species for filtering
            "filters": {"pc1": species.capitalize()}  # Add species filter (Dog/Cat)
        }
        slots.append(slot)
    
    # Create LLM-compatible format
    llm_format = {
        "pet_id": pet_id,  # Now using actual pet_id, not journey_id
        "month": month_idx,
        "slots": slots
    }
    
    return llm_format

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python run_stage2_structured_recommendations.py <stage2_structured_output_filename.json>")
        print("Example: python run_stage2_structured_recommendations.py stage2_structured_queries_1c4083d7_month2_20251001_205537.json")
        sys.exit(1)
    
    stage2_filename = sys.argv[1]
    
    # If full path provided, use as-is; if just filename, prepend stage2_structured path
    if "/" in stage2_filename:
        stage2_output_file = stage2_filename
    else:
        # Auto-prepend the stage2_structured directory path
        backend_dir = Path(__file__).parent.parent.parent  # Go up to backend dir
        stage2_output_file = str(backend_dir / "testing" / "outputs" / "stage2_structured" / stage2_filename)
    
    logger.info("🚀 STAGE 2 STRUCTURED → PRODUCT RECOMMENDATIONS")
    logger.info("=" * 60)
    logger.info(f"📁 Stage 2 structured input: {stage2_output_file}")
    
    try:
        # Load Stage 2 structured output
        logger.info("\n🔍 Loading Stage 2 structured output...")
        with open(stage2_output_file, 'r') as f:
            stage2_data = json.load(f)
        
        # Validate Stage 2 structured format
        if "queries" not in stage2_data or "total_queries" not in stage2_data:
            raise ValueError("Invalid Stage 2 structured format - expected 'queries' and 'total_queries' fields")
        
        logger.info(f"✅ Loaded {len(stage2_data['queries'])} queries from Stage 2 structured")
        
        # Show bucket distribution
        buckets = {"essentials": 0, "nice_to_haves": 0, "enrichment": 0}
        for query in stage2_data['queries']:
            bucket = query.get("bucket", "enrichment")
            if bucket in buckets:
                buckets[bucket] += 1
        
        logger.info(f"📦 Bucket distribution:")
        logger.info(f"   🏥 Essentials: {buckets['essentials']}")
        logger.info(f"   🌟 Nice-to-Haves: {buckets['nice_to_haves']}")
        logger.info(f"   🎁 Enrichment: {buckets['enrichment']}")
        
        # Convert to LLM format
        logger.info("\n🔄 Converting Stage 2 structured format to LLM format...")
        llm_data = convert_stage2_structured_to_llm_format(stage2_data)
        logger.info(f"✅ Converted to {len(llm_data['slots'])} slots (with bucket info)")
        journey_id = stage2_data.get('metadata', {}).get('journey_id', 'unknown')
        species = llm_data['slots'][0]['filters']['pc1'] if llm_data['slots'] else 'Unknown'
        logger.info(f"🐕 Pet ID: {llm_data['pet_id']} | Species: {species} (from journey: {journey_id})")
        
        # Save converted format temporarily
        temp_file = Path(stage2_output_file).parent / f"temp_llm_format_{Path(stage2_output_file).name}"
        with open(temp_file, 'w') as f:
            json.dump(llm_data, f, indent=2)
        
        # Initialize recommendation engine
        engine = ProductRecommendationEngine()
        
        logger.info("\n📊 Initializing recommendation engine...")
        stats = engine.initialize()
        
        logger.info(f"✅ Loaded {stats['total_products']:,} products")
        logger.info(f"   🐕 Dog products: {stats['dog_products']:,}")
        logger.info(f"   🐱 Cat products: {stats['cat_products']:,}")
        
        # Process recommendations
        logger.info(f"\n🔍 Generating product recommendations...")
        results = engine.process_file(str(temp_file))
        
        # Clean up temp file
        temp_file.unlink()
        
        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract journey info from Stage 2 metadata
        metadata = stage2_data.get("metadata", {})
        journey_id = metadata.get("journey_id", "unknown")
        month_idx = metadata.get("month_idx", 0)
        
        # Create output filename with short journey ID (consistent with Stage 1)
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        output_filename = f"recommendations_structured_{journey_short}_month{month_idx}_{timestamp}.json"
        
        # Save to backend/testing/outputs/recommendations_stage2_structured/ directory
        project_root = Path(__file__).parent.parent.parent.parent
        output_dir = project_root / "backend" / "testing" / "outputs" / "recommendations_stage2_structured"
        output_dir.mkdir(exist_ok=True)  # Create directory if it doesn't exist
        output_path = output_dir / output_filename
        
        # Add bucket information to results for organization
        for slot_result in results.get('results', []):
            slot_id = slot_result.get('slot_id')
            # Find original query to get bucket info
            for query in stage2_data['queries']:
                if stage2_data['queries'].index(query) == slot_id - 1:  # slot_id is 1-based
                    slot_result['bucket'] = query.get('bucket', 'enrichment')
                    break
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 STAGE 2 STRUCTURED RECOMMENDATIONS COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"📊 Pet ID: {results['pet_id']}")
        logger.info(f"📅 Month: {results['month']}")
        logger.info(f"🎯 Queries processed: {results['processed_slots']}")
        logger.info(f"🛍️  Unique products: {results['total_unique_products']}")
        logger.info(f"💾 Output saved: {output_path}")
        
        # Show sample results by bucket
        if results['results']:
            logger.info(f"\n📋 Sample results by bucket:")
            
            # Group by bucket
            by_bucket = {"essentials": [], "nice_to_haves": [], "enrichment": []}
            for slot_result in results['results']:
                bucket = slot_result.get('bucket', 'enrichment')
                if bucket in by_bucket:
                    by_bucket[bucket].append(slot_result)
            
            for bucket_name, slots in by_bucket.items():
                if slots:
                    icon = {"essentials": "🏥", "nice_to_haves": "🌟", "enrichment": "🎁"}[bucket_name]
                    logger.info(f"\n   {icon} {bucket_name.upper().replace('_', '-')}: {len(slots)} queries")
                    first_slot = slots[0]
                    logger.info(f"      Sample - {first_slot['top_family']}")
                    for product in first_slot['products'][:2]:  # Show first 2
                        logger.info(f"        {product['rank']}. {product['name'][:40]}... (sim: {product['similarity']:.3f})")
        
        logger.info(f"\n✅ Stage 2 structured recommendations ready! Check: {output_path}")
        
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

