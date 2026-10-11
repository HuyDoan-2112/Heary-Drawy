"""Run the API against a local Postgres for adult/synthetic checks only.

No child-facing Room admission is configured. Requires the dev extra (pgserver, Python 3.12).
"""

import os
from pathlib import Path

import pgserver
import uvicorn

from services.api.app.db import apply_migrations
from services.api.app.main import create_app


def main() -> None:
    # Outside the repo: pg_ctl cannot start from a path containing spaces.
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    data_dir = Path(os.environ.get("LOCAL_DB_DIR", cache / "heary-drawy" / "local-db"))
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    server = pgserver.get_server(data_dir, cleanup_mode="stop")
    url = server.get_uri()
    apply_migrations(url)
    print(f"Local Postgres at {data_dir}; no guest admission route is configured", flush=True)
    uvicorn.run(create_app(url), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
