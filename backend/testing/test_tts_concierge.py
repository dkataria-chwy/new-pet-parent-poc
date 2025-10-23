#!/usr/bin/env python3
"""
Test script for TTS Concierge Summary Generation (Stage 5)
Tests the TTS summary generation from Stage 4 subscription plan
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

from agents.tts_concierge.run_tts_concierge import TTSConciergeAgent

def test_tts_concierge_runner(subscription_plan_path=None):
    print("🎤 Testing TTS Concierge Summary Generation...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    if subscription_plan_path is None:
        subscription_plan_filename = input("Enter subscription plan filename (e.g., subscription_plan_91b7aa35_month0_20251013_103046.json): ").strip()
        subscription_plan_path = f"agents/outputs/subscription_plans/{subscription_plan_filename}"
    
    subscription_plan_path = Path(subscription_plan_path)
    if not subscription_plan_path.exists():
        print(f"❌ Subscription plan not found: {subscription_plan_path}")
        return
    
    # Load plan to get journey info
    with open(subscription_plan_path) as f:
        plan_data = json.load(f)
    
    metadata = plan_data.get("metadata", {})
    journey_id = metadata.get("journey_id", "unknown")
    month_idx = metadata.get("month_idx", 0)
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting TTS summary for {journey_short}_month{month_idx}...")
    # Remove old TTS summaries for this exact journey+month combination
    tts_dir = outputs_dir / "tts_summaries"
    tts_dir.mkdir(exist_ok=True)
    for file in tts_dir.glob("tts_summary_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
    
    try:
        print(f"\n🚀 Running TTS Concierge Summary Generation...")
        print(f"Journey ID: {journey_id}")
        print(f"Month Index: {month_idx}")
        print(f"Subscription Plan: {subscription_plan_path.name}")
        
        # Initialize agent
        templates_dir = backend_dir / "agents" / "tts_concierge" / "templates"
        agent = TTSConciergeAgent(templates_dir)
        
        # Generate summary
        result = agent.generate_summary(subscription_plan_path)

        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = tts_dir / f"tts_summary_{journey_short}_month{month_idx}_{timestamp}.json"
        
        # Write JSON result
        output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n💾 Saved TTS summary to: {output_file}")
        
        print("\n✅ TTS Concierge Summary Generation Success!")
        
        # Display the result
        print("\n" + "="*80)
        print("🎤 TTS SUMMARY (SPOKEN TEXT)")
        print("="*80)
        print(f"\n{result['tts_summary']}")
        print("\n" + "="*80)
        
        print(f"\n📊 Summary Metrics:")
        print(f"  • Word Count: {result['word_count']} words")
        print(f"  • Target Range: 50-75 words")
        if result['word_count'] < 50:
            print(f"  ⚠️  WARNING: Summary is shorter than target (50 words)")
        elif result['word_count'] > 75:
            print(f"  ⚠️  WARNING: Summary is longer than target (75 words)")
        else:
            print(f"  ✅ Word count within target range")
        
        print(f"\n⏱️  Generation Time: {result['metadata']['elapsed_seconds']}s")
        print(f"🤖 Model Used: {result['metadata']['model']}")
        print(f"🎫 Total Tokens: {result['metadata']['tokens']['total']}")
        
        print(f"\n📄 Full JSON saved to: {output_file}")
        print(f"\nView with: cat {output_file}")
            
    except Exception as e:
        print(f"❌ TTS Concierge Summary Generation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Accept command line arguments
    if len(sys.argv) >= 2:
        # If full path provided, use as-is; if just filename, prepend path
        plan_path = sys.argv[1] if "/" in sys.argv[1] else f"agents/outputs/subscription_plans/{sys.argv[1]}"
        test_tts_concierge_runner(plan_path)
    else:
        test_tts_concierge_runner()

