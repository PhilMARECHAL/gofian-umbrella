"""
GOFIAN Umbrella BUILDER v2.2.0
Module: config
Description: All constants, feature flags, and environment variable overrides.
             Single source of truth for VERSION and all configurable values.
Author: Philippe Marechal / GOFIAN AI
Last modified: 2026-02-23
"""

import os

# ============================================================
# VERSION -- Single source of truth
# ============================================================
VERSION = "0.1.0"

# ============================================================
# API CONFIGURATION
# ============================================================
MODEL = os.getenv("MODEL", "gpt-5.2")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "90"))

# ============================================================
# SESSION MANAGEMENT
# ============================================================
SESSION_TTL_SECONDS = 1800          # 30 minutes inactivity -> cleanup
MAX_HISTORY_MESSAGES = 20           # Keep last 20 messages per session
CLEANUP_INTERVAL_SECONDS = 300      # Run cleanup every 5 minutes

# ============================================================
# RATE LIMITING
# ============================================================
RATE_LIMIT_MAX_REQUESTS = 30        # Max requests per window
RATE_LIMIT_WINDOW_SECONDS = 60      # Sliding window duration

# ============================================================
# VALIDATION
# ============================================================
MAX_MESSAGE_LENGTH = 2000           # Standard chat message
MAX_PROMPT_PASTE_LENGTH = 10000     # Improve mode: pasted prompt

# ============================================================
# INSPIRATION API (mod #13)
# ============================================================
INSPIRATION_CACHE_SECONDS = 3600    # Cache inspiration data for 1 hour
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")  # Optional: gnews.io free tier

# ============================================================
# FEATURE FLAGS
# ============================================================
FEATURES = {
    "dual_mode": True,              # Create + Improve modes
    "star_feedback": True,          # Star post-prompt rating
    "email_share": True,            # Email button
    "inspiration": True,            # Dynamic welcome inspiration
    "emailjs": False,               # Phase 2: EmailJS HTML emails
    "streaming": False,             # Phase 2: SSE streaming
    "pdf_export": False,            # Phase 2: downloadable PDF
    "user_accounts": False,         # Phase 3: auth + history
}

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================
# SERVER
# ============================================================
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
