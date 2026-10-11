"""Provision a server-private Room. Does not grant a guest admission or publish a join route.

The lifetime is explicit because the retention policy remains unresolved.
"""

import argparse
import os
import sys
from datetime import timedelta

from services.api.app.game.store import GameStore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ttl-hours", type=float, required=True, help="Room lifetime in hours")
    args = parser.parse_args()
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1
    try:
        room_id = GameStore(url).provision_room(timedelta(hours=args.ttl_hours))
    except ValueError as exc:
        parser.error(str(exc))
    print(f"room_id={room_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
