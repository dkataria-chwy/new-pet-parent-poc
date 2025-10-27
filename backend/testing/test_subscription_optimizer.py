#!/usr/bin/env python3
"""
Test script for Subscription Optimizer Agent
Tests subscription vs. one-time purchase optimization on recommendations
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Change to backend directory so database path works correctly
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, str(backend_dir))

from agents.subscription_optimizer.run_subscription_optimizer import SubscriptionOptimizer


def test_subscription_optimizer(journey_id=None, month_idx=None, recommendations_path=None):
    """Run subscription optimizer test"""
    print("🔍 Testing Subscription Optimizer...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # Get inputs
    if recommendations_path is None:
        if journey_id is None:
            journey_id = input("Enter a journey_id to test: ").strip()
        if month_idx is None:
            month_idx = int(input("Enter month index (0-based): ").strip() or "0")
        
        recommendations_filename = input("Enter recommendations filename (e.g., recommendations_structured_a11a5c83_month1_20251008_132711.json): ").strip()
        recommendations_path = f"testing/outputs/recommendations_stage2_structured/{recommendations_filename}"
    
    recommendations_path = Path(recommendations_path)
    
    if not recommendations_path.exists():
        print(f"❌ Recommendations file not found: {recommendations_path}")
        sys.exit(1)
    
    # Smart clearing: remove subscription_plans output files for this exact journey+month combination
    if journey_id:
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        print(f"🔄 Overwriting subscription_plans for {journey_short}_month{month_idx}...")
        
        subscription_plans_dir = outputs_dir / "subscription_plans"
        subscription_plans_dir.mkdir(exist_ok=True)
        for file in subscription_plans_dir.glob("subscription_plan_*.json"):
            if f"{journey_short}" in file.name and f"month{month_idx}_" in file.name:
                print(f"  Removing: {file.name}")
                file.unlink()
    
    # Initialize optimizer
    templates_dir = backend_dir / "agents" / "subscription_optimizer" / "templates"
    optimizer = SubscriptionOptimizer(templates_dir)
    
    # Sample order history (empty for now - in production, load from database)
    order_history = []
    
    # Run optimization
    try:
        print(f"\n🚀 Running subscription optimization...")
        print(f"Recommendations: {recommendations_path.name}")
        
        result = optimizer.optimize(
            recommendations_path=recommendations_path,
            order_history=order_history
        )
        
        # Save result (optimizer already saves, but we track it here too)
        output_dir = outputs_dir / "subscription_plans"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        journey_id = result["metadata"]["journey_id"]
        month_idx = result["metadata"]["month_idx"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"subscription_plan_{journey_id}_month{month_idx}_{timestamp}.json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved subscription plan to: {output_path}")
        
        print("\n✅ Subscription Optimization Success!")
        
        # Display summary
        print(f"\n📊 Optimization Summary:")
        print(f"Journey ID: {result['metadata']['journey_id']}")
        print(f"Month: {result['metadata']['month_idx']}")
        print(f"Model: {result['metadata']['model']}")
        print(f"Tokens: {result['metadata']['tokens']['total']:,}")
        print(f"Time: {result['metadata']['elapsed_seconds']}s")
        
        print(f"\n🔄 SUBSCRIPTION PRODUCTS ({len(result['subscription_products'])} items):")
        for i, product in enumerate(result['subscription_products'], 1):
            print(f"\n{i}. {product['product_name']}")
            print(f"   Category: {product['top_family']} ({product['bucket']})")
            print(f"   Frequency: {product['estimated_frequency']}")
            print(f"   Rationale: {product['subscription_rationale'][:100]}...")
            if product.get('personalized_note'):
                print(f"   Note: {product['personalized_note'][:80]}...")
        
        print(f"\n🛒 ONE-TIME PURCHASE PRODUCTS ({len(result['one_time_products'])} items):")
        for i, product in enumerate(result['one_time_products'], 1):
            print(f"\n{i}. {product['product_name']}")
            print(f"   Category: {product['top_family']} ({product['bucket']})")
            print(f"   Rationale: {product['one_time_rationale'][:100]}...")
            if product.get('personalized_note'):
                print(f"   Note: {product['personalized_note'][:80]}...")
        
        print(f"\n💡 OVERALL STRATEGY:")
        print(f"{result['overall_strategy']}")
        
        # Quality checks
        print(f"\n🔎 Quality Checks:")
        
        # Check item counts
        sub_count = len(result['subscription_products'])
        one_count = len(result['one_time_products'])
        if sub_count == 15:
            print(f"  ✅ Subscription count: {sub_count} (target: 15)")
        else:
            print(f"  ⚠️  Subscription count: {sub_count} (target: 15)")
        
        if one_count == 15:
            print(f"  ✅ One-time count: {one_count} (target: 15)")
        else:
            print(f"  ⚠️  One-time count: {one_count} (target: 15)")
        
        # Check for variety in subscriptions
        subscription_families = [p['top_family'] for p in result['subscription_products']]
        unique_families = len(set(subscription_families))
        if unique_families >= 3:
            print(f"  ✅ Subscription variety: {unique_families} unique categories")
        else:
            print(f"  ⚠️  Subscription variety: {unique_families} unique categories (aim for 3+)")
        
        # Check for personalized notes
        has_notes = all(p.get('personalized_note') for p in result['subscription_products'] + result['one_time_products'])
        if has_notes:
            print(f"  ✅ All products have personalized notes")
        else:
            print(f"  ⚠️  Some products missing personalized notes")
        
        print(f"\n📄 Full JSON saved to: {output_path}")
        print(f"\nView with: cat {output_path}")
            
    except Exception as e:
        print(f"❌ Subscription Optimization Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Accept command line arguments (flexible like Stage 2)
    if len(sys.argv) >= 4:
        # If full path provided, use as-is; if just filename, prepend path
        rec_path = sys.argv[3] if "/" in sys.argv[3] else f"testing/outputs/recommendations_stage2_structured/{sys.argv[3]}"
        test_subscription_optimizer(sys.argv[1], int(sys.argv[2]), rec_path)
    elif len(sys.argv) == 2:
        # Just recommendations path - auto-prepend if just filename
        rec_path = sys.argv[1] if "/" in sys.argv[1] else f"testing/outputs/recommendations_stage2_structured/{sys.argv[1]}"
        test_subscription_optimizer(recommendations_path=rec_path)
    else:
        test_subscription_optimizer()
