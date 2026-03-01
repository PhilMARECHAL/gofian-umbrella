"""
GOFIAN Umbrella or Sunglasses — Ephemeris Engine
Module: ephemeris
Description: Computes sunrise, sunset, golden hour, sun elevation, and daylight
             context. Pure math — no external API dependency.
Author: GOFIAN AI
Version: 0.1.0
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional


def _julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day Number."""
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0


def _sun_declination(julian_day: float) -> float:
    """Approximate solar declination in degrees."""
    n = julian_day - 2451545.0  # Days since J2000.0
    L = (280.460 + 0.9856474 * n) % 360  # Mean longitude
    g = math.radians((357.528 + 0.9856003 * n) % 360)  # Mean anomaly
    ecliptic_lon = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    obliquity = 23.439 - 0.0000004 * n
    return math.degrees(
        math.asin(math.sin(math.radians(obliquity)) * math.sin(math.radians(ecliptic_lon)))
    )


def _equation_of_time(julian_day: float) -> float:
    """Equation of time in minutes."""
    n = julian_day - 2451545.0
    B = math.radians((360 / 365.24) * (n - 81))
    return 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)


def sun_elevation(lat: float, lon: float, dt: Optional[datetime] = None) -> float:
    """Calculate current sun elevation angle in degrees.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        dt: Datetime (UTC). Defaults to now.

    Returns:
        Sun elevation angle in degrees. Positive = above horizon.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    jd = _julian_day(dt)
    decl = _sun_declination(jd)
    eot = _equation_of_time(jd)

    # Solar time
    hour_offset = lon / 15.0
    solar_time = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + hour_offset + eot / 60.0
    hour_angle = 15.0 * (solar_time - 12.0)

    # Elevation
    lat_rad = math.radians(lat)
    decl_rad = math.radians(decl)
    ha_rad = math.radians(hour_angle)

    sin_elev = (
        math.sin(lat_rad) * math.sin(decl_rad)
        + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad)
    )
    return math.degrees(math.asin(max(-1, min(1, sin_elev))))


def _sunrise_sunset_hour_angle(lat: float, decl: float, angle: float = -0.833) -> Optional[float]:
    """Compute the hour angle for sunrise/sunset.

    Args:
        lat: Latitude in degrees.
        decl: Solar declination in degrees.
        angle: Sun altitude angle (-0.833° for standard, -6° civil twilight).

    Returns:
        Hour angle in degrees, or None if polar day/night.
    """
    lat_rad = math.radians(lat)
    decl_rad = math.radians(decl)
    cos_ha = (
        math.sin(math.radians(angle)) - math.sin(lat_rad) * math.sin(decl_rad)
    ) / (math.cos(lat_rad) * math.cos(decl_rad))

    if cos_ha > 1 or cos_ha < -1:
        return None  # Polar day or polar night
    return math.degrees(math.acos(cos_ha))


def compute_ephemeris(lat: float, lon: float, dt: Optional[datetime] = None) -> dict:
    """Compute full ephemeris data for a location and date.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        dt: Datetime (UTC). Defaults to now.

    Returns:
        Dictionary with sunrise, sunset, golden hours, sun elevation, day length.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    jd = _julian_day(dt)
    decl = _sun_declination(jd)
    eot = _equation_of_time(jd)
    elev = sun_elevation(lat, lon, dt)

    # Timezone offset approximation from longitude
    tz_offset_h = lon / 15.0

    result = {
        "latitude": lat,
        "longitude": lon,
        "date": dt.strftime("%Y-%m-%d"),
        "utc_time": dt.strftime("%H:%M:%S"),
        "sun_elevation": round(elev, 2),
        "sun_declination": round(decl, 2),
        "is_daytime": elev > 0,
        "is_golden_hour": 0 < elev < 10,
        "is_twilight": -6 < elev <= 0,
        "is_night": elev <= -6,
    }

    # Sunrise / sunset
    ha = _sunrise_sunset_hour_angle(lat, decl)
    if ha is not None:
        solar_noon = 12.0 - tz_offset_h - eot / 60.0
        sunrise_h = solar_noon - ha / 15.0
        sunset_h = solar_noon + ha / 15.0

        # Convert decimal hours to HH:MM
        def h_to_hm(h):
            h = h % 24
            return f"{int(h):02d}:{int((h % 1) * 60):02d}"

        result["sunrise"] = h_to_hm(sunrise_h)
        result["sunset"] = h_to_hm(sunset_h)
        result["day_length_hours"] = round(2 * ha / 15.0, 2)

        # Golden hour: sun between 0° and 10°
        ha_golden = _sunrise_sunset_hour_angle(lat, decl, angle=10.0)
        if ha_golden is not None:
            golden_morning_end = solar_noon - ha_golden / 15.0
            golden_evening_start = solar_noon + ha_golden / 15.0
            result["golden_hour_morning"] = f"{h_to_hm(sunrise_h)}-{h_to_hm(golden_morning_end)}"
            result["golden_hour_evening"] = f"{h_to_hm(golden_evening_start)}-{h_to_hm(sunset_h)}"
    else:
        # Polar day or polar night
        result["sunrise"] = None
        result["sunset"] = None
        result["day_length_hours"] = 24.0 if elev > 0 else 0.0
        result["polar"] = "day" if elev > 0 else "night"

    return result
