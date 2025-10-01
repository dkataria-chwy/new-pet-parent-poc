from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from openai import OpenAI, APITimeoutError
import time
from datetime import datetime
import sys

"""
Model selection flag (set here).

Options:
- "gpt-5-2025-08-07"  (primary)
- "gpt-4.1-2025-04-14" (fallback/alternative)
- "auto" (try primary, then fallback on timeout)
"""
# MODEL_SELECTION = "gpt-4.1-2025-04-14"
MODEL_SELECTION = "gpt-5-mini-2025-08-07"

# Canonical model IDs
MODEL_PRIMARY = "gpt-5-2025-08-07"
MODEL_FALLBACK = "gpt-4.1-2025-04-14"

from .context_builder import build_generation_context
from .variables import build_prompt_variables
from .prompt_loader import load_prompt, render_prompt


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_schema() -> Dict[str, Any]:
    schema_path = TEMPLATES_DIR / "schema.json"
    return json.loads(_load_text(schema_path))


def _create_relaxed_schema(original_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Create a relaxed schema that skips enum validation for top_family and family."""
    import copy
    relaxed_schema = copy.deepcopy(original_schema)
    
    try:
        # Navigate to slots.items.properties
        slot_props = relaxed_schema["properties"]["slots"]["items"]["properties"]
        
        # Remove enum constraints for top_family and family, keep them as strings
        if "top_family" in slot_props and "enum" in slot_props["top_family"]:
            slot_props["top_family"] = {"type": "string"}
            
        if "family" in slot_props and "enum" in slot_props["family"]:
            slot_props["family"] = {"type": "string"}
            
    except KeyError as e:
        _log(f"Warning: Could not relax schema structure: {e}")
    
    return relaxed_schema


def _extract_schema_enums(schema: Dict[str, Any]) -> Dict[str, str]:
    """Extract enum values from schema for template rendering."""
    try:
        slot_props = schema["properties"]["slots"]["items"]["properties"]
        
        # Extract top_family enums
        top_family_enums = slot_props.get("top_family", {}).get("enum", [])
        top_family_str = ", ".join(f'"{enum}"' for enum in top_family_enums)
        
        # Extract family enums
        family_enums = slot_props.get("family", {}).get("enum", [])
        # Format family enums in a more readable way (limit to avoid overwhelming)
        family_str = ", ".join(f'"{enum}"' for enum in family_enums[:50])  # Show first 50
        if len(family_enums) > 50:
            family_str += f", ... and {len(family_enums) - 50} more"
        
        return {
            "top_family_enums": top_family_str,
            "family_enums": family_str
        }
    except Exception as e:
        _log(f"Warning: Could not extract schema enums: {e}")
        return {
            "top_family_enums": "Schema enums not available",
            "family_enums": "Schema enums not available"
        }


def _validate_enum_values(data: Dict[str, Any], original_schema: Dict[str, Any]) -> None:
    """Log warnings for unknown enum values without failing validation."""
    try:
        # Extract valid enums from original schema
        slot_props = original_schema["properties"]["slots"]["items"]["properties"]
        valid_top_families = set(slot_props.get("top_family", {}).get("enum", []))
        valid_families = set(slot_props.get("family", {}).get("enum", []))
        
        # Check each slot for unknown values
        slots = data.get("slots", [])
        for i, slot in enumerate(slots):
            if isinstance(slot, dict):
                top_family = slot.get("top_family")
                family = slot.get("family")
                slot_id = slot.get("slot_id", f"slot_{i}")
                
                if top_family and top_family not in valid_top_families:
                    _log(f"⚠️  Unknown top_family '{top_family}' in {slot_id} (will be preserved)")
                    
                if family and family not in valid_families:
                    _log(f"⚠️  Unknown family '{family}' in {slot_id} (will be preserved)")
                    
    except Exception as e:
        _log(f"Warning: Could not validate enum values: {e}")


def _normalize_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize model output to match schema expectations.

    - Map optional_nice_to_haves -> nice_to_haves per slot
    - Ensure 'safety' object exists
    - Ensure 'fusion' is an object with defaults
    """
    if not isinstance(data, dict):
        return data

    # Normalize slots
    slots = data.get("slots")
    if isinstance(slots, list):
        for slot in slots:
            if isinstance(slot, dict):
                # Handle various naming variations for nice_to_haves
                if "optional_nice_to_haves" in slot and "nice_to_haves" not in slot:
                    slot["nice_to_haves"] = slot.pop("optional_nice_to_haves")
                elif "optional" in slot and "nice_to_haves" not in slot:
                    slot["nice_to_haves"] = slot.pop("optional")
                # Normalize evidence: schema requires arrays of strings per source
                ev = slot.get("evidence")
                if isinstance(ev, dict):
                    for k, v in list(ev.items()):
                        if isinstance(v, bool):
                            ev[k] = []
                        elif isinstance(v, str):
                            ev[k] = [v]
                        elif isinstance(v, list):
                            # keep as-is
                            pass
                        else:
                            ev[k] = []

    # Ensure safety block
    if not isinstance(data.get("safety"), dict):
        data["safety"] = {
            "enforce_allergens": True,
            "species_lock": True,
        }

    # Ensure fusion block
    if not isinstance(data.get("fusion"), dict):
        data["fusion"] = {
            "strategy": "rrf",
            "k": 60,
        }

    return data


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def _build_correction_prompt(error_message: str, schema: Dict[str, Any]) -> str:
    """Build a comprehensive correction prompt with context and examples."""
    
    # Extract enum values for guidance
    slot_schema = schema.get("properties", {}).get("slots", {}).get("items", {}).get("properties", {})
    top_family_enums = slot_schema.get("top_family", {}).get("enum", [])
    
    prompt = f"""Your JSON output failed validation with this error: {error_message}

Please fix the JSON and return ONLY the corrected JSON. Common issues and fixes:

**Required Fields (every slot must have):**
- slot_id: string (e.g., "nutrition_001", "calming_002")
- top_family: one of {top_family_enums[:8]}... (or custom value for important pet needs)
- family: string describing the specific family
- rationale: string explaining why this slot was generated
- musts: array of strings (positive constraints only)
- negatives: array of strings (MANDATORY - allergens and exclusions, can be empty [])
- embedding_query: string max 300 chars (facet-bag format: "dog; puppy; dry-kibble; mars" etc. - NO allergen terms)
- bm25_query: string (boolean search terms)
- filters: object with pc1 field (species filter)
- top_k: integer 20-40

**Evidence Structure:**
- evidence.pet_profile: array of strings
- evidence.calendar: array of strings
- evidence.weather: array of strings

**Data Types:**
- top_k must be integer, not string
- Arrays must be [...], not single values
- Use schema enum values when possible, but custom values are allowed for important pet needs

**CRITICAL ALLERGEN RULE:**
- NEVER put allergen terms (no-duck, chicken-free, grain-free) in embedding_query
- ALL allergens MUST go in negatives field only
- embedding_query should focus on positive product attributes + brands

Return the corrected JSON now:"""
    
    return prompt


def _save_output_and_history(journey_id: str, month_idx: int, result_data: Dict[str, Any]) -> None:
    """Save production output and update run history."""
    try:
        # Determine outputs directory (create in backend/outputs/)
        backend_dir = Path(__file__).resolve().parents[2]
        outputs_dir = backend_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        journey_short = journey_id[:8] if isinstance(journey_id, str) else "journey"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Smart clearing: remove old production outputs for this exact journey+month combination
        _log(f"Managing production outputs for {journey_short}_month{month_idx}...")
        for file in outputs_dir.glob("model_output_*.json"):
            if f"{journey_short}_month{month_idx}_" in file.name:
                _log(f"  Removing: {file.name}")
                file.unlink()
            elif file.name.startswith(f"model_output_{journey_short}_") and "month" not in file.name:
                _log(f"  Removing old format (no month specified): {file.name}")
                file.unlink()
        
        # Save new output
        output_file = outputs_dir / f"model_output_{journey_short}_month{month_idx}_{timestamp}.json"
        output_file.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"Saved production output to: {output_file}")
        
        # Update run history
        run_history_file = outputs_dir / ".run_history"
        current_run = f"{journey_id}_month{month_idx}"
        
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
        new_entry = f"{timestamp} {current_run} production"
        history.insert(0, new_entry)
        
        # Keep only last 100 entries to prevent file from growing too large
        history = history[:100]
        
        # Write back to file
        run_history_file.write_text('\n'.join(history) + '\n')
        _log(f"Updated production run history")
        
    except Exception as e:
        _log(f"Warning: Failed to save output/history: {e}")
        # Don't fail the main function if saving fails


