#!/usr/bin/env python3
"""
Subscription Optimizer Agent

Takes structured recommendations and intelligently categorizes products into:
- Subscription (recurring auto-ship for consumables)
- One-Time Purchase (durables, seasonal items, setup essentials)

Uses LLM's pet care expertise + contextual inputs to make smart purchasing decisions.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from openai import OpenAI, APITimeoutError
from jsonschema import validate, ValidationError
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Initialize OpenAI client
client = OpenAI()

# Model selection (matching Stage 2 pattern)
MODEL_PRIMARY = "gpt-5-mini-2025-08-07"
MODEL_FALLBACK = "gpt-4.1-2025-04-14"

def _log(msg: str):
    """Simple logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


class SubscriptionOptimizer:
    """Agent that optimizes subscription vs. one-time purchase decisions"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.system_prompt = self._load_template("subscription_optimizer_system_prompt.md")
        self.user_prompt_template = self._load_template("subscription_optimizer_user_prompt.md")
        self.schema = self._load_schema("subscription_optimizer_schema.json")
    
    def _load_template(self, filename: str) -> str:
        """Load a prompt template"""
        path = self.templates_dir / filename
        with open(path, 'r') as f:
            return f.read()
    
    def _load_schema(self, filename: str) -> Dict[str, Any]:
        """Load JSON schema"""
        path = self.templates_dir / filename
        with open(path, 'r') as f:
            return json.load(f)
    
    def _build_user_prompt(
        self,
        pet_profile: Dict[str, Any],
        month_idx: int,
        journey_id: str,
        recommended_products: List[Dict[str, Any]],
        order_history: List[Dict[str, Any]],
        weather_context: Dict[str, Any],
        calendar_context: Dict[str, Any]
    ) -> str:
        """Build the user prompt with all inputs"""
        
        # Determine journey context
        if month_idx <= 2:
            journey_context = "New pet (Month 1-2): Focus on essential setup items + initial consumables"
        elif month_idx <= 6:
            journey_context = "Establishing routine (Month 3-6): Transition to consumable subscriptions"
        else:
            journey_context = "Established pet (Month 7+): Optimize ongoing consumable subscriptions"
        
        # Format inputs as JSON strings
        prompt = self.user_prompt_template
        prompt = prompt.replace("{{pet_profile_json}}", json.dumps(pet_profile, indent=2))
        prompt = prompt.replace("{{month_idx}}", str(month_idx + 1))  # Convert 0-based to 1-based for display
        prompt = prompt.replace("{{journey_id}}", journey_id)
        prompt = prompt.replace("{{journey_context}}", journey_context)
        prompt = prompt.replace("{{order_history_json}}", json.dumps(order_history, indent=2))
        prompt = prompt.replace("{{weather_json}}", json.dumps(weather_context, indent=2))
        prompt = prompt.replace("{{calendar_json}}", json.dumps(calendar_context, indent=2))
        prompt = prompt.replace("{{recommended_products_json}}", json.dumps(recommended_products, indent=2))
        
        return prompt
    
    def optimize(
        self,
        recommendations_path: Path,
        order_history: List[Dict[str, Any]] = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Run subscription optimization on recommendations
        
        Args:
            recommendations_path: Path to recommendations_structured_*.json file
            order_history: List of previous orders (optional)
            model: OpenAI model to use
            temperature: Sampling temperature
        
        Returns:
            Dict with subscription_products, one_time_products, overall_strategy
        """
        _log(f"Loading recommendations from: {recommendations_path.name}")
        
        # Load recommendations file
        with open(recommendations_path, 'r') as f:
            recommendations = json.load(f)
        
        # Extract metadata from recommendations (inherited from Stage 1)
        metadata = recommendations.get("metadata", {})
        journey_id = metadata.get("journey_id", "unknown")
        pet_id = metadata.get("pet_id", recommendations.get("pet_id", "unknown"))  # Fallback to old location
        month_idx = metadata.get("month_idx", recommendations.get("month", 0))  # Fallback to old location
        pet_name = metadata.get("pet_name", "your pet")
        
        # Extract all products from all buckets
        results = recommendations.get("results", [])
        
        # Send ALL products from ALL slots to LLM - let LLM decide what to pick
        recommended_products = []
        for slot in results:  # All slots from all buckets
            if slot.get("products"):
                # Send ALL products from this slot (not just rank 1)
                for product in slot["products"]:
                    recommended_products.append({
                        "slot_id": slot["slot_id"],
                        "sku": product["sku"],
                        "product_name": product["name"],
                        "product_link": product.get("product_link", ""),
                        "product_price_current": product.get("product_price_current", None),
                        "autoship_eligible": product.get("autoship_eligible", False),
                        "top_family": slot["top_family"],
                        "bucket": slot["bucket"],
                        "rationale": slot.get("rationale", ""),
                        "similarity": product.get("similarity", 0.0),
                        "rank": product.get("rank", 0)
                    })
        
        _log(f"Analyzing {len(recommended_products)} products for subscription optimization")
        
        # Get pet profile with current age (initial age + month_idx)
        pet_profile = self._get_pet_profile(pet_id, month_idx)
        
        # Get weather/calendar context (simplified - load from actual sources if needed)
        weather_context = {"note": "Load from weather API if needed"}
        calendar_context = {"note": "Load from calendar API if needed"}
        
        # Default order history if not provided
        if order_history is None:
            order_history = []
        
        # Default to primary model if not specified
        if model is None:
            model = MODEL_PRIMARY
        
        # Build user prompt
        user_prompt = self._build_user_prompt(
            pet_profile=pet_profile,
            month_idx=month_idx,
            journey_id=journey_id,  # Use actual journey_id from metadata, not pet_id
            recommended_products=recommended_products,
            order_history=order_history,
            weather_context=weather_context,
            calendar_context=calendar_context
        )
        
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
                    response_format={"type": "json_object"}
                )
                
                # Parse response
                content = response.choices[0].message.content
                data = json.loads(content)
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
        
        # Pre-validation cleanup (matching Stage 2 pattern)
        data = self._cleanup_llm_output(data)
        
        # Validate against schema with retry logic
        max_retries = 3
        for retry_attempt in range(max_retries):
            try:
                validate(instance=data, schema=self.schema)
                _log("✅ Schema validation passed")
                break  # Success, exit retry loop
            except ValidationError as e:
                sub_count = len(data.get("subscription_products", []))
                one_time_count = len(data.get("one_time_products", []))
                
                _log(f"⚠️  Schema validation failed (attempt {retry_attempt + 1}/{max_retries})")
                _log(f"   Subscription products: {sub_count} (need 12-15)")
                _log(f"   One-time products: {one_time_count} (need 12-15)")
                _log(f"   ACTUAL ERROR: {e.message}")
                _log(f"   Error path: {'.'.join(str(p) for p in e.path) if e.path else 'root'}")
                
                if retry_attempt < max_retries - 1:
                    # Retry with feedback
                    _log(f"🔄 Retrying with corrective feedback...")
                    
                    feedback_prompt = f"""
IMPORTANT: Your previous response had an error. Please correct it:

- You provided {sub_count} subscription products, but need 12-15 (target 15)
- You provided {one_time_count} one-time products, but need 12-15 (target 15)

Please regenerate the COMPLETE response with:
- 12-15 subscription products (aim for 15 if suitable products exist)
- 12-15 one-time products (aim for 15 if suitable products exist)
- Use the same pet profile and recommendations as before
- Select additional products from different slot_ids if needed, but prioritize quality over quantity

{user_prompt}
"""
                    
                    retry_start = time.time()
                    retry_response = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": feedback_prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    content = retry_response.choices[0].message.content
                    data = json.loads(content)
                    data = self._cleanup_llm_output(data)
                    
                    retry_elapsed = time.time() - retry_start
                    _log(f"Retry completed in {retry_elapsed:.1f}s")
                    
                else:
                    # Final retry failed
                    _log(f"❌ Schema validation failed after {max_retries} attempts: {e.message}")
                    raise
        
        # Add metadata (inherit from recommendations and extend)
        data["metadata"] = {
            **metadata,  # Inherit journey_id, pet_id, month_idx, pet_name, pet_species from previous stages
            "stage": "stage4_subscription_optimizer",
            "model": model,
            "recommendations_source": str(recommendations_path),
            "generated_at": datetime.now().isoformat(),
            "tokens": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            },
            "elapsed_seconds": round(elapsed, 2)
        }
        
        return data
    
    def _cleanup_llm_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-validation cleanup to handle common LLM mistakes (matching Stage 2 pattern).
        """
        # Get schema required fields
        schema_sub = self.schema["properties"]["subscription_products"]["items"]
        schema_one = self.schema["properties"]["one_time_products"]["items"]
        required_sub = set(schema_sub.get("required", []))
        required_one = set(schema_one.get("required", []))
        
        # Clean subscription products
        if "subscription_products" in data:
            for product in data["subscription_products"]:
                # Remove extra fields not in schema
                allowed_fields = set(schema_sub["properties"].keys())
                extra_fields = set(product.keys()) - allowed_fields
                for field in extra_fields:
                    del product[field]
                
                # Add missing required fields with defaults
                for field in required_sub:
                    if field not in product:
                        if field == "personalized_note":
                            product[field] = ""
                        elif field == "estimated_frequency":
                            product[field] = "Monthly"
                        elif field == "product_link":
                            product[field] = ""
                        elif field == "product_price_current":
                            product[field] = None
                        elif field == "autoship_eligible":
                            product[field] = False
        
        # Clean one-time products
        if "one_time_products" in data:
            for product in data["one_time_products"]:
                # Remove extra fields not in schema
                allowed_fields = set(schema_one["properties"].keys())
                extra_fields = set(product.keys()) - allowed_fields
                for field in extra_fields:
                    del product[field]
                
                # Add missing required fields with defaults
                for field in required_one:
                    if field not in product:
                        if field == "personalized_note":
                            product[field] = ""
                        elif field == "product_link":
                            product[field] = ""
                        elif field == "product_price_current":
                            product[field] = None
                        elif field == "autoship_eligible":
                            product[field] = False
        
        return data
    
    def _get_pet_profile(self, pet_id: str, month_idx: int = 0) -> Dict[str, Any]:
        """
        Get pet profile directly from pet database with current age
        
        Args:
            pet_id: Pet's UUID
            month_idx: Current month index (to calculate current age)
        """
        from database import db
        
        # Load pet from database using pet_id (not journey_id!)
        pet = db.get_pet(pet_id)
        if not pet:
            _log(f"⚠️  Pet {pet_id} not found in database, using placeholder")
            return {
                "species": "dog",
                "breed": "Unknown",
                "age_months": 0,
                "weight_lb": 0.0,
                "name": "your pet"
            }
        
        # Calculate current age: initial age + month index (same pattern as Stage 1 & 2)
        current_age_months = pet.ageMonths + month_idx
        
        return {
            "name": pet.name,
            "species": pet.species.value if hasattr(pet.species, 'value') else str(pet.species),
            "breed": pet.breed,
            "age_months": current_age_months,
            "weight_lb": pet.weightLbs,
            "activity_level": pet.activityLevel.value if pet.activityLevel and hasattr(pet.activityLevel, 'value') else None,
            "chew_strength": pet.chewStrength.value if pet.chewStrength and hasattr(pet.chewStrength, 'value') else None,
            "allergies": pet.allergies,
            "brand_preferences": pet.brandPreferences,
            "environment": {
                "household_type": pet.householdType.value if pet.householdType and hasattr(pet.householdType, 'value') else None,
                "yard_access": pet.yardAccess.value if pet.yardAccess and hasattr(pet.yardAccess, 'value') else None,
                "zip_code": pet.zipCode
            }
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Subscription Optimizer")
    parser.add_argument(
        "recommendations_file",
        help="Path to recommendations_structured_*.json file"
    )
    parser.add_argument(
        "--model",
        default=MODEL_PRIMARY,
        help=f"OpenAI model to use (default: {MODEL_PRIMARY})"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: backend/testing/outputs/subscription_plans/)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    recommendations_path = Path(args.recommendations_file)
    if not recommendations_path.exists():
        print(f"❌ Recommendations file not found: {recommendations_path}")
        sys.exit(1)
    
    templates_dir = Path(__file__).parent / "templates"
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = backend_dir / "testing" / "outputs" / "subscription_plans"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize optimizer
    optimizer = SubscriptionOptimizer(templates_dir)
    
    # Run optimization
    try:
        result = optimizer.optimize(
            recommendations_path=recommendations_path,
            model=args.model
        )
        
        # Generate output filename
        journey_id = result["metadata"]["journey_id"]
        month_idx = result["metadata"]["month_idx"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use short journey ID for consistency with other stages
        journey_short = journey_id[:8] if isinstance(journey_id, str) and len(journey_id) > 8 else journey_id
        
        # Clean old outputs for this journey+month
        for file in output_dir.glob(f"subscription_plan_{journey_short}*_month{month_idx}_*.json"):
            _log(f"  Removing old: {file.name}")
            file.unlink()
        
        output_filename = f"subscription_plan_{journey_short}_month{month_idx}_{timestamp}.json"
        output_path = output_dir / output_filename
        
        # Save result
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        _log(f"✅ Saved subscription plan: {output_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("📦 SUBSCRIPTION OPTIMIZATION SUMMARY")
        print("="*80)
        
        print(f"\n🔄 SUBSCRIPTION PRODUCTS ({len(result['subscription_products'])} items):")
        for i, product in enumerate(result['subscription_products'], 1):
            print(f"\n{i}. {product['product_name']}")
            print(f"   Category: {product['top_family']} ({product['bucket']})")
            print(f"   Frequency: {product['estimated_frequency']}")
            print(f"   Rationale: {product['subscription_rationale'][:120]}...")
        
        print(f"\n\n🛒 ONE-TIME PURCHASE PRODUCTS ({len(result['one_time_products'])} items):")
        for i, product in enumerate(result['one_time_products'], 1):
            print(f"\n{i}. {product['product_name']}")
            print(f"   Category: {product['top_family']} ({product['bucket']})")
            print(f"   Rationale: {product['one_time_rationale'][:120]}...")
        
        print(f"\n\n💡 OVERALL STRATEGY:")
        print(f"   {result['overall_strategy']}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        _log(f"❌ Error during optimization: {e}")
        raise


if __name__ == "__main__":
    main()
