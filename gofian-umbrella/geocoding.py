"""
GOFIAN Umbrella or Sunglasses — Geocoding Client
Module: geocoding
Description: Forward city search (OWM) + Reverse geocoding (Nominatim).
             Caches results for 24h.
Author: GOFIAN AI
Version: 0.4.0
"""

import logging
import time
import os
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory cache (same pattern as weather_client.py)
_geo_cache: dict = {}
GEOCODE_CACHE_TTL = int(os.getenv("UOS_GEOCODE_CACHE_TTL", "86400"))  # 24 hours

# Nominatim config
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
NOMINATIM_USER_AGENT = "UoS/0.4.0 (GOFIAN AI)"

# Rate limiter for Nominatim (1 req/sec)
_last_nominatim_call = 0.0


def _cache_get(key: str) -> Optional[dict]:
    entry = _geo_cache.get(key)
    if entry and (time.time() - entry["ts"]) < GEOCODE_CACHE_TTL:
        logger.debug("Geocode cache hit: %s", key)
        return entry["data"]
    return None


def _cache_set(key: str, data) -> None:
    _geo_cache[key] = {"data": data, "ts": time.time()}


def _nominatim_throttle():
    """Ensure at least 1 second between Nominatim calls."""
    global _last_nominatim_call
    elapsed = time.time() - _last_nominatim_call
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_nominatim_call = time.time()


def search_cities(query: str, limit: int = 5) -> list:
    """Forward geocoding: query string -> list of city matches.
    
    Tries OpenWeatherMap Geocoding first, falls back to WeatherAPI.
    
    Returns:
        List of dicts: [{name, state, country, lat, lon}]
    """
    cache_key = f"search:{query.lower().strip()}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = _search_owm(query, limit)
    if not results:
        results = _search_weatherapi(query, limit)
    if results is None:
        results = []

    _cache_set(cache_key, results)
    return results


def _search_owm(query: str, limit: int) -> Optional[list]:
    """Search via OpenWeatherMap Geocoding API."""
    try:
        import requests
    except ImportError:
        return None

    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        return None

    try:
        url = "https://api.openweathermap.org/geo/1.0/direct"
        r = requests.get(url, params={
            "q": query,
            "limit": limit,
            "appid": api_key,
        }, timeout=8)

        if r.status_code != 200:
            logger.warning("OWM Geocode returned %d", r.status_code)
            return None

        data = r.json()
        results = []
        seen = set()
        for item in data:
            key = f"{item.get('name','')}-{item.get('country','')}"
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "name": item.get("name", ""),
                "state": item.get("state", ""),
                "country": item.get("country", ""),
                "lat": round(item.get("lat", 0), 4),
                "lon": round(item.get("lon", 0), 4),
            })
        logger.info("OWM Geocode: '%s' -> %d results", query, len(results))
        return results
    except Exception as e:
        logger.error("OWM Geocode error: %s", e)
        return None


def _search_weatherapi(query: str, limit: int) -> Optional[list]:
    """Fallback: Search via WeatherAPI."""
    try:
        import requests
    except ImportError:
        return None

    api_key = os.getenv("WEATHERAPI_KEY", "")
    if not api_key:
        return None

    try:
        url = "https://api.weatherapi.com/v1/search.json"
        r = requests.get(url, params={
            "q": query,
            "key": api_key,
        }, timeout=8)

        if r.status_code != 200:
            return None

        data = r.json()
        results = []
        for item in data[:limit]:
            # WeatherAPI returns country as full name, try to extract code
            country = item.get("country", "")
            # Simple mapping for common countries
            results.append({
                "name": item.get("name", ""),
                "state": item.get("region", ""),
                "country": _country_name_to_code(country),
                "lat": item.get("lat", 0),
                "lon": item.get("lon", 0),
            })
        logger.info("WeatherAPI Geocode: '%s' -> %d results", query, len(results))
        return results
    except Exception as e:
        logger.error("WeatherAPI Geocode error: %s", e)
        return None


