#!/usr/bin/env python3
"""
Test script for Stage 2 Structured Query Generation
Tests the structured query generation system from Stage 1 structured needs
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Change to backend directory so database path works correctly
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, str(backend_dir))

from agents.semantic_query.run_stage2_structured import generate_queries

def test_stage2_structured_runner(journey_id=None, month_idx=None, stage1_output_path=None):
    print("🔍 Testing Stage 2 Structured Query Generation...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    if journey_id is None:
        journey_id = input("Enter a journey_id to test: ").strip()
    if month_idx is None:
        month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    if stage1_output_path is None:
        stage1_filename = input("Enter Stage 1 structured output filename (e.g., stage1_structured_needs_1c4083d7_month2_20251001_200724.json): ").strip()
        stage1_output_path = f"testing/outputs/stage1_structured/{stage1_filename}"
    
    # Smart clearing: only remove stage2_structured output files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting stage2_structured output files for {journey_short}_month{month_idx}...")
    # Remove stage2_structured output files for this exact journey+month combination
    stage2_dir = outputs_dir / "stage2_structured"
    stage2_dir.mkdir(exist_ok=True)
    for file in stage2_dir.glob("stage2_structured_queries_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
    
    try:
        print(f"\n🚀 Running Stage 2 structured query generation...")
        print(f"Journey ID: {journey_id}")
        print(f"Month Index: {month_idx}")
        print(f"Stage 1 Structured Output: {stage1_output_path}")
        
        result = generate_queries(journey_id, month_idx, stage1_output_path)

        # Save outputs for this test run (Stage 2 already saves, but we track it here too)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        output_file = outputs_dir / "stage2_structured" / f"stage2_structured_queries_{journey_short}_month{month_idx}_{timestamp}.json"
        
        # Write JSON result (backup copy)
        output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n💾 Saved stage2_structured output to: {output_file}")
        
        print("\n✅ Stage 2 Structured Query Generation Success!")
        
        # Display the result
        print(f"\n📊 Query Generation Summary:")
        
        queries = result.get("queries", [])
        total_queries = result.get("total_queries", 0)
        print(f"Total Queries Generated: {len(queries)}")
        
        if total_queries != len(queries):
            print(f"⚠️  WARNING: total_queries ({total_queries}) != actual queries ({len(queries)})")
        
        # Bucket breakdown
        buckets = {"essentials": 0, "nice_to_haves": 0, "enrichment": 0}
        for query in queries:
            bucket = query.get("bucket", "unknown")
            if bucket in buckets:
                buckets[bucket] += 1
        
        print(f"\n📦 Bucket Distribution:")
        print(f"  🏥 Essentials: {buckets['essentials']}")
        print(f"  🌟 Nice-to-Haves: {buckets['nice_to_haves']}")
        print(f"  🎁 Enrichment: {buckets['enrichment']}")
        
        # Quality checks
        print(f"\n🔎 Quality Checks:")
        
        # Check for allergens in embedding_query
        allergen_issues = []
        for i, query in enumerate(queries):
            emb = query.get('embedding_query', '').lower()
            if 'free' in emb or 'no-' in emb or '-free' in emb:
                allergen_issues.append(f"Query {i+1}")
        
        if allergen_issues:
            print(f"  ⚠️  Potential allergen issues found in {len(allergen_issues)} queries")
        else:
            print(f"  ✅ No allergen terms in embedding queries")
        
        # Check for missing species/lifestage
        missing_species = []
        for i, query in enumerate(queries):
            emb = query.get('embedding_query', '').lower()
            has_species = any(x in emb for x in ['dog', 'cat', 'puppy', 'kitten', 'adult', 'senior'])
            if not has_species:
                missing_species.append(f"Query {i+1}")
        
        if missing_species:
            print(f"  ⚠️  Missing species/lifestage in {len(missing_species)} queries")
        else:
            print(f"  ✅ All queries have species/lifestage")
        
        # Check for bucket field presence
        missing_bucket = []
        for i, query in enumerate(queries):
            if "bucket" not in query or query.get("bucket") not in ["essentials", "nice_to_haves", "enrichment"]:
                missing_bucket.append(f"Query {i+1}")
        
        if missing_bucket:
            print(f"  ⚠️  Missing or invalid bucket in {len(missing_bucket)} queries")
        else:
            print(f"  ✅ All queries have valid bucket field")
        
        print(f"\n📄 Full Generated JSON saved to: {output_file}")
        print(f"\nView with: cat {output_file}")
            
    except Exception as e:
        print(f"❌ Stage 2 Structured Query Generation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Accept command line arguments (flexible like Stage 1)
    if len(sys.argv) >= 4:
        # If full path provided, use as-is; if just filename, prepend path
        stage1_path = sys.argv[3] if "/" in sys.argv[3] else f"testing/outputs/stage1_structured/{sys.argv[3]}"
        test_stage2_structured_runner(sys.argv[1], int(sys.argv[2]), stage1_path)
    elif len(sys.argv) == 3:
        test_stage2_structured_runner(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) == 2:
        test_stage2_structured_runner(sys.argv[1])
    else:
        test_stage2_structured_runner()



