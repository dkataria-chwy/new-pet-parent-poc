from typing import Optional, Dict, List, Any
from pydantic import BaseModel
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
    decisions: Dict[str, Dict[str, bool]]  # monthIdx -> section -> decision

class UpdateJourneyStateRequest(BaseModel):
    action: str
    journeyId: Optional[str] = None
    monthIdx: Optional[int] = None
    section: Optional[str] = None
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

class EventRequest(BaseModel):
    type: str
    journeyId: str
    meta: Optional[Dict[str, Any]] = None
