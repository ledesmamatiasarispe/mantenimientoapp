from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Generator
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from gestion_mantenimiento.data.paths import (  # noqa: E402
    get_database_path as get_desktop_database_path,
)
from gestion_mantenimiento.data.schema import initialize_database  # noqa: E402


def resolve_database_path() -> Path:
    configured = os.environ.get("DB_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    return get_desktop_database_path()


def initialize_api_database() -> Path:
    database_path = resolve_database_path()
    initialize_database(database_path, seed=False)
    return database_path


def create_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(resolve_database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = create_connection()
    try:
        yield connection
    finally:
        connection.close()

