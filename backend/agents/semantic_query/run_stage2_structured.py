"""
Stage 2 Structured Query Generation Runner
Converts Stage 1 structured needs (with buckets) into search queries (embedding + BM25).
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
    schema_path = TEMPLATES_DIR / "stage2_structured_query_schema.json"
    return json.loads(_load_text(schema_path))


def _load_taxonomy() -> Dict[str, Any]:
    """Load product taxonomy from schema.json"""
    schema_path = TEMPLATES_DIR / "schema.json"
    schema = json.loads(_load_text(schema_path))
    
    # Extract enums from schema
    top_family_enum = schema["properties"]["slots"]["items"]["properties"]["top_family"]["enum"]
    family_enum = schema["properties"]["slots"]["items"]["properties"]["family"]["enum"]
    
    return {
        "top_family": top_family_enum,
        "family": family_enum
    }


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def _save_output(journey_id: str, month_idx: int, result_data: Dict[str, Any]) -> None:
    """Save stage 2 structured output to file."""
    try:
        backend_dir = Path(__file__).resolve().parents[2]
        outputs_dir = backend_dir / "testing" / "outputs" / "stage2_structured"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = outputs_dir / f"stage2_structured_queries_{journey_short}_month{month_idx}_{timestamp}.json"
        output_file.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"✅ Saved output to: {output_file}")
        
    except Exception as e:
        _log(f"⚠️  Failed to save output: {e}")




def generate_queries(
    journey_id: str,
    month_idx: int,
    stage1_output_path: str,
    tz: str = "America/Los_Angeles",
    model_name: str | None = None,
) -> Dict[str, Any]:
    """
    Generate Stage 2 structured queries from Stage 1 structured needs.
    
    Args:
        journey_id: Journey ID
        month_idx: Month index
        stage1_output_path: Path to Stage 1 structured output JSON
        tz: Timezone
        model_name: Optional model override
        
    Returns:
        Dict with queries and metadata
    """
    _log("=" * 80)
    _log(f"STAGE 2 STRUCTURED: Query Generation - Journey {journey_id[:8]}, Month {month_idx}")
    _log("=" * 80)
    
    # Initialize OpenAI client
    _log("Initializing OpenAI client...")
    client = OpenAI(timeout=180)
    
    # Load Stage 1 structured output
    stage1_path = Path(stage1_output_path)
    if not stage1_path.exists():
        raise FileNotFoundError(f"Stage 1 structured output not found: {stage1_path}")
    
    _log(f"📂 Loading Stage 1 structured output: {stage1_path}")
    with open(stage1_path, "r", encoding="utf-8") as f:
        stage1_data = json.load(f)
    
    actual_needs_count = len(stage1_data.get('needs', []))
    reported_count = stage1_data.get('total_categories', actual_needs_count)
    if actual_needs_count != reported_count:
        _log(f"📊 Stage 1 reports {reported_count} needs but actually has {actual_needs_count} needs (using actual count)")
    else:
        _log(f"📊 Stage 1 has {actual_needs_count} needs")
    
    # Build context (same as Stage 1)
    _log("Building context...")
    context = build_generation_context(journey_id=journey_id, month_idx=month_idx, tz=tz)
    
    _log("Mapping variables...")
    variables = build_prompt_variables(context)
    
    # Add Stage 1 data and taxonomy to variables
    _log("📚 Loading product taxonomy")
    taxonomy = _load_taxonomy()
    
    variables["stage1_needs_json"] = json.dumps(stage1_data, indent=2)
    variables["top_family_taxonomy"] = json.dumps(taxonomy["top_family"], indent=2)
    variables["family_taxonomy"] = json.dumps(taxonomy["family"], indent=2)
    
    # Load structured prompts
    _log("Loading stage 2 structured prompts...")
    system_prompt = _load_text(TEMPLATES_DIR / "stage2_structured_query_system_prompt.md")
    user_template = load_prompt(str(TEMPLATES_DIR / "stage2_structured_query_user_prompt.md"))
    user_prompt = render_prompt(user_template, variables)
    
    # Load schema for validation
    schema = _load_schema()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    # Call model with retry (same as Stage 1)
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
    
    # Clean up common LLM errors before validation using schema
    _log("Cleaning up LLM output...")
    queries = data.get("queries", [])
    fixed_count = 0
    
    # Get required and allowed fields from schema
    query_schema = schema["properties"]["queries"]["items"]
    required_fields = set(query_schema["required"])
    allowed_fields = set(query_schema["properties"].keys())
    
    # Define common typo mappings for each field
    field_variants = {
        "negatives": ["negativeS", "negals", "negative", "exclusions", "allergens"],
        "rationale": ["rationle", "rationale_extra_removed", "reason"],
        "top_family": ["topFamily", "top_fam"],
        "embedding_query": ["embeddingQuery", "embedding"],
        "bm25_query": ["bm25Query", "bm25"],
        "top_k": ["topK", "top_k_value", "k"]
    }
    
    for query in queries:
        # Fix missing required fields by looking for variants
        for required_field in required_fields:
            if required_field not in query:
                # Look for typo variants
                variants = field_variants.get(required_field, [])
                found = False
                for variant in variants:
                    if variant in query:
                        query[required_field] = query.pop(variant)
                        fixed_count += 1
                        _log(f"  ⚠️  Renamed '{variant}' → '{required_field}'")
                        found = True
                        break
                
                # If still missing, add default value
                if not found and required_field not in query:
                    if required_field == "negatives":
                        query[required_field] = []
                    elif required_field in ["rationale", "embedding_query", "bm25_query", "top_family", "family", "bucket"]:
                        query[required_field] = ""
                    elif required_field == "top_k":
                        query[required_field] = 10
                    fixed_count += 1
                    _log(f"  ⚠️  Added missing '{required_field}' with default value")
        
        # Remove extra fields not in schema
        extra_fields = set(query.keys()) - allowed_fields
        if extra_fields:
            for field in extra_fields:
                query.pop(field)
                fixed_count += 1
            _log(f"  ⚠️  Removed extra fields: {', '.join(extra_fields)}")
    
    if fixed_count > 0:
        _log(f"✅ Fixed {fixed_count} issues in LLM output")
    
    # Validate against schema
    try:
        _log("Validating against schema...")
        validate(instance=data, schema=schema)
        _log("✅ Validation passed!")
    except ValidationError as ve:
        _log(f"❌ Validation failed: {ve.message}")
        _log(f"Failed path: {'.'.join(str(p) for p in ve.path)}")
        raise
    
    # Fix total_queries count if incorrect (same pattern as Stage 1)
    actual_count = len(data.get("queries", []))
    reported_count = data.get("total_queries", 0)
    if actual_count != reported_count:
        _log(f"⚠️  Correcting total_queries: {reported_count} → {actual_count}")
        data["total_queries"] = actual_count
    
    # Print summary grouped by bucket
    queries = data.get("queries", [])
    _log(f"\n📋 Generated {len(queries)} queries:")
    
    # Group by bucket
    buckets = {
        "essentials": [],
        "nice_to_haves": [],
        "enrichment": []
    }
    
    for query in queries:
        bucket = query.get("bucket", "unknown")
        if bucket in buckets:
            buckets[bucket].append(query)
        else:
            # Handle unknown buckets
            if "unknown" not in buckets:
                buckets["unknown"] = []
            buckets["unknown"].append(query)
    
    # Print by bucket
    _log(f"\n🏥 ESSENTIALS ({len(buckets['essentials'])} queries):")
    for query in buckets['essentials']:
        family = query.get("family", "?")
        top_k = query.get("top_k", "?")
        _log(f"   [{top_k}] {family}")
    
    _log(f"\n🌟 NICE-TO-HAVES ({len(buckets['nice_to_haves'])} queries):")
    for query in buckets['nice_to_haves']:
        family = query.get("family", "?")
        top_k = query.get("top_k", "?")
        _log(f"   [{top_k}] {family}")
    
    _log(f"\n🎁 ENRICHMENT ({len(buckets['enrichment'])} queries):")
    for query in buckets['enrichment']:
        family = query.get("family", "?")
        top_k = query.get("top_k", "?")
        _log(f"   [{top_k}] {family}")
    
    if "unknown" in buckets and buckets["unknown"]:
        _log(f"\n⚠️  UNKNOWN BUCKET ({len(buckets['unknown'])} queries):")
        for query in buckets["unknown"]:
            family = query.get("family", "?")
            top_k = query.get("top_k", "?")
            _log(f"   [{top_k}] {family}")
    
    # Add metadata (including pet_profile for quick reference)
    data["metadata"] = {
        "journey_id": journey_id,
        "month_idx": month_idx,
        "pet_profile": json.loads(variables.get("pet_profile_json", "{}")),
        "model": effective_model,
        "stage1_source": str(stage1_path),
        "generated_at": datetime.now().isoformat(),
        "tokens": {
            "prompt": usage.prompt_tokens,
            "completion": usage.completion_tokens,
            "total": usage.total_tokens
        },
        "elapsed_seconds": round(time.time() - time.time(), 2)  # Will be updated if needed
    }
    
    # Save output
    _save_output(journey_id, month_idx, data)
    
    _log("\n" + "=" * 80)
    _log("STAGE 2 STRUCTURED COMPLETE")
    _log("=" * 80)
    
    return data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m backend.agents.semantic_query.run_stage2_structured <journey_id> <month_idx> [stage1_structured_output_path]")
        sys.exit(1)
    
    journey_id = sys.argv[1]
    month_idx = int(sys.argv[2])
    stage1_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = generate_queries(journey_id, month_idx, stage1_path)
    print(json.dumps(result, indent=2))



