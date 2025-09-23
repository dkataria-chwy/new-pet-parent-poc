from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SlotQuery(BaseModel):
    slot: str = Field(description="Logical slot name, e.g., 'food', 'toys', 'dental', 'supplements'")
    query_text: str = Field(description="Semantic query text for this slot")
    species: Optional[str] = Field(default=None, description="dog|cat if applicable")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Optional constraints like budget, exclusions")


class MultiSlotQueryOutput(BaseModel):
    model_used: Optional[str] = None
    journey_id: Optional[str] = None
    month_idx: Optional[int] = None
    slots: List[SlotQuery]


