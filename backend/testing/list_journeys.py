#!/usr/bin/env python3
"""
Quick script to list available journeys in the database
"""

import sys
import sqlite3
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db

def list_journeys():
    print("🔍 Finding available journeys in database...")
    
    try:
        # Ensure we use the correct database path
        db_path = str(Path(__file__).parent.parent / "chewy_journey.db")
        conn = sqlite3.connect(db_path)
        print(f"📁 Using database: {db_path}")
        cursor = conn.cursor()
        
        # First, get basic table counts
        cursor.execute("SELECT COUNT(*) FROM pets")
        pet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM journeys")
        journey_count = cursor.fetchone()[0]
        
        print(f"📊 Database summary: {pet_count} pets, {journey_count} journeys")
        
        if journey_count == 0:
            print("❌ No journeys found in database")
            print("💡 You need to create a pet and journey first through the frontend")
            conn.close()
            return
        
        # Get all journeys first
        cursor.execute("""
            SELECT id, pet_id, current, total_months, decisions
            FROM journeys
            ORDER BY current DESC, id
        """)
        
        journeys = cursor.fetchall()
        
        print(f"✅ Found {len(journeys)} journeys:")
        print()
        
        for journey_row in journeys:
            journey_id, pet_id, current, total_months, decisions_json = journey_row
            
            # Get pet info separately
            cursor.execute("""
                SELECT name, species, breed, age_months
                FROM pets 
                WHERE id = ?
            """, (pet_id,))
            
            pet_row = cursor.fetchone()
            if pet_row:
                pet_name, species, breed, age_months = pet_row
            else:
                pet_name, species, breed, age_months = "Unknown", "Unknown", "Unknown", 0
            
            # Parse decisions to count months with data
            try:
                decisions = json.loads(decisions_json) if decisions_json else {}
                months_with_decisions = len(decisions)
                
                # Show which months have decisions
                decision_months = sorted([int(k) for k in decisions.keys() if k.isdigit()])
            except Exception as e:
                months_with_decisions = 0
                decision_months = []
            
            # Determine recommendation
            if months_with_decisions >= 3:
                recommendation = "🟢 EXCELLENT for testing (lots of history)"
            elif months_with_decisions >= 1:
                recommendation = "🟡 GOOD for testing (some history)"
            else:
                recommendation = "🔴 Limited (no decision history)"
            
            print(f"📋 Journey ID: {journey_id}")
            print(f"   Pet: {pet_name} ({species}, {breed}, {age_months}mo)")
            print(f"   Progress: Month {current}/{total_months}")
            print(f"   Decisions: {months_with_decisions} months with data {decision_months}")
            print(f"   {recommendation}")
            print()
        
        conn.close()
        
        # Show best recommendations
        print("🎯 RECOMMENDED JOURNEY IDS FOR TESTING:")
        print("   (Copy one of these IDs for your tests)")
        print()
        
        # Get journeys with most decisions
        best_journeys = []
        for journey_row in journeys:
            journey_id, pet_id, current, total_months, decisions_json = journey_row
            try:
                decisions = json.loads(decisions_json) if decisions_json else {}
                months_with_decisions = len(decisions)
                if months_with_decisions > 0:
                    best_journeys.append((journey_id, months_with_decisions))
            except:
                pass
        
        # Sort by most decisions first
        best_journeys.sort(key=lambda x: x[1], reverse=True)
        
        for i, (journey_id, decision_count) in enumerate(best_journeys):
            print(f"   {i+1}. {journey_id} ({decision_count} months of decisions)")
        
        if not best_journeys:
            print("   No journeys with decision history found.")
            print("   You may need to go through more months in your frontend app.")
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_journeys()