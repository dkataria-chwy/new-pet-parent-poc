#!/usr/bin/env python3
"""
Test script for prompt_loader.py
Tests template rendering with actual variables
"""

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# Change to backend directory so database path works correctly
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, str(backend_dir))

from agents.semantic_query.context_builder import build_generation_context
from agents.semantic_query.variables import build_prompt_variables
from agents.semantic_query.prompt_loader import load_prompt, render_prompt

def test_prompt_rendering():
    print("🔍 Testing Prompt Rendering...")
    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    journey_id = input("Enter a journey_id to test: ").strip()
    month_idx = int(input("Enter month index (0-based): ").strip() or "0")
    
    # Smart clearing: only remove prompt files for this exact journey+month combination
    journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
    
    print(f"🔄 Overwriting prompt files for {journey_short}_month{month_idx}...")
    # Remove prompt files for this exact journey+month combination
    for file in outputs_dir.glob("system_prompt_*.md"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
        elif file.name.startswith(f"system_prompt_{journey_short}_") and "month" not in file.name:
            print(f"  Removing old format (no month specified): {file.name}")
            file.unlink()
    for file in outputs_dir.glob("user_prompt_*.md"):
        if f"{journey_short}_month{month_idx}_" in file.name:
            print(f"  Removing: {file.name}")
            file.unlink()
        elif file.name.startswith(f"user_prompt_{journey_short}_") and "month" not in file.name:
            print(f"  Removing old format (no month specified): {file.name}")
            file.unlink()
    
    # Update run history
    run_history_file = outputs_dir / ".run_history"
    current_run = f"{journey_id}_month{month_idx}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Read existing history
    history = []
    if run_history_file.exists():
        try:
            history = run_history_file.read_text().strip().split('\n')
            history = [line for line in history if line.strip()]  # Remove empty lines
        except:
            history = []
    
    # Remove old entries for same journey+month (if any)
    history = [line for line in history if len(line.split()) >= 2 and line.split()[1] != current_run]
    
    # Add new entry at the top (latest first)
    new_entry = f"{timestamp} {current_run} prompt_rendering"
    history.insert(0, new_entry)
    
    # Keep only last 50 entries to prevent file from growing too large
    history = history[:50]
    
    # Write back to file
    run_history_file.write_text('\n'.join(history) + '\n')
    
    try:
        # Build context and variables
        print("\n1️⃣ Building context and variables...")
        context = build_generation_context(journey_id=journey_id, month_idx=month_idx)
        variables = build_prompt_variables(context)
        
        # Load templates
        print("\n2️⃣ Loading templates...")
        templates_dir = Path(__file__).parent.parent / "agents" / "semantic_query" / "templates"
        
        system_template = load_prompt(str(templates_dir / "system_prompt.md"))
        user_template = load_prompt(str(templates_dir / "semantic_query_prompt.md"))
        
        print(f"✅ Loaded system template ({len(system_template)} chars)")
        print(f"✅ Loaded user template ({len(user_template)} chars)")
        
        # Render prompts
        print("\n3️⃣ Rendering prompts...")
        rendered_user_prompt = render_prompt(user_template, variables)

        # Save outputs for this test run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        system_file = outputs_dir / f"system_prompt_{journey_short}_month{month_idx}_{timestamp}.md"
        user_file = outputs_dir / f"user_prompt_{journey_short}_month{month_idx}_{timestamp}.md"
        system_file.write_text(system_template, encoding='utf-8')
        user_file.write_text(rendered_user_prompt, encoding='utf-8')
        print(f"\n💾 Saved system prompt to: {system_file}")
        print(f"💾 Saved user prompt to: {user_file}")
        
        print("✅ Prompt Rendering Success!")
        
        print(f"\n📄 System Prompt ({len(system_template)} chars):")
        print("="*60)
        print(system_template[:500] + "..." if len(system_template) > 500 else system_template)
        
        print(f"\n📄 Rendered User Prompt ({len(rendered_user_prompt)} chars):")
        print("="*60)
        print(rendered_user_prompt)
        
        # Check for any unreplaced variables
        unreplaced = []
        for line in rendered_user_prompt.split('\n'):
            if '{{' in line and '}}' in line:
                unreplaced.append(line.strip())
        
        if unreplaced:
            print(f"\n⚠️ Found {len(unreplaced)} unreplaced variables:")
            for line in unreplaced:
                print(f"  {line}")
        else:
            print("\n✅ All variables successfully replaced!")
            
    except Exception as e:
        print(f"❌ Prompt Rendering Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt_rendering()
