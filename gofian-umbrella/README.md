# GOFIAN Umbrella BUILDER v0.1.0

> iOS-first specification engine for the **Umbrella** app (minimalist, chic & fun).

This repo is a **lightweight Flask web app** that chats with an AI assistant configured to produce a **complete, implementation-ready cahier des charges** for Umbrella, plus backlog + architecture.

## ✨ What it does

- **iOS-first Umbrella spec builder** (SwiftUI, CoreLocation, WidgetKit)
- **Expert panel workflow** (product, iOS engineering, meteorology/data, privacy/security + skeptic)
- **Instant-use focus**: “Open → Umbrella YES/NO/MAYBE”
- **Structured outputs**: spec sections + epics/user stories + acceptance criteria

## 📁 Architecture

See [MANIFEST.md](MANIFEST.md) for the complete file registry.

```
gofian-umbrella/
├── app.py                 # Flask routes (/chat, /reset, /health, /metrics)
├── config.py              # Constants, flags, env overrides (VERSION source of truth)
├── system_prompt.py       # UMBRELLA-SPEC OS (AI brain)
├── api_client.py          # OpenAI wrapper with retry logic
├── session_manager.py     # Sessions, cleanup, rate limiting, metrics
├── static/
│   └── index.html         # Frontend SPA (HTML + CSS + JS)
├── Procfile               # Gunicorn config for Render
├── requirements.txt       # Python dependencies (pinned)
├── MANIFEST.md            # File registry and conventions
├── CHANGELOG.md           # Version history
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## ⚡ Quick Start

```bash
# 1) Unpack / clone
cd gofian-umbrella

# 2) Set env var
export OPENAI_API_KEY="..."

# 3) Install + run
pip install -r requirements.txt
python app.py

# Open http://localhost:5000
```

## 🌐 Deploy (Render)

- Create a Web Service
- Set env var: `OPENAI_API_KEY`
- Deploy (Render uses the `Procfile`)

## 📊 Endpoints

| Route | Method | Description |
|------:|:------:|-------------|
| `/` | GET | Main application |
| `/chat` | POST | Chat with UmbrellaBuilder |
| `/reset` | POST | Reset conversation |
| `/health` | GET | Health check (returns version) |
| `/metrics` | GET | Operational metrics |

## 🔒 Notes

- Location/privacy constraints must be handled in the **spec**, not by this web app.
- This web app stores **short-lived sessions in memory** (see `SESSION_TTL_SECONDS`).

---

Built by Philippe Marechal · GOFIAN AI · v0.1.0
