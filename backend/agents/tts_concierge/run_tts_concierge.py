#!/usr/bin/env python3
"""
TTS Concierge Summary Agent (Stage 5)

Generates a personalized 20-30 second spoken welcome message for the monthly
product selections. Designed to sound like a warm, knowledgeable concierge
presenting curated selections to a valued client.

Input: Stage 4 subscription plan + Pet profile
Output: 50-75 word spoken summary ready for TTS conversion
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from openai import OpenAI, APITimeoutError
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Initialize OpenAI client
client = OpenAI()

# Model selection (matching Stage 4 pattern)
MODEL_PRIMARY = "gpt-5-mini-2025-08-07"
MODEL_FALLBACK = "gpt-4.1-2025-04-14"

def _log(msg: str):
    """Simple logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


class TTSConciergeAgent:
    """Agent that generates personalized spoken summaries for TTS"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.system_prompt = self._load_template("tts_system_prompt.md")
        self.user_prompt_template = self._load_template("tts_user_prompt.md")
    
    def _load_template(self, filename: str) -> str:
        """Load a prompt template"""
        path = self.templates_dir / filename
        with open(path, 'r') as f:
            return f.read()
    
    def _get_pet_profile(self, pet_id: str, month_idx: int = 0) -> Dict[str, Any]:
        """Load pet profile from database with current age"""
        from database import db
        
        pet = db.get_pet(pet_id)
        if not pet:
            _log(f"⚠️  Pet {pet_id} not found in database")
            return {}
        
        # Calculate current age: initial age + month index (same pattern as Stage 1 & 2)
        current_age_months = pet.ageMonths + month_idx
        
        return {
            "name": pet.name,
            "species": pet.species.value if hasattr(pet.species, 'value') else str(pet.species),
            "breed": pet.breed,
            "age_months": current_age_months,
            "weight_lb": pet.weightLbs,
            "about": pet.about,
        }
    
    def _build_user_prompt(
        self,
        pet_profile: Dict[str, Any],
        subscription_plan: Dict[str, Any],
        month_idx: int
    ) -> str:
        """Build the user prompt from template"""
        
        # Use the template and replace placeholders
        prompt = self.user_prompt_template
        
        # Pass the ENTIRE subscription plan output
        prompt = prompt.replace("{{pet_profile_json}}", json.dumps(pet_profile, indent=2))
        prompt = prompt.replace("{{month_number}}", str(month_idx + 1))
        prompt = prompt.replace("{{subscription_plan_json}}", json.dumps(subscription_plan, indent=2))
        
        return prompt
    
    def generate_summary(
        self,
        subscription_plan_path: Path,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Generate TTS summary from subscription plan
        
        Args:
            subscription_plan_path: Path to Stage 4 subscription plan JSON
            model: OpenAI model to use (defaults to gpt-4o-mini)
        
        Returns:
            Dict with 'tts_summary' and metadata
        """
        _log(f"🎤 Generating TTS summary from {subscription_plan_path.name}")
        
        # Load subscription plan
        with open(subscription_plan_path) as f:
            subscription_plan = json.load(f)
        
        # Extract metadata
        metadata = subscription_plan.get("metadata", {})
        pet_id = metadata.get("pet_id")
        month_idx = metadata.get("month_idx", 0)
        
        if not pet_id:
            raise ValueError("Pet ID not found in subscription plan metadata")
        
        # Load pet profile with current age (initial age + month_idx)
        pet_profile = self._get_pet_profile(pet_id, month_idx)
        if not pet_profile:
            raise ValueError(f"Could not load pet profile for {pet_id}")
        
        # Build user prompt - LLM does all the work!
        user_prompt = self._build_user_prompt(
            pet_profile=pet_profile,
            subscription_plan=subscription_plan,
            month_idx=month_idx
        )
        
        # Default to primary model if not specified
        if model is None:
            model = MODEL_PRIMARY
        
        # Try primary model, fallback if needed
        data = None
        final_model = model
        start_time = time.time()
        
        for attempt_model in [model, MODEL_FALLBACK if model == MODEL_PRIMARY else None]:
            if attempt_model is None:
                continue
                
            try:
                _log(f"Calling OpenAI API with model: {attempt_model}")
                
                response = client.chat.completions.create(
                    model=attempt_model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    # temperature=0,
                    # max_tokens=450
                )
                
                tts_summary = response.choices[0].message.content.strip()
                final_model = attempt_model
                break
                
            except (APITimeoutError, Exception) as e:
                _log(f"⚠️  Model {attempt_model} failed: {e}")
                if attempt_model == MODEL_FALLBACK or model != MODEL_PRIMARY:
                    raise
                _log(f"Retrying with fallback model: {MODEL_FALLBACK}")
                continue
        
        elapsed = time.time() - start_time
        _log(f"API call completed in {elapsed:.1f}s using {final_model}")
        _log(f"📝 Summary ({len(tts_summary.split())} words): {tts_summary[:100]}...")
        
        # Generate audio file using OpenAI TTS with warm instructions
        _log("🎙️  Generating audio file with warm, empathetic voice...")
        audio_start = time.time()
        
        # Voice instructions for warm, pet-parent-friendly delivery
        voice_instructions = """Voice: Warm, empathetic, and professional, reassuring the customer that their issue is understood and will be resolved.\n\nPunctuation: Well-structured with natural pauses, allowing for clarity and a steady, calming flow.\n\nDelivery: Calm, excited and story teller, with a supportive and understanding tone that reassures the listener.\n\nPhrasing: Clear and concise, using customer-friendly language that avoids jargon while maintaining professionalism.\n\nTone: Empathetic and solution-focused, emphasizing both understanding and proactive assistance."""
        try:
            audio_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",  # New model with instructions support
                voice="fable",  # British, sympathetic
                input=tts_summary,
                instructions=voice_instructions
            )
            
            audio_elapsed = time.time() - audio_start
            _log(f"Audio generated in {audio_elapsed:.1f}s")
            
            # Return with audio content
            return {
                "tts_summary": tts_summary,
                "audio_content": audio_response.content,  # Binary MP3 data
                "word_count": len(tts_summary.split()),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model": final_model,
                    "voice": "fable",
                    "audio_model": "gpt-4o-mini-tts",
                    "elapsed_seconds": round(elapsed, 2),
                    "audio_elapsed_seconds": round(audio_elapsed, 2),
                    "tokens": {
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            }
        except Exception as audio_error:
            _log(f"⚠️  Audio generation failed: {audio_error}")
            # Return text-only result if audio fails
            return {
                "tts_summary": tts_summary,
                "audio_content": None,
                "word_count": len(tts_summary.split()),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model": final_model,
                    "elapsed_seconds": round(elapsed, 2),
                    "audio_error": str(audio_error),
                    "tokens": {
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens
                    }
                }
            }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run TTS Concierge Summary Generator (Stage 5)")
    parser.add_argument(
        "subscription_plan_file",
        help="Path to subscription_plan_*.json file from Stage 4"
    )
    parser.add_argument(
        "--model",
        default=MODEL_PRIMARY,
        help=f"OpenAI model to use (default: {MODEL_PRIMARY})"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: backend/agents/outputs/tts_summaries/)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    subscription_plan_path = Path(args.subscription_plan_file)
    if not subscription_plan_path.exists():
        print(f"❌ Subscription plan file not found: {subscription_plan_path}")
        sys.exit(1)
    
    templates_dir = Path(__file__).parent / "templates"
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = backend_dir / "agents" / "outputs" / "tts_summaries"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize agent
    agent = TTSConciergeAgent(templates_dir)
    
    # Generate summary
    try:
        result = agent.generate_summary(
            subscription_plan_path=subscription_plan_path,
            model=args.model
        )
        
        # Extract metadata from subscription plan for filename
        with open(subscription_plan_path) as f:
            plan_data = json.load(f)
        
        metadata = plan_data.get("metadata", {})
        journey_id = metadata.get("journey_id", "unknown")
        month_idx = metadata.get("month_idx", 0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use short journey ID for consistency
        journey_short = journey_id[:8] if isinstance(journey_id, str) and len(journey_id) > 8 else journey_id
        
        # Clean old outputs for this journey+month (both JSON and MP3)
        for file in output_dir.glob(f"tts_summary_{journey_short}*_month{month_idx}_*.*"):
            _log(f"  Removing old: {file.name}")
            file.unlink()
        
        # Generate output filenames
        base_filename = f"tts_summary_{journey_short}_month{month_idx}_{timestamp}"
        json_path = output_dir / f"{base_filename}.json"
        audio_path = output_dir / f"{base_filename}.mp3"
        
        # Save JSON (without binary audio_content)
        json_data = result.copy()
        audio_content = json_data.pop("audio_content", None)
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        _log(f"✅ Saved TTS summary: {json_path}")
        
        # Save audio file if generated
        if audio_content:
            with open(audio_path, 'wb') as f:
                f.write(audio_content)
            _log(f"✅ Saved audio file: {audio_path}")
        else:
            _log(f"⚠️  No audio file saved (generation failed)")
        
        # Print summary
        print("\n" + "="*80)
        print("🎤 TTS CONCIERGE SUMMARY (STAGE 5)")
        print("="*80)
        print(f"\n{result['tts_summary']}")
        print("\n" + "="*80)
        print(f"Word count: {result['word_count']} words")
        print(f"Model: {result['metadata']['model']}")
        print(f"Generated in: {result['metadata']['elapsed_seconds']}s")
        print(f"Tokens: {result['metadata']['tokens']['total']}")
        print("="*80)
        
    except Exception as e:
        _log(f"❌ Error during TTS summary generation: {e}")
        raise


if __name__ == "__main__":
    main()

