#!/usr/bin/env python3
"""
Database export utility for sharing the SQLite database.
Creates a SQL dump that can be imported by others.
"""

import sqlite3
import argparse
import os
from datetime import datetime

def export_database(db_path: str = "chewy_journey.db", output_path: str = None):
    """Export database to SQL dump file."""
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return False
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"database_export_{timestamp}.sql"
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Create SQL dump
        with open(output_path, 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        conn.close()
        
        print(f"Database exported successfully to: {output_path}")
        print(f"File size: {os.path.getsize(output_path)} bytes")
        
        # Show some stats
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count records in main tables
        cursor.execute("SELECT COUNT(*) FROM pets")
        pet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM journeys")
        journey_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM journey_checkpoints")
        checkpoint_count = cursor.fetchone()[0]
        
        print(f"\nDatabase contents:")
        print(f"  - Pets: {pet_count}")
        print(f"  - Journeys: {journey_count}")
        print(f"  - Checkpoints: {checkpoint_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error exporting database: {e}")
        return False

def import_database(sql_file: str, db_path: str = "chewy_journey.db"):
    """Import database from SQL dump file."""
    
    if not os.path.exists(sql_file):
        print(f"Error: SQL file '{sql_file}' not found.")
        return False
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_path, backup_path)
        print(f"Existing database backed up to: {backup_path}")
    
    try:
        # Create new database from SQL dump
        conn = sqlite3.connect(db_path)
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        conn.executescript(sql_script)
        conn.close()
        
        print(f"Database imported successfully from: {sql_file}")
        return True
        
    except Exception as e:
        print(f"Error importing database: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export/Import SQLite database")
    parser.add_argument("action", choices=["export", "import"], help="Action to perform")
    parser.add_argument("--db", default="chewy_journey.db", help="Database file path")
    parser.add_argument("--file", help="SQL file path (for import) or output path (for export)")
    
    args = parser.parse_args()
    
    if args.action == "export":
        export_database(args.db, args.file)
    elif args.action == "import":
        if not args.file:
            print("Error: --file is required for import")
            exit(1)
        import_database(args.file, args.db)
