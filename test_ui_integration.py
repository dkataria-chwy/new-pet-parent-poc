#!/usr/bin/env python3
"""
Test script to verify the complete UI integration for on-demand recommendations.
This script tests the full flow from user query to product recommendations.
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import db

async def test_ui_integration():
    """Test the complete UI integration flow."""
    print("🧪 Testing UI Integration for On-Demand Recommendations")
    print("=" * 60)
    
    # Test data
    test_journey_id = "1c4083d7-bc29-4365-99c4-64dcff316555"
    test_query = "teething this week"
    
    try:
        # 1. Verify the journey exists in database
        print(f"📋 Checking journey: {test_journey_id}")
        journey = db.get_journey(test_journey_id)
        if not journey:
            print("❌ Journey not found in database")
            return False
            
        pet = db.get_pet(journey.pet_id)
        print(f"✅ Found pet: {pet.name} ({pet.species})")
        
        # 2. Test the API endpoint
        print(f"\n🔍 Testing API with query: '{test_query}'")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/on-demand-recommendations",
                json={
                    "user_query": test_query,
                    "journey_id": test_journey_id,
                    "top_k": 10
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
            result = response.json()
            
        # 3. Validate response structure
        print("✅ API Response received")
        
        required_fields = [
            "timestamp", "query_used", "rationale", "total_products", 
            "products", "user_query", "journey_id", "pet_name", "pet_species"
        ]
        
        for field in required_fields:
            if field not in result:
                print(f"❌ Missing field: {field}")
                return False
                
        print(f"✅ All required fields present")
        
        # 4. Validate products structure
        products = result["products"]
        if not products:
            print("❌ No products returned")
            return False
            
        print(f"✅ {len(products)} products returned")
        
        # Check first product structure
        first_product = products[0]
        product_fields = ["rank", "sku", "parentSKU", "name", "similarity"]
        
        for field in product_fields:
            if field not in first_product:
                print(f"❌ Missing product field: {field}")
                return False
                
        print("✅ Product structure valid")
        
        # 5. Display results summary
        print(f"\n📊 Results Summary:")
        print(f"   Pet: {result['pet_name']} ({result['pet_species']})")
        print(f"   Query: {result['user_query']}")
        print(f"   Enhanced Query: {result['query_used']}")
        print(f"   Products Found: {result['total_products']}")
        print(f"   Rationale Length: {len(result['rationale'])} chars")
        
        # Show top 3 products
        print(f"\n🏆 Top 3 Products:")
        for i, product in enumerate(products[:3], 1):
            print(f"   {i}. {product['name']} (SKU: {product['sku']}, Match: {product['similarity']:.1%})")
        
        print(f"\n✅ UI Integration Test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the integration test."""
    success = await test_ui_integration()
    
    if success:
        print("\n🎉 All tests passed! The UI integration is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Start the backend: cd backend && python main.py")
        print("   2. Start the frontend: cd frontend && npm run dev")
        print("   3. Test the UI at http://localhost:3000")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
