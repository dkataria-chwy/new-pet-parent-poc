from __future__ import annotations

from typing import Any, Dict, List, Optional
import json


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _pet_to_profiles(pet: Dict[str, Any]) -> Dict[str, Any]:
    # Map internal pet to required pet_profile fields
    return {
        "species": pet.get("species"),
        "breed": pet.get("breed"),
        "age_months": pet.get("ageMonths"),
        "weight_lb": pet.get("weightLbs"),
        "sex_neuter": None,  # not tracked in current DB
        "chew_strength": pet.get("chewStrength"),
        "activity": pet.get("activityLevel"),
        "allergies": _split_csv(pet.get("allergies")),
        "sensitivities": [],  # not tracked
        "house_type": pet.get("householdType"),
        "yard": pet.get("yardAccess"),
        "zip": pet.get("zipCode"),
        "brand_bias": _split_csv(pet.get("brandPreferences")),
        "budget_band": pet.get("budgetBand"),
    }


def _journey_prev_month_summary(journey: Dict[str, Any], month_idx: int) -> Dict[str, Any]:
    prev_key = str(month_idx - 1)
    md = journey.get("decisions", {}).get(prev_key, {})
    accepted, skipped = [], []
    for section, val in md.items():
        if isinstance(val, bool):
            (accepted if val else skipped).append(section)
        elif isinstance(val, dict):
            for item_id, v in val.items():
                (accepted if v else skipped).append(item_id)
    return {"accepted": sorted(set(accepted)), "skipped": sorted(set(skipped))}


def _weather_to_expected_shape(weather: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not weather:
        return {"alerts": [], "daily": []}
    alerts = [a.get("event") for a in weather.get("alerts", []) if a.get("event")]
    daily = []
    for d in weather.get("forecast", []) or []:
        daily.append({
            "date": d.get("date"),
            "max_f": d.get("high_f"),
            "min_f": d.get("low_f"),
            "max_c": d.get("high_c"),
            "min_c": d.get("low_c"),
        })
    return {"alerts": alerts, "daily": daily}


def _calendar_to_expected_shape(calendar: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not calendar:
        return {"events": []}
    events = []
    for ev in calendar.get("events", []) or []:
        events.append({
            "id": ev.get("id"),
            "name": ev.get("label"),
            "date_window": ev.get("window"),
            "tags": ev.get("pet_relevance_tags") or [],
            "relevance_to_pets": ev.get("slot_triggers_seed") or [],
        })
    return {"events": events}


def _extract_order_history(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract order history from journey decisions and pet history data."""
    order_history = []
    
    journey = context.get("journey", {})
    decisions = journey.get("decisions", {})
    
    # Process each month's decisions
    for month_str, month_decisions in decisions.items():
        try:
            month_idx = int(month_str)
        except (ValueError, TypeError):
            continue
            
        month_entry = {
            "month": month_idx,
            "decisions": [],
            "summary": {"accepted": [], "skipped": []}
        }
        
        accepted_items = []
        skipped_items = []
        
        for section, decision in month_decisions.items():
            if isinstance(decision, bool):
                # Section-level decision (e.g., food section accepted/skipped)
                decision_entry = {
                    "item_type": "section",
                    "item_id": section,
                    "accepted": decision,
                    "category": section
                }
                month_entry["decisions"].append(decision_entry)
                (accepted_items if decision else skipped_items).append(section)
                
            elif isinstance(decision, dict):
                # Item-level decisions within a section
                for item_id, item_decision in decision.items():
                    decision_entry = {
                        "item_type": "product",
                        "item_id": item_id,
                        "accepted": item_decision,
                        "category": section
                    }
                    month_entry["decisions"].append(decision_entry)
                    (accepted_items if item_decision else skipped_items).append(item_id)
        
        month_entry["summary"]["accepted"] = sorted(accepted_items)
        month_entry["summary"]["skipped"] = sorted(skipped_items)
        
        if month_entry["decisions"]:  # Only add months with actual decisions
            order_history.append(month_entry)
    
    # Sort by month
    order_history.sort(key=lambda x: x["month"])
    
    return order_history


def build_prompt_variables(context: Dict[str, Any]) -> Dict[str, str]:
    pet_profile = _pet_to_profiles(context["pet"]) if context.get("pet") else {}
    # Optional profiles not tracked yet
    user_profile: Dict[str, Any] = {}
    order_history = _extract_order_history(context)

    weather = _weather_to_expected_shape(context.get("weather"))
    calendar = _calendar_to_expected_shape(context.get("calendar"))

    species = pet_profile.get("species")
    pc1 = "Dog" if species == "dog" else ("Cat" if species == "cat" else None)
    catalog_filters = {"pc1": pc1} if pc1 else {}

    return {
        "nowIso": context.get("nowIso", ""),
        "pet_profile_json": json.dumps(pet_profile, ensure_ascii=False),
        "user_profile_json": json.dumps(user_profile, ensure_ascii=False),
        "order_history_json": json.dumps(order_history, ensure_ascii=False),
        "weather_json": json.dumps(weather, ensure_ascii=False),
        "calendar_json": json.dumps(calendar, ensure_ascii=False),
        "catalog_filters_json": json.dumps(catalog_filters, ensure_ascii=False),
    }


