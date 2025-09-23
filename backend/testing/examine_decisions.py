#!/usr/bin/env python3
"""
Examine actual decision data in the database
"""

import sys
import sqlite3
import json
from pathlib import Path

def examine_decisions():
    db_path = str(Path(__file__).parent.parent / "chewy_journey.db")
    print(f"🔍 Examining decision data in: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get journeys with non-empty decisions
        cursor.execute("""
            SELECT id, pet_id, current, decisions
            FROM journeys 
            WHERE decisions != '{}' AND decisions IS NOT NULL
            ORDER BY LENGTH(decisions) DESC
            LIMIT 5
        """)
        
        journeys = cursor.fetchall()
        
        if not journeys:
            print("❌ No journeys with decision data found")
            conn.close()
            return
        
        print(f"✅ Found {len(journeys)} journeys with decision data:")
        
        for journey_id, pet_id, current, decisions_json in journeys:
            print(f"\n📋 Journey: {journey_id}")
            print(f"   Current Month: {current}")
            
            try:
                decisions = json.loads(decisions_json)
                print(f"   Raw Decisions: {decisions}")
                
                # Count actual decisions
                total_decisions = 0
                for month_key, month_data in decisions.items():
                    if isinstance(month_data, dict):
                        total_decisions += len(month_data)
                    
                print(f"   Total Decision Count: {total_decisions}")
                
                # Show structure
                for month_key, month_data in decisions.items():
                    print(f"   Month {month_key}: {month_data}")
                    
            except Exception as e:
                print(f"   Error parsing decisions: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    examine_decisions()
