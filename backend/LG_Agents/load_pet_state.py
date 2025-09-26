from __future__ import annotations
from typing import List, Optional, Literal, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from nppState import PetProfile, nppState, RetrievalParams

# ---------- Example usage ----------

def build_pet_profile(pet_id: int) -> PetProfile:
    if pet_id == 1:
        return PetProfile(
            species="dog",
            breed="Golden Retriever",
            gender="male",
            age_months=4,
            weight_lb=18.5,
            location_zip="78701", #Austin, TX
            habits=["chewer", "crate-trained", "likes to roll in mud", "destroyed couch", "loves to chew on shoes"],
            recent_conditions=["healthy", "ticks", "ordor", "outdoor", "does not play well with other dogs", "easy to overfeed"],
            geo_eventcondition=["heavy rain predicted in coming 2 weeks", "Halloween in coming 2 weeks"],
            recent_purchases=["kibble", "leash", "bed", "toy"]

        )
    elif pet_id == 2:
        return PetProfile(
            species="dog",
            breed="French Bulldog",
            gender="female",
            age_months=12,
            weight_lb=22.0,
            location_zip="33130", #Florida
            habits=["sensitive_skin", "indoor"],
            recent_conditions=["overweight", "sleeping disorder", "timid and shy"],
            geo_eventcondition=["heatwave predicted in coming 2 weeks", "bring pet to beer festival in 10 days"],
            recent_purchases=["kibble", "leash", "bed", "toy"]

        )
    elif pet_id == 3:
        return PetProfile(
            species="cat",
            breed="Maine Coon",
            gender="female",
            age_months=1,
            weight_lb=7.2,
            location_zip="60607", #Chicago, IL
            habits=["long-hair", "indoor", "likes to play with string"],
            recent_conditions=["healthy", "clean", "fights with other cats", "easily startled"],
            geo_eventcondition=["mild weather"],
            recent_purchases=["kibble", "leash", "bed", "toy"]

        )
    elif pet_id == 4:
        return PetProfile(
            species="dog",
            breed="Doberman",
            gender="male",
            age_months=5,
            weight_lb=7.2,
            location_zip="55418", #Minneapolis, MN
            habits=["aggressive", "teething", "hyperactive"],            
            recent_conditions=["healthy", "clean", "chew on shoes", "barks alot"],
            geo_eventcondition=["winter storm predicted in coming 2 weeks", "Christmas in 3 weeks"]
        )
    else:
        raise ValueError("Invalid pet ID. Choose 1, 2, 3, or 4.")

# ----------------------------
# Loader function
# ----------------------------

def load_pet_state(pet_id: int) -> nppState:
    pet = build_pet_profile(pet_id)
    return nppState(
        version="1.0",
        pet_id=f"P-{pet_id:03}",
        user_id=f"user-{pet_id}",
        pet=pet,
        slots=[],  # planner/enricher will fill these
        retrieval_params=RetrievalParams()
    )
