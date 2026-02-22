# GOFIAN Umbrella BUILDER — File Manifest

> Master registry of all project files.
> Last updated: 2026-02-22 | Version: 0.1.0

## Versioning Standard

This project follows **Semantic Versioning (SemVer 2.0.0)**: `MAJOR.MINOR.PATCH`.

**Single Source of Truth**: The version number lives in `config.py` (`VERSION`).

## File Registry

### Backend (Python)

| File | Module | Description |
|------|--------|-------------|
| `config.py` | Configuration | Constants, feature flags, env overrides. Single source of truth for `VERSION`, model, timeouts, rate limits. |
| `app.py` | Orchestration | Flask routes (`/chat`, `/reset`, `/health`, `/metrics`). Thin wrapper — delegates to other modules. |
| `system_prompt.py` | AI Brain | **UMBRELLA-SPEC OS** — system instructions to generate a complete Umbrella specification/backlog using an expert-panel workflow. |
| `api_client.py` | API Layer | OpenAI API wrapper with retry logic, timeouts, error normalization. |
| `session_manager.py` | Sessions | Session store, conversation history, TTL cleanup daemon, rate limiting, per-session metrics. |

### Frontend

| File | Description |
|------|-------------|
| `static/index.html` | Single-file SPA (HTML + CSS + JS). Chat UI + session handling. |

### Deployment & Config

| File | Description |
|------|-------------|
| `Procfile` | Gunicorn startup command for Render |
| `requirements.txt` | Python dependencies (pinned) |
| `.gitignore` | Git exclusions |

### Documentation

| File | Description |
|------|-------------|
| `README.md` | Project overview, setup, endpoints |
| `CHANGELOG.md` | Version history |
| `MANIFEST.md` | This file |
