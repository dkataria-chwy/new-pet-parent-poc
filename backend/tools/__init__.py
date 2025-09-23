"""
Tools package for LLM function calling.

Contains various utility tools that can be called by LLMs to perform
specific tasks like calendar lookups, weather forecasts, data retrieval, etc.
"""

from .calendar_tool import get_calendar_context
from .calendar_tool import OPENAI_TOOL_DEFINITION as CALENDAR_TOOL_DEFINITION
from .weather_tool import get_weather_context
from .weather_tool import OPENAI_TOOL_DEFINITION as WEATHER_TOOL_DEFINITION

__all__ = [
    "get_calendar_context", 
    "CALENDAR_TOOL_DEFINITION",
    "get_weather_context",
    "WEATHER_TOOL_DEFINITION"
]
