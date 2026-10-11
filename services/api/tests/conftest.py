"""Real Postgres for domain tests.

Uses TEST_DATABASE_URL (an admin connection) when set, otherwise a throwaway
local server from the pgserver dev dependency. Each test gets its own database
cloned from a migrated template, so migrations are exercised for real.
"""

import os
from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from services.api.app.db import apply_migrations


@pytest.fixture(scope="session")
def pg_admin_url(tmp_path_factory) -> Iterator[str]:
    configured = os.environ.get("TEST_DATABASE_URL")
    if configured:
        yield configured
        return
    import pgserver

    server = pgserver.get_server(tmp_path_factory.mktemp("pg"))
    try:
        yield server.get_uri()
    finally:
        server.cleanup()


@pytest.fixture(scope="session")
def template_db(pg_admin_url: str) -> str:
    name = f"hd_template_{uuid4().hex[:8]}"
    with psycopg.connect(pg_admin_url, autocommit=True) as admin:
        admin.execute(f'create database "{name}"')
    apply_migrations(make_conninfo(pg_admin_url, dbname=name))
    return name


@pytest.fixture
def database_url(pg_admin_url: str, template_db: str) -> Iterator[str]:
    name = f"hd_test_{uuid4().hex[:12]}"
    with psycopg.connect(pg_admin_url, autocommit=True) as admin:
        admin.execute(f'create database "{name}" template "{template_db}"')
    try:
        yield make_conninfo(pg_admin_url, dbname=name)
    finally:
        with psycopg.connect(pg_admin_url, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{name}" with (force)')


@pytest.fixture
def client(database_url: str) -> Iterator["TestClient"]:
    """API client with a server-provisioned Room and a shared event loop."""
    from datetime import timedelta

    from services.api.app.main import create_app

    app = create_app(database_url, allowed_origins=("http://testserver",))
    room = app.state.game_store.provision_room(timedelta(days=1))
    app.state.test_room_id = room.room_id
    app.state.test_room_passcode = room.passcode
    with TestClient(app) as test_client:
        yield test_client
