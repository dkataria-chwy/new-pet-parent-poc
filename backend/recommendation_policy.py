import os
from typing import List, Dict, Any
from models import Pet, JourneyState, RecommendationItem, MonthRecommendations
from database import db

class RecommendationPolicy:
    """Pluggable recommendation policy system."""
    
    def __init__(self, policy_type: str = "rules"):
        self.policy_type = os.getenv("AI_POLICY", policy_type)
    
    def get_baseline_recommendations(self, journey_id: str, month_idx: int) -> MonthRecommendations:
        """Get baseline recommendations for a month."""
        journey = db.get_journey(journey_id)
        if not journey:
            raise ValueError("Journey not found")
        
        pet = db.get_pet(journey.petId)
        if not pet:
            raise ValueError("Pet not found")
        
        if self.policy_type == "rules":
            return self._get_rules_based_recommendations(pet, journey, month_idx)
        elif self.policy_type == "llm":
            # Placeholder for LLM-based recommendations
            return self._get_llm_recommendations(pet, journey, month_idx)
        elif self.policy_type == "ml":
            # Placeholder for ML-based recommendations
            return self._get_ml_recommendations(pet, journey, month_idx)
        else:
            return self._get_rules_based_recommendations(pet, journey, month_idx)
    
    def get_ai_recommendations(self, journey_id: str, month_idx: int, note: str) -> Dict[str, Any]:
        """Get AI-generated recommendations based on user input."""
        journey = db.get_journey(journey_id)
        if not journey:
            raise ValueError("Journey not found")
        
        pet = db.get_pet(journey.petId)
        if not pet:
            raise ValueError("Pet not found")
        
        return self._process_ai_note(pet, journey, month_idx, note)
    
    def _get_rules_based_recommendations(self, pet: Pet, journey: JourneyState, month_idx: int) -> MonthRecommendations:
        """Simple rules-based recommendation engine."""
        
        # Basic recommendations based on pet age and species
        age_group = self._get_age_group(pet.ageMonths)
        
        # Generate summary why
        summary_why = f"For {pet.name}, a {age_group} {pet.species.value}, we've curated essentials focused on {self._get_life_stage_focus(age_group)}."
        
        # Base recommendations
        subscriptions = []
        bundles = []
        singles = []
        
        if pet.species.value == "dog":
            subscriptions = self._get_dog_subscriptions(pet, age_group, month_idx)
            bundles = self._get_dog_bundles(pet, age_group, month_idx)
            singles = self._get_dog_singles(pet, age_group, month_idx)
        else:  # cat
            subscriptions = self._get_cat_subscriptions(pet, age_group, month_idx)
            bundles = self._get_cat_bundles(pet, age_group, month_idx)
            singles = self._get_cat_singles(pet, age_group, month_idx)
        
        # Adjust based on journey history
        if month_idx > 0:
            subscriptions, bundles, singles = self._adjust_for_history(
                pet, journey, month_idx, subscriptions, bundles, singles
            )
        
        return MonthRecommendations(
            summaryWhy=summary_why,
            subscriptions=subscriptions,
            bundles=bundles,
            singles=singles
        )
    
    def _get_age_group(self, age_months: int) -> str:
        """Categorize pet by age."""
        if age_months <= 12:
            return "puppy" if age_months <= 6 else "young"
        elif age_months <= 84:  # 7 years
            return "adult"
        else:
            return "senior"
    
    def _get_life_stage_focus(self, age_group: str) -> str:
        """Get focus area for life stage."""
        focus_map = {
            "puppy": "healthy growth and training",
            "young": "energy and development", 
            "adult": "maintenance and wellness",
            "senior": "joint health and comfort"
        }
        return focus_map.get(age_group, "overall wellness")
    
    def _get_dog_subscriptions(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get dog subscription recommendations."""
        base_items = [
            RecommendationItem(
                id="sub_dog_food_1",
                title="Premium Adult Dog Food",
                subtitle="Tailored nutrition for daily energy",
                tags=["Premium", "Balanced"],
                price="$24.99",
                cadence="Every 4 weeks",
                whyForPet=f"Perfect protein balance supports {pet.name}'s daily activity level and {age_group} nutritional needs."
            ),
            RecommendationItem(
                id="sub_dog_treats_1",
                title="Training Treats Subscription",
                subtitle="Monthly variety of healthy rewards",
                tags=["Training", "Variety Pack"],
                price="$18.99",
                cadence="Every 4 weeks",
                whyForPet=f"Consistent training treats help reinforce {pet.name}'s good behavior with variety to keep training engaging."
            )
        ]
        
        if age_group == "puppy":
            base_items[0] = RecommendationItem(
                id="sub_puppy_food_1",
                title="Puppy Growth Formula",
                subtitle="Essential nutrients for growing pups",
                tags=["Puppy", "Growth", "DHA"],
                price="$28.99",
                cadence="Every 3 weeks",
                whyForPet=f"{pet.name} needs extra protein and DHA for healthy brain and body development during this crucial growth phase."
            )
            base_items.append(RecommendationItem(
                id="sub_puppy_vitamins_1",
                title="Puppy Vitamin Supplement",
                subtitle="Essential vitamins for healthy growth",
                tags=["Puppy", "Vitamins", "Growth"],
                price="$16.99",
                cadence="Every 6 weeks",
                whyForPet=f"Growing puppies like {pet.name} benefit from additional vitamins to support bone and immune system development."
            ))
        elif age_group == "senior":
            base_items.append(RecommendationItem(
                id="sub_joint_1",
                title="Joint Support Supplement",
                subtitle="Daily joint and mobility support",
                tags=["Senior", "Joint Health"],
                price="$19.99",
                cadence="Every 6 weeks",
                whyForPet=f"As {pet.name} ages, joint support helps maintain mobility and comfort for continued adventure."
            ))
        else:
            # Adult dogs get additional subscription option
            base_items.append(RecommendationItem(
                id="sub_dental_chews_1",
                title="Daily Dental Chews",
                subtitle="Convenient oral care solution",
                tags=["Dental", "Daily Care"],
                price="$22.99",
                cadence="Every 5 weeks",
                whyForPet=f"Regular dental care is essential for {pet.name}'s overall health and prevents costly dental issues later."
            ))
        
        return base_items
    
    def _get_dog_bundles(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get dog bundle recommendations."""
        bundles = [
            RecommendationItem(
                id="bundle_dental_1",
                title="Dental Care Bundle",
                subtitle="Complete oral health kit",
                tags=["Dental", "Bundle", "Save 15%"],
                price="$31.99",
                whyForPet=f"Dental health is crucial for {pet.name}'s overall wellness - this bundle makes daily care simple and effective."
            ),
            RecommendationItem(
                id="bundle_grooming_1",
                title="Grooming Essentials Bundle",
                subtitle="Everything for at-home grooming",
                tags=["Grooming", "Bundle", "Save 20%"],
                price="$45.99",
                whyForPet=f"Regular grooming keeps {pet.name} comfortable and healthy while strengthening your bond during care time."
            )
        ]
        
        if age_group == "puppy":
            bundles.append(RecommendationItem(
                id="bundle_puppy_starter_1",
                title="Puppy Starter Bundle",
                subtitle="Everything new puppy parents need",
                tags=["Puppy", "Starter Kit", "Save 25%"],
                price="$67.99",
                whyForPet=f"New puppy parents need reliable essentials - this bundle gives {pet.name} everything for a great start."
            ))
        elif age_group == "senior":
            bundles.append(RecommendationItem(
                id="bundle_comfort_1",
                title="Senior Comfort Bundle",
                subtitle="Comfort and mobility support",
                tags=["Senior", "Comfort", "Save 18%"],
                price="$52.99",
                whyForPet=f"Senior dogs like {pet.name} deserve extra comfort - this bundle addresses their changing needs."
            ))
        
        return bundles
    
    def _get_dog_singles(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get dog single item recommendations."""
        items = [
            RecommendationItem(
                id="single_toy_1",
                title="Enrichment Puzzle Toy",
                subtitle="Mental stimulation and fun",
                tags=["Toy", "Mental Health"],
                price="$12.99",
                whyForPet=f"Mental stimulation keeps {pet.name} engaged and helps prevent boredom-related behaviors."
            ),
            RecommendationItem(
                id="single_treat_1",
                title="Training Treats Variety Pack",
                subtitle="High-value rewards for training",
                tags=["Treats", "Training"],
                price="$8.99",
                whyForPet=f"Variety keeps training sessions exciting for {pet.name} and reinforces positive behaviors."
            )
        ]
        
        if age_group == "puppy":
            items.append(RecommendationItem(
                id="single_chew_toy_1",
                title="Puppy Teething Ring",
                subtitle="Safe relief for teething discomfort",
                tags=["Puppy", "Teething", "Safety"],
                price="$7.99",
                whyForPet=f"Teething puppies like {pet.name} need safe outlets to relieve discomfort and protect your furniture."
            ))
        elif age_group == "senior":
            items.append(RecommendationItem(
                id="single_orthopedic_1",
                title="Orthopedic Comfort Bed",
                subtitle="Joint-supporting sleep surface",
                tags=["Senior", "Orthopedic", "Comfort"],
                price="$34.99",
                whyForPet=f"Quality sleep on a supportive surface helps {pet.name}'s joints recover and stay comfortable."
            ))
        else:
            # Adult dogs get seasonal/monthly variety
            if month_idx % 2 == 0:
                items.append(RecommendationItem(
                    id="single_rope_toy_1",
                    title="Heavy-Duty Rope Toy",
                    subtitle="Durable tug and chew toy",
                    tags=["Toy", "Durable", "Interactive"],
                    price="$9.99",
                    whyForPet=f"Active dogs like {pet.name} need durable toys that can withstand enthusiastic play sessions."
                ))
            else:
                items.append(RecommendationItem(
                    id="single_supplement_1",
                    title="Skin & Coat Supplement",
                    subtitle="Supports healthy skin and shiny coat",
                    tags=["Supplement", "Skin", "Coat"],
                    price="$16.99",
                    whyForPet=f"A healthy coat reflects {pet.name}'s overall wellness and keeps them looking their best."
                ))
        
        return items
    
    def _get_cat_subscriptions(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get cat subscription recommendations."""
        return [
            RecommendationItem(
                id="sub_cat_food_1",
                title="Premium Indoor Cat Food",
                subtitle="Complete nutrition for indoor cats",
                tags=["Premium", "Indoor Formula"],
                price="$22.99",
                cadence="Every 4 weeks",
                whyForPet=f"Indoor cats like {pet.name} need specialized nutrition for optimal weight and digestion."
            )
        ]
    
    def _get_cat_bundles(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get cat bundle recommendations."""
        return [
            RecommendationItem(
                id="bundle_litter_1", 
                title="Litter & Wellness Bundle",
                subtitle="Monthly essentials combo",
                tags=["Litter", "Bundle", "Save 20%"],
                price="$28.99",
                whyForPet=f"This bundle covers {pet.name}'s monthly litter needs plus grooming essentials for convenience."
            )
        ]
    
    def _get_cat_singles(self, pet: Pet, age_group: str, month_idx: int) -> List[RecommendationItem]:
        """Get cat single item recommendations."""
        return [
            RecommendationItem(
                id="single_catnip_1",
                title="Organic Catnip Toy",
                subtitle="Natural enrichment and play",
                tags=["Toy", "Organic", "Enrichment"],
                price="$6.99",
                whyForPet=f"Natural play enrichment helps {pet.name} express hunting instincts in a healthy way."
            )
        ]
    
    def _adjust_for_history(self, pet: Pet, journey: JourneyState, month_idx: int, 
                           subscriptions: List[RecommendationItem], 
                           bundles: List[RecommendationItem], 
                           singles: List[RecommendationItem]) -> tuple:
        """Adjust recommendations based on journey history."""
        
        # Check previous decisions
        prev_month = str(month_idx - 1)
        if prev_month in journey.decisions:
            prev_decisions = journey.decisions[prev_month]
            
            # If they skipped all last month, suggest trials/samplers
            if all(not decision for decision in prev_decisions.values()):
                singles.append(RecommendationItem(
                    id="single_sampler_1",
                    title="Treat Sampler Pack",
                    subtitle="Try new flavors risk-free",
                    tags=["Sampler", "Trial Size"],
                    price="$4.99",
                    whyForPet=f"Let's find new favorites for {pet.name} with these small trial sizes."
                ))
        
        return subscriptions, bundles, singles
    
    def _process_ai_note(self, pet: Pet, journey: JourneyState, month_idx: int, note: str) -> Dict[str, Any]:
        """Process AI note and generate targeted recommendations."""
        note_lower = note.lower()
        
        # Simple keyword-based rules (would be replaced with real NLP/LLM)
        items = []
        summary = f"Based on your note about {pet.name}, here are some targeted suggestions:"
        
        if "teething" in note_lower:
            items.append({
                "section": "singles",
                "item": RecommendationItem(
                    id="ai_teething_1",
                    title="Teething Relief Toys",
                    subtitle="Soothing toys for teething discomfort",
                    tags=["Teething", "Relief", "AI Suggested"],
                    price="$9.99",
                    whyForPet=f"These specially designed toys will help soothe {pet.name}'s teething discomfort safely.",
                    isAIGenerated=True
                )
            })
            summary = f"Since {pet.name} is teething, I've added some soothing relief options to help with this phase."
        
        elif "energetic" in note_lower or "energy" in note_lower:
            items.append({
                "section": "singles",
                "item": RecommendationItem(
                    id="ai_energy_1",
                    title="High-Energy Exercise Toy",
                    subtitle="Channel that energy productively",
                    tags=["Exercise", "High Energy", "AI Suggested"],
                    price="$15.99",
                    whyForPet=f"This interactive toy will help {pet.name} burn energy in a fun, engaging way.",
                    isAIGenerated=True
                )
            })
            summary = f"Perfect! I've found some great ways to channel {pet.name}'s energy into positive play."
        
        elif "scratch" in note_lower or "itch" in note_lower:
            items.append({
                "section": "singles", 
                "item": RecommendationItem(
                    id="ai_skin_1",
                    title="Soothing Skin Care Spray",
                    subtitle="Natural relief for sensitive skin",
                    tags=["Skin Care", "Soothing", "AI Suggested"],
                    price="$12.99",
                    whyForPet=f"This gentle formula can help provide {pet.name} relief from skin irritation.",
                    isAIGenerated=True
                )
            })
            summary = f"I've added some gentle skin care options that might help {pet.name} feel more comfortable."
        
        elif "anxious" in note_lower or "anxiety" in note_lower:
            items.append({
                "section": "singles",
                "item": RecommendationItem(
                    id="ai_calm_1",
                    title="Calming Support Treats",
                    subtitle="Natural anxiety relief",
                    tags=["Calming", "Anxiety", "AI Suggested"],
                    price="$18.99",
                    whyForPet=f"These natural calming treats can help {pet.name} feel more relaxed and secure.",
                    isAIGenerated=True
                )
            })
            summary = f"I understand anxiety can be tough. These calming options may help {pet.name} feel more at ease."
        
        if not items:
            # Default response
            items.append({
                "section": "singles",
                "item": RecommendationItem(
                    id="ai_general_1",
                    title="Wellness Supplement",
                    subtitle="General health support",
                    tags=["Wellness", "AI Suggested"],
                    price="$14.99",
                    whyForPet=f"A great general wellness boost for {pet.name} based on your input.",
                    isAIGenerated=True
                )
            })
            summary = f"Thanks for the note about {pet.name}! I've added a wellness option that might help."
        
        return {
            "summary": summary,
            "items": items
        }
    
    def _get_llm_recommendations(self, pet: Pet, journey: JourneyState, month_idx: int) -> MonthRecommendations:
        """Placeholder for LLM-based recommendations."""
        # This would integrate with an LLM API
        return self._get_rules_based_recommendations(pet, journey, month_idx)
    
    def _get_ml_recommendations(self, pet: Pet, journey: JourneyState, month_idx: int) -> MonthRecommendations:
        """Placeholder for ML-based recommendations."""
        # This would integrate with an ML model
        return self._get_rules_based_recommendations(pet, journey, month_idx)

# Global policy instance
recommendation_policy = RecommendationPolicy()
