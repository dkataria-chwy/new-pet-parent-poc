#!/usr/bin/env python3
"""
Test script for Stage 1 Structured Needs Analysis
Tests the bucketed needs identification system (essentials/nice_to_haves/enrichment)
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

from agents.semantic_query.run_stage1_structured import run_stage1_structured_analysis

def test_structured_stage1_runner(journey_id=None, month_idx=None):
    print("🔍 Testing Stage 1 Structured Needs Analysis...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    if journey_id is None:
        journey_id = input("Enter a journey_id to test: ").strip()
    if month_idx is None:
        month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    
    # Smart clearing: only remove stage1_structured output files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting stage1_structured output files for {journey_short}_month{month_idx}...")
    # Remove stage1_structured output files for this exact journey+month combination
    structured_dir = outputs_dir / "stage1_structured"
    structured_dir.mkdir(exist_ok=True)
    for file in structured_dir.glob("stage1_structured_*.json"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
    
    try:
        print(f"\n🚀 Running Stage 1 structured needs analysis...")
        print(f"Journey ID: {journey_id}")
        print(f"Month Index: {month_idx}")
        
        result = run_stage1_structured_analysis(journey_id=journey_id, month_idx=month_idx)

        # Save outputs for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        output_file = outputs_dir / "stage1_structured" / f"stage1_structured_{journey_short}_month{month_idx}_{timestamp}.json"
        
        # Write JSON result
        output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n💾 Saved stage1_structured output to: {output_file}")
        
        print("\n✅ Stage 1 Structured Analysis Success!")
        
        # Display the result
        print(f"\n📊 Needs Analysis Summary:")
        
        needs = result.get("needs", [])
        print(f"Total Needs Identified: {len(needs)}")
        
        # Group by bucket
        by_bucket = {"essentials": [], "nice_to_haves": [], "enrichment": []}
        for need in needs:
            bucket = need.get("bucket", "unknown")
            if bucket in by_bucket:
                by_bucket[bucket].append(need)
        
        print(f"\n🪣 Breakdown by Bucket:")
        print(f"  • ESSENTIALS: {len(by_bucket['essentials'])} items")
        print(f"  • NICE-TO-HAVES: {len(by_bucket['nice_to_haves'])} items")
        print(f"  • ENRICHMENT: {len(by_bucket['enrichment'])} items")
        
        # Group by top_family and priority
        by_top_family = {}
        by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        
        for need in needs:
            top_fam = need.get("top_family", "unknown")
            if top_fam not in by_top_family:
                by_top_family[top_fam] = []
            by_top_family[top_fam].append(need)
            
            priority = need.get("priority", "medium")
            if priority in by_priority:
                by_priority[priority].append(need)
        
        print(f"\n📋 Breakdown by Department (top_family):")
        for top_fam, fam_needs in sorted(by_top_family.items()):
            families = set(n.get("family", "?") for n in fam_needs)
            print(f"  • {top_fam}: {len(fam_needs)} needs")
            for fam in sorted(families):
                fam_count = len([n for n in fam_needs if n.get("family") == fam])
                print(f"    - {fam}: {fam_count}")
        
        print(f"\n🎯 Breakdown by Priority:")
        for priority in ["critical", "high", "medium", "low"]:
            count = len(by_priority[priority])
            if count > 0:
                print(f"  • {priority.upper()}: {count} needs")
        
        print(f"\n📝 Sample Needs:")
        for i, need in enumerate(needs[:5], 1):
            bucket = need.get('bucket', '?')
            print(f"\n{i}. [{bucket.upper()}] [{need.get('priority', '?').upper()}] {need.get('top_family', '?')} → {need.get('family', '?')}")
            print(f"   Description: {need.get('description', '')[:100]}...")
            print(f"   Rationale: {need.get('rationale', '')[:100]}...")
            if need.get('negatives'):
                print(f"   Exclusions: {', '.join(need.get('negatives', []))}")
        
        if len(needs) > 5:
            print(f"\n   ... and {len(needs) - 5} more needs")
        
        print(f"\n📄 Full Generated JSON saved to: {output_file}")
        print(f"\nView with: cat {output_file}")
            
    except Exception as e:
        print(f"❌ Stage 1 Structured Analysis Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Accept command line arguments
    if len(sys.argv) >= 3:
        test_structured_stage1_runner(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) == 2:
        test_structured_stage1_runner(sys.argv[1])
    else:
        test_structured_stage1_runner()
