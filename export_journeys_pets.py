#!/usr/bin/env python3
"""
Export all journeys and pet data to CSV file
"""

import sys
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

def export_journeys_pets_csv():
    """Export all journey and pet data to CSV"""
    
    # Database path
    db_path = Path("backend/chewy_journey.db")
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Query to get journey and pet data
    query = '''
        SELECT 
            j.id as journey_id,
            j.pet_id,
            j.current as current_month,
            j.total_months,
            p.name as pet_name,
            p.species,
            p.breed,
            p.age_months,
            p.weight_lbs,
            p.activity_level,
            p.chew_strength,
            p.allergies,
            p.brand_preferences,
            p.household_type,
            p.yard_access,
            p.zip_code,
            p.gender,
            p.height_at_shoulder_inches,
            p.about,
            p.appearance,
            p.budget_band
        FROM journeys j
        LEFT JOIN pets p ON j.pet_id = p.id
        ORDER BY j.id
    '''
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Get column names
    columns = [description[0] for description in cursor.description]
    
    conn.close()
    
    # Create CSV filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"journeys_pets_export_{timestamp}.csv"
    
    # Write to CSV
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(columns)
        
        # Write data rows
        for row in results:
            writer.writerow(row)
    
    print(f"✅ Exported {len(results)} records to: {csv_filename}")
    print(f"📁 File location: {Path.cwd() / csv_filename}")
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total Journeys: {len(results)}")
    
    # Count by species
    species_count = {}
    for row in results:
        species = row[5] or "Unknown"  # species column
        species_count[species] = species_count.get(species, 0) + 1
    
    print(f"   By Species:")
    for species, count in species_count.items():
        print(f"     {species}: {count}")
    
    return csv_filename

if __name__ == "__main__":
    export_journeys_pets_csv()
