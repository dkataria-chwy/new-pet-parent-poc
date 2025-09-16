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
        
        # Create pet_history table for tracking changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_history (
                id TEXT PRIMARY KEY,
                pet_id TEXT NOT NULL,
                checkpoint_month INTEGER NOT NULL,
                journey_id TEXT,
                -- Core pet data at this checkpoint
                weight_lbs REAL,
                height_at_shoulder_inches REAL,
                chew_strength TEXT,
                activity_level TEXT,
                -- Checkpoint-specific data
                health_issues TEXT,
                product_returns TEXT,
                -- Change tracking
                changes_made TEXT,  -- JSON of what fields changed
                ai_warnings_shown TEXT,  -- JSON of AI warnings shown to user
                user_responses TEXT,  -- JSON of how user responded to warnings
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pet_id) REFERENCES pets (id)
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
    
    def update_pet(self, pet_id: str, updates: Dict[str, Any]) -> Optional[Pet]:
        """Update provided, non-null pet fields and return the updated pet."""
        if not updates:
            return self.get_pet(pet_id)
        
        # Map camelCase API fields to DB column names
        field_map = {
            "name": "name",
            "species": "species",
            "breed": "breed",
            "ageMonths": "age_months",
            "gender": "gender",
            "householdType": "household_type",
            "yardAccess": "yard_access",
            "zipCode": "zip_code",
            "weightLbs": "weight_lbs",
            "heightAtShoulderInches": "height_at_shoulder_inches",
            "chewStrength": "chew_strength",
            "activityLevel": "activity_level",
            "allergies": "allergies",
            "about": "about",
            "appearance": "appearance",
            "budgetBand": "budget_band",
            "brandPreferences": "brand_preferences",
        }
        
        set_parts: List[str] = []
        values: List[Any] = []
        for key, col in field_map.items():
            if key in updates and updates[key] is not None:
                value = updates[key]
                # Unwrap enums
                if hasattr(value, "value"):
                    value = value.value
                set_parts.append(f"{col} = ?")
                values.append(value)
        
        if not set_parts:
            return self.get_pet(pet_id)
        
        values.append(pet_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE pets SET {', '.join(set_parts)} WHERE id = ?", values)
        conn.commit()
        conn.close()
        
        return self.get_pet(pet_id)
    
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
    
    def record_pet_history(
        self, 
        pet_id: str, 
        checkpoint_month: int, 
        journey_id: Optional[str] = None,
        current_data: Optional[Dict[str, Any]] = None,
        previous_data: Optional[Dict[str, Any]] = None,
        health_issues: Optional[str] = None,
        product_returns: Optional[str] = None,
        ai_warnings: Optional[List[Dict[str, Any]]] = None,
        user_responses: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a pet history entry for this checkpoint."""
        history_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate what changed
        changes_made = {}
        if current_data and previous_data:
            for key in ["weightLbs", "heightAtShoulderInches", "chewStrength", "activityLevel"]:
                current_val = current_data.get(key)
                previous_val = previous_data.get(key)
                if current_val != previous_val:
                    changes_made[key] = {
                        "from": previous_val,
                        "to": current_val
                    }
        
        cursor.execute("""
            INSERT INTO pet_history (
                id, pet_id, checkpoint_month, journey_id,
                weight_lbs, height_at_shoulder_inches, chew_strength, activity_level,
                health_issues, product_returns,
                changes_made, ai_warnings_shown, user_responses
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            history_id, pet_id, checkpoint_month, journey_id,
            current_data.get("weightLbs") if current_data else None,
            current_data.get("heightAtShoulderInches") if current_data else None,
            current_data.get("chewStrength") if current_data else None,
            current_data.get("activityLevel") if current_data else None,
            health_issues,
            product_returns,
            json.dumps(changes_made) if changes_made else None,
            json.dumps(ai_warnings) if ai_warnings else None,
            json.dumps(user_responses) if user_responses else None
        ))
        
        conn.commit()
        conn.close()
        return history_id
    
    def get_pet_history(self, pet_id: str) -> List[Dict[str, Any]]:
        """Get the complete history of changes for a pet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pet_history 
            WHERE pet_id = ? 
            ORDER BY checkpoint_month ASC, created_at ASC
        """, (pet_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Column names for reference
        columns = [
            "id", "pet_id", "checkpoint_month", "journey_id",
            "weight_lbs", "height_at_shoulder_inches", "chew_strength", "activity_level",
            "health_issues", "product_returns",
            "changes_made", "ai_warnings_shown", "user_responses", "created_at"
        ]
        
        history = []
        for row in rows:
            entry = dict(zip(columns, row))
            # Parse JSON fields
            for json_field in ["changes_made", "ai_warnings_shown", "user_responses"]:
                if entry[json_field]:
                    try:
                        entry[json_field] = json.loads(entry[json_field])
                    except:
                        entry[json_field] = None
            history.append(entry)
        
        return history

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
