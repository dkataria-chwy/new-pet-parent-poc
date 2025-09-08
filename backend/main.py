from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from models import (
    CreatePetRequest, Pet, CreateJourneyRequest, JourneyState,
    UpdateJourneyStateRequest, MonthRecommendations,
    AIRecommendationRequest, AIRecommendationResponse,
    EventRequest
)
from database import db
from recommendation_policy import recommendation_policy

# Load environment variables from project root .env (prototype)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI(title="Chewy Journey API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            journey.decisions[month_key][request.section] = request.value
            
            updated_journey = db.update_journey(journey)
            
            # Log decision event
            db.log_event("decision_made", journey.id, {
                "monthIdx": request.monthIdx,
                "section": request.section,
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
class GenerateImageRequest(BaseModel):
    name: str
    species: str
    breed: str | None = None
    ageMonths: int | None = None
    appearance: str | None = None


@app.post("/generate-image")
async def generate_image(req: GenerateImageRequest):
    """Generate a pet portrait (prototype - returns base64, no storage)."""
    ENABLE = os.getenv("ENABLE_AI_IMAGE", "true").lower() == "true"
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

    if not ENABLE:
        raise HTTPException(status_code=503, detail="Image generation disabled")
    if not OPENAI_KEY:
        raise HTTPException(status_code=500, detail="Missing OpenAI API key")

    # Build prompt using only pet-specific fields (keep defaults for style/pose)
    prompt = (
        f"Photorealistic portrait of a {req.ageMonths or 'young'}-month-old "
        f"{(req.breed + ' ') if req.breed else ''}{req.species} named {req.name}. "
        f"{(req.appearance + ' ') if req.appearance else ''}Sitting three-quarter view facing right, "
        "soft studio lighting, high detail, shallow depth of field, pastel background, 3:2 aspect ratio. "
        "No text or watermark."
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-image-1",
                    "prompt": prompt,
                    "size": "1024x1024"
                }
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Image API failed: {resp.text}")

        data = resp.json()
        b64 = data["data"][0]["b64_json"]
        return {"b64": b64, "mime": "image/png"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
