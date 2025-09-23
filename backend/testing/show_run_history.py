#!/usr/bin/env python3
"""
View the run history of all test executions
"""

from pathlib import Path

def show_run_history():
    outputs_dir = Path(__file__).parent / "outputs"
    run_history_file = outputs_dir / ".run_history"
    
    if not run_history_file.exists():
        print("📝 No run history found yet. Run some tests to create history!")
        return
    
    try:
        history = run_history_file.read_text().strip().split('\n')
        history = [line for line in history if line.strip()]
        
        if not history:
            print("📝 Run history is empty.")
            return
        
        print("📊 Test Run History (Latest First):")
        print("=" * 100)
        print(f"{'Timestamp':<15} {'Journey+Month':<50} {'Script':<20}")
        print("-" * 100)
        
        for line in history:
            parts = line.split()
            if len(parts) >= 3:
                timestamp = parts[0]
                journey_month = parts[1]
                script = parts[2]
                
                # Format timestamp for readability
                formatted_time = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
                
                # Truncate journey_month if too long for display
                display_journey = journey_month if len(journey_month) <= 48 else journey_month[:45] + "..."
                
                print(f"{formatted_time:<15} {display_journey:<50} {script:<20}")
        
        print("-" * 100)
        print(f"Total runs: {len(history)}")
        
    except Exception as e:
        print(f"❌ Error reading run history: {e}")

if __name__ == "__main__":
    show_run_history()
