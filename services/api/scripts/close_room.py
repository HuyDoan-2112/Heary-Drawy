"""Close a Room now: no new admissions, and every child session and device unlock stops working.

Running API processes notice on the children's next request or reconnect.
"""

import argparse
import os
import sys

from services.api.app.game.store import GameError, GameStore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("room_id")
    args = parser.parse_args()
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1
    try:
        players = GameStore(url).close_room(args.room_id)
    except GameError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    print(f"closed {args.room_id}; {len(players)} admitted player(s) signed out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
