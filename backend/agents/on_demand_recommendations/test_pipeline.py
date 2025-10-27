"""
Test Script for On-Demand Recommendations Pipeline

Validates the complete pipeline from user query to product recommendations.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api_handler import OnDemandRecommendationHandler


def test_pipeline():
    """Test the complete on-demand recommendations pipeline."""
    
    print("🚀 TESTING ON-DEMAND RECOMMENDATIONS PIPELINE")
    print("=" * 60)
    
    # Initialize handler
    print("\n📊 Initializing system...")
    handler = OnDemandRecommendationHandler()
    
    try:
        stats = handler.initialize()
        print(f"✅ System ready with {stats['total_products']:,} products")
        print(f"   🐕 Dog products: {stats['dog_products']:,}")
        print(f"   🐱 Cat products: {stats['cat_products']:,}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test cases
    test_cases = [
        {
            "name": "Teething Puppy",
            "query": "Max has been chewing everything lately",
            "journey_id": "1c4083d7-bc29-4365-99c4-64dcff316555",
            "expected_facets": ["teething", "chew", "puppy"]
        },
        {
            "name": "Energetic Dog", 
            "query": "My dog has too much energy and needs more exercise",
            "journey_id": "1c4083d7-bc29-4365-99c4-64dcff316555",
            "expected_facets": ["exercise", "energy", "toys"]
        },
        {
            "name": "Anxious Pet",
            "query": "Luna seems stressed and hiding a lot",
            "journey_id": "1c4083d7-bc29-4365-99c4-64dcff316555", 
            "expected_facets": ["anxiety", "calming", "stress"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Query: '{test_case['query']}'")
        
        try:
            # Process recommendation
            result = handler.process_recommendation_request(
                user_query=test_case['query'],
                journey_id=test_case['journey_id'],
                top_k=10
            )
            
            # Validate results
            validation = validate_result(result, test_case)
            results.append({
                "test_case": test_case['name'],
                "success": validation['success'],
                "result": result,
                "validation": validation
            })
            
            # Display results
            print(f"✅ Pet: {result['pet_name']} ({result['pet_species']})")
            print(f"🧠 Enhanced Query: {result['query_used']}")
            print(f"📊 Products Found: {result['total_products']}")
            print(f"💡 Rationale: {result['rationale'][:100]}...")
            
            if result['products']:
                print(f"🛍️  Top Products:")
                for j, product in enumerate(result['products'][:3], 1):
                    print(f"   {j}. {product['sku']} - {product['name'][:40]}... (sim: {product['similarity']})")
            
            # Validation feedback
            if validation['success']:
                print(f"✅ Validation: PASSED")
            else:
                print(f"⚠️  Validation: {validation['issues']}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    for result in results:
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"{status} - {result['test_case']}")
        if not result.get('success', False) and 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Save detailed results
    save_test_results(results)
    
    return passed == total


def validate_result(result: dict, test_case: dict) -> dict:
    """Validate a recommendation result."""
    
    issues = []
    
    # Check required fields
    required_fields = ['products', 'rationale', 'query_used', 'pet_name', 'pet_species']
    for field in required_fields:
        if field not in result:
            issues.append(f"Missing field: {field}")
    
    # Check products
    if 'products' in result:
        if not result['products']:
            issues.append("No products returned")
        elif len(result['products']) < 5:
            issues.append(f"Only {len(result['products'])} products (expected at least 5)")
        
        # Check product structure
        for i, product in enumerate(result['products'][:3]):
            required_product_fields = ['sku', 'name', 'similarity', 'parentSKU']
            for field in required_product_fields:
                if field not in product:
                    issues.append(f"Product {i+1} missing field: {field}")
    
    # Check embedding query contains expected facets
    if 'query_used' in result:
        query_lower = result['query_used'].lower()
        found_facets = []
        for facet in test_case.get('expected_facets', []):
            if facet.lower() in query_lower:
                found_facets.append(facet)
        
        if len(found_facets) == 0:
            issues.append(f"Query doesn't contain expected facets: {test_case['expected_facets']}")
    
    # Check rationale quality
    if 'rationale' in result:
        rationale = result['rationale']
        if len(rationale) < 50:
            issues.append("Rationale too short (< 50 characters)")
        if 'pet_name' in result and result['pet_name'].lower() not in rationale.lower():
            issues.append("Rationale doesn't mention pet name")
    
    return {
        "success": len(issues) == 0,
        "issues": issues,
        "found_facets": found_facets if 'query_used' in result else []
    }


def save_test_results(results: list):
    """Save test results to file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(__file__).parent / f"test_results_{timestamp}.json"
    
    test_summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "passed_tests": sum(1 for r in results if r.get('success', False)),
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_summary, f, indent=2)
    
    print(f"\n💾 Detailed results saved: {output_file}")


def main():
    """Main test runner."""
    
    success = test_pipeline()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED! On-demand recommendations pipeline is working correctly.")
        exit(0)
    else:
        print(f"\n💥 SOME TESTS FAILED! Check the results above for details.")
        exit(1)


if __name__ == "__main__":
    main()
