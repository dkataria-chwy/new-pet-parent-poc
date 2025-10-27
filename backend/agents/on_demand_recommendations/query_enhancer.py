"""
Query Enhancement Module for On-Demand Recommendations

Combines user queries with pet context to generate optimized embedding queries
and personalized rationales using LLM.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """Enhances user queries with pet context using LLM."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize query enhancer.
        
        Args:
            model: OpenAI model to use for query enhancement
        """
        self.model = model
        self.openai_client = openai.OpenAI(timeout=180)
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from template file."""
        prompt_path = Path(__file__).parent / "templates" / "query_enhancement_prompt.md"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"System prompt not found at {prompt_path}")
            raise
    
    def enhance_query(self, user_query: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance user query with context to generate embedding query and rationale.
        
        Args:
            user_query: The user's input query about their pet
            context_data: Dictionary containing pet_profile with brand preferences
            
        Returns:
            Dictionary with embedding_query and rationale
        """
        logger.info(f"Enhancing query: '{user_query}'")
        
        # Build user prompt with context
        user_prompt = self._build_user_prompt(user_query, context_data)
        
        # Call OpenAI API
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse response
            raw_content = response.choices[0].message.content
            logger.info(f"🔍 Raw LLM response: {raw_content}")
            logger.info(f"🔍 Response length: {len(raw_content)} characters")
            
            try:
                result = json.loads(raw_content)
                logger.info(f"🔍 Parsed JSON keys: {list(result.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
                logger.error(f"❌ Raw content: {repr(raw_content)}")
                raise
            
            # Log token usage
            usage = response.usage
            logger.info(f"✅ Query enhanced successfully")
            logger.info(f"📊 Tokens: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
            
            # Handle both old and new formats for backward compatibility
            if "queries" in result and "overall_rationale" in result:
                # New multi-query format
                if not isinstance(result["queries"], list) or len(result["queries"]) == 0:
                    raise ValueError("queries must be a non-empty array")
                logger.info(f"✅ Using new multi-query format with {len(result['queries'])} queries")
                
            elif "embedding_query" in result and "rationale" in result:
                # Old single-query format - convert to new format
                logger.info("🔄 Converting old single-query format to new multi-query format")
                result = {
                    "queries": [{
                        "top_family": "Toys/Chews",  # Default fallback
                        "family": "Toys (General)",  # Default fallback
                        "embedding_query": result["embedding_query"],
                        "rationale": result["rationale"]
                    }],
                    "overall_rationale": result["rationale"]
                }
                
            else:
                logger.error(f"❌ Invalid LLM response format: {result}")
                raise ValueError("LLM response missing required fields: either (queries + overall_rationale) or (embedding_query + rationale)")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to enhance query: {e}")
            raise
    
    def _build_user_prompt(self, user_query: str, context_data: Dict[str, Any]) -> str:
        """Build the user prompt with query and context data."""
        
        pet_profile = context_data.get('pet_profile', {})
        
        prompt = f"""Please analyze this user query and generate an enhanced embedding query and rationale.

## User Query
"{user_query}"

## Pet Profile
- Name: {pet_profile.get('name', 'Unknown')}
- Species: {pet_profile.get('species', 'Unknown')}
- Breed: {pet_profile.get('breed', 'Unknown')}
- Age: {pet_profile.get('age', 'Unknown')}
- Lifestage: {pet_profile.get('lifestage', 'Unknown')}
- Size: {pet_profile.get('size', 'Unknown')}
- Weight: {pet_profile.get('weight', 'Unknown')}
- Activity Level: {pet_profile.get('activityLevel', 'Unknown')}
- Chew Strength: {pet_profile.get('chewStrength', 'Unknown')}
- Allergies: {pet_profile.get('allergies', 'None')}
- Brand Preferences: (not used in query generation)

Please generate a JSON response with an optimized embedding_query and detailed rationale for this specific pet and situation."""
        
        return prompt


def main():
    """Test function for query enhancer."""
    enhancer = QueryEnhancer()
    
    # Test data
    test_query = "Max has been chewing everything lately"
    test_context = {
        'pet_profile': {
            'name': 'Max',
            'species': 'Dog',
            'breed': 'Golden Retriever',
            'age': '4 months',
            'lifestage': 'Puppy',
            'size': 'Medium',
            'weight': '25 lbs',
            'brand_preferences': ['KONG', 'Nylabone', 'Hill\'s Science Diet']
        }
    }
    
    try:
        result = enhancer.enhance_query(test_query, test_context)
        print("🎉 Query Enhancement Result:")
        print(f"Embedding Query: {result['embedding_query']}")
        print(f"Rationale: {result['rationale']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
