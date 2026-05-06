from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS repuestos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    observaciones TEXT NOT NULL DEFAULT '',
    stock_actual NUMERIC NOT NULL DEFAULT 0,
    stock_minimo NUMERIC NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tipos_equipo (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo_id INTEGER,
    numero_serie TEXT NOT NULL DEFAULT '',
    marca TEXT NOT NULL DEFAULT '',
    modelo TEXT NOT NULL DEFAULT '',
    ubicacion TEXT NOT NULL DEFAULT '',
    fecha_adquisicion TEXT NOT NULL DEFAULT '',
    observaciones TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_id) REFERENCES tipos_equipo(id)
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    legajo TEXT NOT NULL DEFAULT '',
    telefono TEXT NOT NULL DEFAULT '',
    especialidad TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ordenes_trabajo (
    id INTEGER PRIMARY KEY,
    equipo_id INTEGER NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'CORRECTIVO'
        CHECK (tipo IN ('PREVENTIVO', 'CORRECTIVO', 'MEJORA')),
    descripcion TEXT NOT NULL DEFAULT '',
    fecha_apertura TEXT NOT NULL DEFAULT '',
    fecha_cierre TEXT NOT NULL DEFAULT '',
    estado TEXT NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'CANCELADA')),
    tecnico_id INTEGER,
    costo_mano_obra NUMERIC NOT NULL DEFAULT 0,
    observaciones TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
);

CREATE TABLE IF NOT EXISTS repuestos_orden (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL,
    repuesto_id INTEGER,
    descripcion TEXT NOT NULL DEFAULT '',
    cantidad NUMERIC NOT NULL DEFAULT 1,
    costo_unitario NUMERIC NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
    FOREIGN KEY (repuesto_id) REFERENCES repuestos(id)
);

CREATE TABLE IF NOT EXISTS programas_mantenimiento (
    id INTEGER PRIMARY KEY,
    equipo_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    frecuencia_meses INTEGER NOT NULL DEFAULT 1,
    ultima_ejecucion TEXT NOT NULL DEFAULT '',
    proxima_ejecucion TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

CREATE TABLE IF NOT EXISTS alertas_app (
    clave TEXT PRIMARY KEY,
    avisar_nuevamente_desde TEXT NOT NULL DEFAULT '',
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orden_colaboradores (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (orden_id, tecnico_id),
    FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
    FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
);

CREATE TABLE IF NOT EXISTS orden_programas (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL,
    programa_id INTEGER NOT NULL,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (orden_id, programa_id),
    FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
    FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
);

CREATE TABLE IF NOT EXISTS orden_adjuntos (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL,
    nombre TEXT NOT NULL DEFAULT '',
    ruta TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id)
);

CREATE TABLE IF NOT EXISTS programa_pasos (
    id INTEGER PRIMARY KEY,
    programa_id INTEGER NOT NULL,
    posicion INTEGER NOT NULL DEFAULT 0,
    descripcion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
);

CREATE TABLE IF NOT EXISTS orden_paso_estado (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL,
    paso_id INTEGER NOT NULL,
    completado INTEGER NOT NULL DEFAULT 0,
    tecnico_id INTEGER,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (orden_id, paso_id),
    FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
    FOREIGN KEY (paso_id) REFERENCES programa_pasos(id),
    FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
);

CREATE TABLE IF NOT EXISTS programa_adjuntos (
    id INTEGER PRIMARY KEY,
    programa_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('FOTO', 'PDF')),
    nombre TEXT NOT NULL DEFAULT '',
    ruta TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
);