def compose_queries(
    journey_id: str,
    month_idx: int,
    tz: str = "America/Los_Angeles",
    model_name: str | None = None,
) -> Dict[str, Any]:
    """
    Build context, render prompts, call GPT-5, validate JSON output against schema, and return it.
    This function performs no search or ranking.
    """
    _log("Loading environment and initializing client...")
    # Try current CWD, backend/.env, and repo root .env
    load_dotenv()
    backend_dir = Path(__file__).resolve().parents[2]
    load_dotenv(backend_dir / ".env")
    load_dotenv(backend_dir.parent / ".env")
    # Add a reasonable timeout to avoid hanging indefinitely
    # Allow longer generation time; GPT-5 responses can be slow
    client = OpenAI(timeout=180)

    _log("Building context...")
    context = build_generation_context(journey_id=journey_id, month_idx=month_idx, tz=tz)
    _log("Mapping variables...")
    variables = build_prompt_variables(context)

    _log("Loading and rendering prompts...")
    system_prompt = _load_text(TEMPLATES_DIR / "system_prompt.md")
    user_template = load_prompt(str(TEMPLATES_DIR / "semantic_query_prompt.md"))
    original_schema = _load_schema()
    
    # Add schema enums to template variables
    schema_enums = _extract_schema_enums(original_schema)
    variables.update(schema_enums)
    
    user_prompt = render_prompt(user_template, variables)
    relaxed_schema = _create_relaxed_schema(original_schema)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Call with retry and automatic fallback model on repeated timeout
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
                    time.sleep(2 ** attempt)
                else:
                    raise

    # Resolve effective model strategy
    effective_selection = model_name if model_name else MODEL_SELECTION

    def _create_with_selection(msgs):
        # If a specific model is selected (not auto), use only that
        if effective_selection and effective_selection != "auto":
            return _create_with_retry(effective_selection, msgs)
        # Otherwise use primary with fallback to secondary on timeout
        try:
            return _create_with_retry(MODEL_PRIMARY, msgs)
        except APITimeoutError:
            return _create_with_retry(MODEL_FALLBACK, msgs)

    # First attempt: request JSON object
    _log(f"Calling model ({effective_selection})...")
    resp = _create_with_selection(messages)
    text = resp.choices[0].message.content
    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Model did not return JSON: {e}\n{text}")

    # Validate against relaxed schema; if invalid, ask for corrected JSON once
    try:
        _log("Normalizing and validating output (pass 1)...")
        data = _normalize_output(data)
        validate(instance=data, schema=relaxed_schema)
        _validate_enum_values(data, original_schema)  # Log warnings for unknown enums
        _log("Validation succeeded (pass 1).")
        _save_output_and_history(journey_id, month_idx, data)
        return data
    except ValidationError as ve:
        _log(f"Validation failed (pass 1): {ve.message}. Requesting correction...")
        correction_prompt = _build_correction_prompt(ve.message, original_schema)  # Use original schema for guidance
        _log(f"Correction prompt sent to LLM:\n{correction_prompt}")
        messages.append({"role": "assistant", "content": json.dumps(data)})
        messages.append({"role": "user", "content": correction_prompt})
        _log("Calling model for corrected JSON...")
        resp2 = _create_with_selection(messages)
        text2 = resp2.choices[0].message.content
        data2 = json.loads(text2)
        _log("Normalizing and validating output (pass 2)...")
        data2 = _normalize_output(data2)
        try:
            validate(instance=data2, schema=relaxed_schema)
            _validate_enum_values(data2, original_schema)  # Log warnings for unknown enums
            _log("Validation succeeded (pass 2).")
            _save_output_and_history(journey_id, month_idx, data2)
            return data2
        except ValidationError as ve2:
            _log(f"Validation failed (pass 2): {ve2.message}. Final attempt...")
            # Pass 3: Simple, direct correction
            final_prompt = f"Your JSON still has errors: {ve2.message}\n\nFix this specific error and return ONLY valid JSON:"
            _log(f"Final correction prompt: {final_prompt}")
            messages.append({"role": "assistant", "content": json.dumps(data2)})
            messages.append({"role": "user", "content": final_prompt})
            resp3 = _create_with_selection(messages)
            text3 = resp3.choices[0].message.content
            data3 = json.loads(text3)
            _log("Normalizing and validating output (pass 3)...")
            data3 = _normalize_output(data3)
            validate(instance=data3, schema=relaxed_schema)
            _validate_enum_values(data3, original_schema)  # Log warnings for unknown enums
            _log("Validation succeeded (pass 3).")
            _save_output_and_history(journey_id, month_idx, data3)
            return data3


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m backend.agents.semantic_query.runner <journey_id> <month_idx>")
        sys.exit(1)
    journey_id = sys.argv[1]
    month_idx = int(sys.argv[2])
    result = compose_queries(journey_id, month_idx)
    print(json.dumps(result, indent=2, ensure_ascii=False))