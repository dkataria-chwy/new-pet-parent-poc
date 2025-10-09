"""
Stage 1 Structured Needs Analysis Runner
Generates pet needs analysis using the bucketed system (essentials/nice_to_haves/enrichment).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from openai import OpenAI, APITimeoutError
import time

# Load environment variables from project root
project_root = Path(__file__).resolve().parents[3]  # Navigate up to project root
load_dotenv(project_root / '.env')

from .context_builder import build_generation_context
from .variables import build_prompt_variables
from .prompt_loader import load_prompt, render_prompt

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Model selection
MODEL_SELECTION = "gpt-5-mini-2025-08-07"
MODEL_PRIMARY = "gpt-5-mini-2025-08-07"
MODEL_FALLBACK = "gpt-4.1-2025-04-14"


def _load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_schema() -> Dict[str, Any]:
    schema_path = TEMPLATES_DIR / "stage1_structured_schema.json"
    return json.loads(_load_text(schema_path))


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def _save_output(journey_id: str, month_idx: int, result_data: Dict[str, Any]) -> None:
    """Save stage 1 structured output to file."""
    try:
        backend_dir = Path(__file__).resolve().parents[2]
        outputs_dir = backend_dir / "testing" / "outputs" / "stage1_structured"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean old outputs for this journey+month
        for file in outputs_dir.glob(f"stage1_structured_{journey_short}_month{month_idx}_*.json"):
            _log(f"  Removing old: {file.name}")
            file.unlink()
        
        # Save new output
        output_file = outputs_dir / f"stage1_structured_{journey_short}_month{month_idx}_{timestamp}.json"
        output_file.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"✅ Saved output to: {output_file}")
        
    except Exception as e:
        _log(f"⚠️  Failed to save output: {e}")


def run_stage1_structured_analysis(
    journey_id: str,
    month_idx: int,
    tz: str = "America/Los_Angeles",
    model_name: str | None = None,
) -> Dict[str, Any]:
    """
    Run Stage 1 structured needs analysis with bucketing.
    
    Args:
        journey_id: Journey ID to analyze
        month_idx: Month index (0-14)
        tz: Timezone for context
        model_name: Optional model override
        
    Returns:
        Dict with bucketed needs analysis
    """
    _log("=" * 80)
    _log(f"STAGE 1 STRUCTURED: Bucketed Needs Analysis - Journey {journey_id[:8]}, Month {month_idx}")
    _log("=" * 80)
    
    # Initialize OpenAI client
    _log("Initializing OpenAI client...")
    client = OpenAI(timeout=180)
    
    # Build context (same as main system)
    _log("Building context...")
    context = build_generation_context(journey_id=journey_id, month_idx=month_idx, tz=tz)
    
    _log("Mapping variables...")
    variables = build_prompt_variables(context)
    
    # Load structured prompts
    _log("Loading structured prompts...")
    system_prompt = _load_text(TEMPLATES_DIR / "stage1_structured_system_prompt.md")
    user_template = load_prompt(str(TEMPLATES_DIR / "stage1_structured_user_prompt.md"))
    user_prompt = render_prompt(user_template, variables)
    
    # Load schema for validation
    schema = _load_schema()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    # Call model with retry
    def _create_with_retry(selected_model: str, msgs):
        last_err = None
        for attempt in range(3):
            try:
                return client.chat.completions.create(
                    model=selected_model,
                    messages=msgs,
                    response_format={"type": "json_object"},        
                )
            except APITimeoutError as e:
                last_err = e
                if attempt < 2:
                    _log(f"⚠️  Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    # Resolve model
    effective_model = model_name if model_name else MODEL_SELECTION
    
    _log(f"Calling model ({effective_model})...")
    resp = _create_with_retry(effective_model, messages)
    
    # Track token usage
    usage = resp.usage
    _log(f"Token usage - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
    
    text = resp.choices[0].message.content
    _log(f"Received {len(text)} characters")
    
    # Parse JSON
    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Model did not return valid JSON: {e}\n{text[:500]}")
    
    # Validate against schema
    try:
        _log("Validating against schema...")
        validate(instance=data, schema=schema)
        _log("✅ Validation passed!")
    except ValidationError as ve:
        _log(f"❌ Validation failed: {ve.message}")
        _log(f"Failed path: {'.'.join(str(p) for p in ve.path)}")
        raise
    
    # Fix total_categories count if incorrect
    actual_count = len(data.get("needs", []))
    reported_count = data.get("total_categories", 0)
    if actual_count != reported_count:
        _log(f"⚠️  Correcting total_categories: {reported_count} → {actual_count}")
        data["total_categories"] = actual_count
    
    # Add metadata with inputs used
    data["metadata"] = {
        "journey_id": journey_id,
        "pet_profile": json.loads(variables.get("pet_profile_json", "{}"))
    }
    
    # Print summary grouped by bucket
    needs = data.get("needs", [])
    _log(f"\n📋 Generated {len(needs)} needs:")
    
    # Group by bucket
    by_bucket = {"essentials": [], "nice_to_haves": [], "enrichment": []}
    for need in needs:
        bucket = need.get("bucket", "unknown")
        if bucket in by_bucket:
            by_bucket[bucket].append(need)
    
    _log(f"\n🏥 ESSENTIALS: {len(by_bucket['essentials'])} items")
    for need in by_bucket['essentials']:
        family = need.get("family", "unknown")
        priority = need.get("priority", "?")
        _log(f"    [{priority}] {family}")
    
    _log(f"\n🌟 NICE-TO-HAVES: {len(by_bucket['nice_to_haves'])} items")
    for need in by_bucket['nice_to_haves']:
        family = need.get("family", "unknown")
        priority = need.get("priority", "?")
        _log(f"    [{priority}] {family}")
    
    _log(f"\n🎁 ENRICHMENT: {len(by_bucket['enrichment'])} items")
    for need in by_bucket['enrichment']:
        family = need.get("family", "unknown")
        priority = need.get("priority", "?")
        _log(f"    [{priority}] {family}")
    
    # Save output
    _save_output(journey_id, month_idx, data)
    
    _log("\n" + "=" * 80)
    _log("STAGE 1 STRUCTURED COMPLETE")
    _log("=" * 80)
    
    return data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m backend.agents.semantic_query.run_stage1_structured <journey_id> <month_idx>")
        print("\nExample: python -m backend.agents.semantic_query.run_stage1_structured 1c4083d7 2")
        sys.exit(1)
    
    journey_id = sys.argv[1]
    month_idx = int(sys.argv[2])
    
    result = run_stage1_structured_analysis(journey_id, month_idx)
    
    # Print JSON to stdout for piping
    print(json.dumps(result, indent=2, ensure_ascii=False))

