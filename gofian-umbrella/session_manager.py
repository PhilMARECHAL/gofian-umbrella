"""
GOFIAN Umbrella BUILDER v2.2.0
Module: session_manager
Description: Unified session management -- TTL cleanup daemon, per-IP rate limiting,
             session fingerprinting, conversation history, per-session metrics.
Author: Philippe Marechal / GOFIAN AI
Last modified: 2026-02-23
"""

import hashlib
import logging
import threading
import time

from config import (
    SESSION_TTL_SECONDS,
    MAX_HISTORY_MESSAGES,
    CLEANUP_INTERVAL_SECONDS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_MESSAGE_LENGTH,
    MAX_PROMPT_PASTE_LENGTH,
)

logger = logging.getLogger(__name__)


# ============================================================
# METRICS -- Operational counters
# ============================================================
metrics = {
    "total_messages": 0,
    "total_prompts_delivered": 0,
    "total_sessions_created": 0,
    "total_sessions_cleaned": 0,
    "total_rate_limited": 0,
    "total_errors": 0,
}


# ============================================================
# SESSION STORE -- Unified dict (single source of truth)
# ============================================================
# Structure per session:
# {
#     "messages": [{"role": "user/assistant", "content": "..."}],
#     "prompt_count": 0,
#     "last_active": timestamp,
#     "fingerprint": "sha256_hash",
#     "mode": None | "create" | "improve",
#     "user_name": None | "Philippe",
#     "last_message_id": None,
# }
sessions = {}


# ============================================================
# RATE LIMIT STORE -- Per-IP sliding window
# ============================================================
# { ip_string: [timestamp1, timestamp2, ...] }
rate_limits = {}


def create_session(session_id: str, user_agent: str = "", ip: str = "") -> dict:
    """Create a new session with fingerprint."""
    fingerprint = _make_fingerprint(user_agent, ip)

    sessions[session_id] = {
        "messages": [],
        "prompt_count": 0,
        "last_active": time.time(),
        "fingerprint": fingerprint,
        "mode": None,
        "user_name": None,
        "last_message_id": None,
    }

    metrics["total_sessions_created"] += 1
    logger.info(f"Session created: {session_id[:16]}... (fingerprint: {fingerprint[:8]})")
    return sessions[session_id]


def get_session(session_id: str) -> dict | None:
    """Get session data, updating last_active timestamp."""
    session = sessions.get(session_id)
    if session:
        session["last_active"] = time.time()
    return session


def add_message(session_id: str, role: str, content: str, message_id: str = None) -> bool:
    """
    Add a message to session history.
    Returns False if message is a duplicate.
    Enforces MAX_HISTORY_MESSAGES limit.
    """
    session = sessions.get(session_id)
    if not session:
        return False

    # Deduplication check
    if message_id and session["last_message_id"] == message_id:
        logger.warning(f"Duplicate message blocked: {session_id[:16]}... id={message_id}")
        return False

    session["messages"].append({"role": role, "content": content})
    session["last_active"] = time.time()

    if message_id:
        session["last_message_id"] = message_id

    # Enforce history limit -- keep system-relevant context
    if len(session["messages"]) > MAX_HISTORY_MESSAGES:
        session["messages"] = session["messages"][-MAX_HISTORY_MESSAGES:]

    metrics["total_messages"] += 1
    return True


def increment_prompt_count(session_id: str) -> int:
    """Increment and return new prompt count for session."""
    session = sessions.get(session_id)
    if session:
        session["prompt_count"] += 1
        metrics["total_prompts_delivered"] += 1
        return session["prompt_count"]
    return 0


def get_prompt_count(session_id: str) -> int:
    """Get current prompt count for session."""
    session = sessions.get(session_id)
    return session["prompt_count"] if session else 0


def get_messages(session_id: str) -> list:
    """Get message history for API call (respects MAX_HISTORY limit)."""
    session = sessions.get(session_id)
    if not session:
        return []
    return session["messages"][-MAX_HISTORY_MESSAGES:]


def delete_session(session_id: str) -> bool:
    """Delete a session (used by reset endpoint)."""
    if session_id in sessions:
        del sessions[session_id]
        logger.info(f"Session deleted: {session_id[:16]}...")
        return True
    return False


# ============================================================
# VALIDATION
# ============================================================

def validate_message(message: str, is_prompt_paste: bool = False) -> str | None:
    """
    Validate user message. Returns error string or None if valid.
    """
    if not message or not message.strip():
        return "Message cannot be empty"

    max_len = MAX_PROMPT_PASTE_LENGTH if is_prompt_paste else MAX_MESSAGE_LENGTH

    if len(message) > max_len:
        return f"Message too long (max {max_len} characters)"

    return None


# ============================================================
# RATE LIMITING -- Sliding window per IP
# ============================================================

def check_rate_limit(ip: str) -> bool:
    """
    Check if IP is within rate limit.
    Returns True if allowed, False if rate limited.
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    if ip not in rate_limits:
        rate_limits[ip] = []

    # Clean expired entries
    rate_limits[ip] = [t for t in rate_limits[ip] if t > window_start]

    if len(rate_limits[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        metrics["total_rate_limited"] += 1
        logger.warning(f"Rate limited: {ip} ({len(rate_limits[ip])} requests in {RATE_LIMIT_WINDOW_SECONDS}s)")
        return False

    rate_limits[ip].append(now)
    return True


# ============================================================
# FINGERPRINT -- SHA256(User-Agent + IP)[:16]
# ============================================================

def _make_fingerprint(user_agent: str, ip: str) -> str:
    """Create a short session fingerprint for logging."""
    raw = f"{user_agent}:{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ============================================================
# CLEANUP DAEMON -- Removes expired sessions every 5 minutes
# ============================================================

def _cleanup_loop():
    """Background thread that removes expired sessions."""
    while True:
        time.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            now = time.time()
            expired = [
                sid for sid, data in sessions.items()
                if now - data["last_active"] > SESSION_TTL_SECONDS
            ]
            for sid in expired:
                del sessions[sid]

            if expired:
                metrics["total_sessions_cleaned"] += len(expired)
                logger.info(f"Cleanup: removed {len(expired)} expired sessions. Active: {len(sessions)}")

            # Also clean rate limit entries
            _cleanup_rate_limits(now)

        except Exception as e:
            logger.error(f"Cleanup error: {type(e).__name__} - {str(e)}")


def _cleanup_rate_limits(now: float):
    """Remove old rate limit entries."""
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    expired_ips = []

    for ip, timestamps in rate_limits.items():
        rate_limits[ip] = [t for t in timestamps if t > window_start]
        if not rate_limits[ip]:
            expired_ips.append(ip)

    for ip in expired_ips:
        del rate_limits[ip]


def start_cleanup_daemon():
    """Start the background cleanup thread (call once at app startup)."""
    thread = threading.Thread(target=_cleanup_loop, daemon=True, name="session-cleanup")
    thread.start()
    logger.info(f"Cleanup daemon started: interval={CLEANUP_INTERVAL_SECONDS}s, TTL={SESSION_TTL_SECONDS}s")


# ============================================================
# METRICS ENDPOINT DATA
# ============================================================

def get_metrics() -> dict:
    """Return operational metrics for /metrics endpoint."""
    return {
        **metrics,
        "active_sessions": len(sessions),
        "active_rate_limits": len(rate_limits),
    }
