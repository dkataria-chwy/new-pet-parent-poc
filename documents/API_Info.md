# API Information & Data Sources

## Current Implementation

### Weather Data
- **Current**: National Weather Service (NWS) API - Free, official US weather alerts
- **Endpoint**: `https://api.weather.gov/alerts/active`
- **Data Retrieved**: 
  - Temperature forecasts (7-day)
  - Weather alerts (heat warnings, storm warnings, etc.)
  - Current conditions
- **Update Frequency**: Real-time
- **Coverage**: United States only
- **Status**: ✅ Implemented in `backend/tools/weather_tool.py`

### Calendar/Events Data
- **Current**: Static CSV file (`usa_zip_calendar_events.csv`)
- **Data Source**: Manually curated events with made-up confidence scores
- **Coverage**: 75 events including national holidays, seasonal patterns, regional events
- **Limitations**: 
  - Not real-time
  - Subjective confidence scores
  - Limited regional specificity
- **Status**: ✅ Implemented in `backend/tools/csv_calendar_tool.py`

## Available Real-World APIs

### 🌤️ Weather APIs
| API | Cost | Coverage | Features |
|-----|------|----------|----------|
| **National Weather Service** | Free | US Only | Official alerts, forecasts |
| **OpenWeatherMap** | Freemium | Global | Weather + air quality + pollution |
| **AccuWeather** | Paid | Global | Detailed forecasts + historical |
| **Weather.com (IBM)** | Paid | Global | Enterprise weather data |

### 🏗️ Local Events & Municipal Data
| API | Cost | Coverage | Features |
|-----|------|----------|----------|
| **Eventbrite API** | Freemium | Global | Public events, festivals, concerts |
| **Google Places API** | Paid | Global | Business activity, construction permits |
| **Foursquare API** | Freemium | Global | Local business density, activity |
| **City Open Data APIs** | Free | City-specific | Construction permits, noise complaints |

### 🎆 Event-Specific APIs
| API | Cost | Coverage | Features |
|-----|------|----------|----------|
| **PredictHQ** | Paid | Global | Major events impact prediction |
| **TicketMaster API** | Paid | Global | Concerts, sports events |
| **Facebook Events API** | Limited | Global | Community events |
| **Meetup API** | Freemium | Global | Local gatherings |

### 🏙️ Municipal/Government APIs
| City | API Endpoint | Data Available |
|------|--------------|----------------|
| **Seattle** | `data.seattle.gov` | Construction permits, road closures |
| **San Francisco** | `data.sfgov.org` | Municipal activities, permits |
| **Chicago** | `data.cityofchicago.org` | Construction, events, permits |
| **NYC** | `opendata.cityofnewyork.us` | Comprehensive city data |

### 🔊 Noise/Activity Specific
| API | Cost | Coverage | Features |
|-----|------|----------|----------|
| **FlightRadar24** | Freemium | Global | Aircraft tracking (air shows, airport noise) |
| **Road Closure APIs** | Varies | Regional | Traffic, construction impacts |
| **School District APIs** | Free | District-specific | Bell schedules, events |

## Implementation Priorities

### Phase 1: Current (Completed)
- ✅ NWS Weather API for alerts and forecasts
- ✅ Static calendar events for testing

### Phase 2: Enhanced Real-Time Data
- 🔄 **City of Seattle Open Data** - Construction permits, road work
- 🔄 **Eventbrite API** - Local events and festivals
- 🔄 **School District Calendar APIs** - Schedule changes

### Phase 3: Advanced Integration
- 🔄 **PredictHQ** - Major event impact prediction
- 🔄 **Air Quality APIs** - Pollution-based product recommendations
- 🔄 **Regional Sound/Noise APIs** - Construction, aircraft patterns

## Data Quality Considerations

### Current Limitations
1. **Calendar Confidence Scores**: Manually assigned, not data-driven
2. **Regional Specificity**: Generic events not tailored to specific locations
3. **Real-Time Updates**: Static data doesn't reflect current conditions
4. **Pet-Specific Relevance**: Events not filtered by pet characteristics

### Ideal Future State
1. **Dynamic Confidence**: Based on historical pet product demand
2. **Location-Aware**: Real municipal data for each zip code
3. **Pet-Personalized**: Events filtered by pet size, breed, living situation
4. **Real-Time Updates**: Live data from multiple API sources

## API Integration Architecture

### Current Flow
```
Pet Request → Static CSV → Calendar Events → LLM → Product Recommendations
```

### Proposed Enhanced Flow
```
Pet Request → Multiple APIs → Event Aggregation → Relevance Scoring → LLM → Product Recommendations
              ↓
        [NWS Weather, City Data, Event APIs, School Calendars]
```

## Cost Estimates (Monthly)

### Free Tier
- NWS Weather: Free
- City Open Data: Free  
- Basic Eventbrite: Free (limited calls)
- School Calendars: Free
- **Total: $0/month**

### Enhanced Tier
- Google Places API: ~$200/month (moderate usage)
- PredictHQ: ~$500/month (basic plan)
- AccuWeather: ~$100/month
- **Total: ~$800/month**

## Notes & Assumptions

1. **Weather Thresholds**: Heat warnings >100°F, freeze warnings <30°F (based on system prompt)
2. **Calendar Confidence**: Current threshold ≥0.6 for event inclusion
3. **Geographic Scope**: Initially focused on US due to NWS API limitation
4. **Update Frequency**: Daily for calendar events, real-time for weather alerts
5. **Data Retention**: No historical data storage currently implemented

---

**Last Updated**: September 25, 2025  
**Document Version**: 1.0  
**Related Files**: 
- `backend/tools/weather_tool.py`
- `backend/tools/csv_weather_tool.py` 
- `backend/tools/csv_calendar_tool.py`
- `usa_zip_calendar_events.csv`
