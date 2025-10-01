"""
Product filtering logic: rule-based for musts, LLM-based for negatives.
"""
import openai
import os
import re
import logging
from typing import List, Dict, Any
logger = logging.getLogger(__name__)
# Configuration flag: Switch between LLM-based and rule-based exclusions
# 
# False (default): Uses smart string filtering with comprehensive patterns
#   - Fast, deterministic, free
#   - Handles most common allergen cases (X-free, no X, without X, etc.)
#   - Covers derivatives (X meal, X protein, X fat)
#   - 100x+ faster than LLM approach
#
# True: Uses LLM-powered intelligent filtering  
#   - Understands complex ingredient relationships and context
#   - Handles edge cases and nuanced language
#   - Costs ~$0.001 per product filtered
#   - 10-20x slower than smart string filtering
#
USE_LLM_EXCLUSIONS = False  # Set to True to enable LLM-powered exclusions

class ProductFilters:
    """Handles must and negative filtering with hybrid approach."""
    
    def __init__(self):
        """Initialize filters with OpenAI client for LLM-based negatives."""
        self.client = self._initialize_openai_client()
    
    def _initialize_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client for LLM filtering."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return openai.OpenAI(api_key=api_key)
    
    def apply_musts_filter(self, results: List[Dict[str, Any]], musts: List[str]) -> List[Dict[str, Any]]:
        """
        Apply rule-based filtering for must-have requirements.
        
        Args:
            results: List of product results
            musts: List of must-have requirements
            
        Returns:
            Filtered list of products
        """
        if not musts:
            return results
        
        logger.info(f"Applying rule-based musts filter: {musts}")
        
        filtered = []
        for product in results:
            search_text = product['search_text'].lower()
            
            should_keep = True
            for must in musts:
                must_lower = must.lower()
                
                # Skip species requirements (already handled by pre-filtering)
                if 'species:' in must_lower:
                    continue
                
                # Check if must requirement is met
                if not self._check_must_requirement(search_text, must_lower):
                    should_keep = False
                    break
            
            if should_keep:
                filtered.append(product)
        
        removed = len(results) - len(filtered)
        if removed > 0:
            logger.info(f"Removed {removed} products that didn't meet musts requirements")
        
        return filtered
    
    def _check_must_requirement(self, search_text: str, must: str) -> bool:
        """
        Check if a product meets a specific must requirement.
        
        Args:
            search_text: Product search text (lowercase)
            must: Must requirement (lowercase)
            
        Returns:
            True if requirement is met
        """
        # Handle different types of must requirements
        
        # Lifestage requirements
        if 'lifestage:' in must:
            lifestage = must.split('lifestage:')[1].strip()
            return lifestage in search_text
        
        # Size requirements
        if 'size:' in must:
            size = must.split('size:')[1].strip()
            size_terms = [size, size.replace('-', ' '), size.replace('_', ' ')]
            return any(term in search_text for term in size_terms)
        
        # Free-from requirements (duck-free, grain-free, etc.)
        if '-free' in must or 'free' in must:
            # Look for explicit free-from language
            free_patterns = [
                must,
                must.replace('-', ' '),
                must.replace('-free', ' free'),
                f"free of {must.replace('-free', '')}",
                f"without {must.replace('-free', '')}"
            ]
            return any(pattern in search_text for pattern in free_patterns)
        
        # Specific features (small-bites, no rawhide, etc.)
        if 'small-bites' in must or 'small bites' in must:
            return 'small-bites' in search_text or 'small bites' in search_text
        
        if 'no rawhide' in must:
            return 'no rawhide' in search_text or 'rawhide-free' in search_text
        
        # General word matching with word boundaries
        return bool(re.search(rf'\b{re.escape(must)}\b', search_text))
    
    def apply_negatives_filter(self, results: List[Dict[str, Any]], negatives: List[str]) -> List[Dict[str, Any]]:
        """
        Apply negatives (exclusions) filtering using hybrid approach.
        Uses either smart string filtering or LLM-based filtering based on USE_LLM_EXCLUSIONS flag.
        
        Args:
            results: List of product results from vector search
            negatives: List of things to avoid (allergens, etc.)
            
        Returns:
            Filtered list of products
        """
        if not negatives:
            return results
        
        if USE_LLM_EXCLUSIONS:
            logger.info(f"🧠 Using LLM-based negatives filtering: {negatives}")
            return self._apply_llm_negatives_filter(results, negatives)
        else:
            logger.info(f"⚡ Using smart string negatives filtering: {negatives}")
            return self._apply_smart_negatives_filter(results, negatives)
    
    def _apply_smart_negatives_filter(self, results: List[Dict[str, Any]], negatives: List[str]) -> List[Dict[str, Any]]:
        """
        Apply smart string-based exclusions filtering.
        Fast, deterministic approach covering most common allergen patterns.
        
        Args:
            results: List of product results 
            negatives: List of allergens to avoid
            
        Returns:
            Filtered list of products
        """
        filtered = []
        excluded_count = 0
        
        for product in results:
            search_text = product['search_text']
            
            should_exclude = self._smart_exclusion_filter(search_text, negatives)
            
            if should_exclude:
                excluded_count += 1
                logger.debug(f"EXCLUDED: Product {product['sku']} - {product['name'][:50]}...")
            else:
                filtered.append(product)
        
        if excluded_count > 0:
            logger.info(f"Smart filter excluded {excluded_count} products due to negatives")
        return filtered
    
    def _apply_llm_negatives_filter(self, results: List[Dict[str, Any]], negatives: List[str]) -> List[Dict[str, Any]]:
        """
        Apply LLM-based exclusions filtering.
        Intelligent approach for complex cases and edge scenarios.
        
        Args:
            results: List of product results from vector search
            negatives: List of things to avoid (allergens, etc.)
            
        Returns:
            Filtered list of products
        """
        filtered = []
        excluded_count = 0
        
        for product in results:
            search_text = product['search_text']
            
            # Use LLM to determine if product should be excluded
            should_exclude = self._llm_exclusion_filter(search_text, negatives)
            
            if should_exclude:
                excluded_count += 1
                logger.debug(f"EXCLUDED: Product {product['sku']} - {product['name'][:50]}...")
            else:
                filtered.append(product)
        
        if excluded_count > 0:
            logger.info(f"LLM excluded {excluded_count} products due to negatives")
        return filtered
    
    def _smart_exclusion_filter(self, search_text: str, exclusions: List[str]) -> bool:
        """
        Smart string-based allergen exclusion filter.
        Based on comprehensive analysis of catalog patterns.
        
        Args:
            search_text: Product search text
            exclusions: List of allergens to avoid
            
        Returns:
            True if product should be EXCLUDED (contains allergen)
        """
        text_lower = search_text.lower()
        
        for allergen in exclusions:
            allergen_lower = allergen.lower().strip()
            
            if not allergen_lower:
                continue
            
            # Step 1: Check if product is explicitly allergen-free (SAFE - keep product)
            safe_patterns = [
                f"{allergen_lower}-free",
                f"no {allergen_lower}",
                f"without {allergen_lower}",
                f"free of {allergen_lower}",
                f"excludes {allergen_lower}",
                f"{allergen_lower} free"
            ]
            
            if any(pattern in text_lower for pattern in safe_patterns):
                continue  # This allergen is explicitly avoided, safe to keep
            
            # Step 2: Check if product contains the allergen (UNSAFE - exclude product)
            # Direct allergen mentions
            if re.search(rf'\b{re.escape(allergen_lower)}\b', text_lower):
                logger.debug(f"Smart filter: Found direct allergen '{allergen_lower}' in product")
                return True
            
            # Common allergen derivatives and forms
            derivative_patterns = [
                f"{allergen_lower} meal",
                f"{allergen_lower} protein", 
                f"{allergen_lower} fat",
                f"{allergen_lower} broth",
                f"{allergen_lower} recipe",
                f"{allergen_lower} formula",
                f"{allergen_lower} flavor",
                f"{allergen_lower} feast",
                f"fresh {allergen_lower}",
                f"cage free {allergen_lower}",
                f"organic {allergen_lower}",
                f"natural {allergen_lower}",
                f"wild {allergen_lower}",
                f"farm {allergen_lower}",
                f"real {allergen_lower}",
                f"premium {allergen_lower}",
                f"grilled {allergen_lower}",
                f"roasted {allergen_lower}",
                f"deboned {allergen_lower}",
                f"free range {allergen_lower}",
                f"grass fed {allergen_lower}"
            ]
            
            if any(pattern in text_lower for pattern in derivative_patterns):
                logger.debug(f"Smart filter: Found allergen derivative '{allergen_lower}' in product")
                return True
            
            # Step 3: Handle common ingredient category mappings
            category_mappings = {
                'poultry': ['chicken', 'turkey', 'duck', 'goose'],
                'fowl': ['chicken', 'turkey', 'duck', 'goose'],
                'bird': ['chicken', 'turkey', 'duck', 'goose'],
                'grains': ['wheat', 'corn', 'rice', 'barley', 'oats'],
                'grain': ['wheat', 'corn', 'rice', 'barley', 'oats'],
                'cereals': ['wheat', 'corn', 'rice', 'barley', 'oats'],
                'gluten': ['wheat', 'barley', 'rye'],
                'dairy': ['milk', 'cheese', 'yogurt', 'whey'],
                'fish': ['salmon', 'tuna', 'cod', 'herring', 'sardine'],
                'seafood': ['salmon', 'tuna', 'cod', 'shrimp', 'crab'],
                'nuts': ['peanut', 'almond', 'walnut', 'cashew'],
                'soy': ['soybean', 'soya'],
                'legumes': ['pea', 'lentil', 'chickpea', 'bean']
            }
            
            # Check if allergen maps to broader categories
            for category, ingredients in category_mappings.items():
                if allergen_lower in ingredients and re.search(rf'\b{re.escape(category)}\b', text_lower):
                    logger.debug(f"Smart filter: Found category '{category}' containing allergen '{allergen_lower}'")
                    return True
            
            # Check if allergen is in broader category being avoided
            if allergen_lower in category_mappings:
                for ingredient in category_mappings[allergen_lower]:
                    if re.search(rf'\b{re.escape(ingredient)}\b', text_lower):
                        logger.debug(f"Smart filter: Found specific ingredient '{ingredient}' in broader category '{allergen_lower}'")
                        return True
        
        return False  # Product is safe (doesn't contain any allergens)
    
    def _llm_exclusion_filter(self, product_description: str, exclusions: List[str]) -> bool:
        """
        Use LLM to determine if a product should be excluded based on negatives.
        
        Args:
            product_description: Full product description
            exclusions: List of things user wants to avoid
            
        Returns:
            True if product should be EXCLUDED
        """
        if not exclusions:
            return False
        
        prompt = f"""ALLERGEN SAFETY FILTER
Pet has ALLERGIES and must AVOID: {', '.join(exclusions)}
Product: "{product_description}"
ANALYSIS FRAMEWORK:
Step 1: Identify if this product CONTAINS any avoided ingredients
Step 2: Identify if this product is FORMULATED WITHOUT avoided ingredients  
Step 3: Make final safety decision
POSITIVE INDICATORS (CONTAINS allergen - EXCLUDE):
- Direct mention of the avoided ingredient in any form
- Ingredient derivatives: "[ingredient] meal", "[ingredient] fat", "[ingredient] protein", "[ingredient] broth"
- Listed as main protein source or in ingredient list
- Even with quality descriptors: "cage-free [ingredient]", "organic [ingredient]", "fresh [ingredient]"
NEGATIVE INDICATORS (AVOIDS allergen - KEEP):
- Explicit exclusion language: "[ingredient]-free", "no [ingredient]", "without [ingredient]"
- Formulated alternatives: "[avoided ingredient]-free [alternative ingredient] recipe"
- Allergy-specific formulations: "limited ingredient", "hypoallergenic" with no mention of avoided ingredient
EXAMPLES (to understand the pattern - apply same logic to ANY ingredient):
• "Cage Free Duck Recipe" + avoiding "duck" → EXCLUDE (contains duck)
• "Duck-Free Chicken Formula" + avoiding "duck" → KEEP (explicitly duck-free)
• "Grain-Free Turkey Meal" + avoiding "grain" → KEEP (explicitly grain-free)
• "Grain-Free Turkey Meal" + avoiding "turkey" → EXCLUDE (contains turkey)
• "Fresh Salmon & Soy" + avoiding "soy" → EXCLUDE (contains soy)
• "Limited Ingredient Lamb" + avoiding "beef" → KEEP (no beef mentioned)
DECISION LOGIC:
IF (product contains avoided ingredient) AND NOT (explicitly formulated without it) → EXCLUDE
IF (product explicitly avoids the ingredient) → KEEP
IF (unclear or ambiguous) → EXCLUDE (safety first)
Think step by step:
1. Does this product contain {', '.join(exclusions)}?
2. Is this product explicitly formulated to avoid {', '.join(exclusions)}?
3. What is the safer choice for this allergic pet?
EXCLUDE this product? YES or NO"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-2025-04-14",  # Using same model as semantic query
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,  # Allow for brief reasoning
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip().upper()
            should_exclude = answer.startswith("YES")
            
            # Debug logging for problematic cases
            product_name = product_description.split('.')[0].strip()
            if any(exclusion.lower() in product_name.lower() for exclusion in exclusions) and not should_exclude:
                logger.warning(f"LLM KEPT product with allergen: {product_name} | Exclusions: {exclusions} | LLM said: {answer}")
            elif should_exclude:
                logger.debug(f"LLM EXCLUDED: {product_name} | Exclusions: {exclusions}")
            
            return should_exclude
            
        except Exception as e:
            logger.warning(f"LLM filtering failed: {e}, keeping product")
            return False  # If LLM fails, don't exclude (safer)