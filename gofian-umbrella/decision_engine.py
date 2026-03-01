"""
GOFIAN Umbrella or Sunglasses — Decision Engine v1
Module: decision_engine
Description: Transforms weather data into a binary/multi-icon visual recommendation.
             Scoring model with Analyst-approved weights. Outputs primary + secondary
             icon, animation intensity, and confidence glow level.
Author: GOFIAN AI
Version: 0.1.0
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# Scoring Weights (Council of Ten — Analyst v1)
# ============================================================
WEIGHTS = {
    "rain_probability": 0.35,
    "uv_index": 0.20,
    "wind_speed": 0.15,
    "temperature": 0.15,
    "forecast_confidence": 0.10,
    "sun_elevation": 0.05,
}

# ============================================================
# Thresholds
# ============================================================
THRESHOLDS = {
    "rain_umbrella": 0.40,
    "rain_heavy": 0.70,
    "uv_sunglasses": 3,
    "uv_high": 6,
    "wind_alert_kmh": 40,
    "wind_strong_kmh": 60,
    "temp_cold_c": 5,
    "temp_freezing_c": 0,
    "temp_hot_c": 32,
    "temp_extreme_c": 38,
}


# ============================================================
# Icon Priorities (lower = higher priority)
# ============================================================
ICON_PRIORITY = {
    "danger": 0,
    "umbrella": 1,
    "sunglasses": 2,
    "wind": 3,
    "cold": 4,
    "heat": 4,
    "sunrise": 5,
    "sunset": 5,
    "clear": 6,
}


def _compute_icon_scores(weather: dict, ephemeris: dict) -> list[dict]:
    """Compute a scored list of candidate icons from weather + ephemeris data.

    Args:
        weather: Dict with keys: rain_probability (0-1), uv_index (0-15),
                 wind_speed_kmh, temperature_c, feels_like_c,
                 forecast_confidence (0-1), is_severe.
        ephemeris: Dict with keys: sun_elevation, is_daytime, sunrise, sunset.

    Returns:
        List of icon dicts sorted by score (highest first).
    """
    icons = []

    rain_prob = weather.get("rain_probability", 0)
    uv = weather.get("uv_index", 0)
    wind = weather.get("wind_speed_kmh", 0)
    temp = weather.get("temperature_c", 20)
    feels_like = weather.get("feels_like_c", temp)
    confidence = weather.get("forecast_confidence", 0.8)
    is_severe = weather.get("is_severe", False)
    sun_elev = ephemeris.get("sun_elevation", 45)
    is_daytime = ephemeris.get("is_daytime", True)

    # ----- DANGER (severe weather override) -----
    if is_severe:
        icons.append({
            "icon": "danger",
            "score": 100,
            "intensity": "urgent",
            "reason": "Severe weather alert active",
        })

    # ----- UMBRELLA -----
    if rain_prob >= THRESHOLDS["rain_umbrella"]:
        # Score 50-100 based on rain probability
        score = 50 + (rain_prob - THRESHOLDS["rain_umbrella"]) / (1 - THRESHOLDS["rain_umbrella"]) * 50
        intensity = "intense" if rain_prob >= THRESHOLDS["rain_heavy"] else "moderate"
        icons.append({
            "icon": "umbrella",
            "score": round(score, 1),
            "intensity": intensity,
            "reason": f"Rain probability: {rain_prob*100:.0f}%",
        })

    # ----- SUNGLASSES -----
    if uv >= THRESHOLDS["uv_sunglasses"] and is_daytime:
        score = min(90, 40 + (uv - THRESHOLDS["uv_sunglasses"]) * 8)
        intensity = "intense" if uv >= THRESHOLDS["uv_high"] else "moderate"
        icons.append({
            "icon": "sunglasses",
            "score": round(score, 1),
            "intensity": intensity,
            "reason": f"UV index: {uv}",
        })
    elif is_daytime and sun_elev > 15 and rain_prob < THRESHOLDS["rain_umbrella"]:
        # Bright day without rain → mild sunglasses suggestion
        icons.append({
            "icon": "sunglasses",
            "score": 35,
            "intensity": "calm",
            "reason": f"Bright sky (sun elevation: {sun_elev:.0f}°)",
        })

    # ----- WIND -----
    if wind >= THRESHOLDS["wind_alert_kmh"]:
        score = min(80, 40 + (wind - THRESHOLDS["wind_alert_kmh"]) * 1.5)
        intensity = "intense" if wind >= THRESHOLDS["wind_strong_kmh"] else "moderate"
        icons.append({
            "icon": "wind",
            "score": round(score, 1),
            "intensity": intensity,
            "reason": f"Wind: {wind:.0f} km/h",
        })

    # ----- COLD -----
    if feels_like <= THRESHOLDS["temp_cold_c"]:
        score = min(75, 40 + (THRESHOLDS["temp_cold_c"] - feels_like) * 4)
        intensity = "intense" if feels_like <= THRESHOLDS["temp_freezing_c"] else "moderate"
        icons.append({
            "icon": "cold",
            "score": round(score, 1),
            "intensity": intensity,
            "reason": f"Feels like: {feels_like:.0f}°C",
        })

    # ----- HEAT -----
    if feels_like >= THRESHOLDS["temp_hot_c"]:
        score = min(75, 40 + (feels_like - THRESHOLDS["temp_hot_c"]) * 4)
        intensity = "intense" if feels_like >= THRESHOLDS["temp_extreme_c"] else "moderate"
        icons.append({
            "icon": "heat",
            "score": round(score, 1),
            "intensity": intensity,
            "reason": f"Feels like: {feels_like:.0f}°C",
        })

    # ----- SUNRISE / SUNSET context -----
    if ephemeris.get("is_golden_hour", False):
        if sun_elev > 0 and sun_elev < 10:
            # Determine if morning or evening golden hour
            try:
                sunrise_h = int(ephemeris.get("sunrise", "06:00").split(":")[0])
                sunset_h = int(ephemeris.get("sunset", "18:00").split(":")[0])
                from datetime import datetime, timezone
                now_h = datetime.now(timezone.utc).hour + ephemeris.get("longitude", 0) / 15
                if abs(now_h - sunrise_h) < abs(now_h - sunset_h):
                    icon_name = "sunrise"
                else:
                    icon_name = "sunset"
            except (ValueError, TypeError):
                icon_name = "sunrise"

            icons.append({
                "icon": icon_name,
                "score": 20,
                "intensity": "calm",
                "reason": "Golden hour",
            })

    # ----- CLEAR (fallback) -----
    if not icons:
        icons.append({
            "icon": "sunglasses" if is_daytime else "clear",
            "score": 30,
            "intensity": "calm",
            "reason": "Clear conditions",
        })

    # Sort by score descending, then by icon priority
    icons.sort(key=lambda x: (-x["score"], ICON_PRIORITY.get(x["icon"], 99)))
    return icons


def decide(weather: dict, ephemeris: dict) -> dict:
    """Main decision function. Returns the recommendation.

    Args:
        weather: Weather data dictionary.
        ephemeris: Ephemeris data dictionary.

    Returns:
        Decision dict with primary_icon, secondary_icon, confidence_glow,
        animation_intensity, all_icons, and explanation.
    """
    icons = _compute_icon_scores(weather, ephemeris)
    confidence = weather.get("forecast_confidence", 0.8)

    primary = icons[0] if icons else {"icon": "sunglasses", "score": 30, "intensity": "calm", "reason": "Default"}
    secondary = icons[1] if len(icons) > 1 else None

    # Confidence glow: 0.0 (no glow) to 1.0 (full glow)
    # Based on forecast confidence + primary icon score
    glow = min(1.0, confidence * 0.6 + (primary["score"] / 100) * 0.4)

    # Animation intensity from primary icon
    intensity = primary.get("intensity", "calm")

    decision = {
        "primary_icon": primary["icon"],
        "primary_score": primary["score"],
        "primary_reason": primary["reason"],
        "secondary_icon": secondary["icon"] if secondary else None,
        "secondary_score": secondary["score"] if secondary else None,
        "secondary_reason": secondary["reason"] if secondary else None,
        "confidence_glow": round(glow, 3),
        "animation_intensity": intensity,
        "all_icons": [
            {"icon": ic["icon"], "score": ic["score"], "intensity": ic["intensity"]}
            for ic in icons
        ],
        "forecast_confidence": confidence,
        "is_severe": weather.get("is_severe", False),
    }

    logger.info(
        "Decision: %s (%.0f) + %s | glow=%.2f | %s",
        primary["icon"],
        primary["score"],
        secondary["icon"] if secondary else "none",
        glow,
        intensity,
    )

    return decision


def decide_from_raw(
    rain_probability: float = 0,
    uv_index: float = 0,
    wind_speed_kmh: float = 0,
    temperature_c: float = 20,
    feels_like_c: Optional[float] = None,
    forecast_confidence: float = 0.8,
    is_severe: bool = False,
    sun_elevation: float = 45,
    is_daytime: bool = True,
    is_golden_hour: bool = False,
) -> dict:
    """Convenience wrapper that accepts raw values instead of dicts.

    Returns:
        Same decision dict as decide().
    """
    weather = {
        "rain_probability": rain_probability,
        "uv_index": uv_index,
        "wind_speed_kmh": wind_speed_kmh,
        "temperature_c": temperature_c,
        "feels_like_c": feels_like_c if feels_like_c is not None else temperature_c,
        "forecast_confidence": forecast_confidence,
        "is_severe": is_severe,
    }
    ephemeris_data = {
        "sun_elevation": sun_elevation,
        "is_daytime": is_daytime,
        "is_golden_hour": is_golden_hour,
    }
    return decide(weather, ephemeris_data)
