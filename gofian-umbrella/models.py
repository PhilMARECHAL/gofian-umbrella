"""
GOFIAN Umbrella or Sunglasses — Data Models
Module: models
Description: SQLAlchemy models for UoS. Stores decision history, user feedback,
             and location preferences.
Author: GOFIAN AI
Version: 0.1.0
"""

import uuid
from datetime import datetime, timezone

try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
except ImportError:
    # Allow import without Flask for testing
    from unittest.mock import MagicMock
    db = MagicMock()


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Location(db.Model):
    """A saved location (home, work, etc.)."""
    __tablename__ = "uos_locations"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    name = db.Column(db.String(100), nullable=False)  # "Home", "Work", etc.
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100), default="")
    country = db.Column(db.String(10), default="")
    is_home = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_now)

    decisions = db.relationship("Decision", backref="location", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "city": self.city,
            "country": self.country,
            "is_home": self.is_home,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Decision(db.Model):
    """A weather decision record."""
    __tablename__ = "uos_decisions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    location_id = db.Column(db.String(36), db.ForeignKey("uos_locations.id"), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Decision output
    primary_icon = db.Column(db.String(20), nullable=False)
    primary_score = db.Column(db.Float, default=0)
    secondary_icon = db.Column(db.String(20), nullable=True)
    secondary_score = db.Column(db.Float, nullable=True)
    confidence_glow = db.Column(db.Float, default=0.5)
    animation_intensity = db.Column(db.String(20), default="calm")

    # Weather snapshot
    temperature_c = db.Column(db.Float, nullable=True)
    feels_like_c = db.Column(db.Float, nullable=True)
    rain_probability = db.Column(db.Float, nullable=True)
    uv_index = db.Column(db.Float, nullable=True)
    wind_speed_kmh = db.Column(db.Float, nullable=True)
    weather_source = db.Column(db.String(50), default="demo")

    # Ephemeris snapshot
    sun_elevation = db.Column(db.Float, nullable=True)
    is_daytime = db.Column(db.Boolean, default=True)

    # User feedback
    feedback = db.Column(db.String(10), nullable=True)  # "correct", "wrong"
    feedback_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location_id": self.location_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "primary_icon": self.primary_icon,
            "primary_score": self.primary_score,
            "secondary_icon": self.secondary_icon,
            "confidence_glow": self.confidence_glow,
            "animation_intensity": self.animation_intensity,
            "temperature_c": self.temperature_c,
            "feels_like_c": self.feels_like_c,
            "rain_probability": self.rain_probability,
            "uv_index": self.uv_index,
            "wind_speed_kmh": self.wind_speed_kmh,
            "weather_source": self.weather_source,
            "sun_elevation": self.sun_elevation,
            "is_daytime": self.is_daytime,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Streak(db.Model):
    """Daily check-in streak tracking."""
    __tablename__ = "uos_streaks"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_check_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD
    total_checks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_check_date": self.last_check_date,
            "total_checks": self.total_checks,
        }
