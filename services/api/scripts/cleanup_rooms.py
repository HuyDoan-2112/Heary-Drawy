"""Delete Rooms, and all of their data, 7 days after they closed or expired (retention policy).

Run it daily, for example from cron or a scheduled job.
"""

import os
import sys

from services.api.app.game.store import GameStore


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1
    deleted = GameStore(url).delete_expired_rooms()
    print(f"deleted {deleted} room(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
