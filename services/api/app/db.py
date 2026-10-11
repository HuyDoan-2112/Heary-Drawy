"""Postgres connection and local/test migration helpers."""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "supabase" / "migrations"
_MIGRATION_LOCK_ID = 7_283_461_902


def connect(database_url: str) -> psycopg.Connection:
    """Open a short-lived connection that returns rows as dicts."""
    return psycopg.connect(database_url, row_factory=dict_row)


def apply_migrations(database_url: str, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply pending SQL files in filename order.

    This is the local/test applier. A deployed Supabase project applies the same
    files with the Supabase CLI. Returns the versions applied by this call.
    """
    applied: list[str] = []
    with psycopg.connect(database_url, autocommit=True) as db:
        db.execute("select pg_advisory_lock(%s)", (_MIGRATION_LOCK_ID,))
        try:
            db.execute(
                "create table if not exists public.app_schema_migrations "
                "(version text primary key, applied_at timestamptz not null default now())"
            )
            done = {row[0] for row in db.execute("select version from public.app_schema_migrations")}
            for path in sorted(directory.glob("*.sql")):
                if path.stem in done:
                    continue
                with db.transaction():
                    db.execute(path.read_text())
                    db.execute("insert into public.app_schema_migrations(version) values (%s)", (path.stem,))
                applied.append(path.stem)
        finally:
            db.execute("select pg_advisory_unlock(%s)", (_MIGRATION_LOCK_ID,))
    return applied
