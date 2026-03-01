"""
GOFIAN Umbrella or Sunglasses — Seed Data
Creates demo locations for first-run experience.
"""

import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_PROJECT_DIR, "..", ".."))
for p in (_PROJECT_DIR, _REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import create_app
from models import db, Location, Streak

DEMO_LOCATIONS = [
    {"name": "Paris", "latitude": 48.8566, "longitude": 2.3522, "city": "Paris", "country": "FR", "is_home": True},
    {"name": "Limassol", "latitude": 34.6841, "longitude": 33.0379, "city": "Limassol", "country": "CY", "is_home": False},
    {"name": "New York", "latitude": 40.7128, "longitude": -74.0060, "city": "New York", "country": "US", "is_home": False},
    {"name": "Tokyo", "latitude": 35.6762, "longitude": 139.6503, "city": "Tokyo", "country": "JP", "is_home": False},
    {"name": "Sydney", "latitude": -33.8688, "longitude": 151.2093, "city": "Sydney", "country": "AU", "is_home": False},
]

app = create_app()

with app.app_context():
    # Only seed if no locations exist
    if Location.query.count() == 0:
        for loc_data in DEMO_LOCATIONS:
            loc = Location(**loc_data)
            db.session.add(loc)
        db.session.commit()
        print(f"[seed] Created {len(DEMO_LOCATIONS)} demo locations")
    else:
        print(f"[seed] Locations already exist ({Location.query.count()}), skipping")

    # Create default streak if none exists
    if Streak.query.count() == 0:
        streak = Streak(current_streak=0, longest_streak=0, total_checks=0)
        db.session.add(streak)
        db.session.commit()
        print("[seed] Created default streak tracker")
    else:
        print("[seed] Streak already exists, skipping")

    print("[seed] Done!")
