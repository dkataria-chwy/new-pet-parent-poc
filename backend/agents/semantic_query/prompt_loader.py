from __future__ import annotations

from typing import Dict, Any
from pathlib import Path


def load_prompt(template_path: str) -> str:
    path = Path(template_path)
    return path.read_text(encoding="utf-8")


def render_prompt(template_text: str, variables: Dict[str, Any]) -> str:
    """
    Very small, safe renderer: replaces {{key}} with str(value) for top-level keys.
    Nested dicts should be pre-serialized in variables.
    """
    rendered = template_text
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


