from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from gestion_mantenimiento.data.schema import (
    clear_database,
    initialize_database,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.sqlite3"
    initialize_database(path, seed=True)
    return path


def test_initialize_creates_tables(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    expected = {
        "repuestos",
        "tipos_equipo",
        "equipos",
        "tecnicos",
        "ordenes_trabajo",
        "repuestos_orden",
        "programas_mantenimiento",
        "alertas_app",
    }
    assert expected <= tables


def test_seed_inserts_tipos_equipo(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tipos_equipo").fetchone()[0]
    assert count >= 5


def test_seed_inserts_tecnicos(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tecnicos").fetchone()[0]
    assert count >= 3


def test_seed_inserts_equipos(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM equipos").fetchone()[0]
    assert count >= 3


def test_idempotent_initialize(db_path: Path) -> None:
    initialize_database(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tipos_equipo").fetchone()[0]
    assert count >= 5


def test_clear_database(db_path: Path) -> None:
    clear_database(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        for table in ("tipos_equipo", "equipos", "tecnicos", "ordenes_trabajo"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count == 0
