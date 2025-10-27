#!/usr/bin/env python3
"""
Integration Test for On-Demand Recommendations

Tests the complete flow from frontend API call to backend response.
"""

import requests
import json

def test_integration():
    """Test the on-demand recommendations endpoint."""
    
    print("🧪 TESTING ON-DEMAND RECOMMENDATIONS INTEGRATION")
    print("=" * 60)
    
    # Test data
    test_request = {
        "user_query": "Max has been teething a lot lately",
        "journey_id": "1c4083d7-bc29-4365-99c4-64dcff316555",
        "top_k": 10
    }
    
    print(f"📤 Sending request:")
    print(f"   Query: '{test_request['user_query']}'")
    print(f"   Journey ID: {test_request['journey_id']}")
    print(f"   Top K: {test_request['top_k']}")
    
    try:
        # Make request to backend
        response = requests.post(
            "http://localhost:8000/on-demand-recommendations",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ SUCCESS! Received response:")
            print(f"   Pet: {data['pet_name']} ({data['pet_species']})")
            print(f"   Enhanced Query: {data['query_used']}")
            print(f"   Total Products: {data['total_products']}")
            print(f"   Rationale: {data['rationale'][:100]}...")
            
            if data['products']:
                print(f"\n🛍️  Sample Products:")
                for i, product in enumerate(data['products'][:3], 1):
                    print(f"   {i}. {product['sku']} (Parent: {product['parentSKU']}) - {product['name'][:50]}... (sim: {product['similarity']})")
            
            print(f"\n🎉 Integration test PASSED!")
            return True
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - is the backend server running on http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)
