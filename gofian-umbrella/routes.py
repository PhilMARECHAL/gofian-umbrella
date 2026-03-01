"""
GOFIAN Umbrella or Sunglasses — API Routes
Module: routes
Description: REST API endpoints for UoS. Decision, weather, ephemeris, locations,
             feedback, and streak management.
Author: GOFIAN AI
Version: 0.1.0
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from decision_engine import decide, decide_from_raw
from weather_client import get_weather, clear_cache
from ephemeris import compute_ephemeris, sun_elevation
from models import db, Location, Decision, Streak

logger = logging.getLogger(__name__)

# ============================================================
# Blueprint
# ============================================================
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _error(message: str, status: int = 400) -> tuple:
    return jsonify({"error": message, "status": status}), status


# ============================================================
# DECISION — Core endpoint
# ============================================================

@api_bp.route("/decide", methods=["GET"])
def get_decision():
    """Get weather decision for a location.

    Query params:
        lat (float, required): Latitude
        lon (float, required): Longitude

    Returns:
        Decision with primary/secondary icons, confidence glow, animation.
    """
    try:
        lat = float(request.args.get("lat", 48.8566))
        lon = float(request.args.get("lon", 2.3522))
    except (TypeError, ValueError):
        return _error("Invalid lat/lon parameters")

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return _error("lat must be -90..90, lon must be -180..180")

    # Get weather + ephemeris
    weather = get_weather(lat, lon)
    ephem = compute_ephemeris(lat, lon)

    # Estimate UV from sun elevation if not provided by API
    if weather.get("uv_index", 0) == 0 and ephem.get("sun_elevation", 0) > 0:
        # Rough UV estimate: UV ~ 0.4 * elevation_degrees (capped at 11)
        weather["uv_index"] = min(11, round(ephem["sun_elevation"] * 0.15, 1))

    # Run decision engine
    decision = decide(weather, ephem)

    # Store decision in DB
    try:
        record = Decision(
            latitude=lat,
            longitude=lon,
            primary_icon=decision["primary_icon"],
            primary_score=decision["primary_score"],
            secondary_icon=decision.get("secondary_icon"),
            secondary_score=decision.get("secondary_score"),
            confidence_glow=decision["confidence_glow"],
            animation_intensity=decision["animation_intensity"],
            temperature_c=weather.get("temperature_c"),
            feels_like_c=weather.get("feels_like_c"),
            rain_probability=weather.get("rain_probability"),
            uv_index=weather.get("uv_index"),
            wind_speed_kmh=weather.get("wind_speed_kmh"),
            weather_source=weather.get("source", "unknown"),
            sun_elevation=ephem.get("sun_elevation"),
            is_daytime=ephem.get("is_daytime", True),
        )
        db.session.add(record)
        db.session.commit()
        decision["decision_id"] = record.id
    except Exception as e:
        logger.warning("Failed to store decision: %s", e)
        db.session.rollback()

    return jsonify({"data": decision}), 200


@api_bp.route("/decide/simulate", methods=["POST"])
def simulate_decision():
    """Simulate a decision with custom weather parameters.

    JSON body: rain_probability, uv_index, wind_speed_kmh, temperature_c,
               feels_like_c, sun_elevation, is_daytime, is_severe.
    """
    data = request.get_json(silent=True) or {}

    decision = decide_from_raw(
        rain_probability=float(data.get("rain_probability", 0)),
        uv_index=float(data.get("uv_index", 0)),
        wind_speed_kmh=float(data.get("wind_speed_kmh", 0)),
        temperature_c=float(data.get("temperature_c", 20)),
        feels_like_c=data.get("feels_like_c"),
        forecast_confidence=float(data.get("forecast_confidence", 0.8)),
        is_severe=bool(data.get("is_severe", False)),
        sun_elevation=float(data.get("sun_elevation", 45)),
        is_daytime=bool(data.get("is_daytime", True)),
        is_golden_hour=bool(data.get("is_golden_hour", False)),
    )

    return jsonify({"data": decision}), 200


# ============================================================
# WEATHER — Raw weather data
# ============================================================

@api_bp.route("/weather", methods=["GET"])
def get_weather_data():
    """Get raw weather data for a location.

    Query params: lat, lon
    """
    try:
        lat = float(request.args.get("lat", 48.8566))
        lon = float(request.args.get("lon", 2.3522))
    except (TypeError, ValueError):
        return _error("Invalid lat/lon parameters")

    weather = get_weather(lat, lon)
    return jsonify({"data": weather}), 200


@api_bp.route("/weather/cache", methods=["DELETE"])
def clear_weather_cache():
    """Clear the weather cache."""
    count = clear_cache()
    return jsonify({"cleared": count}), 200


# ============================================================
# EPHEMERIS — Sun data
# ============================================================

@api_bp.route("/ephemeris", methods=["GET"])
def get_ephemeris():
    """Get ephemeris data (sunrise, sunset, sun elevation, etc.).

    Query params: lat, lon
    """
    try:
        lat = float(request.args.get("lat", 48.8566))
        lon = float(request.args.get("lon", 2.3522))
    except (TypeError, ValueError):
        return _error("Invalid lat/lon parameters")

    data = compute_ephemeris(lat, lon)
    return jsonify({"data": data}), 200


# ============================================================
# LOCATIONS — Saved places
# ============================================================

@api_bp.route("/locations", methods=["GET"])
def list_locations():
    """List all saved locations."""
    locations = Location.query.filter_by(is_active=True).order_by(Location.created_at).all()
    return jsonify({
        "data": [loc.to_dict() for loc in locations],
        "count": len(locations),
    }), 200


@api_bp.route("/locations", methods=["POST"])
def create_location():
    """Save a new location.

    JSON body: name (required), latitude (required), longitude (required),
               city, country, is_home.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return _error("'name' is required")

    try:
        lat = float(data.get("latitude", 0))
        lon = float(data.get("longitude", 0))
    except (TypeError, ValueError):
        return _error("Invalid latitude/longitude")

    location = Location(
        name=name,
        latitude=lat,
        longitude=lon,
        city=data.get("city", ""),
        country=data.get("country", ""),
        is_home=bool(data.get("is_home", False)),
    )

    # If marking as home, unset other home locations
    if location.is_home:
        Location.query.filter_by(is_home=True).update({"is_home": False})

    db.session.add(location)
    db.session.commit()
    return jsonify({"data": location.to_dict()}), 201


