"""
Product Recommendations Agent

Processes LLM-generated slots and returns ranked product recommendations
using vector search with smart filtering.
"""

from .recommendation_engine import ProductRecommendationEngine

__all__ = ['ProductRecommendationEngine']
