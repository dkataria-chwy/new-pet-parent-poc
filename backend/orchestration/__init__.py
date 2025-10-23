"""
Pet Parent Journey Pipeline Orchestration

This module orchestrates the complete recommendation pipeline using LangGraph:
Stage 1 (Needs Analysis) → Stage 2 (Query Generation) → 
Stage 3 (Product Recommendations) → Stage 4 (Subscription Optimizer)

Designed for:
- UI-triggered recommendations
- Scheduled batch processing
- Manual CLI execution for testing
"""

from .run_full_pipeline import run_pipeline

__all__ = ["run_pipeline"]

