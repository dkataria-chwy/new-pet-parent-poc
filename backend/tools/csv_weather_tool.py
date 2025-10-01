#!/usr/bin/env python3
"""
CSV-based weather tool that reads from usa_zip_weather_alerts.csv
Returns data in the exact same format as the NWS API weather tool
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo

# Path to the CSV file (absolute path to handle spaces in directory names)
CSV_PATH = Path("/Users/dkataria/Desktop/dkataria/AI agents/NPP Testing/usa_zip_weather_alerts.csv")

def get_csv_weather_context(
    zip_code: str,
    days_ahead: int = 7,
    tz: str = "America/Los_Angeles",
) -> Dict[str, Any]:
    """
    Get weather data from CSV file in the exact same format as NWS API.
    
    Args:
        zip_code: 5-digit ZIP code as a string.
        days_ahead: Number of forecast days (1..14) - currently supports up to 7.
        tz: IANA timezone string (e.g., "America/Los_Angeles").

    Returns:
        Dict[str, Any]: Weather data in the same format as get_weather_context()
    """
    
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")
    
    # Find the zip code in CSV
    weather_data = None
    with open(CSV_PATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['zip5'] == zip_code:
                weather_data = row
                break
    
    if not weather_data:
        # Return empty data if zip not found (same behavior as NWS API failure)
        return {
            "location": {"zip": zip_code, "state": None},
            "current": None,
            "forecast": [],
            "triggers": [],
            "raw": {"provider": "csv"},
            "generated_at": datetime.now(ZoneInfo(tz)),
        }
    
    # Parse temperature data (limit to days_ahead)
    max_days = min(days_ahead, 7)  # CSV only has 7 days
    forecast = []
    
    base_date = datetime.now(ZoneInfo(tz)).date()
    
    for day_idx in range(max_days):
        day_num = day_idx + 1
        temp_f_key = f"temp_{day_num}_f"
        temp_c_key = f"temp_{day_num}_c"
        
        if temp_f_key in weather_data and weather_data[temp_f_key]:
            temp_f = float(weather_data[temp_f_key])
            temp_c = float(weather_data[temp_c_key])
            
            # For simplicity, use the daily temp as both high and low
            # In real scenario, you might want separate high/low columns
            forecast_date = base_date + timedelta(days=day_idx)
            
            forecast.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "high_f": temp_f,
                "low_f": temp_f - 10,  # Simulate low temp (10 degrees lower)
                "high_c": temp_c,
                "low_c": temp_c - 5.6,  # Simulate low temp in Celsius
                "conditions": "Clear"  # Default condition
            })
    
    # Parse alerts/warnings
    triggers = []
    warnings_text = weather_data.get('warnings', '').strip()
    if warnings_text:
        # Split multiple warnings by comma if needed
        warning_list = [w.strip() for w in warnings_text.split(',') if w.strip()]
        
        for warning in warning_list:
            # Map CSV warning names to trigger format
            trigger = {
                "id": f"csv_{warning}",
                "event": warning,
                "urgency": "expected",
                "severity": "moderate",
                "certainty": "likely"
            }
            triggers.append(trigger)
    
    # Use first day's temperature as current temperature
    current_temp = None
    if forecast and len(forecast) > 0:
        current_temp = {
            "temperature_f": forecast[0]["high_f"],
            "temperature_c": forecast[0]["high_c"],
            "conditions": "Clear",
            "humidity": 50.0,  # Default values
            "wind_speed_mph": 5.0
        }
    
    return {
        "location": {
            "zip": zip_code, 
            "state": weather_data.get('state')
        },
        "current": current_temp,
        "forecast": forecast,
        "triggers": triggers,
        "alerts": [{"event": t.get("event")} for t in triggers],  # Match NWS API format
        "raw": {"provider": "csv"},
        "generated_at": datetime.now(ZoneInfo(tz)),
    }


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python csv_weather_tool.py <zip_code> [days_ahead]")
        print("Example: python csv_weather_tool.py 98052 7")
        sys.exit(1)
    
    zip_code = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    try:
        result = get_csv_weather_context(zip_code=zip_code, days_ahead=days)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
