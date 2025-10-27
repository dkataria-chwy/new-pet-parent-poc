#!/usr/bin/env python3
"""
Test script for context_builder.py
Tests data fetching from database and external tools
"""

import sys
import json
import os
import shutil
from pathlib import Path
from datetime import datetime

# Change to backend directory so database path works correctly
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Add backend to path  
sys.path.insert(0, str(backend_dir))

from agents.semantic_query.context_builder import build_generation_context

def test_context_builder():
    print("🔍 Testing Context Builder...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # You'll need to provide actual journey_id from your database
    journey_id = input("Enter a journey_id to test (or 'demo' for mock): ").strip()
    
    if journey_id == 'demo':
        print("❌ Demo mode not implemented. Please provide a real journey_id from your database.")
        return
    
    month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    
    # Smart clearing: only remove context files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting context files for {journey_short}_month{month_idx}...")
    # Remove context files for this exact journey+month combination
    for file in outputs_dir.glob("context_*.json"):
        # Check for new format: journey_monthX_ pattern
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
        # Check for old format files that belong to this journey
        elif file.name.startswith(f"context_{journey_short}_") and "month" not in file.name:
            # Old format files don't specify month, so they match any month for same journey
            print(f"  Removing old format (no month specified): {file.name}")
            file.unlink()
    
    # Update run history
    run_history_file = outputs_dir / ".run_history"
    current_run = f"{journey_id}_month{month_idx}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Read existing history
    history = []
    if run_history_file.exists():
        try:
            history = run_history_file.read_text().strip().split('\n')
            history = [line for line in history if line.strip()]  # Remove empty lines
        except:
            history = []
    
    # Remove old entries for same journey+month (if any)
    history = [line for line in history if len(line.split()) >= 2 and line.split()[1] != current_run]
    
    # Add new entry at the top (latest first)
    new_entry = f"{timestamp} {current_run} context_builder"
    history.insert(0, new_entry)
    
    # Keep only last 50 entries to prevent file from growing too large
    history = history[:50]
    
    # Write back to file
    run_history_file.write_text('\n'.join(history) + '\n')
    
    try:
        context = build_generation_context(journey_id=journey_id, month_idx=month_idx)

        # Save outputs for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        context_file = outputs_dir / f"context_{journey_short}_month{month_idx}_{timestamp}.json"
        context_file.write_text(json.dumps(context, indent=2, default=str), encoding="utf-8")
        print(f"\n💾 Saved context to: {context_file}")
        
        print("\n✅ Context Builder Success!")
        print("\n📊 Context Structure:")
        
        # Pretty print the context
        for key, value in context.items():
            print(f"- {key}: {type(value).__name__}")
            if key == "pet":
                print(f"  Pet: {value.get('name')} ({value.get('species')}, {value.get('ageMonths')}mo)")
            elif key == "journey":
                decisions_count = len(value.get('decisions', {}))
                print(f"  Journey: {decisions_count} months of decisions")
            elif key == "weather":
                if value:
                    alerts = len(value.get('alerts', []))
                    forecast = len(value.get('forecast', []))
                    print(f"  Weather: {alerts} alerts, {forecast} forecast days")
                else:
                    print("  Weather: None (likely zip code issue)")
            elif key == "calendar":
                if value:
                    events = len(value.get('events', []))
                    print(f"  Calendar: {events} events")
                else:
                    print("  Calendar: None")
        
        print(f"\n📄 Full Context JSON:")
        print(json.dumps(context, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Context Builder Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_builder()
