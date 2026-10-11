"""Provision a server-private Room and print its grown-up passcode.

The passcode is shown once and only its hash is stored. A grown-up enters it on each device
to unlock that device for the Room; it is not for children.
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
        room = GameStore(url).provision_room(timedelta(hours=args.ttl_hours))
    except ValueError as exc:
        parser.error(str(exc))
    print(f"room_id={room.room_id}")
    print(f"passcode={room.passcode}  (shown once; give it only to the grown-ups running the session)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
