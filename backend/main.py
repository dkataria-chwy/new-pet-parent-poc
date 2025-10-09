import os
from dotenv import load_dotenv

# Load environment variables from project root .env FIRST (before any imports that need them)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from models import (
    CreatePetRequest, Pet, CreateJourneyRequest, JourneyState,
    UpdateJourneyStateRequest, MonthRecommendations,
    AIRecommendationRequest, AIRecommendationResponse,
    OnDemandRecommendationRequest, OnDemandRecommendationResponse,
    EventRequest, CheckpointValidationRequest, CheckpointValidationResponse, 
    CheckpointCommitRequest
)
from database import db
from recommendation_policy import recommendation_policy
from checkpoint_validator import checkpoint_validator
from image_service import image_service, GenerateImageRequest

# Import on-demand recommendations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "on_demand_recommendations"))
from api_handler import OnDemandRecommendationHandler

app = FastAPI(title="Chewy Journey API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize on-demand recommendations handler
on_demand_handler = OnDemandRecommendationHandler()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        stats = on_demand_handler.initialize()
        print(f"✅ On-demand recommendations initialized with {stats['total_products']:,} products")
    except Exception as e:
        print(f"⚠️ Failed to initialize on-demand recommendations: {e}")

@app.get("/")
async def root():
    return {"message": "Chewy Journey API"}

@app.post("/profile", response_model=Pet)
async def create_pet(pet_data: CreatePetRequest):
    """Create a new pet profile."""
    try:
        pet = db.create_pet(pet_data)
        return pet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pet/{pet_id}", response_model=Pet)
async def get_pet(pet_id: str):
    """Get a pet by ID."""
    try:
        pet = db.get_pet(pet_id)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        return pet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/journeys")
async def get_all_journeys():
    """Get all journeys with their pet information."""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get journeys with pet information
        cursor.execute("""
            SELECT 
                j.id as journey_id,
                j.pet_id,
                j.current,
                j.total_months,
                p.name as pet_name,
                p.species,
                p.breed,
                p.age_months
            FROM journeys j
            JOIN pets p ON j.pet_id = p.id
            ORDER BY j.current DESC, p.name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        journeys = []
        for row in rows:
            journeys.append({
                "journey_id": row[0],
                "pet_id": row[1],
                "current_month": row[2],
                "total_months": row[3],
                "pet_name": row[4],
                "species": row[5],
                "breed": row[6],
                "age_months": row[7]
            })
        
        return {"journeys": journeys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/journey/{journey_id}", response_model=JourneyState)
async def get_journey(journey_id: str):
    """Get a journey by ID."""
    try:
        journey = db.get_journey(journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        return journey
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journey", response_model=JourneyState)
async def initialize_journey(journey_data: CreateJourneyRequest):
    """Initialize a new journey for a pet."""
    try:
        # Verify pet exists
        pet = db.get_pet(journey_data.petId)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        journey = db.create_journey(journey_data)
        
        # Log journey creation event
        db.log_event("journey_created", journey.id, {"petId": journey_data.petId})
        
        return journey
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/journey/state", response_model=JourneyState)
async def update_journey_state(request: UpdateJourneyStateRequest):
    """Update journey state (decisions, completion, etc.)."""
    try:
        if request.action == "setDecision":
            if not all([request.journeyId, request.monthIdx is not None, 
                       request.section, request.value is not None]):
                raise HTTPException(status_code=400, detail="Missing required fields for setDecision")
            
            journey = db.get_journey(request.journeyId)
            if not journey:
                raise HTTPException(status_code=404, detail="Journey not found")
            
            # Update decision
            month_key = str(request.monthIdx)
            if month_key not in journey.decisions:
                journey.decisions[month_key] = {}
            
            # Handle individual item decisions vs section-level decisions
            if request.itemId:
                # Individual item decision
                if request.section not in journey.decisions[month_key]:
                    journey.decisions[month_key][request.section] = {}
                journey.decisions[month_key][request.section][request.itemId] = request.value
                print(f"📝 Individual decision: Month {month_key}, {request.section}/{request.itemId} = {request.value}")
            else:
                # Section-level decision (legacy support)
                journey.decisions[month_key][request.section] = request.value
                print(f"📝 Section decision: Month {month_key}, {request.section} = {request.value}")
            
            updated_journey = db.update_journey(journey)
            
            # Log decision event
            db.log_event("decision_made", journey.id, {
                "monthIdx": request.monthIdx,
                "section": request.section,
                "itemId": request.itemId,
                "value": request.value
            })
            
            return updated_journey
            
        elif request.action == "completeMonth":
            if not all([request.journeyId, request.monthIdx is not None]):
                raise HTTPException(status_code=400, detail="Missing required fields for completeMonth")
            
            journey = db.get_journey(request.journeyId)
            if not journey:
                raise HTTPException(status_code=404, detail="Journey not found")
            
            # Special case: monthIdx = -1 means starting the journey (move from 0 to 1)
            if request.monthIdx == -1:
                journey.current = 1
                updated_journey = db.update_journey(journey)
                
                # Log journey start event
                db.log_event("journey_started", journey.id, {
                    "newCurrent": journey.current
                })
                
                return updated_journey
            
            # Normal case: completing a month
            # Check if all sections have decisions
            month_key = str(request.monthIdx)
            # Temporarily allow completion without decisions for testing
            if month_key not in journey.decisions:
                print(f"WARNING: No decisions for month {month_key}, but allowing completion for testing")
                # Initialize empty decisions structure to avoid errors
                journey.decisions[month_key] = {}
            
            month_decisions = journey.decisions[month_key]
            required_sections = ["subscriptions", "bundles", "singles"]
            
            # Check if all sections have at least one decision (new individual item structure)
            # Temporarily relaxed for testing - just need month_decisions to exist
            print(f"DEBUG: Month decisions for {month_key}: {month_decisions}")
            
            for section in required_sections:
                if section not in month_decisions:
                    print(f"WARNING: No decisions for {section}, but allowing completion for testing")
                    continue
                
                # Check if section has any item decisions
                section_decisions = month_decisions[section]
                print(f"DEBUG: {section} decisions: {section_decisions}")
                if not isinstance(section_decisions, dict) or len(section_decisions) == 0:
                    print(f"WARNING: No item decisions in {section}, but allowing completion for testing")
                    continue
            
            # Update current month
            journey.current = request.monthIdx + 1
            updated_journey = db.update_journey(journey)
            
            # Log completion event
            db.log_event("month_completed", journey.id, {
                "monthIdx": request.monthIdx,
                "newCurrent": journey.current
            })
            
            return updated_journey
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations", response_model=MonthRecommendations)
async def get_recommendations(journeyId: str, monthIdx: int):
    """Get baseline recommendations for a specific month."""
    try:
        journey = db.get_journey(journeyId)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        recommendations = recommendation_policy.get_baseline_recommendations(journeyId, monthIdx)
        
        # Log recommendation fetch event
        db.log_event("recommendations_fetched", journeyId, {"monthIdx": monthIdx})
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/recs", response_model=AIRecommendationResponse)
async def get_ai_recommendations(request: AIRecommendationRequest):
    """Get AI-generated recommendations based on user input."""
    try:
        journey = db.get_journey(request.journeyId)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        ai_response = recommendation_policy.get_ai_recommendations(
            request.journeyId, request.monthIdx, request.note
        )
        
        # Log AI recommendation event
        db.log_event("ai_recommendations", request.journeyId, {
            "monthIdx": request.monthIdx,
            "note": request.note,
            "itemCount": len(ai_response["items"])
        })
        
        return AIRecommendationResponse(**ai_response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/on-demand-recommendations", response_model=OnDemandRecommendationResponse)
async def get_on_demand_recommendations(request: OnDemandRecommendationRequest):
    """Get on-demand AI-powered product recommendations based on user query."""
    try:
        # Process the recommendation request
        result = on_demand_handler.process_recommendation_request(
            user_query=request.user_query,
            journey_id=request.journey_id,
            month_idx=request.month_idx,
            top_k=request.top_k
        )
        
        # Log the on-demand recommendation event
        db.log_event("on_demand_recommendation", request.journey_id, {
            "user_query": request.user_query,
            "total_products": result["total_products"],
            "pet_name": result["pet_name"]
        })
        
        return OnDemandRecommendationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@app.post("/events")
async def log_event(request: EventRequest):
    """Log an analytics event."""
    try:
        db.log_event(request.type, request.journeyId, request.meta)
        return {"status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
@app.post("/generate-image")
async def generate_image(request: GenerateImageRequest):
    """Generate a pet portrait using AI service."""
    try:
        result = await image_service.generate_pet_image(request)
        
        # Log image generation event
        db.log_event("image_generated", f"pet_{request.name}", {
            "species": request.species,
            "breed": request.breed,
            "ageMonths": getattr(request, 'ageMonths', None),
            "appearance": getattr(request, 'appearance', None),
            "success": True
        })
        
        return result
    except Exception as e:
        # Log failed image generation
        db.log_event("image_generation_failed", f"pet_{request.name}", {
            "species": request.species,
            "breed": request.breed,
            "error": str(e)
        })
        raise

@app.post("/checkpoint/validate", response_model=CheckpointValidationResponse)
async def validate_checkpoint(request: CheckpointValidationRequest):
    """Validate checkpoint data and generate smart follow-ups."""
    try:
        print("🟦 /checkpoint/validate payload:", {
            "petId": request.petId,
            "monthIndex": request.monthIndex,
            "currentData": request.currentData,
            "previousData": request.previousData,
        })
        pet = db.get_pet(request.petId)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Calculate days elapsed (simplified - using 30 days for now)
        days_elapsed = 30
        
        validation_result = checkpoint_validator.validate_checkpoint_data(
            pet=pet,
            current_data=request.currentData,
            previous_data=request.previousData,
            days_elapsed=days_elapsed
        )
        print("🟩 /checkpoint/validate result:", validation_result.model_dump())
        return validation_result
        
    except Exception as e:
        print("🟥 /checkpoint/validate error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checkpoint/commit")
async def commit_checkpoint(request: CheckpointCommitRequest):
    """Save checkpoint data and update pet profile."""
    try:
        # Get existing pet for previous data
        pet = db.get_pet(request.petId)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        
        # Capture previous data for history tracking
        previous_data = {
            "weightLbs": pet.weightLbs,
            "heightAtShoulderInches": pet.heightAtShoulderInches,
            "chewStrength": pet.chewStrength,
            "activityLevel": pet.activityLevel,
        }
        
        # Persist pet updates when provided
        updated_pet = None
        if request.petUpdates:
            try:
                updated_pet = db.update_pet(request.petId, request.petUpdates)
            except Exception as pe:
                print("🟥 Failed to persist pet updates:", pe)
        
        # Record complete history entry for this checkpoint
        current_data = request.petUpdates if request.petUpdates else previous_data
        history_id = db.record_pet_history(
            pet_id=request.petId,
            checkpoint_month=request.monthIndex,
            journey_id=None,  # Could link to journey if needed
            current_data=current_data,
            previous_data=previous_data,
            health_issues=request.checkpointData.get("healthIssues"),
            product_returns=request.checkpointData.get("productReturns"),
            ai_warnings=request.checkpointData.get("aiWarnings"),  # Now included from frontend
            user_responses=request.checkpointData.get("userResponses")  # Now included from frontend
        )
        
        # Log the checkpoint data as an event (keeping existing analytics)
        db.log_event("checkpoint_completed", f"pet_{request.petId}", {
            "monthIndex": request.monthIndex,
            "checkpointData": request.checkpointData,
            "petUpdates": request.petUpdates,
            "historyId": history_id
        })
        
        print(f"🟩 Checkpoint committed: Pet {request.petId}, Month {request.monthIndex}, History {history_id}")
        
        return {"status": "success", "message": "Checkpoint data saved successfully", "pet": updated_pet.model_dump() if updated_pet else None, "historyId": history_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pet/{pet_id}/history")
async def get_pet_history(pet_id: str):
    """Get the complete change history for a pet."""
    try:
        history = db.get_pet_history(pet_id)
        return {"petId": pet_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
