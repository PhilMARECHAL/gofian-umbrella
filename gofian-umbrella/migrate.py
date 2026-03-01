"""
GOFIAN Umbrella or Sunglasses — Database Migration
Creates all tables from SQLAlchemy models.
"""

import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_PROJECT_DIR, "..", ".."))
for p in (_PROJECT_DIR, _REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import create_app
from models import db

app = create_app()

with app.app_context():
    db.create_all()
    print(f"[migrate] Database tables created: {list(db.metadata.tables.keys())}")
