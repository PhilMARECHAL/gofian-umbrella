"""
GOFIAN Umbrella BUILDER v2.2.0
Module: app
Description: Flask orchestration layer -- thin wrapper implementing the 6-step Agent Loop.
             All logic delegated to config, system_prompt, api_client, session_manager.
Author: Philippe Marechal / GOFIAN AI
Last modified: 2026-02-23
"""

import logging
import os
import time
import random

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

from config import VERSION, PORT, DEBUG, LOG_LEVEL, INSPIRATION_CACHE_SECONDS, GNEWS_API_KEY, FEATURES
from system_prompt import get_system_prompt
from api_client import AIClient
from session_manager import (
    create_session,
    get_session,
    add_message,
    get_messages,
    increment_prompt_count,
    get_prompt_count,
    delete_session,
    validate_message,
    check_rate_limit,
    start_cleanup_daemon,
    get_metrics,
)

# ============================================================
# INITIALIZATION
# ============================================================

load_dotenv()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Initialize AI client
try:
    ai_client = AIClient()
    if not ai_client.validate_key():
        logger.warning("API key validation failed -- app will start but API calls may fail")
except ValueError as e:
    logger.error(f"Failed to initialize AIClient: {e}")
    ai_client = None

# Start session cleanup daemon
start_cleanup_daemon()

