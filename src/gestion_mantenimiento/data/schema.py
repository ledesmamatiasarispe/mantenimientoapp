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
    horas_trabajo_activo INTEGER NOT NULL DEFAULT 0,
    horas_trabajo_actual REAL NOT NULL DEFAULT 0,
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
    es_admin INTEGER NOT NULL DEFAULT 0,
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
    horas_trabajo REAL,
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

CREATE TABLE IF NOT EXISTS medidores (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    nro_medidor TEXT NOT NULL DEFAULT '',
    nro_cliente TEXT NOT NULL DEFAULT '',
    descripcion TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facturas_electricas (
    id INTEGER PRIMARY KEY,
    medidor_id INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    tipo_tarifa TEXT NOT NULL DEFAULT 'T3'
        CHECK (tipo_tarifa IN ('T1', 'T2', 'T3')),
    nro_lsp TEXT NOT NULL DEFAULT '',
    fecha_factura TEXT NOT NULL DEFAULT '',
    fecha_vto1 TEXT NOT NULL DEFAULT '',
    fecha_vto2 TEXT NOT NULL DEFAULT '',
    cap_convenida_kw REAL NOT NULL DEFAULT 0,
    cap_adquirida_kw REAL NOT NULL DEFAULT 0,
    tangente_fi REAL NOT NULL DEFAULT 0,
    kwh_punta REAL NOT NULL DEFAULT 0,
    kwh_valle_noc REAL NOT NULL DEFAULT 0,
    kwh_restantes REAL NOT NULL DEFAULT 0,
    kvar_reactiva REAL NOT NULL DEFAULT 0,
    drp_kw REAL NOT NULL DEFAULT 0,
    drfp_kw REAL NOT NULL DEFAULT 0,
    cargo_fijo REAL NOT NULL DEFAULT 0,
    importe_cap_convenida REAL NOT NULL DEFAULT 0,
    importe_cap_adquirida REAL NOT NULL DEFAULT 0,
    importe_kwh_punta REAL NOT NULL DEFAULT 0,
    importe_kwh_valle_noc REAL NOT NULL DEFAULT 0,
    importe_kwh_restantes REAL NOT NULL DEFAULT 0,
    recargo_reactiva REAL NOT NULL DEFAULT 0,
    ley_7290 REAL NOT NULL DEFAULT 0,
    iva_27 REAL NOT NULL DEFAULT 0,
    contrib_art34 REAL NOT NULL DEFAULT 0,
    contrib_provincial REAL NOT NULL DEFAULT 0,
    percep_iva REAL NOT NULL DEFAULT 0,
    cestab REAL NOT NULL DEFAULT 0,
    tasa_mun_ap REAL NOT NULL DEFAULT 0,
    bonificaciones REAL NOT NULL DEFAULT 0,
    acpot REAL NOT NULL DEFAULT 0,
    iva_otros REAL NOT NULL DEFAULT 0,
    importe REAL NOT NULL DEFAULT 0,
    observaciones TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (medidor_id, periodo),
    FOREIGN KEY (medidor_id) REFERENCES medidores(id)
);

CREATE INDEX IF NOT EXISTS idx_facturas_electricas_medidor ON facturas_electricas(medidor_id);
CREATE INDEX IF NOT EXISTS idx_facturas_electricas_periodo ON facturas_electricas(periodo);
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
        _migrate_tecnicos_es_admin(connection)
        _migrate_orden_colaboradores(connection)
        _migrate_orden_programas(connection)
        _migrate_programa_adjuntos(connection)
        _migrate_orden_adjuntos(connection)
        _migrate_programa_pasos(connection)
        _migrate_programa_pasos_observaciones(connection)
        _migrate_programa_pasos_adjunto(connection)
        _migrate_orden_paso_estado(connection)
        _migrate_medidores(connection)
        _migrate_facturas_electricas(connection)
        _migrate_facturas_electricas_v2(connection)
        _migrate_equipos_horas_trabajo(connection)
        _migrate_ordenes_horas_trabajo(connection)
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


def _migrate_tecnicos_es_admin(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "tecnicos"):
        return
    if "es_admin" not in _table_columns(connection, "tecnicos"):
        connection.execute(
            "ALTER TABLE tecnicos ADD COLUMN es_admin INTEGER NOT NULL DEFAULT 0"
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


def _migrate_programa_pasos_observaciones(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "programa_pasos"):
        return
    if "observaciones" not in _table_columns(connection, "programa_pasos"):
        connection.execute(
            "ALTER TABLE programa_pasos ADD COLUMN observaciones TEXT NOT NULL DEFAULT ''"
        )


def _migrate_programa_pasos_adjunto(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "programa_pasos"):
        return
    cols = _table_columns(connection, "programa_pasos")
    if "adjunto_nombre" not in cols:
        connection.execute(
            "ALTER TABLE programa_pasos ADD COLUMN adjunto_nombre TEXT NOT NULL DEFAULT ''"
        )
    if "adjunto_ruta" not in cols:
        connection.execute(
            "ALTER TABLE programa_pasos ADD COLUMN adjunto_ruta TEXT NOT NULL DEFAULT ''"
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


def _migrate_medidores(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS medidores (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            nro_medidor TEXT NOT NULL DEFAULT '',
            nro_cliente TEXT NOT NULL DEFAULT '',
            descripcion TEXT NOT NULL DEFAULT '',
            activo INTEGER NOT NULL DEFAULT 1,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Agregar columnas a DBs anteriores
    if _table_exists(connection, "medidores"):
        cols = _table_columns(connection, "medidores")
        for col, defn in [("nro_medidor", "TEXT NOT NULL DEFAULT ''"),
                          ("nro_cliente",  "TEXT NOT NULL DEFAULT ''")]:
            if col not in cols:
                connection.execute(
                    f"ALTER TABLE medidores ADD COLUMN {col} {defn}"
                )


def _migrate_facturas_electricas(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS facturas_electricas (
            id INTEGER PRIMARY KEY,
            medidor_id INTEGER NOT NULL,
            periodo TEXT NOT NULL,
            tipo_tarifa TEXT NOT NULL DEFAULT 'T3'
                CHECK (tipo_tarifa IN ('T1', 'T2', 'T3')),
            nro_lsp TEXT NOT NULL DEFAULT '',
            fecha_factura TEXT NOT NULL DEFAULT '',
            fecha_vto1 TEXT NOT NULL DEFAULT '',
            fecha_vto2 TEXT NOT NULL DEFAULT '',
            cap_convenida_kw REAL NOT NULL DEFAULT 0,
            cap_adquirida_kw REAL NOT NULL DEFAULT 0,
            tangente_fi REAL NOT NULL DEFAULT 0,
            kwh_punta REAL NOT NULL DEFAULT 0,
            kwh_valle_noc REAL NOT NULL DEFAULT 0,
            kwh_restantes REAL NOT NULL DEFAULT 0,
            kvar_reactiva REAL NOT NULL DEFAULT 0,
            drp_kw REAL NOT NULL DEFAULT 0,
            drfp_kw REAL NOT NULL DEFAULT 0,
            cargo_fijo REAL NOT NULL DEFAULT 0,
            importe_cap_convenida REAL NOT NULL DEFAULT 0,
            importe_cap_adquirida REAL NOT NULL DEFAULT 0,
            importe_kwh_punta REAL NOT NULL DEFAULT 0,
            importe_kwh_valle_noc REAL NOT NULL DEFAULT 0,
            importe_kwh_restantes REAL NOT NULL DEFAULT 0,
            recargo_reactiva REAL NOT NULL DEFAULT 0,
            ley_7290 REAL NOT NULL DEFAULT 0,
            iva_27 REAL NOT NULL DEFAULT 0,
            contrib_art34 REAL NOT NULL DEFAULT 0,
            contrib_provincial REAL NOT NULL DEFAULT 0,
            percep_iva REAL NOT NULL DEFAULT 0,
            cestab REAL NOT NULL DEFAULT 0,
            tasa_mun_ap REAL NOT NULL DEFAULT 0,
            bonificaciones REAL NOT NULL DEFAULT 0,
            acpot REAL NOT NULL DEFAULT 0,
            iva_otros REAL NOT NULL DEFAULT 0,
            importe REAL NOT NULL DEFAULT 0,
            observaciones TEXT NOT NULL DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (medidor_id, periodo),
            FOREIGN KEY (medidor_id) REFERENCES medidores(id)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_facturas_electricas_medidor"
        " ON facturas_electricas(medidor_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_facturas_electricas_periodo"
        " ON facturas_electricas(periodo)"
    )


def _migrate_facturas_electricas_v2(connection: sqlite3.Connection) -> None:
    """Migra tablas de facturas creadas con schemas anteriores al schema EDESUR completo."""
    if not _table_exists(connection, "facturas_electricas"):
        return
    cols = _table_columns(connection, "facturas_electricas")
    nuevas = [
        ("tipo_tarifa",           "TEXT NOT NULL DEFAULT 'T3'"),
        ("nro_lsp",               "TEXT NOT NULL DEFAULT ''"),
        ("fecha_vto1",            "TEXT NOT NULL DEFAULT ''"),
        ("fecha_vto2",            "TEXT NOT NULL DEFAULT ''"),
        ("cap_convenida_kw",      "REAL NOT NULL DEFAULT 0"),
        ("cap_adquirida_kw",      "REAL NOT NULL DEFAULT 0"),
        ("tangente_fi",           "REAL NOT NULL DEFAULT 0"),
        ("kwh_punta",             "REAL NOT NULL DEFAULT 0"),
        ("kwh_valle_noc",         "REAL NOT NULL DEFAULT 0"),
        ("kwh_restantes",         "REAL NOT NULL DEFAULT 0"),
        ("kvar_reactiva",         "REAL NOT NULL DEFAULT 0"),
        ("drp_kw",                "REAL NOT NULL DEFAULT 0"),
        ("drfp_kw",               "REAL NOT NULL DEFAULT 0"),
        ("cargo_fijo",            "REAL NOT NULL DEFAULT 0"),
        ("importe_cap_convenida", "REAL NOT NULL DEFAULT 0"),
        ("importe_cap_adquirida", "REAL NOT NULL DEFAULT 0"),
        ("importe_kwh_punta",     "REAL NOT NULL DEFAULT 0"),
        ("importe_kwh_valle_noc", "REAL NOT NULL DEFAULT 0"),
        ("importe_kwh_restantes", "REAL NOT NULL DEFAULT 0"),
        ("recargo_reactiva",      "REAL NOT NULL DEFAULT 0"),
        ("ley_7290",              "REAL NOT NULL DEFAULT 0"),
        ("iva_27",                "REAL NOT NULL DEFAULT 0"),
        ("contrib_art34",         "REAL NOT NULL DEFAULT 0"),
        ("contrib_provincial",    "REAL NOT NULL DEFAULT 0"),
        ("percep_iva",            "REAL NOT NULL DEFAULT 0"),
        ("cestab",                "REAL NOT NULL DEFAULT 0"),
        ("tasa_mun_ap",           "REAL NOT NULL DEFAULT 0"),
        ("bonificaciones",        "REAL NOT NULL DEFAULT 0"),
        ("acpot",                 "REAL NOT NULL DEFAULT 0"),
        ("iva_otros",             "REAL NOT NULL DEFAULT 0"),
    ]
    for col, defn in nuevas:
        if col not in cols:
            connection.execute(
                f"ALTER TABLE facturas_electricas ADD COLUMN {col} {defn}"
            )


def _migrate_equipos_horas_trabajo(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "equipos"):
        return
    cols = _table_columns(connection, "equipos")
    if "horas_trabajo_activo" not in cols:
        connection.execute(
            "ALTER TABLE equipos ADD COLUMN horas_trabajo_activo INTEGER NOT NULL DEFAULT 0"
        )
    if "horas_trabajo_actual" not in cols:
        connection.execute(
            "ALTER TABLE equipos ADD COLUMN horas_trabajo_actual REAL NOT NULL DEFAULT 0"
        )


def _migrate_ordenes_horas_trabajo(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "ordenes_trabajo"):
        return
    if "horas_trabajo" not in _table_columns(connection, "ordenes_trabajo"):
        connection.execute(
            "ALTER TABLE ordenes_trabajo ADD COLUMN horas_trabajo REAL"
        )


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None
