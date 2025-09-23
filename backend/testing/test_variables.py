#!/usr/bin/env python3
"""
Test script for variables.py
Tests the order_history extraction and variable mapping
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
from agents.semantic_query.variables import build_prompt_variables

def test_variables():
    print("🔍 Testing Variables Mapping...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    journey_id = input("Enter a journey_id to test: ").strip()
    month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    
    # Smart clearing: only remove variables files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting variables files for {journey_short}_month{month_idx}...")
    # Remove variables and order_history files for this exact journey+month combination
    for file in outputs_dir.glob("variables_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
        elif file.name.startswith(f"variables_{journey_short}_") and "month" not in file.name:
            print(f"  Removing old format (no month specified): {file.name}")
            file.unlink()
    for file in outputs_dir.glob("order_history_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
        elif file.name.startswith(f"order_history_{journey_short}_") and "month" not in file.name:
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
    new_entry = f"{timestamp} {current_run} variables"
    history.insert(0, new_entry)
    
    # Keep only last 50 entries to prevent file from growing too large
    history = history[:50]
    
    # Write back to file
    run_history_file.write_text('\n'.join(history) + '\n')
    
    try:
        # First get the context
        print("\n1️⃣ Building context...")
        context = build_generation_context(journey_id=journey_id, month_idx=month_idx)
        
        # Then test the variables mapping
        print("\n2️⃣ Mapping variables...")
        variables = build_prompt_variables(context)

        # Save outputs for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"

        # Clean variables for readability
        variables_clean = {}
        for key, value in variables.items():
            if key.endswith('_json'):
                try:
                    variables_clean[key] = json.loads(value)
                except Exception:
                    variables_clean[key] = value
            else:
                variables_clean[key] = value

        variables_file = outputs_dir / f"variables_{journey_short}_month{month_idx}_{timestamp}.json"
        variables_file.write_text(json.dumps(variables_clean, indent=2, default=str), encoding="utf-8")

        # Save order history separately
        order_history = variables_clean.get("order_history_json", [])
        order_history_file = outputs_dir / f"order_history_{journey_short}_month{month_idx}_{timestamp}.json"
        order_history_file.write_text(json.dumps(order_history, indent=2, default=str), encoding="utf-8")
        print(f"\n💾 Saved variables to: {variables_file}")
        print(f"💾 Saved order history to: {order_history_file}")
        
        print("\n✅ Variables Mapping Success!")
        print("\n📊 Variable Keys:")
        for key in variables.keys():
            print(f"- {key}")
        
        print("\n🎯 Key Variable Contents:")
        
        # Parse and show order_history
        order_history = json.loads(variables["order_history_json"])
        print(f"\n📋 Order History ({len(order_history)} months):")
        for month_data in order_history:
            month = month_data["month"]
            decisions_count = len(month_data["decisions"])
            accepted = len(month_data["summary"]["accepted"])
            skipped = len(month_data["summary"]["skipped"])
            print(f"  Month {month}: {decisions_count} decisions ({accepted} accepted, {skipped} skipped)")
        
        # Parse and show pet profile
        pet_profile = json.loads(variables["pet_profile_json"])
        print(f"\n🐕 Pet Profile:")
        print(f"  Species: {pet_profile.get('species')}")
        print(f"  Age: {pet_profile.get('age_months')} months")
        print(f"  Allergies: {pet_profile.get('allergies')}")
        
        # Parse and show weather
        weather = json.loads(variables["weather_json"])
        print(f"\n🌤️ Weather:")
        print(f"  Alerts: {len(weather.get('alerts', []))}")
        print(f"  Forecast days: {len(weather.get('daily', []))}")
        
        # Parse and show calendar
        calendar = json.loads(variables["calendar_json"])
        print(f"\n📅 Calendar:")
        print(f"  Events: {len(calendar.get('events', []))}")
        
        # Parse and show catalog filters
        catalog_filters = json.loads(variables["catalog_filters_json"])
        print(f"\n🗂️ Catalog Filters:")
        print(f"  PC1: {catalog_filters.get('pc1')}")
        
        print(f"\n📄 Full Variables JSON:")
        for key, value in variables.items():
            print(f"\n{key}:")
            print(value)
            
    except Exception as e:
        print(f"❌ Variables Mapping Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_variables()
