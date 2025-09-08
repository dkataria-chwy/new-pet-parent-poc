import sqlite3
import json
import uuid
from typing import Optional, Dict, List, Any
from models import Pet, JourneyState, CreatePetRequest, CreateJourneyRequest

class Database:
    def __init__(self, db_path: str = "chewy_journey.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create pets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT NOT NULL,
                age_months INTEGER NOT NULL,
                -- Step 1 fields
                gender TEXT,
                household_type TEXT,
                yard_access TEXT,
                zip_code TEXT,
                -- Step 2 fields
                weight_lbs REAL,
                height_at_shoulder_inches REAL,
                chew_strength TEXT,
                activity_level TEXT,
                allergies TEXT,
                -- Step 3 fields
                about TEXT,
                appearance TEXT,
                budget_band TEXT,
                brand_preferences TEXT
            )
        """)
        
        # Create journeys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journeys (
                id TEXT PRIMARY KEY,
                pet_id TEXT NOT NULL,
                current INTEGER NOT NULL DEFAULT 0,
                total_months INTEGER NOT NULL,
                decisions TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (pet_id) REFERENCES pets (id)
            )
        """)
        
        # Create events table for analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                journey_id TEXT NOT NULL,
                meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_pet(self, pet_data: CreatePetRequest) -> Pet:
        """Create a new pet in the database."""
        pet_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pets (
                id, name, species, breed, age_months,
                gender, household_type, yard_access, zip_code,
                weight_lbs, height_at_shoulder_inches, chew_strength, activity_level, allergies,
                about, appearance, budget_band, brand_preferences
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pet_id, pet_data.name, pet_data.species.value, pet_data.breed, pet_data.ageMonths,
            pet_data.gender.value if pet_data.gender else None,
            pet_data.householdType.value if pet_data.householdType else None,
            pet_data.yardAccess.value if pet_data.yardAccess else None,
            pet_data.zipCode,
            pet_data.weightLbs, pet_data.heightAtShoulderInches,
            pet_data.chewStrength.value if pet_data.chewStrength else None,
            pet_data.activityLevel.value if pet_data.activityLevel else None,
            pet_data.allergies,
            pet_data.about, pet_data.appearance,
            pet_data.budgetBand.value if pet_data.budgetBand else None,
            pet_data.brandPreferences
        ))
        
        conn.commit()
        conn.close()
        
        return Pet(
            id=pet_id,
            name=pet_data.name,
            species=pet_data.species,
            breed=pet_data.breed,
            ageMonths=pet_data.ageMonths,
            gender=pet_data.gender,
            householdType=pet_data.householdType,
            yardAccess=pet_data.yardAccess,
            zipCode=pet_data.zipCode,
            weightLbs=pet_data.weightLbs,
            heightAtShoulderInches=pet_data.heightAtShoulderInches,
            chewStrength=pet_data.chewStrength,
            activityLevel=pet_data.activityLevel,
            allergies=pet_data.allergies,
            about=pet_data.about,
            appearance=pet_data.appearance,
            budgetBand=pet_data.budgetBand,
            brandPreferences=pet_data.brandPreferences
        )
    
    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Get a pet by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Pet(
            id=row[0],
            name=row[1],
            species=row[2],
            breed=row[3],
            ageMonths=row[4],
            gender=row[5],
            householdType=row[6],
            yardAccess=row[7],
            zipCode=row[8],
            weightLbs=row[9],
            heightAtShoulderInches=row[10],
            chewStrength=row[11],
            activityLevel=row[12],
            allergies=row[13],
            about=row[14],
            appearance=row[15],
            budgetBand=row[16],
            brandPreferences=row[17]
        )
    
    def create_journey(self, journey_data: CreateJourneyRequest) -> JourneyState:
        """Create a new journey in the database."""
        journey_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO journeys (id, pet_id, current, total_months, decisions)
            VALUES (?, ?, ?, ?, ?)
        """, (journey_id, journey_data.petId, 0, journey_data.months, '{}'))
        
        conn.commit()
        conn.close()
        
        return JourneyState(
            id=journey_id,
            petId=journey_data.petId,
            current=0,
            totalMonths=journey_data.months,
            decisions={}
        )
    
    def get_journey(self, journey_id: str) -> Optional[JourneyState]:
        """Get a journey by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM journeys WHERE id = ?", (journey_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return JourneyState(
            id=row[0],
            petId=row[1],
            current=row[2],
            totalMonths=row[3],
            decisions=json.loads(row[4])
        )
    
    def update_journey(self, journey: JourneyState) -> JourneyState:
        """Update a journey in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE journeys 
            SET current = ?, decisions = ?
            WHERE id = ?
        """, (journey.current, json.dumps(journey.decisions), journey.id))
        
        conn.commit()
        conn.close()
        
        return journey
    
    def log_event(self, event_type: str, journey_id: str, meta: Optional[Dict[str, Any]] = None):
        """Log an event for analytics."""
        event_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (id, type, journey_id, meta)
            VALUES (?, ?, ?, ?)
        """, (event_id, event_type, journey_id, json.dumps(meta) if meta else None))
        
        conn.commit()
        conn.close()

# Global database instance
db = Database()
