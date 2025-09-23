from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, field_validator
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import re
import requests
import json

# This tool is purely alert-based - no temperature threshold analysis

# ---- NWS alert → trigger mapping (OFFICIAL GOVERNMENT WEATHER ALERTS ONLY) ----
# These are official National Weather Service warnings/alerts that come from the NWS API
# Each maps: (NWS Alert Name, Internal Trigger Type, Pet-Relevant Slot Triggers)
ALERT_MAP = [
    ("Hurricane Warning",          "hurricane_warning",        ["evacuation_kit","waterproof_carrier","extra_food_water","id_tag_check","medication_refill"]),
    ("Tornado Warning",            "tornado_warning",          ["calming_storm_chews","safe_space_setup"]),
    ("Freeze Warning",             "freeze_warning",           ["heated_bed","coat_or_booties"]),
    ("Excessive Heat Warning",     "excessive_heat_warning",   ["cooling_mat","hydration_bowl"]),
    ("Severe Thunderstorm Warning","severe_thunderstorm_warning", ["calming_storm_chews","safe_space_setup"]),
    ("Winter Storm Warning",       "winter_storm_warning",     ["coat_or_booties","paw_balm","heated_bed"]),
]


class WeatherWindow(BaseModel):
    start: date
    end: date
    tz: str


class Trigger(BaseModel):
    type: str
    slot_triggers: List[str] = []
    window: Dict[str, date]
    confidence: float
    metrics: Dict[str, Any] = {}
    rationale: str


class CurrentWeather(BaseModel):
    temperature_f: Optional[float]
    temperature_c: Optional[float]
    conditions: Optional[str]
    humidity: Optional[float]
    wind_speed_mph: Optional[float]


class ForecastDay(BaseModel):
    date: str
    high_f: Optional[float]
    low_f: Optional[float]
    high_c: Optional[float]
    low_c: Optional[float]
    conditions: Optional[str]


class WeatherResponse(BaseModel):
    location: Dict[str, Optional[str]]  # {"zip": "...", "state": None}
    current: Optional[CurrentWeather]
    forecast: List[ForecastDay]
    triggers: List[Trigger]
    raw: Dict[str, str]
    generated_at: datetime


class WeatherRequest(BaseModel):
    zip_code: str
    days_ahead: conint(ge=1, le=14) = 7
    tz: str = "America/Los_Angeles"

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


# NOTE: This tool is purely alert-based and does not use heuristic temperature analysis


def _parse_nws_datetime(dt_str: Optional[str]) -> Optional[date]:
    """Parse NWS datetime string to date."""
    if not dt_str:
        return None
    try:
        # NWS uses ISO format like "2025-09-19T18:00:00-05:00"
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.date()
    except Exception:
        return None


def _alerts_to_triggers(alerts: List[Dict[str, Any]]) -> List[Trigger]:
    """Convert NWS alerts to triggers using ALERT_MAP."""
    triggers = []
    
    for alert in alerts:
        alert_title = alert.get("event", "")
        
        for nws_name, trigger_type, slot_triggers in ALERT_MAP:
            if nws_name.lower() in alert_title.lower():
                # Parse actual alert timing from NWS data
                onset_date = _parse_nws_datetime(alert.get("onset"))
                expires_date = _parse_nws_datetime(alert.get("expires"))
                
                # Use actual alert window, fallback to today + 1 day if parsing fails
                start_date = onset_date or date.today()
                end_date = expires_date or (start_date + timedelta(days=1))
                
                # Calculate confidence based on alert severity and certainty
                severity = alert.get("severity", "").lower()
                certainty = alert.get("certainty", "").lower()
                
                confidence = 0.95  # Default high confidence
                if severity == "extreme":
                    confidence = 0.98
                elif severity == "severe":
                    confidence = 0.95
                elif severity == "moderate":
                    confidence = 0.85
                elif severity == "minor":
                    confidence = 0.75
                
                # Adjust for certainty
                if certainty == "observed":
                    confidence = min(0.99, confidence + 0.05)
                elif certainty == "likely":
                    confidence = confidence  # No change
                elif certainty == "possible":
                    confidence = max(0.60, confidence - 0.15)
                
                triggers.append(Trigger(
                    type=trigger_type,
                    slot_triggers=slot_triggers,
                    window={"from": start_date, "to": end_date},
                    confidence=confidence,
                    metrics={
                        "alert_source": "nws", 
                        "alert_title": alert_title,
                        "severity": severity,
                        "certainty": certainty,
                        "onset": alert.get("onset"),
                        "expires": alert.get("expires")
                    },
                    rationale=f"Official NWS {nws_name} ({severity} severity, {certainty} certainty)"
                ))
                break
    
    return triggers




