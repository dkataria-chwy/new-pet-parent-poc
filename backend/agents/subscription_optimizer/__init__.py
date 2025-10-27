"""
Subscription Optimizer Agent

Intelligently categorizes recommended products into:
- Subscription (recurring auto-ship for consumables)
- One-Time Purchase (durables, seasonal items, setup essentials)
"""

from .run_subscription_optimizer import SubscriptionOptimizer

__all__ = ["SubscriptionOptimizer"]
