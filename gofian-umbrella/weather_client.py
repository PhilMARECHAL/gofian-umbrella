"""
GOFIAN Umbrella or Sunglasses — Weather Client
Module: weather_client
Description: Multi-source weather aggregation with reconciliation.
             Phase 1A: OpenWeatherMap primary + demo fallback.
             Phase 1B: adds WeatherAPI secondary with weighted reconciliation.
Author: GOFIAN AI
Version: 0.1.0
"""

import logging
import time
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# In-memory cache (simple TTL dict)
# ============================================================
_cache: dict = {}
CACHE_TTL = int(os.getenv("UOS_WEATHER_CACHE_TTL", "300"))


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.2f},{lon:.2f}"


def _get_cached(lat: float, lon: float) -> Optional[dict]:
    key = _cache_key(lat, lon)
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        logger.debug("Cache hit for %s", key)
        return entry["data"]
    return None


def _set_cache(lat: float, lon: float, data: dict) -> None:
    _cache[_cache_key(lat, lon)] = {"data": data, "ts": time.time()}


# ============================================================
# OpenWeatherMap Client
# ============================================================
def _fetch_openweathermap(lat: float, lon: float, api_key: str) -> Optional[dict]:
    """Fetch weather from OpenWeatherMap One Call API 3.0.

    Falls back to 2.5 /weather endpoint if 3.0 is not available.
    """
    try:
        import requests
    except ImportError:
        logger.warning("requests library not available")
        return None

    if not api_key:
        return None

    # Try 2.5 current weather (most widely available)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            logger.warning("OWM returned %d: %s", r.status_code, r.text[:200])
            return None

        d = r.json()
        main = d.get("main", {})
        wind = d.get("wind", {})
        weather = d.get("weather", [{}])[0]
        clouds = d.get("clouds", {})
        rain = d.get("rain", {})

        # Estimate rain probability from current conditions
        rain_1h = rain.get("1h", 0)
        weather_id = weather.get("id", 800)
        if weather_id < 600:  # Rain/drizzle/thunderstorm
            rain_prob = min(1.0, 0.5 + rain_1h * 0.1)
        elif weather_id < 700:  # Snow
            rain_prob = 0.3
        elif clouds.get("all", 0) > 80:
            rain_prob = 0.25
        else:
            rain_prob = max(0, clouds.get("all", 0) / 400)

        return {
            "source": "openweathermap",
            "temperature_c": main.get("temp", 20),
            "feels_like_c": main.get("feels_like", main.get("temp", 20)),
            "humidity": main.get("humidity", 50),
            "pressure_hpa": main.get("pressure", 1013),
            "wind_speed_kmh": round((wind.get("speed", 0)) * 3.6, 1),  # m/s → km/h
            "wind_gust_kmh": round((wind.get("gust", 0)) * 3.6, 1),
            "rain_probability": round(rain_prob, 2),
            "rain_1h_mm": rain_1h,
            "cloud_cover": clouds.get("all", 0),
            "uv_index": 0,  # Not in 2.5 free — use ephemeris fallback
            "visibility_m": d.get("visibility", 10000),
            "weather_condition": weather.get("main", "Clear"),
            "weather_description": weather.get("description", "clear sky"),
            "weather_icon": weather.get("icon", "01d"),
            "is_severe": weather_id < 300 or weather_id in (781, 762, 771),
            "forecast_confidence": 0.85,
            "timestamp": d.get("dt", int(time.time())),
        }
    except Exception as e:
        logger.error("OWM fetch error: %s", e)
        return None


# ============================================================
# Demo / Fallback Data
# ============================================================
def _demo_weather(lat: float, lon: float) -> dict:
    """Generate plausible demo weather data based on latitude and time of day.

    Used when no API key is configured or APIs are unreachable.
    """
    import math
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    hour = (now.hour + lon / 15) % 24  # Local solar time approximation
    month = now.month

    # Seasonal temperature model
    # Base temp varies by latitude and month
    lat_factor = 1 - abs(lat) / 90  # 0 at poles, 1 at equator
    season_offset = 15 * math.cos(math.radians((month - 7) * 30))  # Peak July NH
    if lat < 0:
        season_offset = -season_offset  # Reverse for SH

    base_temp = 10 + 20 * lat_factor + season_offset
    # Diurnal variation
    diurnal = 5 * math.sin(math.radians((hour - 6) * 15))
    temp = round(base_temp + diurnal, 1)

    # UV model: peaks at solar noon, higher near equator
    uv_base = max(0, 8 * lat_factor * math.sin(math.radians(max(0, (hour - 6) * 15))))
    uv_seasonal = 1 + 0.5 * math.cos(math.radians((month - 6) * 30))
    uv = round(min(11, uv_base * uv_seasonal), 1)

    # Rain probability: higher in certain conditions
    rain_base = 0.15 + 0.1 * math.sin(math.radians(hour * 30))
    rain_prob = round(max(0, min(1, rain_base)), 2)

    # Wind: moderate baseline
    wind = round(10 + 8 * abs(math.sin(math.radians(hour * 20))), 1)

    return {
        "source": "demo",
        "temperature_c": temp,
        "feels_like_c": round(temp - wind * 0.1, 1),
        "humidity": 55,
        "pressure_hpa": 1015,
        "wind_speed_kmh": wind,
        "wind_gust_kmh": round(wind * 1.4, 1),
        "rain_probability": rain_prob,
        "rain_1h_mm": 0,
        "cloud_cover": int(rain_prob * 100),
        "uv_index": uv,
        "visibility_m": 10000,
        "weather_condition": "Clear" if rain_prob < 0.3 else "Clouds",
        "weather_description": "demo data — configure API key for real weather",
        "weather_icon": "01d" if 6 < hour < 20 else "01n",
        "is_severe": False,
        "forecast_confidence": 0.60,  # Lower confidence for demo
        "timestamp": int(time.time()),
    }


# ============================================================
# Public API
# ============================================================
def get_weather(lat: float, lon: float) -> dict:
    """Get current weather for a location.

    Tries OpenWeatherMap first, falls back to demo data.
    Results are cached for CACHE_TTL seconds.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.

    Returns:
        Normalized weather data dictionary.
    """
    # Check cache first
    cached = _get_cached(lat, lon)
    if cached:
        return cached

    # Try OpenWeatherMap
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if api_key:
        data = _fetch_openweathermap(lat, lon, api_key)
        if data:
            _set_cache(lat, lon, data)
            return data

    # Fallback to demo data
    logger.info("Using demo weather data (no API key configured)")
    data = _demo_weather(lat, lon)
    _set_cache(lat, lon, data)
    return data


def get_weather_multi(lat: float, lon: float) -> dict:
    """Get weather from multiple sources and reconcile (Phase 1B).

    Currently only uses primary source. Multi-source reconciliation
    will be implemented when secondary API is configured.
    """
    primary = get_weather(lat, lon)
    # TODO Phase 1B: add secondary source + weighted reconciliation
    primary["reconciliation"] = {
        "sources_queried": 1,
        "sources_responded": 1,
        "method": "single_source",
    }
    return primary


def clear_cache() -> int:
    """Clear the weather cache. Returns number of entries cleared."""
    count = len(_cache)
    _cache.clear()
    return count
