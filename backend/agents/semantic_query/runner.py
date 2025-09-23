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
MODEL_SELECTION = "gpt-4.1-2025-04-14"

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
    user_prompt = render_prompt(user_template, variables)
    schema = _load_schema()

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

    # Validate against schema; if invalid, ask for corrected JSON once
    try:
        _log("Normalizing and validating output (pass 1)...")
        data = _normalize_output(data)
        validate(instance=data, schema=schema)
        _log("Validation succeeded (pass 1).")
        _save_output_and_history(journey_id, month_idx, data)
        return data
    except ValidationError as ve:
        _log(f"Validation failed (pass 1): {ve.message}. Requesting correction...")
        correction_prompt = (
            f"Output failed schema: {ve.message}. Return corrected JSON only."
        )
        messages.append({"role": "assistant", "content": json.dumps(data)})
        messages.append({"role": "user", "content": correction_prompt})
        _log("Calling model for corrected JSON...")
        resp2 = _create_with_selection(messages)
        text2 = resp2.choices[0].message.content
        data2 = json.loads(text2)
        _log("Normalizing and validating output (pass 2)...")
        data2 = _normalize_output(data2)
        validate(instance=data2, schema=schema)
        _log("Validation succeeded (pass 2).")
        _save_output_and_history(journey_id, month_idx, data2)
        return data2


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m backend.agents.semantic_query.runner <journey_id> <month_idx>")
        sys.exit(1)
    journey_id = sys.argv[1]
    month_idx = int(sys.argv[2])
    result = compose_queries(journey_id, month_idx)
    print(json.dumps(result, indent=2, ensure_ascii=False))


