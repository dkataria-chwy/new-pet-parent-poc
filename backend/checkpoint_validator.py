import os
import openai
from typing import Dict, Any
from dotenv import load_dotenv
from models import Pet, CheckpointValidationResponse, AIFollowUp, AIValidationOutput

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class CheckpointValidator:
    """AI-powered checkpoint validation service."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Use GPT-4.1 for checkpoint validation (faster and reliable)
        self.model = "gpt-4.1"
        if not self.api_key:
            print("🚨 WARNING: OPENAI_API_KEY not found! AI follow-ups will be disabled.")
            self.openai_client = None
        else:
            print(f"✅ OpenAI API key found, AI validation enabled (model: {self.model})")
            self.openai_client = openai.OpenAI(api_key=self.api_key)
    
    def validate_checkpoint_data(
        self, 
        pet: Pet, 
        current_data: Dict[str, Any], 
        previous_data: Dict[str, Any],
        days_elapsed: int = 30
    ) -> CheckpointValidationResponse:
        """
        Validate checkpoint data using AI and generate smart follow-ups.
        
        Args:
            pet: Pet object with current profile
            current_data: New checkpoint data from user
            previous_data: Previous profile data for comparison
            days_elapsed: Days since last checkpoint
            
        Returns:
            CheckpointValidationResponse with any follow-ups needed
        """
        try:
            # Check if OpenAI is available
            if not self.openai_client:
                print("❌ No OpenAI client available")
                return CheckpointValidationResponse(
                    hasAnomalies=False,
                    followUps=[],
                    confidence="low"
                )
            
            # Use AI for all validation
            ai_response = self._validate_with_ai(pet, current_data, previous_data, days_elapsed)
            return ai_response
            
        except Exception as e:
            import traceback
            print(f"🟥 VALIDATION ERROR: {e}")
            print(f"🟥 FULL TRACEBACK:")
            print(traceback.format_exc())
            # NO FALLBACK - let it fail so we can see the real issue
            raise e
    
    def _validate_with_ai(
        self, 
        pet: Pet, 
        current_data: Dict, 
        previous_data: Dict, 
        days_elapsed: int
    ) -> CheckpointValidationResponse:
        """Use AI with Pydantic structured outputs for validation."""
        
        print(f"🔍 Validation Input:")
        print(f"  Pet: {pet.name} ({pet.species}) - {pet.ageMonths} months")
        print(f"  Previous: weight={previous_data.get('weightLbs')}, chew={previous_data.get('chewStrength')}")
        print(f"  Current: weight={current_data.get('weightLbs')}, chew={current_data.get('chewStrength')}")
        print(f"  Health: {current_data.get('healthIssues', 'None')}")
        print(f"  Returns: {current_data.get('productReturns', 'None')}")
        
        # Build validation prompt with structured instructions
        prompt = f"""You are Chewy's Pet Profile Validator. Use veterinary knowledge to judge whether new checkpoint inputs are plausible for the pet's species, age, and breed-size. Identify only material issues that need human confirmation.

CONTEXT:
- Pet: {pet.name}, {pet.species}, {pet.ageMonths} months, {pet.breed}
- Previous: weight={previous_data.get('weightLbs', 'N/A')} lbs, height={previous_data.get('heightAtShoulderInches', 'N/A')} inches, chew={previous_data.get('chewStrength', 'N/A')}, activity={previous_data.get('activityLevel', 'N/A')}
- New: weight={current_data.get('weightLbs', 'N/A')} lbs, height={current_data.get('heightAtShoulderInches', 'N/A')} inches, chew={current_data.get('chewStrength', 'N/A')}, activity={current_data.get('activityLevel', 'N/A')}
- Health issues: {current_data.get('healthIssues', 'None')}
- Product returns: {current_data.get('productReturns', 'None')}
- Days since last update: {days_elapsed}

GUIDELINES:
- Flag fields that changed from previous values, OR where other evidence (returns, health issues) suggests a contradiction or mismatch, even if the field value itself did not change.
- Evaluate weight/height trends using age curves and breed-size expectations (toy/small/medium/large/giant). Factor in lifestage (puppy/kitten vs adult vs senior).
- Detect likely unit mix-ups (lb↔kg, in↔cm), obvious typos/transpositions, and implausible growth for the given age.
- Reconcile contradictions: chew strength vs returns; activity level vs health notes; sudden changes vs recent values.
- Ask at most 2 follow-ups total. Prefer 1 confirmation (e.g., unit check or big jump) plus 1 clarifier (if needed). Skip minor or explainable variation.
- If everything is reasonable, return hasAnomalies=false and an empty followUps array.

EXAMPLES:
- chewStrength="light", productReturns="toys too flimsy" → Flag chewStrength contradiction
- activityLevel="high", healthIssues="lethargic" → Flag activityLevel contradiction
- Weight 12→50 lbs in 30 days for puppy → Flag weightLbs unit mix-up
- Height 18→23 inches in month for adult dog → Flag heightAtShoulderInches growth anomaly

REQUIRED JSON OUTPUT FORMAT:
{{
  "hasAnomalies": boolean,
  "followUps": [
    {{
      "field": "weightLbs|heightAtShoulderInches|chewStrength|activityLevel",
      "question": "short, friendly clarification question",
      "explanation": "1 sentence, pet-centric reason for the question",
      "suggestedValue": "optional corrected value if confident"
    }}
  ],
  "confidence": "high|medium|low"
}}

Return ONLY the JSON object described above.
"""
        
        try:
            # Use regular chat completions with JSON mode for compatibility
            print("🔍 Using chat completions with JSON mode for checkpoint validation… gpt-4.1")
            completion = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a pet profile validation expert. You must respond with valid JSON that matches the AIValidationOutput schema."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=800,
            )
            
            # Parse the JSON response and validate with Pydantic
            import json
            ai_content = completion.choices[0].message.content
            print(f"🤖 AI Raw Response: {ai_content}")
            
            raw_result = json.loads(ai_content)
            ai_result = AIValidationOutput(**raw_result)
            print(f"🤖 AI Structured Response: hasAnomalies={ai_result.hasAnomalies}, followUps={len(ai_result.followUps)}")
            
            # Convert to the response format expected by the rest of the system
            followups = [
                AIFollowUp(
                    field=fu.field,
                    question=fu.question,
                    explanation=fu.explanation,
                    suggestedValue=fu.suggestedValue
                )
                for fu in ai_result.followUps
            ]

            return CheckpointValidationResponse(
                hasAnomalies=ai_result.hasAnomalies,
                followUps=followups,
                confidence=ai_result.confidence
            )
            
        except Exception as e:
            print(f"❌ Structured AI validation failed: {e}")
            return CheckpointValidationResponse(
                hasAnomalies=False,
                followUps=[],
                confidence="low"
            )

# Global validator instance
checkpoint_validator = CheckpointValidator()