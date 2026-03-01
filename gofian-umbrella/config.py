"""
GOFIAN Umbrella or Sunglasses — Project Configuration
Module: config
Description: UoS configuration — decision engine weights, icon mappings, thresholds.
             Decision engine weights, icon mappings, thresholds.
Author: GOFIAN AI
Version: 0.1.0
"""

import os

# ============================================================
# UoS Identity
# ============================================================
VERSION = "0.3.0"
PROJECT_NAME = "umbrella-or-sunglasses"
DISPLAY_NAME = "Umbrella or Sunglasses"
TABLE_PREFIX = "uos_"
TAGLINE = "One glance. One decision."

# ============================================================
# UoS Server
# ============================================================
UOS_PORT = int(os.getenv("UOS_PORT", "5002"))
UOS_SECRET_KEY = os.getenv("UOS_SECRET_KEY", "uos-dev-secret-change-me")
UOS_DEBUG = os.getenv("UOS_DEBUG", "true").lower() == "true"
UOS_CORS_ORIGINS = os.getenv("UOS_CORS_ORIGINS", "*")

# Flask defaults (previously from factory.config.defaults)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ============================================================
# Weather API Configuration
# ============================================================
# Primary: OpenWeatherMap (free tier: 1000 calls/day)
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/3.0"

# Secondary: WeatherAPI (free tier: 1M calls/month)
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
WEATHERAPI_BASE_URL = "https://api.weatherapi.com/v1"

# Cache TTL for weather data (seconds)
WEATHER_CACHE_TTL = int(os.getenv("UOS_WEATHER_CACHE_TTL", "300"))  # 5 minutes

# ============================================================
# Decision Engine — Scoring Weights (Analyst-approved v1)
# ============================================================
SCORING_WEIGHTS = {
    "rain_probability": 0.35,   # Strongest predictor of umbrella need
    "uv_index": 0.20,          # Primary sunglasses trigger
    "wind_speed": 0.15,        # Affects perceived temp + umbrella usability
    "temperature": 0.15,       # Cold/heat alerts
    "forecast_confidence": 0.10,  # Modulates confidence glow
    "sun_elevation": 0.05,     # Sunrise/sunset context
}

# ============================================================
# Decision Thresholds
# ============================================================
THRESHOLDS = {
    "rain_umbrella": 0.40,         # Rain probability >= 40% → umbrella
    "rain_high": 0.70,             # Rain probability >= 70% → strong umbrella
    "uv_sunglasses": 3,            # UV index >= 3 → sunglasses
    "uv_high": 6,                  # UV index >= 6 → strong sunglasses
    "wind_alert": 40,              # Wind km/h >= 40 → wind alert
    "wind_strong": 60,             # Wind km/h >= 60 → strong wind
    "temp_cold": 5,                # °C <= 5 → cold alert
    "temp_freezing": 0,            # °C <= 0 → strong cold
    "temp_hot": 32,                # °C >= 32 → heat alert
    "temp_extreme": 38,            # °C >= 38 → extreme heat
    "confidence_notify": 0.80,     # Min confidence to send notification
    "severe_weather_override": True,  # Always show danger icon for severe weather
}

# ============================================================
# Icon Definitions
# ============================================================
ICONS = {
    "sunglasses": {"emoji": "\u2600\ufe0f", "label": "sunglasses", "priority": 2},
    "umbrella": {"emoji": "\U0001f327\ufe0f", "label": "umbrella", "priority": 1},
    "wind": {"emoji": "\U0001f32c\ufe0f", "label": "wind", "priority": 3},
    "cold": {"emoji": "\u2744\ufe0f", "label": "cold", "priority": 4},
    "heat": {"emoji": "\U0001f525", "label": "heat", "priority": 4},
    "sunrise": {"emoji": "\U0001f305", "label": "sunrise", "priority": 5},
    "sunset": {"emoji": "\U0001f307", "label": "sunset", "priority": 5},
    "danger": {"emoji": "\u26a0\ufe0f", "label": "danger", "priority": 0},
}

# ============================================================
# Feature Flags
# ============================================================
FEATURES = {
    "decision_engine": os.getenv("UOS_FEAT_DECISION", "true").lower() == "true",
    "weather_api": os.getenv("UOS_FEAT_WEATHER_API", "true").lower() == "true",
    "ephemeris": os.getenv("UOS_FEAT_EPHEMERIS", "true").lower() == "true",
    "geofencing": os.getenv("UOS_FEAT_GEOFENCE", "false").lower() == "true",
    "push_notifications": os.getenv("UOS_FEAT_PUSH", "false").lower() == "true",
    "gamification": os.getenv("UOS_FEAT_GAMIFICATION", "false").lower() == "true",
    "feedback_loop": os.getenv("UOS_FEAT_FEEDBACK", "true").lower() == "true",
    "multi_city": os.getenv("UOS_FEAT_MULTI_CITY", "false").lower() == "true",
}

# ============================================================
# Animation Intensity Levels
# ============================================================
ANIMATION_LEVELS = {
    "calm": {"speed": 0.5, "scale": 1.0},
    "moderate": {"speed": 1.0, "scale": 1.1},
    "intense": {"speed": 1.5, "scale": 1.2},
    "urgent": {"speed": 2.0, "scale": 1.3},
}

# ============================================================
# Default Location (Paris, for demo)
# ============================================================
DEFAULT_LOCATION = {
    "lat": 48.8566,
    "lon": 2.3522,
    "city": "Paris",
    "country": "FR",
}
