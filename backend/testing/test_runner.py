#!/usr/bin/env python3
"""
Test script for runner.py
Tests the full end-to-end semantic query generation
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

from agents.semantic_query.runner import compose_queries

def test_runner():
    print("🔍 Testing Full Pipeline (Runner)...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    journey_id = input("Enter a journey_id to test: ").strip()
    month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    
    # Smart clearing: only remove model output files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting model output files for {journey_short}_month{month_idx}...")
    # Remove model output files for this exact journey+month combination
    for file in outputs_dir.glob("model_output_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
    
    # Update run history
    run_history_file = outputs_dir / ".run_history"
    current_run = f"{journey_short}_month{month_idx}"
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
    history = [line for line in history if not line.split()[1] == current_run]
    
    # Add new entry at the top (latest first)
    new_entry = f"{timestamp} {current_run} runner"
    history.insert(0, new_entry)
    
    # Keep only last 50 entries to prevent file from growing too large
    history = history[:50]
    
    # Write back to file
    run_history_file.write_text('\n'.join(history) + '\n')
    
    try:
        print(f"\n🚀 Running full semantic query generation...")
        print(f"Journey ID: {journey_id}")
        print(f"Month Index: {month_idx}")
        
        result = compose_queries(journey_id=journey_id, month_idx=month_idx)

        # Save outputs for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        output_file = outputs_dir / f"model_output_{journey_short}_month{month_idx}_{timestamp}.json"
        
        # Attempt to write JSON result; if not JSON, write raw string
        try:
            if isinstance(result, str):
                parsed = json.loads(result)
            else:
                parsed = result
            output_file.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
        except Exception:
            output_file.write_text(str(result), encoding="utf-8")
        print(f"\n💾 Saved model output to: {output_file}")
        
        print("\n✅ Full Pipeline Success!")
        
        # Parse and display the result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
                print(f"\n📊 Generated Query Structure:")
                
                slots = parsed_result.get("slots", [])
                print(f"Total Slots: {len(slots)}")
                
                for i, slot in enumerate(slots):
                    print(f"\nSlot {i+1}:")
                    print(f"  Top Family: {slot.get('top_family')}")
                    print(f"  Family: {slot.get('family')}")
                    print(f"  Intent Route: {slot.get('intent_route')}")
                    print(f"  Embedding Query: {slot.get('embedding_query', '')[:100]}...")
                    print(f"  BM25 Query: {slot.get('bm25_query')}")
                    print(f"  Top K: {slot.get('top_k')}")
                
                evidence = parsed_result.get("evidence", {})
                print(f"\nEvidence Used:")
                for source, items in evidence.items():
                    if items:
                        print(f"  {source}: {items}")
                
                print(f"\n📄 Full Generated JSON:")
                print(json.dumps(parsed_result, indent=2))
                
            except json.JSONDecodeError:
                print(f"\n📄 Raw Result (not valid JSON):")
                print(result)
        else:
            print(f"\n📄 Result:")
            print(result)
            
    except Exception as e:
        print(f"❌ Full Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_runner()
