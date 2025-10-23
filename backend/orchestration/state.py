"""
Pipeline State Schema

Defines the state structure passed between LangGraph nodes.
Each stage updates specific fields as the pipeline progresses.
"""

from typing import TypedDict, Optional, Any, Dict, List


class PipelineState(TypedDict):
    """
    State object that flows through the entire recommendation pipeline.
    
    Input Fields (required at start):
        journey_id: Unique identifier for the pet parent journey
        month_idx: Current month in the journey (0-based)
    
    Stage 1 Fields (populated by needs analysis):
        stage1_output_path: File path to Stage 1 JSON output
        stage1_result: Dict containing structured needs analysis
    
    Stage 2 Fields (populated by query generation):
        stage2_output_path: File path to Stage 2 JSON output
        stage2_result: Dict containing generated search queries
    
    Stage 3 Fields (populated by product recommendations):
        recommendations_path: File path to recommendations JSON output
        recommendations_result: Dict containing recommended products
    
    Stage 4 Fields (populated by subscription optimizer):
        subscription_plan_path: File path to final subscription plan JSON
        subscription_plan_result: Dict containing subscription/one-time categorization
    
    Stage 5 Fields (populated by TTS concierge):
        tts_summary_path: File path to TTS summary JSON
        tts_summary: String containing the spoken welcome message
    
    Metadata Fields:
        error: Error message if any stage fails
        stage_timings: Dict tracking execution time per stage
        total_products_analyzed: Count of products processed
    """
    
    # Required inputs
    journey_id: str
    month_idx: int
    
    # Stage 1: Needs Analysis
    stage1_output_path: Optional[str]
    stage1_result: Optional[Dict[str, Any]]
    
    # Stage 2: Query Generation
    stage2_output_path: Optional[str]
    stage2_result: Optional[Dict[str, Any]]
    
    # Stage 3: Product Recommendations
    recommendations_path: Optional[str]
    recommendations_result: Optional[Dict[str, Any]]
    
    # Stage 4: Subscription Optimizer
    subscription_plan_path: Optional[str]
    subscription_plan_result: Optional[Dict[str, Any]]
    
    # Stage 5: TTS Concierge
    tts_summary_path: Optional[str]
    tts_summary: Optional[str]
    
    # Metadata
    error: Optional[str]
    stage_timings: Optional[Dict[str, float]]
    total_products_analyzed: Optional[int]