def _get_lat_lon_from_zip(zip_code: str) -> Optional[tuple[float, float]]:
    """Get lat/lon from ZIP code. Returns None if not found."""
    try:
        # Simple, fast geocoding using OpenStreetMap
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            "postalcode": zip_code,
            "country": "United States",
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "ChewyJourney/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        
        return None  # No coordinates found
        
    except Exception:
        return None  # Failed to geocode


def _celsius_to_fahrenheit(celsius: Optional[float]) -> Optional[float]:
    """Convert Celsius to Fahrenheit."""
    if celsius is None:
        return None
    return round((celsius * 9/5) + 32, 1)


def _fahrenheit_to_celsius(fahrenheit: Optional[float]) -> Optional[float]:
    """Convert Fahrenheit to Celsius.""" 
    if fahrenheit is None:
        return None
    return round((fahrenheit - 32) * 5/9, 1)


def _fetch_nws_current_weather(lat: float, lon: float) -> Optional[CurrentWeather]:
    """Fetch current weather conditions from NWS."""
    try:
        # First get the grid point data
        grid_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {"User-Agent": "ChewyJourney/1.0 (contact@example.com)"}
        
        grid_response = requests.get(grid_url, headers=headers, timeout=10)
        grid_response.raise_for_status()
        grid_data = grid_response.json()
        
        # Get the observation station
        stations_url = grid_data["properties"]["observationStations"]
        stations_response = requests.get(stations_url, headers=headers, timeout=10)
        stations_response.raise_for_status()
        stations_data = stations_response.json()
        
        if not stations_data.get("features"):
            return None
            
        # Get latest observation from the first station
        station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
        obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        obs_response = requests.get(obs_url, headers=headers, timeout=10)
        obs_response.raise_for_status()
        obs_data = obs_response.json()
        
        props = obs_data.get("properties", {})
        temp_c = props.get("temperature", {}).get("value")
        temp_f = _celsius_to_fahrenheit(temp_c)
        
        return CurrentWeather(
            temperature_f=temp_f,
            temperature_c=temp_c,
            conditions=props.get("textDescription"),
            humidity=props.get("relativeHumidity", {}).get("value"),
            wind_speed_mph=props.get("windSpeed", {}).get("value")
        )
        
    except Exception as e:
        print(f"Warning: Failed to fetch current weather: {e}")
        return None


def _fetch_nws_forecast(lat: float, lon: float, days: int) -> List[ForecastDay]:
    """Fetch weather forecast from NWS."""
    try:
        # Get grid point data
        grid_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {"User-Agent": "ChewyJourney/1.0 (contact@example.com)"}
        
        grid_response = requests.get(grid_url, headers=headers, timeout=10)
        grid_response.raise_for_status()
        grid_data = grid_response.json()
        
        # Get forecast
        forecast_url = grid_data["properties"]["forecast"]
        forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        forecast_days = []
        periods = forecast_data.get("properties", {}).get("periods", [])
        
        # NWS returns periods (day/night), we want daily highs/lows
        current_day = None
        day_data = {}
        
        for period in periods[:days*2]:  # Get enough periods for the requested days
            period_date = period.get("startTime", "")[:10]  # YYYY-MM-DD
            is_daytime = period.get("isDaytime", False)
            temp_f = period.get("temperature")
            temp_c = _fahrenheit_to_celsius(temp_f)
            
            if period_date != current_day:
                # Save previous day if we have data
                if current_day and day_data:
                    forecast_days.append(ForecastDay(
                        date=current_day,
                        high_f=day_data.get("high_f"),
                        low_f=day_data.get("low_f"),
                        high_c=day_data.get("high_c"),
                        low_c=day_data.get("low_c"),
                        conditions=day_data.get("conditions")
                    ))
                
                # Start new day
                current_day = period_date
                day_data = {}
            
            # Collect high/low temps and conditions
            if is_daytime:
                day_data["high_f"] = temp_f
                day_data["high_c"] = temp_c
                day_data["conditions"] = period.get("shortForecast")
            else:
                day_data["low_f"] = temp_f 
                day_data["low_c"] = temp_c
        
        # Add the last day
        if current_day and day_data:
            forecast_days.append(ForecastDay(
                date=current_day,
                high_f=day_data.get("high_f"),
                low_f=day_data.get("low_f"),
                high_c=day_data.get("high_c"),
                low_c=day_data.get("low_c"),
                conditions=day_data.get("conditions")
            ))
        
        return forecast_days[:days]  # Return only requested number of days
        
    except Exception as e:
        print(f"Warning: Failed to fetch forecast: {e}")
        return []


