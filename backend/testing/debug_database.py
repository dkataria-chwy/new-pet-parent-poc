#!/usr/bin/env python3
"""
Debug script to examine database contents directly
"""

import sys
import sqlite3
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def debug_database():
    db_path = "../chewy_journey.db"
    print(f"🔍 Examining database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 Tables found: {[t[0] for t in tables]}")
        
        # Check pets table
        try:
            cursor.execute("SELECT COUNT(*) FROM pets")
            pet_count = cursor.fetchone()[0]
            print(f"🐕 Pets: {pet_count} records")
            
            if pet_count > 0:
                cursor.execute("SELECT id, name, species, breed FROM pets LIMIT 5")
                pets = cursor.fetchall()
                for pet in pets:
                    print(f"   - {pet[1]} ({pet[2]}, {pet[3]}) ID: {pet[0]}")
        except Exception as e:
            print(f"❌ Error reading pets: {e}")
        
        # Check journeys table
        try:
            cursor.execute("SELECT COUNT(*) FROM journeys")
            journey_count = cursor.fetchone()[0]
            print(f"🗺️ Journeys: {journey_count} records")
            
            if journey_count > 0:
                cursor.execute("SELECT id, pet_id, current, total_months, decisions FROM journeys LIMIT 5")
                journeys = cursor.fetchall()
                for journey in journeys:
                    decisions = json.loads(journey[4]) if journey[4] else {}
                    print(f"   - Journey {journey[0][:8]}... Pet: {journey[1][:8]}... Month: {journey[2]}/{journey[3]} Decisions: {len(decisions)} months")
        except Exception as e:
            print(f"❌ Error reading journeys: {e}")
        
        # Check events table
        try:
            cursor.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]
            print(f"📝 Events: {event_count} records")
        except Exception as e:
            print(f"❌ Error reading events: {e}")
        
        # Check pet_history table
        try:
            cursor.execute("SELECT COUNT(*) FROM pet_history")
            history_count = cursor.fetchone()[0]
            print(f"📋 Pet History: {history_count} records")
        except Exception as e:
            print(f"❌ Error reading pet_history: {e}")
        
        conn.close()
        
        # If we found journeys, show them for testing
        if journey_count > 0:
            print(f"\n🎯 Available Journey IDs for testing:")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM journeys")
            journey_ids = cursor.fetchall()
            for journey_id in journey_ids:
                print(f"   {journey_id[0]}")
            conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    debug_database()
