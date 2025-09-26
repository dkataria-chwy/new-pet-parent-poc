from nppState import PetProfile, SlotSpec
from typing import List
import json
import os
from openai import OpenAI
from typing import Optional


# ----------------------------
# Minimal deterministic helpers (NOT business rules)
# ----------------------------

def _life_stage(species: str, age_months: int) -> str:
    s = (species or "").lower()
    if s == "dog":
        if age_months < 12: return "puppy"
        if age_months >= 96: return "senior"
        return "adult"
    # cat
    if age_months < 12: return "kitten"
    if age_months >= 120: return "senior"
    return "adult"


def _size_class(species: str, weight_lb: float) -> Optional[str]:
    s = (species or "").lower()
    w = weight_lb or 0.0
    if s == "dog":
        if w < 10: return "xs"
        if w < 20: return "s"
        if w < 50: return "m"
        if w < 90: return "l"
        return "xl"
    # cats: coarse bucket
    if w < 7: return "s"
    if w < 15: return "m"
    return "l"


def pet_context_helper(p: PetProfile) -> dict:
    """Slim, explicit context to ground the LLM."""
    return {
        "species": p.species,
        "breed": p.breed,
        "gender": p.gender,
        "age_months": p.age_months,
        "weight_lb": p.weight_lb,
        # "life_stage": _life_stage(p.species, p.age_months),
        # "size_class": _size_class(p.species, p.weight_lb),
        "location_zip": p.location_zip,
        "habits": getattr(p, "habits", []),
        "recent_conditions": getattr(p, "recent_conditions", []),
        # Support either field name if your profile varies
        "geo_eventcondition": getattr(p, "geo_eventcondition", getattr(p, "geo_condition", [])),
    }



   
