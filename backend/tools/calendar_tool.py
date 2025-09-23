from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, field_validator
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import re


class CalendarWindow(BaseModel):
    start: date
    end: date
    tz: str
    month_start: date


class CalendarEvent(BaseModel):
    id: str
    date: date
    label: str
    category: str = Field(description="holiday | seasonal | local")
    pet_relevance_tags: List[str] = []
    slot_triggers_seed: List[str] = []
    hints: Optional[str] = None
    window: Dict[str, date]
    confidence: float
    rationale: str
    days_to_event: int


class CalendarResponse(BaseModel):
    window: CalendarWindow
    location: Dict[str, Optional[str]]  # {"zip": "...", "state": None}
    events: List[CalendarEvent]
    generated_at: datetime


class CalendarRequest(BaseModel):
    zip_code: str
    start_date: Optional[date] = None
    days_ahead: conint(ge=1, le=90) = 30
    tz: str = "America/Los_Angeles"
    include_optional: bool = True

    @field_validator("zip_code")
    @classmethod
    def _validate_zip(cls, v: str) -> str:
        if not re.fullmatch(r"\d{5}", (v or "").strip()):
            raise ValueError("invalid_zip")
        return v

    @field_validator("tz")
    @classmethod
    def _validate_tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
            return v
        except Exception:
            return "America/Los_Angeles"


def _overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return not (a_end < b_start or b_end < a_start)


def _fourth_thursday(year: int) -> date:
    first_of_month = date(year, 11, 1)
    shift = (3 - first_of_month.weekday()) % 7  # Thursday is 3
    first_thu = first_of_month + timedelta(days=shift)
    return first_thu + timedelta(days=21)


def _clamp(n: int, lo: int, hi: int) -> int:
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def get_calendar_context(
    zip_code: str,
    start_date: Optional[str] = None,  # ISO "YYYY-MM-DD"
    days_ahead: int = 30,
    tz: str = "America/Los_Angeles",
    include_optional: bool = True,
) -> Dict[str, Any]:
    """
    Deterministic, pet-relevant USA calendar events.
    No external APIs. Returns JSON-serializable dict produced by Pydantic.

    Args:
        zip_code: 5-digit ZIP code as a string.
        start_date: Optional ISO date (YYYY-MM-DD) to start the window; defaults to
            the first day of the current month in the provided timezone.
        days_ahead: Number of days ahead to include (1..90).
        tz: IANA timezone string (e.g., "America/Los_Angeles").
        include_optional: Whether to include optional/seasonal events.

    Returns:
        Dict[str, Any]: CalendarResponse serialized to a dict.
    """

    parsed_start_date: Optional[date] = None
    if start_date:
        # datetime.fromisoformat handles YYYY-MM-DD safely
        parsed_start_date = datetime.fromisoformat(start_date).date()

    req = CalendarRequest(
        zip_code=zip_code,
        start_date=parsed_start_date,
        days_ahead=days_ahead,
        tz=tz,
        include_optional=include_optional,
    )

    tzinfo = ZoneInfo(req.tz)
    if req.start_date:
        start = req.start_date
        month_start = date(start.year, start.month, 1)
    else:
        today = datetime.now(tzinfo).date()
        month_start = date(today.year, today.month, 1)
        start = month_start
    # Clamp days_ahead as extra safety (Pydantic already enforces bounds)
    horizon_days = _clamp(int(req.days_ahead), 1, 90)
    end = start + timedelta(days=horizon_days)

    events: List[CalendarEvent] = []

    def add_if_overlaps(ev_data: dict) -> None:
        # Calculate days to event from the window start date
        event_date = ev_data["date"]
        days_to_event = (event_date - start).days
        ev_data["days_to_event"] = days_to_event
        
        ev = CalendarEvent(**ev_data)
        if _overlaps(start, end, ev.window["from"], ev.window["to"]):
            events.append(ev)

    # Independence Day (July 4): window Jun 29 – Jul 06
    for year in range(start.year, end.year + 1):
        add_if_overlaps({
            "id": f"fireworks_july4_{year}",
            "date": date(year, 7, 4),
            "label": "Independence Day",
            "category": "holiday",
            "pet_relevance_tags": ["fireworks_noise"],
            "slot_triggers_seed": ["calming_fireworks"],
            "hints": "Typical evening fireworks 6/29–7/6; loud noises and flashes.",
            "window": {"from": date(year, 6, 29), "to": date(year, 7, 6)},
            "confidence": 0.95,
            "rationale": "US federal holiday; widespread consumer fireworks.",
        })

    # New Year's: window Dec 28 – Jan 02 (canonical date = Jan 1)
    for year in range(start.year, end.year + 1):
        add_if_overlaps({
            "id": f"fireworks_newyear_{year + 1}",
            "date": date(year + 1, 1, 1),
            "label": "New Year's",
            "category": "holiday",
            "pet_relevance_tags": ["fireworks_noise"],
            "slot_triggers_seed": ["calming_fireworks"],
            "hints": "Neighborhood fireworks common from 12/28 to 1/2.",
            "window": {"from": date(year, 12, 28), "to": date(year + 1, 1, 2)},
            "confidence": 0.90,
            "rationale": "New Year celebrations often include fireworks.",
        })

    if req.include_optional:
        # Halloween: Oct 29 – Nov 01 (canonical date = Oct 31)
        for year in range(start.year, end.year + 1):
            add_if_overlaps({
                "id": f"halloween_{year}",
                "date": date(year, 10, 31),
                "label": "Halloween",
                "category": "holiday",
                "pet_relevance_tags": ["doorbell_activity", "costumes"],
                "slot_triggers_seed": ["anxiety_costumes", "doorbell_activity"],
                "hints": "Frequent doorbell/visitors; masks/costumes may stress pets.",
                "window": {"from": date(year, 10, 29), "to": date(year, 11, 1)},
                "confidence": 0.70,
                "rationale": "Trick-or-treating increases noise and visitors.",
            })

        # Thanksgiving: fourth Thursday of November → week Monday–Sunday
        for year in range(start.year, end.year + 1):
            t = _fourth_thursday(year)
            week_monday = t - timedelta(days=t.weekday())
            week_sunday = week_monday + timedelta(days=6)
            add_if_overlaps({
                "id": f"thanksgiving_{year}",
                "date": t,
                "label": "Thanksgiving",
                "category": "holiday",
                "pet_relevance_tags": ["travel", "guests"],
                "slot_triggers_seed": ["travel_kit", "guest_management"],
                "hints": "Many households travel or host guests during this week.",
                "window": {"from": week_monday, "to": week_sunday},
                "confidence": 0.60,
                "rationale": "Travel and guests can change routines; preparation helps.",
            })

    response = CalendarResponse(
        window=CalendarWindow(start=start, end=end, tz=req.tz, month_start=month_start),
        location={"zip": req.zip_code, "state": None},
        events=events,
        generated_at=datetime.now(tzinfo),
    )
    return response.model_dump()


# Optional: OpenAI tool registration schema for convenience
OPENAI_TOOL_DEFINITION: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_calendar_context",
        "description": "Return deterministic, pet-relevant USA calendar events for a ZIP and date range.",
        "parameters": CalendarRequest.model_json_schema(),
    },
}


if __name__ == "__main__":
    import json, sys
    zip_code = sys.argv[1] if len(sys.argv) > 1 else "94105"
    start = sys.argv[2] if len(sys.argv) > 2 else None
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    print(json.dumps(get_calendar_context(zip_code=zip_code, start_date=start, days_ahead=days), indent=2, default=str))