# ============================================================
# FEEDBACK — User confirmation/correction
# ============================================================

@api_bp.route("/decisions/<decision_id>/feedback", methods=["POST"])
def submit_feedback(decision_id: str):
    """Submit feedback on a decision (correct/wrong).

    JSON body: feedback ("correct" or "wrong")
    """
    decision = Decision.query.get(decision_id)
    if not decision:
        return _error("Decision not found", 404)

    data = request.get_json(silent=True) or {}
    feedback = data.get("feedback", "").strip().lower()
    if feedback not in ("correct", "wrong"):
        return _error("feedback must be 'correct' or 'wrong'")

    decision.feedback = feedback
    decision.feedback_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "data": {
            "decision_id": decision_id,
            "feedback": feedback,
            "recorded_at": decision.feedback_at.isoformat(),
        }
    }), 200


# ============================================================
# STREAK — Gamification
# ============================================================

@api_bp.route("/streak", methods=["GET"])
def get_streak():
    """Get current streak data."""
    streak = Streak.query.first()
    if not streak:
        streak = Streak(current_streak=0, longest_streak=0, total_checks=0)
        db.session.add(streak)
        db.session.commit()

    return jsonify({"data": streak.to_dict()}), 200


@api_bp.route("/streak/check-in", methods=["POST"])
def streak_check_in():
    """Record a daily check-in."""
    streak = Streak.query.first()
    if not streak:
        streak = Streak(current_streak=0, longest_streak=0, total_checks=0)
        db.session.add(streak)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if streak.last_check_date == today:
        # Already checked in today
        return jsonify({
            "data": streak.to_dict(),
            "message": "Already checked in today",
            "new_check": False,
        }), 200

    # Check if streak continues or breaks
    if streak.last_check_date:
        from datetime import timedelta
        last = datetime.strptime(streak.last_check_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        diff = (today_dt - last).days

        if diff == 1:
            streak.current_streak += 1
        elif diff > 1:
            streak.current_streak = 1  # Reset but don't punish
        # diff == 0 handled above
    else:
        streak.current_streak = 1

    streak.last_check_date = today
    streak.total_checks += 1
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    db.session.commit()

    return jsonify({
        "data": streak.to_dict(),
        "message": f"Day {streak.current_streak} streak!",
        "new_check": True,
    }), 200


# ============================================================
# HISTORY — Recent decisions
# ============================================================

@api_bp.route("/decisions", methods=["GET"])
def list_decisions():
    """List recent decisions.

    Query params: limit (default 10), offset (default 0)
    """
    limit = min(50, int(request.args.get("limit", 10)))
    offset = int(request.args.get("offset", 0))

    query = Decision.query.order_by(Decision.created_at.desc())
    total = query.count()
    decisions = query.offset(offset).limit(limit).all()

    return jsonify({
        "data": [d.to_dict() for d in decisions],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    }), 200


# ============================================================
# STATS — Accuracy stats from feedback
# ============================================================

@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get decision accuracy stats from user feedback."""
    total = Decision.query.count()
    with_feedback = Decision.query.filter(Decision.feedback.isnot(None)).count()
    correct = Decision.query.filter_by(feedback="correct").count()
    wrong = Decision.query.filter_by(feedback="wrong").count()

    accuracy = round(correct / with_feedback * 100, 1) if with_feedback > 0 else None

    return jsonify({
        "data": {
            "total_decisions": total,
            "with_feedback": with_feedback,
            "correct": correct,
            "wrong": wrong,
            "accuracy_percent": accuracy,
        }
    }), 200