def _fetch_nws_alerts(lat: float, lon: float) -> List[Dict[str, Any]]:
    """Fetch active NWS alerts for a location."""
    try:
        # NWS API endpoint for active alerts by point
        url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
        
        headers = {
            "User-Agent": "ChewyJourney/1.0 (contact@example.com)"  # NWS requires User-Agent
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract alerts from NWS response
        alerts = []
        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            alerts.append({
                "event": properties.get("event", ""),
                "headline": properties.get("headline", ""),
                "description": properties.get("description", ""),
                "onset": properties.get("onset", ""),
                "expires": properties.get("expires", ""),
                "severity": properties.get("severity", ""),
                "certainty": properties.get("certainty", "")
            })
        
        return alerts
        
    except Exception as e:
        print(f"Warning: Failed to fetch NWS alerts: {e}")
        return []  # Return empty list on API failure


def _get_nws_data(zip_code: str, days_ahead: int) -> Dict[str, Any]:
    """Get real NWS data for a ZIP code."""
    coords = _get_lat_lon_from_zip(zip_code)
    
    if coords is None:
        # No coordinates found for this ZIP - return empty data
        return {
            "current": None,
            "forecast": [],
            "alerts": []
        }
    
    lat, lon = coords
    
    # Fetch all weather data
    current = _fetch_nws_current_weather(lat, lon)
    forecast = _fetch_nws_forecast(lat, lon, days_ahead)
    alerts = _fetch_nws_alerts(lat, lon)
    
    return {
        "current": current,
        "forecast": forecast,
        "alerts": alerts
    }


def get_weather_context(
    zip_code: str,
    days_ahead: int = 7,
    tz: str = "America/Los_Angeles",
) -> Dict[str, Any]:
    """
    PURELY ALERT-BASED weather triggers for a ZIP and forecast period.
    
    Only generates triggers from official NWS (National Weather Service) alerts/warnings:
    - Hurricane Warning, Tornado Warning, Excessive Heat Warning, etc.
    - No heuristic temperature analysis - only official government weather alerts
    - High confidence (0.95) since these are official warnings
    
    Makes real-time calls to NWS API alerts endpoint: https://api.weather.gov/alerts/active

    Args:
        zip_code: 5-digit ZIP code as a string.
        days_ahead: Number of forecast days (1..14).
        tz: IANA timezone string (e.g., "America/Los_Angeles").

    Returns:
        Dict[str, Any]: WeatherResponse serialized to a dict with triggers from NWS alerts only.
    """
    
    req = WeatherRequest(
        zip_code=zip_code,
        days_ahead=days_ahead,
        tz=tz,
    )

    # Real NWS API call
    nws = _get_nws_data(req.zip_code, req.days_ahead)

    # Generate ONLY alert-based triggers (no heuristics)
    triggers = _alerts_to_triggers(nws["alerts"])

    resp = WeatherResponse(
        location={"zip": req.zip_code, "state": None},
        current=nws["current"],
        forecast=nws["forecast"],
        triggers=triggers,
        raw={"provider": "nws"},
        generated_at=datetime.now(ZoneInfo(req.tz)),
    )
    return resp.model_dump()


# Optional: OpenAI tool registration schema for convenience
OPENAI_TOOL_DEFINITION: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_weather_context",
        "description": "Return deterministic, pet-relevant weather triggers for a ZIP and forecast period.",
        "parameters": WeatherRequest.model_json_schema(),
    },
}


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python weather_tool.py <zip_code> [days_ahead]")
        print("Example: python weather_tool.py 12345 7")
        sys.exit(1)
    zip_code = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    print(json.dumps(get_weather_context(zip_code=zip_code, days_ahead=days), indent=2, default=str))
