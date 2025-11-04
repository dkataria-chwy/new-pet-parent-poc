"""
API Handler for On-Demand Recommendations

Main orchestrator that processes user queries and returns personalized product recommendations.
Integrates query enhancement, pet profile fetching, and product search.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from query_enhancer import QueryEnhancer
from product_searcher import OnDemandProductSearcher
import database

logger = logging.getLogger(__name__)


class OnDemandRecommendationHandler:
    """Main handler for on-demand product recommendations."""
    
    def __init__(self):
        """Initialize the recommendation handler."""
        self.query_enhancer = QueryEnhancer()
        self.product_searcher = OnDemandProductSearcher()
        self.is_initialized = False
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize all components.
        
        Returns:
            Initialization statistics
        """
        logger.info("Initializing On-Demand Recommendation Handler...")
        
        # Initialize product searcher
        stats = self.product_searcher.initialize()
        
        self.is_initialized = True
        logger.info("✅ On-Demand Recommendation Handler ready!")
        
        return stats
    
    def process_recommendation_request(self, 
                                    user_query: str, 
                                    journey_id: str, 
                                    month_idx: int,
                                    top_k: int = 20) -> Dict[str, Any]:
        """
        Process a recommendation request from the UI.
        
        Args:
            user_query: The user's input describing their pet's situation
            journey_id: Journey ID to fetch pet profile
            month_idx: Current month index (to calculate accurate pet age)
            top_k: Number of products to return
            
        Returns:
            Dictionary with products, rationale, and metadata
        """
        if not self.is_initialized:
            raise ValueError("Handler not initialized. Call initialize() first.")
        
        logger.info(f"Processing recommendation request for journey: {journey_id}")
        logger.info(f"User query: '{user_query}'")
        logger.info(f"Month index: {month_idx}")
        
        try:
            # Step 1: Fetch pet profile from database (with current month age)
            pet_profile = self._fetch_pet_profile(journey_id, month_idx)
            logger.info(f"📋 Fetched profile for {pet_profile.get('name', 'Unknown')} ({pet_profile.get('species', 'Unknown')})")
            
            # Step 2: Enhance query using LLM
            context_data = {"pet_profile": pet_profile}
            enhancement_result = self.query_enhancer.enhance_query(user_query, context_data)
            
            queries = enhancement_result["queries"]
            overall_rationale = enhancement_result["overall_rationale"]
            
            logger.info(f"🧠 Generated {len(queries)} enhanced queries")
            
            # 🔍 DETAILED QUERY LOGGING
            print("\n" + "="*80)
            print("🧠 LLM GENERATED QUERIES & SLOTS")
            print("="*80)
            for idx, query in enumerate(queries, 1):
                print(f"\n📋 Query #{idx}:")
                print(f"   Top Family: {query.get('top_family', 'N/A')}")
                print(f"   Family: {query.get('family', 'N/A')}")
                print(f"   Embedding Query: {query.get('embedding_query', 'N/A')}")
                print(f"   Rationale: {query.get('rationale', 'N/A')}")
            print(f"\n💬 Overall Rationale:\n   {overall_rationale}")
            print("="*80 + "\n")
            
            # Step 3: Search for products using multiple queries
            species = pet_profile.get('species', 'Dog')
            brand_preferences = pet_profile.get('brand_preferences', [])
            
            balanced_products = []
            combined_query_used = []
            
            # NEW STRATEGY: Take top N from EACH query to ensure diversity
            products_per_query = max(7, 15 // len(queries))  # Aim for ~7 per query, adjust based on query count
            
            for idx, query in enumerate(queries, 1):
                embedding_query = query["embedding_query"]
                family = query["family"]
                
                # Search with larger pool to find best matches
                search_size = max(30, top_k * 2)
                
                print(f"\n🔎 Query #{idx} - Searching for: {family}")
                print(f"   Embedding Query: {embedding_query[:100]}...")
                
                products = self.product_searcher.search_products(
                    embedding_query=embedding_query,
                    species=species,
                    top_k=search_size,
                    brand_preferences=brand_preferences
                )
                
                top_sim = f"{products[0]['similarity']:.1%}" if products else "N/A"
                print(f"   📦 Found {len(products)} products, top similarity: {top_sim}")
                
                # Add family info to each product
                for product in products:
                    product["family"] = family
                    product["top_family"] = query["top_family"]
                    product["query_index"] = idx  # Track which query this came from
                
                # ✨ KEY CHANGE: Take only top N from THIS query (ensures diversity)
                top_from_query = products[:products_per_query]
                print(f"   ✅ Selected top {len(top_from_query)} products from this query for diversity")
                
                balanced_products.extend(top_from_query)
                combined_query_used.append(f"{family}: {embedding_query}")
            
            # Now we have balanced representation from each query
            # Sort by similarity within the balanced set
            balanced_products.sort(key=lambda x: x["similarity"], reverse=True)
            
            all_products = balanced_products
            
            print(f"\n🎨 DIVERSITY CHECK: Balanced pool has {len(all_products)} products from {len(queries)} queries")
            for idx in range(1, len(queries) + 1):
                count = sum(1 for p in all_products if p.get('query_index') == idx)
                print(f"   Query #{idx}: {count} products")
            
            print(f"\n🚀 Starting deduplication...")
            
            # Deduplicate by parentSKU - keep only the best match per parent product
            seen_parents = set()
            deduplicated_products = []
            
            print(f"🔍 Before deduplication: {len(all_products)} products")
            
            for product in all_products:
                parent_sku = product.get("parentSKU", product.get("sku"))
                query_idx = product.get("query_index", "?")
                family = product.get("family", "Unknown")
                
                if parent_sku not in seen_parents:
                    seen_parents.add(parent_sku)
                    deduplicated_products.append(product)
                    print(f"   ✅ Kept: [Q{query_idx}:{family}] Rank #{product['rank']} - {product['name'][:50]}... (Match: {product['similarity']:.1%})")
                    
                    # Stop when we have enough unique products (aim for 10)
                    if len(deduplicated_products) >= 10:
                        break
                else:
                    print(f"   ❌ Skipped duplicate: [Q{query_idx}] Rank #{product['rank']} - {product['name'][:50]}... (Parent: {parent_sku})")
            
            print(f"🎯 After deduplication: {len(deduplicated_products)} unique products")
            
            # Show final diversity breakdown
            print(f"\n📊 FINAL DIVERSITY BREAKDOWN:")
            for idx in range(1, len(queries) + 1):
                query_obj = queries[idx - 1]
                count = sum(1 for p in deduplicated_products if p.get('query_index') == idx)
                print(f"   Query #{idx} ({query_obj['family']}): {count} products")
            
            # Check if we have enough products for good UI experience
            if len(deduplicated_products) < 8:
                print(f"⚠️  Only {len(deduplicated_products)} unique products found (target: 10). Consider expanding search or adjusting deduplication.")
            
            # Re-rank the deduplicated products to fix sequence (1, 2, 3, 4, 5...)
            print(f"\n🔢 Re-ranking products...")
            for new_rank, product in enumerate(deduplicated_products, 1):
                original_rank = product['rank']
                product['rank'] = new_rank
                query_idx = product.get('query_index', '?')
                print(f"   #{new_rank}: [Q{query_idx}] {product['name'][:55]}...")
            
            final_products = deduplicated_products
            
            # Step 4: Format and return results
            result = self.product_searcher.format_results(
                products=final_products,
                rationale=overall_rationale,
                embedding_query=" | ".join(combined_query_used)
            )
            
            # Add request metadata
            result.update({
                "user_query": user_query,
                "journey_id": journey_id,
                "pet_name": pet_profile.get('name', 'Unknown'),
                "pet_species": species
            })
            
            logger.info(f"✅ Generated {len(final_products)} recommendations")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process recommendation request: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _fetch_pet_profile(self, journey_id: str, month_idx: int) -> Dict[str, Any]:
        """
        Fetch pet profile from database using journey_id.
        
        Args:
            journey_id: Journey identifier
            month_idx: Current month index (to calculate accurate pet age)
            
        Returns:
            Pet profile dictionary
        """
        try:
            # Get journey from database
            journey = database.db.get_journey(journey_id)
            if not journey:
                raise ValueError(f"Journey not found: {journey_id}")
            
            # Get pet from database
            pet = database.db.get_pet(journey.petId)
            if not pet:
                raise ValueError(f"Pet not found for journey: {journey_id}")
            
            # Calculate current age: initial age + month index (same as context_builder.py)
            current_age_months = pet.ageMonths + month_idx
            
            # Build pet profile using correct Pet model attributes
            # Match the structure from context_builder.py to ensure consistency
            pet_profile = {
                "name": pet.name,
                "species": getattr(pet.species, "value", pet.species) if hasattr(pet.species, "value") else pet.species,
                "breed": pet.breed,
                "age": f"{current_age_months} months",
                "ageMonths": current_age_months,  # Include both formats for compatibility
                "lifestage": self._get_lifestage(pet.species, current_age_months),
                "gender": getattr(pet.gender, "value", pet.gender) if pet.gender else None,
                "weightLbs": pet.weightLbs,
                "size": self._get_size_category(pet.weightLbs),
                "weight": f"{pet.weightLbs} lbs" if pet.weightLbs else "Unknown",
                "heightAtShoulderInches": pet.heightAtShoulderInches,
                "activityLevel": getattr(pet.activityLevel, "value", pet.activityLevel) if pet.activityLevel else None,
                "chewStrength": getattr(pet.chewStrength, "value", pet.chewStrength) if pet.chewStrength else None,
                "allergies": pet.allergies,
                "about": pet.about,
                "zipCode": pet.zipCode,
                "brand_preferences": self._parse_brand_preferences(pet.brandPreferences)
            }
            
            # Handle brand preferences - might be stored differently
            if not pet_profile["brand_preferences"]:
                # Try to get from user profile or set defaults
                pet_profile["brand_preferences"] = self._get_default_brands(pet.species)
            
            return pet_profile
            
        except Exception as e:
            logger.error(f"Failed to fetch pet profile for journey {journey_id}: {e}")
            raise
    
    def _get_lifestage(self, species: str, age_months: Optional[int]) -> str:
        """Determine lifestage based on species and age."""
        if not age_months:
            return "Unknown"
        
        if species and species.lower() == 'cat':
            if age_months < 12:
                return "kitten"
            elif age_months < 84:  # 7 years
                return "adult"
            else:
                return "senior"
        else:  # Default to dog
            if age_months < 12:
                return "puppy"
            elif age_months < 84:  # 7 years
                return "adult"
            else:
                return "senior"
    
    def _get_size_category(self, weight_lbs: Optional[float]) -> str:
        """Determine size category based on weight."""
        if not weight_lbs:
            return "Unknown"
        
        if weight_lbs < 25:
            return "small"
        elif weight_lbs < 60:
            return "medium"
        else:
            return "large"
    
    def _parse_brand_preferences(self, brand_preferences: Optional[str]) -> List[str]:
        """Parse brand preferences from string to list."""
        if not brand_preferences:
            return []
        
        # Split by comma and clean up
        brands = [brand.strip() for brand in brand_preferences.split(',') if brand.strip()]
        return brands
    
    def _get_default_brands(self, species: str) -> List[str]:
        """Get default brand preferences based on species."""
        if species and species.lower() == 'cat':
            return ["Hill's Science Diet", "Royal Canin", "Purina Pro Plan", "Feliway"]
        else:  # Default to dog
            return ["Hill's Science Diet", "Royal Canin", "Purina Pro Plan", "KONG", "Nylabone"]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            System status information
        """
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "components": {
                "query_enhancer": "ready",
                "product_searcher": "ready" if self.product_searcher.is_initialized else "not_initialized"
            }
        }


def main():
    """Test function for the API handler."""
    handler = OnDemandRecommendationHandler()
    
    try:
        # Initialize
        stats = handler.initialize()
        print(f"📊 Initialized with {stats['total_products']:,} products")
        
        # Test request
        test_query = "Max has been chewing everything lately"
        test_journey_id = "1c4083d7-bc29-4365-99c4-64dcff316555"  # Use a real journey ID
        
        print(f"\n🔍 Testing query: '{test_query}'")
        print(f"🆔 Journey ID: {test_journey_id}")
        
        result = handler.process_recommendation_request(
            user_query=test_query,
            journey_id=test_journey_id,
            top_k=10
        )
        
        print(f"\n🎉 Recommendation Results:")
        print(f"Pet: {result['pet_name']} ({result['pet_species']})")
        print(f"Enhanced Query: {result['query_used']}")
        print(f"Total Products: {result['total_products']}")
        print(f"Rationale: {result['rationale'][:150]}...")
        
        # Show first few products
        if result['products']:
            print(f"\n📋 Sample Products:")
            for i, product in enumerate(result['products'][:3], 1):
                print(f"{i}. {product['sku']} - {product['name'][:50]}... (sim: {product['similarity']})")
        
        # Health check
        health = handler.health_check()
        print(f"\n💚 Health Status: {health['status']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
