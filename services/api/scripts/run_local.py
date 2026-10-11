"""Run the API against a local Postgres for adult/synthetic checks only.

Pass --room-hours to also create a Room and print its grown-up passcode for a quick demo.
Requires the dev extra (pgserver, Python 3.12).
"""

import argparse
import os
from datetime import timedelta
from pathlib import Path

import pgserver
import uvicorn

from services.api.app.db import apply_migrations
from services.api.app.game.store import GameStore
from services.api.app.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room-hours", type=float, help="create a demo Room that lasts this many hours")
    args = parser.parse_args()
    # Outside the repo: pg_ctl cannot start from a path containing spaces.
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    data_dir = Path(os.environ.get("LOCAL_DB_DIR", cache / "heary-drawy" / "local-db"))
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    server = pgserver.get_server(data_dir, cleanup_mode="stop")
    url = server.get_uri()
    apply_migrations(url)
    print(f"Local Postgres at {data_dir}", flush=True)
    if args.room_hours:
        room = GameStore(url).provision_room(timedelta(hours=args.room_hours))
        print(f"Demo room {room.room_id} passcode: {room.passcode}", flush=True)
    uvicorn.run(create_app(url), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