CREATE INDEX IF NOT EXISTS idx_repuestos_nombre ON repuestos(nombre);
CREATE INDEX IF NOT EXISTS idx_equipos_tipo_id ON equipos(tipo_id);
CREATE INDEX IF NOT EXISTS idx_equipos_nombre ON equipos(nombre);
CREATE INDEX IF NOT EXISTS idx_ordenes_equipo_id ON ordenes_trabajo(equipo_id);
CREATE INDEX IF NOT EXISTS idx_ordenes_tecnico_id ON ordenes_trabajo(tecnico_id);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON ordenes_trabajo(estado);
CREATE INDEX IF NOT EXISTS idx_ordenes_fecha_apertura ON ordenes_trabajo(fecha_apertura);
CREATE INDEX IF NOT EXISTS idx_repuestos_orden_id ON repuestos_orden(orden_id);
CREATE INDEX IF NOT EXISTS idx_programas_equipo_id ON programas_mantenimiento(equipo_id);
CREATE INDEX IF NOT EXISTS idx_programas_proxima ON programas_mantenimiento(proxima_ejecucion);
"""

SEED_SQL = """
INSERT OR IGNORE INTO repuestos (id, nombre, observaciones, stock_actual, stock_minimo) VALUES
    (1, 'Filtro de aceite', '', 10, 3),
    (2, 'Correa dentada', '', 5, 2),
    (3, 'Aceite hidráulico 10L', '', 20, 5),
    (4, 'Rodamiento 6205', '', 8, 3),
    (5, 'Fusible 10A', '', 50, 10);

INSERT OR IGNORE INTO tipos_equipo (id, nombre) VALUES
    (1, 'Maquinaria pesada'),
    (2, 'Vehículo'),
    (3, 'Herramienta'),
    (4, 'Equipamiento eléctrico'),
    (5, 'Sistema hidráulico');

INSERT OR IGNORE INTO tecnicos (id, nombre, apellido, legajo, telefono, especialidad) VALUES
    (1, 'Carlos', 'García', '20111111', '3516000001', 'Mecánica general'),
    (2, 'Martín', 'López', '24222222', '3516000002', 'Electricidad'),
    (3, 'Diego', 'Fernández', '28333333', '3516000003', 'Hidráulica');

INSERT OR IGNORE INTO equipos (id, nombre, tipo_id, marca, modelo, ubicacion) VALUES
    (1, 'Compresor principal', 1, 'Atlas Copco', 'GA37', 'Planta A'),
    (2, 'Montacargas #1', 2, 'Toyota', '8FGU25', 'Depósito'),
    (3, 'Generador auxiliar', 4, 'Cummins', 'C80D5', 'Planta B');
"""


def initialize_database(database_path: Path, *, seed: bool = False) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        # Disable FK enforcement during schema setup to avoid ordering issues
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.executescript(SCHEMA_SQL)
        # Run all migrations explicitly outside executescript so errors surface clearly
        _migrate_tecnicos_legajo(connection)
        _migrate_frecuencia_meses(connection)
        _migrate_repuestos(connection)
        _migrate_repuestos_orden_repuesto_id(connection)
        _migrate_tecnicos_password_hash(connection)
        _migrate_orden_colaboradores(connection)
        _migrate_orden_programas(connection)
        _migrate_programa_adjuntos(connection)
        _migrate_orden_adjuntos(connection)
        _migrate_programa_pasos(connection)
        _migrate_orden_paso_estado(connection)
        connection.execute("PRAGMA foreign_keys = ON")
        if seed:
            connection.executescript(SEED_SQL)
        connection.commit()


def clear_database(database_path: Path) -> None:
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for table_name in (
            "orden_paso_estado",
            "orden_adjuntos",
            "programa_pasos",
            "programa_adjuntos",
            "orden_colaboradores",
            "orden_programas",
            "repuestos_orden",
            "ordenes_trabajo",
            "programas_mantenimiento",
            "alertas_app",
            "equipos",
            "tipos_equipo",
            "tecnicos",
            "repuestos",
        ):
            connection.execute(f"DELETE FROM {table_name}")
        connection.commit()


def _migrate_tecnicos_legajo(connection: sqlite3.Connection) -> None:
    """Renombra dni → legajo en tecnicos."""
    if not _table_exists(connection, "tecnicos"):
        return
    cols = _table_columns(connection, "tecnicos")
    if "dni" in cols and "legajo" not in cols:
        connection.execute("ALTER TABLE tecnicos RENAME COLUMN dni TO legajo")


def _migrate_frecuencia_meses(connection: sqlite3.Connection) -> None:
    """Renombra frecuencia_dias → frecuencia_meses en programas_mantenimiento."""
    if not _table_exists(connection, "programas_mantenimiento"):
        return
    cols = _table_columns(connection, "programas_mantenimiento")
    if "frecuencia_dias" in cols and "frecuencia_meses" not in cols:
        connection.execute(
            "ALTER TABLE programas_mantenimiento"
            " RENAME COLUMN frecuencia_dias TO frecuencia_meses"
        )


def _migrate_repuestos(connection: sqlite3.Connection) -> None:
    """Garantiza que la tabla repuestos exista (DB creadas antes del commit de repuestos)."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS repuestos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            observaciones TEXT NOT NULL DEFAULT '',
            stock_actual NUMERIC NOT NULL DEFAULT 0,
            stock_minimo NUMERIC NOT NULL DEFAULT 0,
            activo INTEGER NOT NULL DEFAULT 1,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_repuestos_nombre ON repuestos(nombre)"
    )