# Common country name to ISO code mapping (WeatherAPI returns full names)
_COUNTRY_CODES = {
    "france": "FR", "united kingdom": "GB", "united states of america": "US",
    "germany": "DE", "spain": "ES", "italy": "IT", "japan": "JP",
    "china": "CN", "australia": "AU", "canada": "CA", "brazil": "BR",
    "india": "IN", "russia": "RU", "mexico": "MX", "south korea": "KR",
    "netherlands": "NL", "belgium": "BE", "switzerland": "CH",
    "portugal": "PT", "sweden": "SE", "norway": "NO", "denmark": "DK",
    "finland": "FI", "poland": "PL", "austria": "AT", "greece": "GR",
    "turkey": "TR", "egypt": "EG", "south africa": "ZA", "argentina": "AR",
    "colombia": "CO", "chile": "CL", "peru": "PE", "thailand": "TH",
    "indonesia": "ID", "malaysia": "MY", "singapore": "SG", "vietnam": "VN",
    "philippines": "PH", "new zealand": "NZ", "ireland": "IE", "israel": "IL",
    "united arab emirates": "AE", "saudi arabia": "SA", "qatar": "QA",
    "morocco": "MA", "tunisia": "TN", "algeria": "DZ", "nigeria": "NG",
    "kenya": "KE", "cyprus": "CY", "czech republic": "CZ", "czechia": "CZ",
    "romania": "RO", "hungary": "HU", "croatia": "HR", "iceland": "IS",
    "luxembourg": "LU", "malta": "MT", "ukraine": "UA",
}


def _country_name_to_code(name: str) -> str:
    """Convert country full name to ISO 2-letter code."""
    if len(name) == 2:
        return name.upper()
    return _COUNTRY_CODES.get(name.lower().strip(), name[:2].upper())


def reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocoding: lat/lon -> street, neighborhood, city info.
    
    Uses Nominatim (OpenStreetMap) — free, no API key needed.
    Rate limited to 1 request/second.
    
    Returns:
        Dict with: city, country, street, neighborhood, display_name
    """
    cache_key = f"reverse:{lat:.4f},{lon:.4f}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    result = _reverse_nominatim(lat, lon)
    if result:
        _cache_set(cache_key, result)
        return result

    # Fallback: minimal info
    fallback = {
        "city": "",
        "country": "",
        "country_name": "",
        "street": "",
        "neighborhood": "",
        "display_name": f"{lat:.4f}, {lon:.4f}",
    }
    return fallback


def _reverse_nominatim(lat: float, lon: float) -> Optional[dict]:
    """Reverse geocode via Nominatim."""
    try:
        import requests
    except ImportError:
        return None

    _nominatim_throttle()

    try:
        url = f"{NOMINATIM_BASE_URL}/reverse"
        r = requests.get(url, params={
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
        }, headers={
            "User-Agent": NOMINATIM_USER_AGENT,
        }, timeout=10)

        if r.status_code != 200:
            logger.warning("Nominatim returned %d", r.status_code)
            return None

        data = r.json()
        address = data.get("address", {})

        city = (address.get("city") or address.get("town") 
                or address.get("village") or address.get("municipality") or "")
        country_code = address.get("country_code", "").upper()

        street = address.get("road", "")
        neighborhood = (address.get("suburb") or address.get("neighbourhood") 
                       or address.get("quarter") or address.get("district") or "")

        result = {
            "city": city,
            "country": country_code,
            "country_name": address.get("country", ""),
            "street": street,
            "neighborhood": neighborhood,
            "display_name": data.get("display_name", ""),
        }

        logger.info("Nominatim reverse: %.4f,%.4f -> %s, %s", lat, lon, city, street)
        return result

    except Exception as e:
        logger.error("Nominatim error: %s", e)
        return None


def clear_geocode_cache() -> int:
    """Clear the geocode cache. Returns number of entries cleared."""
    count = len(_geo_cache)
    _geo_cache.clear()
    return count
