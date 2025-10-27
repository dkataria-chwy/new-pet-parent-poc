from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from database import db
# from tools.calendar_tool import get_calendar_context  # Original version
from tools.csv_calendar_tool import get_csv_calendar_context  # CSV version
# from tools.weather_tool import get_weather_context  # NWS API version
from tools.csv_weather_tool import get_csv_weather_context  # CSV version


def _summarize_prev_month_decisions(journey: Any, month_idx: int) -> Dict[str, Any]:
    prev_key = str(month_idx - 1)
    accepted, skipped = set(), set()
    md = journey.decisions.get(prev_key, {}) if journey and journey.decisions else {}
    for section, val in md.items():
        if isinstance(val, bool):
            (accepted if val else skipped).add(section)
        elif isinstance(val, dict):
            for item_id, v in val.items():
                (accepted if v else skipped).add(item_id)
    return {
        "accepted": sorted(accepted),
        "skipped": sorted(skipped),
    }


def build_generation_context(journey_id: str, month_idx: int, tz: str = "America/Los_Angeles") -> Dict[str, Any]:
    """
    Aggregate latest pet, journey, previous month decisions, and tool outputs
    into a single normalized context dict for the multi-slot semantic query generator.
    Tools may return None/[]; callers should ignore absent data.
    """
    journey = db.get_journey(journey_id)
    if not journey:
        raise ValueError("Journey not found")

    pet = db.get_pet(journey.petId)
    if not pet:
        raise ValueError("Pet not found")

    prev_month = _summarize_prev_month_decisions(journey, month_idx)

    # Calendar: start at month start per tool default; days_ahead 30
    calendar = None
    try:
        # Original calendar tool (commented out)
        # calendar = get_calendar_context(
        #     zip_code=pet.zipCode or "00000",
        #     start_date=None,
        #     days_ahead=30,
        #     tz=tz,
        #     include_optional=True,
        # )
        
        # CSV calendar tool (active) - use current date instead of month start
        current_date = datetime.now(ZoneInfo(tz)).date().isoformat()
        calendar = get_csv_calendar_context(
            zip_code=pet.zipCode or "00000",
            start_date=current_date,
            days_ahead=30,
            tz=tz,
            include_optional=True,
        )
    except Exception:
        calendar = None

    # Weather: 7-day forecast + alerts, may be empty
    weather = None
    try:
        # NWS API version (commented out)
        # weather = get_weather_context(
        #     zip_code=pet.zipCode or "00000",
        #     days_ahead=7,
        #     tz=tz,
        # )
        
        # CSV version (active)
        weather = get_csv_weather_context(
            zip_code=pet.zipCode or "00000",
            days_ahead=7,
            tz=tz,
        )
    except Exception:
        weather = None

    # Parent profile is embedded within pet fields in this system
    parent_profile = {
        "zipCode": pet.zipCode,
        "budgetBand": getattr(pet.budgetBand, "value", pet.budgetBand) if pet.budgetBand else None,
        "householdType": getattr(pet.householdType, "value", pet.householdType) if pet.householdType else None,
        "yardAccess": getattr(pet.yardAccess, "value", pet.yardAccess) if pet.yardAccess else None,
        "brandPreferences": pet.brandPreferences,
    }

    pet_profile = {
        "id": pet.id,
        "name": pet.name,
        "species": getattr(pet.species, "value", pet.species),
        "breed": pet.breed,
        "ageMonths": pet.ageMonths + month_idx,
        "gender": getattr(pet.gender, "value", pet.gender) if pet.gender else None,
        "weightLbs": pet.weightLbs,
        "heightAtShoulderInches": pet.heightAtShoulderInches,
        "activityLevel": getattr(pet.activityLevel, "value", pet.activityLevel) if pet.activityLevel else None,
        "chewStrength": getattr(pet.chewStrength, "value", pet.chewStrength) if pet.chewStrength else None,
        "allergies": pet.allergies,
        "about": pet.about,
        # "appearance": pet.appearance,
        **parent_profile,
    }

    context: Dict[str, Any] = {
        "journey": {
            "id": journey.id,
            "petId": journey.petId,
            "monthIdx": month_idx,
            "decisions": journey.decisions,
            "prevMonthSummary": prev_month,
        },
        "pet": pet_profile,
        "calendar": calendar,   # possibly None
        "weather": weather,     # possibly None
        "nowIso": datetime.now(ZoneInfo(tz)).isoformat(),
    }

    return context