def _migrate_repuestos_orden_repuesto_id(connection: sqlite3.Connection) -> None:
    """Agrega repuesto_id a repuestos_orden si no existe (DB sin esta columna)."""
    if not _table_exists(connection, "repuestos_orden"):
        return
    if "repuesto_id" not in _table_columns(connection, "repuestos_orden"):
        # DEFAULT NULL es obligatorio cuando foreign_keys=ON + REFERENCES en ADD COLUMN.
        # Usamos sólo DEFAULT NULL sin REFERENCES para evitar la restricción de FK.
        connection.execute(
            "ALTER TABLE repuestos_orden ADD COLUMN repuesto_id INTEGER DEFAULT NULL"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_repuestos_orden_repuesto_id"
            " ON repuestos_orden(repuesto_id)"
        )


def _migrate_tecnicos_password_hash(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "tecnicos"):
        return
    if "password_hash" not in _table_columns(connection, "tecnicos"):
        connection.execute(
            "ALTER TABLE tecnicos ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''"
        )


def _migrate_orden_adjuntos(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orden_adjuntos (
            id INTEGER PRIMARY KEY,
            orden_id INTEGER NOT NULL,
            nombre TEXT NOT NULL DEFAULT '',
            ruta TEXT NOT NULL DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_orden_adjuntos_orden_id ON orden_adjuntos(orden_id)"
    )


def _migrate_programa_pasos(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS programa_pasos (
            id INTEGER PRIMARY KEY,
            programa_id INTEGER NOT NULL,
            posicion INTEGER NOT NULL DEFAULT 0,
            descripcion TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_programa_pasos_programa_id ON programa_pasos(programa_id)"
    )


def _migrate_orden_paso_estado(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orden_paso_estado (
            id INTEGER PRIMARY KEY,
            orden_id INTEGER NOT NULL,
            paso_id INTEGER NOT NULL,
            completado INTEGER NOT NULL DEFAULT 0,
            tecnico_id INTEGER,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (orden_id, paso_id),
            FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
            FOREIGN KEY (paso_id) REFERENCES programa_pasos(id),
            FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_orden_paso_estado_orden_id"
        " ON orden_paso_estado(orden_id)"
    )


def _migrate_orden_colaboradores(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orden_colaboradores (
            id INTEGER PRIMARY KEY,
            orden_id INTEGER NOT NULL,
            tecnico_id INTEGER NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (orden_id, tecnico_id),
            FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
            FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_orden_colaboradores_orden_id"
        " ON orden_colaboradores(orden_id)"
    )


def _migrate_orden_programas(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orden_programas (
            id INTEGER PRIMARY KEY,
            orden_id INTEGER NOT NULL,
            programa_id INTEGER NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (orden_id, programa_id),
            FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
            FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_orden_programas_orden_id ON orden_programas(orden_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_orden_programas_programa_id"
        " ON orden_programas(programa_id)"
    )


def _migrate_programa_adjuntos(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS programa_adjuntos (
            id INTEGER PRIMARY KEY,
            programa_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('FOTO', 'PDF')),
            nombre TEXT NOT NULL DEFAULT '',
            ruta TEXT NOT NULL DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (programa_id) REFERENCES programas_mantenimiento(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_programa_adjuntos_programa_id"
        " ON programa_adjuntos(programa_id)"
    )


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None
