"""Apply supabase/migrations to DATABASE_URL (local/test applier; deployed projects use the Supabase CLI)."""

import os
import sys

from services.api.app.db import apply_migrations


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1
    applied = apply_migrations(url)
    print("applied: " + (", ".join(applied) if applied else "nothing to do"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
