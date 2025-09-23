#!/usr/bin/env python3
"""
View the production run history of all semantic query generations
"""

from pathlib import Path

def show_production_history():
    outputs_dir = Path(__file__).parent / "outputs"
    run_history_file = outputs_dir / ".run_history"
    
    if not run_history_file.exists():
        print("📝 No production run history found yet. Run some production queries to create history!")
        return
    
    try:
        history = run_history_file.read_text().strip().split('\n')
        history = [line for line in history if line.strip()]
        
        if not history:
            print("📝 Production run history is empty.")
            return
        
        print("🚀 Production Run History (Latest First):")
        print("=" * 100)
        print(f"{'Timestamp':<15} {'Journey+Month':<50} {'Type':<20}")
        print("-" * 100)
        
        for line in history:
            parts = line.split()
            if len(parts) >= 3:
                timestamp = parts[0]
                journey_month = parts[1]
                run_type = parts[2]
                
                # Format timestamp for readability
                formatted_time = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
                
                # Truncate journey_month if too long for display
                display_journey = journey_month if len(journey_month) <= 48 else journey_month[:45] + "..."
                
                # Add emoji for production runs
                type_display = "🚀 " + run_type if run_type == "production" else run_type
                
                print(f"{formatted_time:<15} {display_journey:<50} {type_display:<20}")
        
        print("-" * 100)
        print(f"Total production runs: {len(history)}")
        
        # Show file counts
        outputs_files = list(outputs_dir.glob("model_output_*.json"))
        print(f"Saved output files: {len(outputs_files)}")
        
    except Exception as e:
        print(f"❌ Error reading production run history: {e}")

if __name__ == "__main__":
    show_production_history()
