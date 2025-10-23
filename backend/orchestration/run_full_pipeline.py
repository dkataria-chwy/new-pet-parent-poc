#!/usr/bin/env python3
"""
Full Pipeline Orchestrator using LangGraph

Orchestrates the complete pet product recommendation pipeline:
Stage 1 (Needs) → Stage 2 (Queries) → Stage 3 (Recommendations) → Stage 4 (Optimizer)

Execution Modes:
1. CLI: python run_full_pipeline.py <journey_id> <month_idx>
2. API: from orchestration import run_pipeline; run_pipeline(journey_id, month_idx)
3. Scheduled: Cron job or scheduler calls run_pipeline()

All intermediate outputs are saved to backend/agents/outputs/ for analysis.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from langgraph.graph import StateGraph, END
from orchestration.state import PipelineState
from orchestration.nodes import (
    stage1_node,
    stage2_node,
    recommendations_node,
    optimizer_node,
    tts_concierge_node
)


def _log(message: str):
    """Console logging with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")


def build_pipeline_graph() -> StateGraph:
    """
    Build the LangGraph workflow.
    
    Graph Structure:
        START → Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 5 → END
    
    Each node is a pure function that:
    - Takes PipelineState as input
    - Returns state updates (partial dict)
    - Handles its own error logging
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize graph with state schema
    workflow = StateGraph(PipelineState)
    
    # Add nodes (agent functions)
    workflow.add_node("stage1_needs_analysis", stage1_node)
    workflow.add_node("stage2_query_generation", stage2_node)
    workflow.add_node("stage3_product_recommendations", recommendations_node)
    workflow.add_node("stage4_subscription_optimizer", optimizer_node)
    workflow.add_node("stage5_tts_concierge", tts_concierge_node)
    
    # Define sequential flow
    workflow.set_entry_point("stage1_needs_analysis")
    workflow.add_edge("stage1_needs_analysis", "stage2_query_generation")
    workflow.add_edge("stage2_query_generation", "stage3_product_recommendations")
    workflow.add_edge("stage3_product_recommendations", "stage4_subscription_optimizer")
    workflow.add_edge("stage4_subscription_optimizer", "stage5_tts_concierge")
    workflow.add_edge("stage5_tts_concierge", END)
    
    # Compile the graph
    return workflow.compile()


def run_pipeline(journey_id: str, month_idx: int) -> Dict[str, Any]:
    """
    Execute the complete recommendation pipeline.
    
    This is the main entry point for all execution modes (UI, scheduler, CLI).
    
    Args:
        journey_id: Unique identifier for the pet parent journey
        month_idx: Current month in the journey (0-based, so Month 1 = 0)
    
    Returns:
        Dict containing:
        - success: bool
        - subscription_plan_path: Path to final output JSON
        - subscription_plan_result: Full subscription plan data
        - stage_timings: Dict of execution times per stage
        - error: Error message if failed
    
    Example:
        >>> result = run_pipeline("a11a5c83-063d-48c2-86de-453f235448f3", 0)
        >>> if result["success"]:
        >>>     print(f"Subscription plan: {result['subscription_plan_path']}")
    """
    _log("="*80)
    _log("🚀 STARTING FULL RECOMMENDATION PIPELINE")
    _log("="*80)
    _log(f"Journey ID: {journey_id}")
    _log(f"Month Index: {month_idx}")
    _log(f"Execution Mode: {'CLI' if __name__ == '__main__' else 'Programmatic'}")
    _log("")
    
    start_time = datetime.now()
    
    try:
        # Build the LangGraph workflow
        _log("Building LangGraph workflow...")
        app = build_pipeline_graph()
        _log("✓ Graph compiled successfully")
        _log("")
        
        # Initialize state with inputs
        initial_state: PipelineState = {
            "journey_id": journey_id,
            "month_idx": month_idx,
            "stage1_output_path": None,
            "stage1_result": None,
            "stage2_output_path": None,
            "stage2_result": None,
            "recommendations_path": None,
            "recommendations_result": None,
            "subscription_plan_path": None,
            "subscription_plan_result": None,
            "error": None,
            "stage_timings": {},
            "total_products_analyzed": None
        }
        
        # Execute the graph
        _log("Executing pipeline...")
        _log("")
        final_state = app.invoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            _log("")
            _log("="*80)
            _log("❌ PIPELINE FAILED")
            _log("="*80)
            _log(f"Error: {final_state['error']}")
            
            return {
                "success": False,
                "error": final_state["error"]
            }
        
        # Success!
        elapsed_total = (datetime.now() - start_time).total_seconds()
        
        _log("")
        _log("="*80)
        _log("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        _log("="*80)
        _log(f"Total execution time: {elapsed_total:.1f}s")
        _log("")
        _log("⏱️  Stage Timings:")
        stage_timings = final_state.get("stage_timings", {})
        _log(f"  📊 Stage 1 (Needs Analysis):      {stage_timings.get('stage1', 0):>6.1f}s")
        _log(f"  🔍 Stage 2 (Query Generation):    {stage_timings.get('stage2', 0):>6.1f}s")
        _log(f"  🛍️  Stage 3 (Recommendations):     {stage_timings.get('stage3', 0):>6.1f}s")
        _log(f"  📦 Stage 4 (Subscription Opt):    {stage_timings.get('stage4', 0):>6.1f}s")
        _log(f"  🎤 Stage 5 (TTS Summary):         {stage_timings.get('stage5', 0):>6.1f}s")
        _log(f"  {'─' * 40}")
        _log(f"  ⏰ Total Pipeline Time:           {elapsed_total:>6.1f}s ({elapsed_total/60:.1f} min)")
        _log("")
        _log("Output Files:")
        _log(f"  Stage 1: {Path(final_state['stage1_output_path']).name}")
        _log(f"  Stage 2: {Path(final_state['stage2_output_path']).name}")
        _log(f"  Stage 3: {Path(final_state['recommendations_path']).name}")
        _log(f"  Stage 4: {Path(final_state['subscription_plan_path']).name}")
        _log(f"  Stage 5: {Path(final_state['tts_summary_path']).name}")
        _log("")
        _log(f"📊 Products Analyzed: {final_state.get('total_products_analyzed', 0)}")
        _log(f"📦 Subscription Products: {len(final_state['subscription_plan_result']['subscription_products'])}")
        _log(f"🛒 One-Time Products: {len(final_state['subscription_plan_result']['one_time_products'])}")
        _log(f"🎤 TTS Summary: {final_state.get('tts_summary', '')[:80]}...")
        _log("")
        _log(f"🎯 Final Output: {final_state['subscription_plan_path']}")
        _log(f"🎤 TTS Output: {final_state['tts_summary_path']}")
        
        # Save subscription plan to database for persistence
        _log("")
        _log("💾 Saving subscription plan to database...")
        try:
            from database import db
            
            # Add TTS summary to the subscription plan data
            plan_data_with_tts = final_state["subscription_plan_result"].copy()
            plan_data_with_tts["tts_summary"] = final_state.get("tts_summary", "")
            
            db.save_subscription_plan(
                journey_id=journey_id,
                month_idx=month_idx,
                plan_data=plan_data_with_tts
            )
            _log("✓ Subscription plan (with TTS) saved to database")
        except Exception as db_error:
            _log(f"⚠️  Warning: Failed to save to database: {db_error}")
            # Non-fatal error - continue execution
        
        _log("="*80)
        
        return {
            "success": True,
            "subscription_plan_path": final_state["subscription_plan_path"],
            "subscription_plan_result": final_state["subscription_plan_result"],
            "stage_timings": final_state.get("stage_timings", {}),
            "total_products_analyzed": final_state.get("total_products_analyzed", 0),
            "intermediate_outputs": {
                "stage1": final_state["stage1_output_path"],
                "stage2": final_state["stage2_output_path"],
                "stage3": final_state["recommendations_path"]
            }
        }
        
    except Exception as e:
        _log("")
        _log("="*80)
        _log("❌ PIPELINE FAILED WITH EXCEPTION")
        _log("="*80)
        _log(f"Error: {e}")
        
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """
    CLI entry point for manual testing.
    
    Usage:
        python run_full_pipeline.py <journey_id> <month_idx>
    
    Example:
        python run_full_pipeline.py a11a5c83-063d-48c2-86de-453f235448f3 0
    """
    parser = argparse.ArgumentParser(
        description="Run the complete pet product recommendation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run for journey a11a5c83 at month 1 (index 0)
  python run_full_pipeline.py a11a5c83-063d-48c2-86de-453f235448f3 0
  
  # Run for month 2 (index 1)
  python run_full_pipeline.py a11a5c83-063d-48c2-86de-453f235448f3 1

Output:
  All intermediate files saved to backend/agents/outputs/
  Final subscription plan includes 15 subscription + 15 one-time products
        """
    )
    
    parser.add_argument(
        "journey_id",
        help="Pet parent journey ID (UUID)"
    )
    
    parser.add_argument(
        "month_idx",
        type=int,
        help="Month index (0-based, so Month 1 = 0)"
    )
    
    args = parser.parse_args()
    
    # Run the pipeline
    result = run_pipeline(args.journey_id, args.month_idx)
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

