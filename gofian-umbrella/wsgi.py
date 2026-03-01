"""
GOFIAN Umbrella or Sunglasses — WSGI Entry Point
"""

import os
import sys

# Ensure project directory is in sys.path
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from app import create_app

app = create_app()

if __name__ == "__main__":
    import config
    port = int(os.getenv("PORT", config.UOS_PORT))
    debug = os.getenv("UOS_DEBUG", "true").lower() == "true"
    print(f"\n  [UoS] Umbrella or Sunglasses v{config.VERSION}")
    print(f"  [URL] http://localhost:{port}")
    print(f"  [DBG] Debug: {debug}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
