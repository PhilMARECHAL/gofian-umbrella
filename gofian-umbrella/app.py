"""
GOFIAN Umbrella or Sunglasses — Flask Application Factory
Module: app
Description: Creates and configures the Flask application.
             Serves both the REST API and the React SPA.
Author: GOFIAN AI
Version: 0.1.0
"""

import os
import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from models import db
import config


# ============================================================
# Application Configuration
# ============================================================

class UoSConfig:
    """Flask configuration for Umbrella or Sunglasses."""
    SECRET_KEY = config.UOS_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///uos_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = config.MAX_CONTENT_LENGTH


# ============================================================
# Application Factory
# ============================================================

def create_app(config_obj=None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_obj: Optional configuration object. Defaults to UoSConfig.

    Returns:
        Configured Flask app.
    """
    app = Flask(
        __name__,
        static_folder="static/dist",
        static_url_path="/static/dist",
    )
    app.config.from_object(config_obj or UoSConfig)

    # ---- Logging ----
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("uos")

    # ---- Database ----
    db.init_app(app)

    # ---- CORS ----
    cors_origins = config.UOS_CORS_ORIGINS
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    logger.info(
        "GOFIAN %s v%s initialized (debug=%s, db=%s)",
        config.DISPLAY_NAME,
        config.VERSION,
        config.UOS_DEBUG,
        "sqlite" if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"] else "postgres",
    )

    # ---- Health endpoints ----
    @app.route("/health")
    @app.route("/api/v1/health")
    def health_check():
        db_ok = False
        try:
            db.session.execute(db.text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        return jsonify({
            "status": "healthy" if db_ok else "degraded",
            "project": config.PROJECT_NAME,
            "version": config.VERSION,
            "tagline": config.TAGLINE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": config.FEATURES,
            "database": {"connected": db_ok},
        })

    @app.route("/api/v1/config")
    def get_public_config():
        return jsonify({
            "data": {
                "version": config.VERSION,
                "project": config.PROJECT_NAME,
                "display_name": config.DISPLAY_NAME,
                "tagline": config.TAGLINE,
                "features": config.FEATURES,
                "scoring_weights": config.SCORING_WEIGHTS,
                "thresholds": {
                    k: v for k, v in config.THRESHOLDS.items()
                    if k != "severe_weather_override"
                },
                "icons": list(config.ICONS.keys()),
                "animation_levels": list(config.ANIMATION_LEVELS.keys()),
                "default_location": config.DEFAULT_LOCATION,
            }
        })

    # ---- API Routes ----
    from routes import api_bp
    app.register_blueprint(api_bp)
    logger.info("API blueprint registered: /api/v1/*")

    # ---- SPA Serving ----
    dist_dir = os.path.join(os.path.dirname(__file__), "static", "dist")
    has_frontend = os.path.isfile(os.path.join(dist_dir, "index.html"))

    # ---- API 404 handler (Council A6: return JSON, not HTML) ----
    @app.errorhandler(404)
    def not_found(e):
        from flask import request
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "not_found",
                "message": f"No API endpoint matches {request.method} {request.path}",
                "status": 404,
            }), 404
        # For non-API routes, let the SPA handle it
        if has_frontend:
            return send_from_directory(dist_dir, "index.html")
        return jsonify({"error": "not_found", "status": 404}), 404

    if has_frontend:
        logger.info("Serving React frontend from %s", dist_dir)

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_spa(path):
            # v0.2: Never serve SPA for API routes (Council A6)
            if path.startswith("api/"):
                return jsonify({
                    "error": "not_found",
                    "message": f"No API endpoint matches /{path}",
                    "status": 404,
                }), 404
            # Serve static files if they exist
            full_path = os.path.join(dist_dir, path)
            if path and os.path.isfile(full_path):
                return send_from_directory(dist_dir, path)
            # SPA fallback: serve index.html
            return send_from_directory(dist_dir, "index.html")
    else:
        logger.info("No frontend build found — API-only mode")

        @app.route("/")
        def index():
            return jsonify({
                "project": config.DISPLAY_NAME,
                "version": config.VERSION,
                "tagline": config.TAGLINE,
                "mode": "api-only",
                "docs": {
                    "decide": "GET /api/v1/decide?lat=48.85&lon=2.35",
                    "weather": "GET /api/v1/weather?lat=48.85&lon=2.35",
                    "ephemeris": "GET /api/v1/ephemeris?lat=48.85&lon=2.35",
                    "simulate": "POST /api/v1/decide/simulate",
                    "health": "GET /health",
                },
            })

    return app
