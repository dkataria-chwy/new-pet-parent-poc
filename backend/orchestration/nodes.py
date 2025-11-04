"""
LangGraph Node Functions

Each node wraps a stage of the recommendation pipeline.
Nodes are pure functions that take state and return state updates.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from orchestration.state import PipelineState
from agents.semantic_query.run_stage1_structured import run_stage1_structured_analysis
from agents.semantic_query.run_stage2_structured import generate_queries
from agents.product_recommendations.run_stage2_structured_recommendations import (
    convert_stage2_structured_to_llm_format,
    get_pet_info_from_journey
)
from agents.product_recommendations.recommendation_engine import ProductRecommendationEngine
from agents.subscription_optimizer.run_subscription_optimizer import SubscriptionOptimizer
from agents.tts_concierge.run_tts_concierge import TTSConciergeAgent


# Production output base directory
OUTPUT_BASE = backend_dir / "agents" / "outputs"


def _log(stage: str, message: str):
    """Unified logging format for all nodes"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [{stage}] {message}")


def _find_latest_output(directory: Path, pattern: str) -> Path:
    """Find the most recently created file matching pattern"""
    files = list(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching {pattern} in {directory}")
    return max(files, key=lambda p: p.stat().st_mtime)


def stage1_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 1: Structured Needs Analysis
    
    Generates bucketed pet needs (essentials/nice-to-haves/enrichment)
    based on pet profile, journey context, and lifestage.
    
    Args:
        state: Pipeline state with journey_id and month_idx
    
    Returns:
        State updates with stage1_output_path and stage1_result
    """
    start_time = time.time()
    journey_id = state["journey_id"]
    month_idx = state["month_idx"]
    
    _log("STAGE 1", f"Starting needs analysis for journey {journey_id[:8]}, month {month_idx}")
    
    try:
        # Call the core Stage 1 function
        # It handles its own output saving to agents/outputs/stage1_structured/
        result = run_stage1_structured_analysis(
            journey_id=journey_id,
            month_idx=month_idx,
            output_base_dir=str(OUTPUT_BASE)
        )
        
        # Find the output file that was just created
        journey_short = journey_id[:8] if len(journey_id) > 8 else journey_id
        output_dir = OUTPUT_BASE / "stage1_structured"
        output_file = _find_latest_output(
            output_dir,
            f"stage1_structured_{journey_short}_month{month_idx}_*.json"
        )
        
        elapsed = time.time() - start_time
        _log("STAGE 1", f"✓ Completed in {elapsed:.1f}s")
        _log("STAGE 1", f"  Generated {len(result.get('needs', []))} needs")
        _log("STAGE 1", f"  Output: {output_file.name}")
        
        return {
            "stage1_output_path": str(output_file),
            "stage1_result": result,
            "stage_timings": {"stage1": elapsed}
        }
        
    except Exception as e:
        _log("STAGE 1", f"✗ Failed: {e}")
        return {"error": f"Stage 1 failed: {str(e)}"}


def stage2_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 2: Query Generation
    
    Converts Stage 1 needs into optimized search queries
    (embedding queries for vector search + BM25 queries for keyword matching).
    
    Args:
        state: Pipeline state with stage1_output_path
    
    Returns:
        State updates with stage2_output_path and stage2_result
    """
    # Check if previous stage failed
    if state.get("error"):
        _log("STAGE 2", "⏭️  Skipping due to previous error")
        return {}
    
    start_time = time.time()
    journey_id = state["journey_id"]
    month_idx = state["month_idx"]
    stage1_path = state.get("stage1_output_path")
    
    if not stage1_path:
        _log("STAGE 2", "✗ Failed: No Stage 1 output available")
        return {"error": "Stage 2 failed: No Stage 1 output"}
    
    _log("STAGE 2", f"Starting query generation for journey {journey_id[:8]}, month {month_idx}")
    _log("STAGE 2", f"  Input: {Path(stage1_path).name}")
    
    try:
        # Call the core Stage 2 function
        # It handles its own output saving to agents/outputs/stage2_structured/
        result = generate_queries(
            journey_id=journey_id,
            month_idx=month_idx,
            stage1_output_path=stage1_path,
            output_base_dir=str(OUTPUT_BASE)
        )
        
        # Find the output file that was just created
        journey_short = journey_id[:8] if len(journey_id) > 8 else journey_id
        output_dir = OUTPUT_BASE / "stage2_structured"
        output_file = _find_latest_output(
            output_dir,
            f"stage2_structured_queries_{journey_short}_month{month_idx}_*.json"
        )
        
        elapsed = time.time() - start_time
        _log("STAGE 2", f"✓ Completed in {elapsed:.1f}s")
        _log("STAGE 2", f"  Generated {len(result.get('queries', []))} search queries")
        _log("STAGE 2", f"  Output: {output_file.name}")
        
        # Update stage timings
        timings = state.get("stage_timings", {})
        timings["stage2"] = elapsed
        
        return {
            "stage2_output_path": str(output_file),
            "stage2_result": result,
            "stage_timings": timings
        }
        
    except Exception as e:
        _log("STAGE 2", f"✗ Failed: {e}")
        return {"error": f"Stage 2 failed: {str(e)}"}


def recommendations_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 3: Product Recommendations
    
    Runs vector search against product catalog using Stage 2 queries.
    Returns top-k products per slot with deduplication by parent SKU.
    
    Args:
        state: Pipeline state with stage2_output_path
    
    Returns:
        State updates with recommendations_path and recommendations_result
    """
    # Check if previous stage failed
    if state.get("error"):
        _log("STAGE 3", "⏭️  Skipping due to previous error")
        return {}
    
    start_time = time.time()
    journey_id = state["journey_id"]
    month_idx = state["month_idx"]
    stage2_path = state.get("stage2_output_path")
    
    if not stage2_path:
        _log("STAGE 3", "✗ Failed: No Stage 2 output available")
        return {"error": "Stage 3 failed: No Stage 2 output"}
    
    _log("STAGE 3", f"Starting product recommendations for journey {journey_id[:8]}, month {month_idx}")
    _log("STAGE 3", f"  Input: {Path(stage2_path).name}")
    
    try:
        # Load Stage 2 output
        with open(stage2_path, 'r') as f:
            stage2_data = json.load(f)
        
        # Convert to LLM format with species filtering
        _log("STAGE 3", "  Converting queries to recommendation format...")
        llm_data = convert_stage2_structured_to_llm_format(stage2_data)
        
        # Initialize recommendation engine
        _log("STAGE 3", "  Initializing recommendation engine...")
        engine = ProductRecommendationEngine()
        stats = engine.initialize()
        
        # Log initialization stats
        if stats.get('mode') == 'qdrant':
            if 'total_products' in stats:
                _log("STAGE 3", f"  Using Qdrant cloud ({stats['total_products']:,} products)")
            else:
                _log("STAGE 3", f"  Using Qdrant cloud vector database")
        else:
            _log("STAGE 3", f"  Loaded {stats['total_products']:,} products from catalog")
        
        # Save temporary LLM format file
        temp_file = OUTPUT_BASE / "stage2_structured" / f"temp_llm_format_{Path(stage2_path).name}"
        with open(temp_file, 'w') as f:
            json.dump(llm_data, f, indent=2)
        
        # Process recommendations
        _log("STAGE 3", f"  Running vector search for {len(llm_data['slots'])} slots...")
        results = engine.process_file(str(temp_file))
        
        # Clean up temp file
        temp_file.unlink()
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if len(journey_id) > 8 else journey_id
        output_dir = OUTPUT_BASE / "recommendations_stage2_structured"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean old outputs for this journey+month
        for file in output_dir.glob(f"recommendations_structured_{journey_short}_month{month_idx}_*.json"):
            _log("STAGE 3", f"  Removing old: {file.name}")
            file.unlink()
        
        output_filename = f"recommendations_structured_{journey_short}_month{month_idx}_{timestamp}.json"
        output_path = output_dir / output_filename
        
        # Add bucket information from Stage 2
        for slot_result in results.get('results', []):
            slot_id = slot_result.get('slot_id')
            # Find corresponding query to get bucket
            for i, query in enumerate(stage2_data['queries']):
                if i == slot_id - 1:  # slot_id is 1-based
                    slot_result['bucket'] = query.get('bucket', 'enrichment')
                    break
        
        # Add comprehensive metadata from Stage 2 (which inherited from Stage 1)
        stage2_metadata = stage2_data.get("metadata", {})
        results['metadata'] = {
            **stage2_metadata,  # Inherit journey_id, pet_id, month_idx, pet_name, pet_species
            "stage": "stage3_recommendations",
            "stage2_source": str(stage2_path),
            "generated_at": timestamp
        }
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        elapsed = time.time() - start_time
        _log("STAGE 3", f"✓ Completed in {elapsed:.1f}s")
        _log("STAGE 3", f"  Found {results['total_unique_products']} unique products")
        _log("STAGE 3", f"  Processed {results['processed_slots']} slots")
        _log("STAGE 3", f"  Output: {output_filename}")
        
        # Update stage timings
        timings = state.get("stage_timings", {})
        timings["stage3"] = elapsed
        
        return {
            "recommendations_path": str(output_path),
            "recommendations_result": results,
            "total_products_analyzed": results['total_unique_products'],
            "stage_timings": timings
        }
        
    except Exception as e:
        _log("STAGE 3", f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Stage 3 failed: {str(e)}"}


def optimizer_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 4: Subscription Optimizer
    
    Intelligently categorizes recommended products into:
    - Subscription: Daily/weekly consumables (food, treats, poop bags, etc.)
    - One-Time Purchase: Durables, seasonal items, setup essentials
    
    Args:
        state: Pipeline state with recommendations_path
    
    Returns:
        State updates with subscription_plan_path and subscription_plan_result
    """
    # Check if previous stage failed
    if state.get("error"):
        _log("STAGE 4", "⏭️  Skipping due to previous error")
        return {}
    
    start_time = time.time()
    journey_id = state["journey_id"]
    month_idx = state["month_idx"]
    recommendations_path = state.get("recommendations_path")
    
    if not recommendations_path:
        _log("STAGE 4", "✗ Failed: No recommendations available")
        return {"error": "Stage 4 failed: No recommendations"}
    
    _log("STAGE 4", f"Starting subscription optimization for journey {journey_id[:8]}, month {month_idx}")
    _log("STAGE 4", f"  Input: {Path(recommendations_path).name}")
    
    try:
        # Initialize optimizer
        templates_dir = backend_dir / "agents" / "subscription_optimizer" / "templates"
        optimizer = SubscriptionOptimizer(templates_dir)
        
        # Run optimization
        _log("STAGE 4", "  Analyzing products for subscription vs. one-time categorization...")
        result = optimizer.optimize(
            recommendations_path=Path(recommendations_path),
            order_history=None  # TODO: Load from database when available
        )
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8]
        output_dir = OUTPUT_BASE / "subscription_plans"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean old outputs for this journey+month
        for file in output_dir.glob(f"subscription_plan_{journey_short}*_month{month_idx}_*.json"):
            _log("STAGE 4", f"  Removing old: {file.name}")
            file.unlink()
        
        output_filename = f"subscription_plan_{journey_short}_month{month_idx}_{timestamp}.json"
        output_path = output_dir / output_filename
        
        # Save result
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        _log("STAGE 4", f"✓ Completed in {elapsed:.1f}s")
        _log("STAGE 4", f"  Subscription products: {len(result['subscription_products'])}")
        _log("STAGE 4", f"  One-time products: {len(result['one_time_products'])}")
        _log("STAGE 4", f"  Output: {output_filename}")
        
        # Update stage timings
        timings = state.get("stage_timings", {})
        timings["stage4"] = elapsed
        
        return {
            "subscription_plan_path": str(output_path),
            "subscription_plan_result": result,
            "stage_timings": timings
        }
        
    except Exception as e:
        _log("STAGE 4", f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Stage 4 failed: {str(e)}"}


def tts_concierge_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 5: TTS Concierge Summary
    
    Generates a personalized 20-30 second spoken welcome message
    for the monthly product selections.
    
    Args:
        state: Pipeline state with subscription_plan_path
    
    Returns:
        State updates with tts_summary_path and tts_summary
    """
    # Check if previous stage failed
    if state.get("error"):
        _log("STAGE 5", "⏭️  Skipping due to previous error")
        return {}
    
    start_time = time.time()
    journey_id = state["journey_id"]
    month_idx = state["month_idx"]
    subscription_plan_path = state.get("subscription_plan_path")
    
    if not subscription_plan_path:
        _log("STAGE 5", "✗ Failed: No subscription plan available")
        return {"error": "Stage 5 failed: No subscription plan"}
    
    _log("STAGE 5", f"Starting TTS concierge summary for journey {journey_id[:8]}, month {month_idx}")
    _log("STAGE 5", f"  Input: {Path(subscription_plan_path).name}")
    
    try:
        # Initialize agent
        templates_dir = backend_dir / "agents" / "tts_concierge" / "templates"
        agent = TTSConciergeAgent(templates_dir)
        
        # Generate summary
        _log("STAGE 5", "  Generating personalized spoken summary...")
        result = agent.generate_summary(
            subscription_plan_path=Path(subscription_plan_path)
        )
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8]
        output_dir = OUTPUT_BASE / "tts_summaries"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean old outputs for this journey+month (both JSON and MP3)
        for file in output_dir.glob(f"tts_summary_{journey_short}*_month{month_idx}_*.*"):
            _log("STAGE 5", f"  Removing old: {file.name}")
            file.unlink()
        
        base_filename = f"tts_summary_{journey_short}_month{month_idx}_{timestamp}"
        json_path = output_dir / f"{base_filename}.json"
        audio_path = output_dir / f"{base_filename}.mp3"
        
        # Save JSON (without binary audio_content)
        json_data = result.copy()
        audio_content = json_data.pop("audio_content", None)
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save audio file if generated
        if audio_content:
            with open(audio_path, 'wb') as f:
                f.write(audio_content)
            _log("STAGE 5", f"  Audio saved: {audio_path.name}")
        
        elapsed = time.time() - start_time
        _log("STAGE 5", f"✓ Completed in {elapsed:.1f}s")
        _log("STAGE 5", f"  Word count: {result['word_count']} words")
        _log("STAGE 5", f"  Summary: {result['tts_summary'][:80]}...")
        _log("STAGE 5", f"  Output: {json_path.name}")
        
        # Update stage timings
        timings = state.get("stage_timings", {})
        timings["stage5"] = elapsed
        
        return {
            "tts_summary_path": str(json_path),
            "tts_audio_path": str(audio_path) if audio_content else None,
            "tts_summary": result['tts_summary'],
            "stage_timings": timings
        }
        
    except Exception as e:
        _log("STAGE 5", f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Stage 5 failed: {str(e)}"}

