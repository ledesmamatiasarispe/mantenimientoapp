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


def test_migrate_legacy_db_sin_repuestos(tmp_path: Path) -> None:
    """Simula una DB creada ANTES del commit de repuestos y verifica que la migración funciona."""
    path = tmp_path / "legacy.sqlite3"

    # Crear DB con el schema antiguo (sin tabla repuestos, sin columna repuesto_id)
    SCHEMA_LEGACY = """
    CREATE TABLE tipos_equipo (
        id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, activo INTEGER NOT NULL DEFAULT 1,
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE equipos (
        id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, tipo_id INTEGER,
        activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE tecnicos (
        id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, apellido TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE ordenes_trabajo (
        id INTEGER PRIMARY KEY, equipo_id INTEGER NOT NULL, tipo TEXT NOT NULL DEFAULT 'CORRECTIVO',
        descripcion TEXT NOT NULL DEFAULT '', fecha_apertura TEXT NOT NULL DEFAULT '',
        fecha_cierre TEXT NOT NULL DEFAULT '', estado TEXT NOT NULL DEFAULT 'PENDIENTE',
        tecnico_id INTEGER, costo_mano_obra NUMERIC NOT NULL DEFAULT 0,
        observaciones TEXT NOT NULL DEFAULT '', creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE repuestos_orden (
        id INTEGER PRIMARY KEY, orden_id INTEGER NOT NULL,
        descripcion TEXT NOT NULL DEFAULT '', cantidad NUMERIC NOT NULL DEFAULT 1,
        costo_unitario NUMERIC NOT NULL DEFAULT 0,
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE programas_mantenimiento (
        id INTEGER PRIMARY KEY, equipo_id INTEGER NOT NULL,
        descripcion TEXT NOT NULL DEFAULT '', frecuencia_dias INTEGER NOT NULL DEFAULT 1,
        ultima_ejecucion TEXT NOT NULL DEFAULT '', proxima_ejecucion TEXT NOT NULL DEFAULT '',
        activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE alertas_app (
        clave TEXT PRIMARY KEY, avisar_nuevamente_desde TEXT NOT NULL DEFAULT '',
        actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(SCHEMA_LEGACY)

    # Verificar que la DB legacy NO tiene repuestos ni repuesto_id
    with closing(sqlite3.connect(path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "repuestos" not in tables
        cols = {r[1] for r in conn.execute("PRAGMA table_info(repuestos_orden)")}
        assert "repuesto_id" not in cols

    # Ejecutar las migraciones
    initialize_database(path)

    # Verificar que después de la migración todo existe
    with closing(sqlite3.connect(path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "repuestos" in tables

        cols = {r[1] for r in conn.execute("PRAGMA table_info(repuestos_orden)")}
        assert "repuesto_id" in cols

        # Verificar que se puede insertar en repuestos
        conn.execute("INSERT INTO repuestos (nombre) VALUES ('Test')")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM repuestos").fetchone()[0]
        assert count == 1

        # Verificar que se puede insertar en repuestos_orden con repuesto_id
        conn.execute(
            "INSERT INTO tipos_equipo (nombre) VALUES ('Tipo test')"
        )
        conn.execute(
            "INSERT INTO equipos (nombre, tipo_id) VALUES ('Equipo test', 1)"
        )
        conn.execute(
            "INSERT INTO ordenes_trabajo (equipo_id, descripcion) VALUES (1, 'Test orden')"
        )
        conn.execute(
            "INSERT INTO repuestos_orden (orden_id, repuesto_id, descripcion, cantidad)"
            " VALUES (1, 1, 'Test', 2)"
        )
        conn.commit()
