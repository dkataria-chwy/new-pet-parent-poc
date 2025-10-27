"""
Simple LLM Query Processor

Understands user search queries to extract:
1. What the user wants (positive search terms)
2. What they DON'T want (negative constraints/exclusions)
3. Brand preferences
"""

import openai
import os
import json
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class LLMQueryProcessor:
    """
    LLM-powered query processor that understands user intent and negative constraints.
    """
    
    def __init__(self, model: str = "gpt-5-2025-08-07"):
        """
        Initialize the LLM query processor.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model
        self.client = self._initialize_client()
        # Load environment variables if available (non-fatal if absent here)
        try:
            load_dotenv()
        except Exception:
            pass
    
    def _initialize_client(self) -> openai.OpenAI:
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return openai.OpenAI(api_key=api_key)

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user search query to understand intent and negative constraints.
        
        Args:
            user_query: Natural language search query
            
        Returns:
            Structured query analysis with positive terms and exclusions
        """
        logger.info(f"Processing query: '{user_query}'")
        
        prompt = f"""Analyze this pet product search query and extract what the user wants vs what they DON'T want:

Query: "{user_query}"

Return ONLY this JSON format:
{{
    "positive_terms": "everything from query EXCEPT negative terms",
    "exclusions": ["list of things to exclude/avoid"],
    "brand_preferences": ["mentioned brands"],
    "target_species": "dog/cat/both/unknown"
}}

Rules:
- "no X", "without X", "avoid X" = exclusions (remove from positive_terms)
- positive_terms = original query minus negative phrases
- Keep everything else intact (brands, ingredients, product types, etc.)"""

        last_error: Optional[Exception] = None
        for candidate_model in [self.model, "gpt-4o", "gpt-4-1106-preview"]:
            try:
                # Build params per-model (GPT-5 disallows temperature and uses max_completion_tokens)
                params = {
                    "model": candidate_model,
                    "messages": [
                        {"role": "system", "content": "You are a search query analyzer. Extract positive search terms and negative exclusions from pet product queries."},
                        {"role": "user", "content": prompt}
                    ]
                }
                if "gpt-5-2025-08-07" in candidate_model:
                    params["max_completion_tokens"] = 2000
                    # Do not pass temperature; GPT-5 only supports default
                else:
                    params["max_tokens"] = 2000
                    params["temperature"] = 0.1

                response = self.client.chat.completions.create(**params)
                
                result_text = response.choices[0].message.content.strip()
                
                # Clean up response
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                
                analysis = json.loads(result_text)
                analysis['original_query'] = user_query
                analysis['model_used'] = candidate_model
                
                return analysis
            except Exception as e:
                last_error = e
                logger.warning(f"Model '{candidate_model}' failed, trying next fallback: {e}")
                continue

        # All models failed; return safe fallback structure
        logger.error(f"LLM processing failed for all models: {last_error}")
        return {
            "positive_terms": user_query,
            "exclusions": [],
            "brand_preferences": [],
            "target_species": "unknown",
            "original_query": user_query,
            "fallback_used": True,
            "error": str(last_error) if last_error else "unknown"
        }
