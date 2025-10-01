#!/usr/bin/env python3
"""
CSV-based calendar tool that reads from usa_zip_calendar_events.csv
Returns data in the exact same format as the calendar_tool.py
"""

import csv
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo

# Path to the CSV file
CSV_PATH = Path("/Users/dkataria/Desktop/dkataria/AI agents/NPP Testing/usa_zip_calendar_events.csv")

def _calculate_event_date(year: int, month: int, day: int) -> date:
    """Calculate the actual event date for a given year."""
    # Handle special cases for holidays that move
    if month == 11 and day == 24:  # Thanksgiving - 4th Thursday
        first_day = date(year, 11, 1)
        first_thursday = first_day + timedelta(days=(3 - first_day.weekday()) % 7)
        return first_thursday + timedelta(weeks=3)
    elif month == 5 and day == 8:  # Mother's Day - 2nd Sunday
        first_day = date(year, 5, 1)
        first_sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
        return first_sunday + timedelta(weeks=1)
    elif month == 6 and day == 19:  # Father's Day - 3rd Sunday
        first_day = date(year, 6, 1)
        first_sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
        return first_sunday + timedelta(weeks=2)
    elif month == 5 and day == 29:  # Memorial Day - last Monday
        last_day = date(year, 5, 31)
        last_monday = last_day - timedelta(days=(last_day.weekday()) % 7)
        return last_monday
    elif month == 9 and day == 5:  # Labor Day - 1st Monday
        first_day = date(year, 9, 1)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        return first_monday
    elif month == 3 and day == 12:  # Daylight Saving - 2nd Sunday in March
        first_day = date(year, 3, 1)
        first_sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
        return first_sunday + timedelta(weeks=1)
    elif month == 11 and day == 6:  # Daylight Saving End - 1st Sunday in November
        first_day = date(year, 11, 1)
        first_sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
        return first_sunday
    elif month == 4 and day == 17:  # Easter (approximate - varies by lunar calendar)
        # Simplified Easter calculation for demonstration
        return date(year, 4, 17)  # This would need proper Easter calculation
    else:
        return date(year, month, day)

def get_csv_calendar_context(
    zip_code: str,
    start_date: Optional[str] = None,
    days_ahead: int = 30,
    tz: str = "America/Los_Angeles",
    include_optional: bool = True,
) -> Dict[str, Any]:
    """
    Get calendar events from CSV file in the exact same format as calendar_tool.
    
    Args:
        zip_code: 5-digit ZIP code as a string.
        start_date: Optional ISO date (YYYY-MM-DD) to start the window.
        days_ahead: Number of days ahead to include (1..90).
        tz: IANA timezone string.
        include_optional: Whether to include optional/seasonal events.

    Returns:
        Dict[str, Any]: Calendar data in the same format as get_calendar_context()
    """
    
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")
    
    # Parse start date
    tzinfo = ZoneInfo(tz)
    if start_date:
        start = datetime.fromisoformat(start_date).date()
        month_start = date(start.year, start.month, 1)
    else:
        today = datetime.now(tzinfo).date()
        month_start = date(today.year, today.month, 1)
        start = month_start
    
    end = start + timedelta(days=days_ahead)
    
    # Load events from CSV
    events = []
    
    with open(CSV_PATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Check if event applies to this zip code
            event_zip = row['zip5']
            if event_zip != '*' and event_zip != zip_code:
                continue
            
            # Parse event data
            month = int(row['month'])
            day = int(row['day'])
            confidence = float(row['confidence'])
            window_before = int(row['window_days_before'])
            window_after = int(row['window_days_after'])
            
            # Calculate event dates for relevant years
            for year in range(start.year, end.year + 1):
                try:
                    event_date = _calculate_event_date(year, month, day)
                    
                    # Calculate window
                    window_start = event_date - timedelta(days=window_before)
                    window_end = event_date + timedelta(days=window_after)
                    
                    # Calculate days to event
                    days_to_event = (event_date - start).days
                    
                    # Only include events that are:
                    # 1. Currently active (within their window)
                    # 2. Upcoming within 14 days and high confidence (>= 0.6)
                    current_date = start  # Using start as current date
                    
                    is_currently_active = window_start <= current_date <= window_end
                    is_upcoming_relevant = days_to_event <= 14 and days_to_event >= 0 and confidence >= 0.6
                    
                    if is_currently_active or is_upcoming_relevant:
                        
                        # Parse slot triggers
                        slot_triggers = []
                        if row['slot_triggers']:
                            slot_triggers = [s.strip() for s in row['slot_triggers'].split(';') if s.strip()]
                        
                        # Parse pet relevance tags
                        pet_tags = []
                        if row['pet_impact'] == 'negative':
                            pet_tags.append('stress_inducing')
                        elif row['pet_impact'] == 'positive':
                            pet_tags.append('enriching')
                        
                        # Add category-specific tags
                        if row['category'] == 'seasonal':
                            pet_tags.append('seasonal_adjustment')
                        elif row['category'] == 'regional':
                            pet_tags.append('local_activity')
                        elif row['category'] == 'pet_specific':
                            pet_tags.append('pet_focused')
                        
                        event = {
                            "id": f"{row['event_id']}_{year}",
                            "date": event_date.isoformat(),
                            "label": row['event_name'],
                            "category": row['category'],
                            "pet_relevance_tags": pet_tags,
                            "slot_triggers_seed": slot_triggers,
                            "hints": row['rationale'],
                            "window": {
                                "from": window_start.isoformat(),
                                "to": window_end.isoformat()
                            },
                            "confidence": confidence,
                            "rationale": row['rationale'],
                            "days_to_event": days_to_event,
                            "pet_impact": row['pet_impact']
                        }
                        
                        events.append(event)
                        
                except ValueError:
                    # Skip invalid dates
                    continue
    
    # Sort events by date
    events.sort(key=lambda e: e['date'])
    
    return {
        "window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "tz": tz,
            "month_start": month_start.isoformat()
        },
        "location": {
            "zip": zip_code,
            "state": None  # Could be enhanced to include state from CSV
        },
        "events": events,
        "generated_at": datetime.now(tzinfo).isoformat(),
    }


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python csv_calendar_tool.py <zip_code> [days_ahead]")
        print("Example: python csv_calendar_tool.py 98052 30")
        sys.exit(1)
    
    zip_code = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    try:
        result = get_csv_calendar_context(zip_code=zip_code, days_ahead=days)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