logger.info(f"GOFIAN Umbrella BUILDER v{VERSION} starting...")


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Expects JSON: { message, session_id, country, language, message_id? }
    Returns JSON: { response, prompt_count } or { error }
    """
    if not ai_client:
        return jsonify({"error": "Service not configured. Please try again later."}), 503

    data = request.json or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id", "")
    country = data.get("country", "US")
    language = data.get("language", "en")
    message_id = data.get("message_id")

    # --- Validation ---
    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400

    error = validate_message(user_message)
    if error:
        return jsonify({"error": error}), 400

    # --- Rate limiting ---
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    ip = ip.split(",")[0].strip()  # First IP if behind proxy

    if not check_rate_limit(ip):
        return jsonify({"error": "Too many requests. Please wait a moment."}), 429

    # --- Session management ---
    session = get_session(session_id)
    if not session:
        user_agent = request.headers.get("User-Agent", "")
        session = create_session(session_id, user_agent=user_agent, ip=ip)

    # --- Enrich message with cultural metadata + inspiration ---
    inspiration_tag = ""
    messages_history = get_messages(session_id)
    if len(messages_history) == 0:
        # First message: include inspiration data
        try:
            import urllib.request
            import json
            insp_url = f"http://127.0.0.1:{PORT}/api/inspiration?country={country}&lang={language}"
            with urllib.request.urlopen(insp_url, timeout=4) as resp:
                insp_data = json.loads(resp.read().decode())
                if insp_data.get("fact"):
                    inspiration_tag = f" [INSPIRATION: {insp_data['fact']} | Prompt idea: {insp_data['prompt_idea']}]"
                    if insp_data.get("holiday"):
                        inspiration_tag += f" [HOLIDAY: {insp_data['holiday']}]"
        except Exception:
            pass

    enriched_message = (
        f"[DETECTED_COUNTRY: {country}] [CHOSEN_LANGUAGE: {language}]{inspiration_tag}\n\n"
        f"{user_message}"
    )

    # --- Add to history (with dedup check) ---
    if not add_message(session_id, "user", enriched_message, message_id):
        # Duplicate message -- return last assistant response
        messages = get_messages(session_id)
        last_assistant = next(
            (m["content"] for m in reversed(messages) if m["role"] == "assistant"),
            "",
        )
        return jsonify({
            "response": last_assistant,
            "prompt_count": get_prompt_count(session_id),
        })

    # --- Build API messages ---
    api_messages = [
        {"role": "system", "content": get_system_prompt()},
    ] + get_messages(session_id)

    # --- Call AI ---
    result = ai_client.chat(api_messages)

    if "error" in result:
        logger.error(f"Session {session_id[:16]}: AI error -- {result['error_type']}")
        return jsonify({"error": result["error"]}), 500

    assistant_content = result["content"]

    # --- Track prompt deliveries via [PROMPT_DELIVERED] marker ---
    prompt_count = get_prompt_count(session_id)
    if "[PROMPT_DELIVERED]" in assistant_content:
        prompt_count = increment_prompt_count(session_id)
        # Replace #[N] placeholder with actual count
        assistant_content = assistant_content.replace(
            "Prompt #[N]", f"Prompt #{prompt_count}"
        )
        # Remove the hidden marker from user-visible content
        assistant_content = assistant_content.replace("[PROMPT_DELIVERED]", "").strip()

    # --- Add assistant response to history ---
    add_message(session_id, "assistant", assistant_content)

    # --- Log usage ---
    if result.get("usage"):
        u = result["usage"]
        logger.info(
            f"Session {session_id[:16]}: tokens={u.get('total_tokens', '?')} "
            f"(prompt={u.get('prompt_tokens', '?')}, completion={u.get('completion_tokens', '?')})"
        )

    return jsonify({
        "response": assistant_content,
        "prompt_count": prompt_count,
    })


@app.route("/reset", methods=["POST"])
def reset():
    """Reset a conversation session."""
    data = request.json or {}
    session_id = data.get("session_id", "")

    if session_id:
        delete_session(session_id)

    return jsonify({"status": "Conversation reset"})


@app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "ai_client": "ready" if ai_client else "not_configured",
    })


@app.route("/metrics")
def metrics_endpoint():
    """Operational metrics endpoint."""
    return jsonify(get_metrics())


# ============================================================
# INSPIRATION API (mod #13) -- Dynamic welcome content
# ============================================================

_inspiration_cache = {"data": None, "ts": 0}

# Fallback examples when APIs are unavailable (rotating by day of month)
FALLBACK_INSPIRATIONS = [
    {"fact": "Le premier email a ete envoye en 1971.", "prompt_idea": "Expert redaction d'emails percutants"},
    {"fact": "Netflix a commence par louer des DVD par courrier.", "prompt_idea": "Assistant strategie de contenu video"},
    {"fact": "Le premier smartphone est apparu en 1992.", "prompt_idea": "Expert marketing mobile"},
    {"fact": "Wikipedia a ete lance en 2001 avec 0 article.", "prompt_idea": "Assistant recherche et synthese"},
    {"fact": "Le premier tweet a ete envoye en 2006.", "prompt_idea": "Expert community management"},
    {"fact": "Airbnb est ne d'un matelas gonflable.", "prompt_idea": "Assistant business plan startup"},
    {"fact": "Le code QR a ete invente en 1994 au Japon.", "prompt_idea": "Expert marketing offline-to-online"},
    {"fact": "Le premier blog est apparu en 1994.", "prompt_idea": "Assistant redaction de blog"},
    {"fact": "Amazon a commence en vendant des livres.", "prompt_idea": "Expert e-commerce et ventes"},
    {"fact": "ChatGPT a atteint 100M d'utilisateurs en 2 mois.", "prompt_idea": "Expert prompting avance"},
    {"fact": "Le premier site web a ete cree en 1991 au CERN.", "prompt_idea": "Assistant creation de landing pages"},
    {"fact": "Spotify a transforme l'industrie musicale en 2008.", "prompt_idea": "Expert strategie de contenu audio"},
    {"fact": "Instagram avait 25K users en 24h.", "prompt_idea": "Assistant creation de contenu visuel"},
    {"fact": "Le GPS est devenu public en 2000.", "prompt_idea": "Expert planification de voyages"},
    {"fact": "Le premier emoji a ete cree en 1999.", "prompt_idea": "Assistant communication digitale"},
    {"fact": "YouTube a ete fonde dans un garage en 2005.", "prompt_idea": "Expert scripts video YouTube"},
    {"fact": "Le mot 'robot' vient du tcheque 'robota' (travail).", "prompt_idea": "Assistant automatisation de taches"},
    {"fact": "Le premier jeu video date de 1958.", "prompt_idea": "Expert gamification et engagement"},
    {"fact": "TikTok a change le format du contenu video.", "prompt_idea": "Assistant creation de short-form content"},
    {"fact": "Le premier livre imprime date de 1455 (Gutenberg).", "prompt_idea": "Expert redaction de livres et ebooks"},
    {"fact": "Slack est ne d'un echec de jeu video.", "prompt_idea": "Assistant communication d'equipe"},
    {"fact": "Le cloud computing a decolle en 2006 avec AWS.", "prompt_idea": "Expert architecture technique"},
    {"fact": "Le premier podcast date de 2004.", "prompt_idea": "Assistant preparation d'interviews"},
    {"fact": "Excel a ete lance en 1985.", "prompt_idea": "Expert analyse de donnees"},
    {"fact": "Le premier appel telephonique date de 1876.", "prompt_idea": "Assistant scripts d'appels commerciaux"},
    {"fact": "La premiere photo date de 1826.", "prompt_idea": "Expert direction artistique visuelle"},
    {"fact": "LinkedIn a ete lance en 2003.", "prompt_idea": "Expert personal branding LinkedIn"},
    {"fact": "Zoom est devenu incontournable en 2020.", "prompt_idea": "Assistant preparation de presentations"},
    {"fact": "Le Bluetooth doit son nom a un roi viking.", "prompt_idea": "Expert naming et branding"},
    {"fact": "Python a ete cree en 1991 par Guido van Rossum.", "prompt_idea": "Assistant code Python et debug"},
]


def _fetch_wikipedia_today(lang="en"):
    """Fetch 'On This Day' from Wikipedia API. Returns a fact string or None."""
    try:
        import urllib.request
        import json
        from datetime import datetime
        now = datetime.utcnow()
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/{lang}/onthisday/events/{now.month}/{now.day}"
        req = urllib.request.Request(url, headers={"User-Agent": "GOFIANUmbrellaBuilder/2.2"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            events = data.get("events", [])
            if events:
                # Pick a random interesting event
                event = random.choice(events[:10])
                year = event.get("year", "")
                text = event.get("text", "")
                if year and text:
                    return f"En {year}, {text[:120]}"
    except Exception as e:
        logger.debug(f"Wikipedia API failed: {e}")
    return None


def _fetch_holidays(country="FR"):
    """Fetch public holidays for today. Returns holiday name or None."""
    try:
        import urllib.request
        import json
        from datetime import datetime
        now = datetime.utcnow()
        url = f"https://date.nager.at/api/v3/PublicHolidays/{now.year}/{country}"
        req = urllib.request.Request(url, headers={"User-Agent": "GOFIANUmbrellaBuilder/2.2"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            holidays = json.loads(resp.read().decode())
            today_str = now.strftime("%Y-%m-%d")
            for h in holidays:
                if h.get("date") == today_str:
                    return h.get("localName") or h.get("name")
    except Exception as e:
        logger.debug(f"Holidays API failed: {e}")
    return None


def _get_fallback(lang="en"):
    """Get a fallback inspiration based on day of month."""
    from datetime import datetime
    day = datetime.utcnow().day - 1  # 0-indexed
    idx = day % len(FALLBACK_INSPIRATIONS)
    return FALLBACK_INSPIRATIONS[idx]


@app.route("/api/inspiration")
def inspiration():
    """
    Dynamic inspiration endpoint (mod #13).
    Returns: { fact, prompt_idea, holiday, source }
    Cached for 1 hour. Falls back to static examples if APIs fail.
    """
    if not FEATURES.get("inspiration", True):
        return jsonify({"fact": None, "prompt_idea": None, "holiday": None, "source": "disabled"})

    now = time.time()
    if _inspiration_cache["data"] and (now - _inspiration_cache["ts"]) < INSPIRATION_CACHE_SECONDS:
        return jsonify(_inspiration_cache["data"])

    country = request.args.get("country", "US")
    lang = request.args.get("lang", "en")
    wiki_lang = "fr" if lang == "fr" else "en"

    # Fetch in sequence (fast, 3s timeout each)
    fact = _fetch_wikipedia_today(wiki_lang)
    holiday = _fetch_holidays(country)

    if fact:
        fallback = _get_fallback(lang)
        result = {
            "fact": fact,
            "prompt_idea": fallback["prompt_idea"],
            "holiday": holiday,
            "source": "wikipedia",
        }
    else:
        fallback = _get_fallback(lang)
        result = {
            "fact": fallback["fact"],
            "prompt_idea": fallback["prompt_idea"],
            "holiday": holiday,
            "source": "fallback",
        }

    _inspiration_cache["data"] = result
    _inspiration_cache["ts"] = now

    return jsonify(result)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
