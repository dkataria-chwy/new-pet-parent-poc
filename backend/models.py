from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum

class Species(str, Enum):
    DOG = "dog"
    CAT = "cat"

# Enums for new fields
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class HouseholdType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"

class YardAccess(str, Enum):
    NO_YARD = "no_yard"
    SMALL_YARD = "small_yard"
    LARGE_YARD = "large_yard"

class ChewStrength(str, Enum):
    LIGHT = "light"
    AVERAGE = "average"
    STRONG = "strong"

class ActivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BudgetBand(str, Enum):
    BUDGET = "budget"
    MODERATE = "moderate"
    PREMIUM = "premium"

# Request/Response Models
class CreatePetRequest(BaseModel):
    name: str
    species: Species
    breed: str
    ageMonths: int
    # Step 1 fields
    gender: Optional[Gender] = None
    householdType: Optional[HouseholdType] = None
    yardAccess: Optional[YardAccess] = None
    zipCode: Optional[str] = None
    # Step 2 fields
    weightLbs: Optional[float] = None
    heightAtShoulderInches: Optional[float] = None
    chewStrength: Optional[ChewStrength] = None
    activityLevel: Optional[ActivityLevel] = None
    allergies: Optional[str] = None
    # Step 3 fields
    about: Optional[str] = None  # Pet characteristics for recommendations
    appearance: Optional[str] = None  # Physical appearance for avatar generation
    budgetBand: Optional[BudgetBand] = None
    brandPreferences: Optional[str] = None  # Brands they like/avoid

class Pet(BaseModel):
    id: str
    name: str
    species: Species
    breed: str
    ageMonths: int
    # Step 1 fields
    gender: Optional[Gender] = None
    householdType: Optional[HouseholdType] = None
    yardAccess: Optional[YardAccess] = None
    zipCode: Optional[str] = None
    # Step 2 fields
    weightLbs: Optional[float] = None
    heightAtShoulderInches: Optional[float] = None
    chewStrength: Optional[ChewStrength] = None
    activityLevel: Optional[ActivityLevel] = None
    allergies: Optional[str] = None
    # Step 3 fields
    about: Optional[str] = None  # Pet characteristics for recommendations
    appearance: Optional[str] = None  # Physical appearance for avatar generation
    budgetBand: Optional[BudgetBand] = None
    brandPreferences: Optional[str] = None  # Brands they like/avoid

class CreateJourneyRequest(BaseModel):
    petId: str
    months: int = 15

class JourneyState(BaseModel):
    id: str
    petId: str
    current: int
    totalMonths: int
    decisions: Dict[str, Dict[str, Any]]  # monthIdx -> section -> (bool | Dict[itemId, bool])

class UpdateJourneyStateRequest(BaseModel):
    action: str
    journeyId: Optional[str] = None
    monthIdx: Optional[int] = None
    section: Optional[str] = None
    itemId: Optional[str] = None  # For individual item decisions
    value: Optional[bool] = None

class RecommendationItem(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    tags: List[str]
    price: str
    cadence: Optional[str] = None
    whyForPet: str
    isAIGenerated: bool = False

class MonthRecommendations(BaseModel):
    summaryWhy: str
    subscriptions: List[RecommendationItem]
    bundles: List[RecommendationItem]
    singles: List[RecommendationItem]

class AIRecommendationRequest(BaseModel):
    journeyId: str
    monthIdx: int
    note: str

class AIRecommendationResponse(BaseModel):
    summary: str
    items: List[Dict[str, Any]]

# On-demand recommendations models
class OnDemandRecommendationRequest(BaseModel):
    user_query: str
    journey_id: str
    month_idx: int  # Current month index to calculate accurate pet age
    top_k: Optional[int] = 20

class OnDemandProduct(BaseModel):
    rank: int
    sku: str
    parentSKU: str
    name: str
    similarity: float
    product_link: Optional[str] = ""
    product_price_current: Optional[float] = None
    autoship_eligible: bool = False
    base_similarity: Optional[float] = None
    brand_boosted: bool = False
    search_text: Optional[str] = None
    species_flags: Optional[Dict[str, bool]] = None
    family: Optional[str] = None
    top_family: Optional[str] = None
    query_index: Optional[int] = None

class OnDemandRecommendationResponse(BaseModel):
    timestamp: str
    query_used: str
    rationale: str
    total_products: int
    products: List[OnDemandProduct]
    user_query: str
    journey_id: str
    pet_name: str
    pet_species: str

# Checkpoint validation models
class CheckpointValidationRequest(BaseModel):
    petId: str
    monthIndex: int
    currentData: Dict[str, Any]
    previousData: Dict[str, Any]

class AIFollowUp(BaseModel):
    field: str
    question: str
    explanation: str
    suggestedValue: Optional[str] = None

class CheckpointValidationResponse(BaseModel):
    hasAnomalies: bool
    followUps: List[AIFollowUp]
    confidence: str

# Structured output models for AI validation
class AIValidationFollowUp(BaseModel):
    """Structured follow-up for AI validation output."""
    field: str = Field(description="Field name: weightLbs, heightAtShoulderInches, chewStrength, or activityLevel")
    question: str = Field(description="Short, friendly clarification question")
    explanation: str = Field(description="1 sentence, pet-centric reason for the question")
    suggestedValue: Optional[str] = Field(default=None, description="Optional corrected value if confident")

class AIValidationOutput(BaseModel):
    """Structured output for AI checkpoint validation."""
    hasAnomalies: bool = Field(description="Whether any anomalies or contradictions were detected")
    followUps: List[AIValidationFollowUp] = Field(description="List of follow-up questions for detected issues")
    confidence: str = Field(description="Confidence level: high, medium, or low")

class CheckpointCommitRequest(BaseModel):
    petId: str
    monthIndex: int
    checkpointData: Dict[str, Any]
    petUpdates: Dict[str, Any]

class EventRequest(BaseModel):
    type: str
    journeyId: str
    meta: Optional[Dict[str, Any]] = None
