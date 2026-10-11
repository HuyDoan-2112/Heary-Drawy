"""Explicit local-only fixture room. Never use for deployment or child sessions."""

from pathlib import Path

from services.api.app.main import create_app

app = create_app(db_path=Path("services/api/.local-demo.sqlite3"), fixture_room=True)
