from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from gestion_mantenimiento.data.models import (
    AppAlert,
    Equipo,
    OrdenTrabajo,
    OrdenTrabajoCreate,
    ProgramaMantenimiento,
    RepuestoOrden,
    Tecnico,
    TipoEquipo,
)


class TipoEquipoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, *, solo_activos: bool = True) -> list[TipoEquipo]:
        query = "SELECT id, nombre, activo FROM tipos_equipo"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre"
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query).fetchall()
        return [TipoEquipo(id=r[0], nombre=r[1], activo=bool(r[2])) for r in rows]

    def create(self, nombre: str) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                "INSERT INTO tipos_equipo (nombre) VALUES (?)", (nombre.strip(),)
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(self, tipo_id: int, nombre: str, activo: bool) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                "UPDATE tipos_equipo SET nombre = ?, activo = ? WHERE id = ?",
                (nombre.strip(), int(activo), tipo_id),
            )
            conn.commit()

    def delete(self, tipo_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM tipos_equipo WHERE id = ?", (tipo_id,))
            conn.commit()


class EquipoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, search: str = "", *, solo_activos: bool = False) -> list[Equipo]:
        query = """
            SELECT
                e.id,
                e.nombre,
                e.tipo_id,
                COALESCE(t.nombre, '') AS tipo_nombre,
                COALESCE(e.numero_serie, '') AS numero_serie,
                COALESCE(e.marca, '') AS marca,
                COALESCE(e.modelo, '') AS modelo,
                COALESCE(e.ubicacion, '') AS ubicacion,
                COALESCE(e.fecha_adquisicion, '') AS fecha_adquisicion,
                COALESCE(e.observaciones, '') AS observaciones,
                e.activo
            FROM equipos e
            LEFT JOIN tipos_equipo t ON t.id = e.tipo_id
        """
        conditions: list[str] = []
        params: list[object] = []

        if solo_activos:
            conditions.append("e.activo = 1")

        if search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                "(e.nombre LIKE ? OR e.marca LIKE ? OR e.modelo LIKE ?"
                " OR e.numero_serie LIKE ? OR e.ubicacion LIKE ?)"
            )
            params.extend([term, term, term, term, term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY e.nombre"

        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Equipo(
                id=r[0],
                nombre=r[1],
                tipo_id=r[2],
                tipo_nombre=r[3],
                numero_serie=r[4],
                marca=r[5],
                modelo=r[6],
                ubicacion=r[7],
                fecha_adquisicion=r[8],
                observaciones=r[9],
                activo=bool(r[10]),
            )
            for r in rows
        ]

    def get_by_id(self, equipo_id: int) -> Equipo | None:
        results = self._fetch_by_id(equipo_id)
        return results[0] if results else None

    def _fetch_by_id(self, equipo_id: int) -> list[Equipo]:
        query = """
            SELECT
                e.id, e.nombre, e.tipo_id, COALESCE(t.nombre, '') AS tipo_nombre,
                COALESCE(e.numero_serie, ''), COALESCE(e.marca, ''),
                COALESCE(e.modelo, ''), COALESCE(e.ubicacion, ''),
                COALESCE(e.fecha_adquisicion, ''), COALESCE(e.observaciones, ''), e.activo
            FROM equipos e
            LEFT JOIN tipos_equipo t ON t.id = e.tipo_id
            WHERE e.id = ?
        """
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, (equipo_id,)).fetchall()
        return [
            Equipo(
                id=r[0], nombre=r[1], tipo_id=r[2], tipo_nombre=r[3],
                numero_serie=r[4], marca=r[5], modelo=r[6], ubicacion=r[7],
                fecha_adquisicion=r[8], observaciones=r[9], activo=bool(r[10]),
            )
            for r in rows
        ]

    def create(
        self,
        nombre: str,
        tipo_id: int | None,
        numero_serie: str,
        marca: str,
        modelo: str,
        ubicacion: str,
        fecha_adquisicion: str,
        observaciones: str,
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO equipos
                    (nombre, tipo_id, numero_serie, marca, modelo,
                     ubicacion, fecha_adquisicion, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    nombre.strip(), tipo_id, numero_serie.strip(), marca.strip(),
                    modelo.strip(), ubicacion.strip(), fecha_adquisicion, observaciones.strip(),
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        equipo_id: int,
        nombre: str,
        tipo_id: int | None,
        numero_serie: str,
        marca: str,
        modelo: str,
        ubicacion: str,
        fecha_adquisicion: str,
        observaciones: str,
        activo: bool,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE equipos SET
                    nombre = ?, tipo_id = ?, numero_serie = ?, marca = ?, modelo = ?,
                    ubicacion = ?, fecha_adquisicion = ?, observaciones = ?, activo = ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    nombre.strip(), tipo_id, numero_serie.strip(), marca.strip(),
                    modelo.strip(), ubicacion.strip(), fecha_adquisicion,
                    observaciones.strip(), int(activo), equipo_id,
                ),
            )
            conn.commit()

    def delete(self, equipo_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,))
            conn.commit()


class TecnicoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, search: str = "", *, solo_activos: bool = False) -> list[Tecnico]:
        query = """
            SELECT id, nombre, apellido, COALESCE(dni, ''), COALESCE(telefono, ''),
                   COALESCE(especialidad, ''), activo
            FROM tecnicos
        """
        conditions: list[str] = []
        params: list[object] = []

        if solo_activos:
            conditions.append("activo = 1")

        if search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                "(nombre LIKE ? OR apellido LIKE ? OR dni LIKE ? OR especialidad LIKE ?)"
            )
            params.extend([term, term, term, term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY apellido, nombre"

        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Tecnico(
                id=r[0], nombre=r[1], apellido=r[2], dni=r[3],
                telefono=r[4], especialidad=r[5], activo=bool(r[6]),
            )
            for r in rows
        ]

    def create(
        self, nombre: str, apellido: str, dni: str, telefono: str, especialidad: str
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO tecnicos (nombre, apellido, dni, telefono, especialidad)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre.strip(), apellido.strip(), dni.strip(),
                 telefono.strip(), especialidad.strip()),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        tecnico_id: int,
        nombre: str,
        apellido: str,
        dni: str,
        telefono: str,
        especialidad: str,
        activo: bool,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE tecnicos SET
                    nombre = ?, apellido = ?, dni = ?, telefono = ?,
                    especialidad = ?, activo = ?
                WHERE id = ?
                """,
                (
                    nombre.strip(), apellido.strip(), dni.strip(),
                    telefono.strip(), especialidad.strip(), int(activo), tecnico_id,
                ),
            )
            conn.commit()

    def delete(self, tecnico_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM tecnicos WHERE id = ?", (tecnico_id,))
            conn.commit()


class OrdenTrabajoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, search: str = "", estado: str = "") -> list[OrdenTrabajo]:
        query = """
            SELECT
                o.id,
                o.equipo_id,
                e.nombre AS equipo_nombre,
                o.tipo,
                COALESCE(o.descripcion, '') AS descripcion,
                COALESCE(o.fecha_apertura, '') AS fecha_apertura,
                COALESCE(o.fecha_cierre, '') AS fecha_cierre,
                o.estado,
                o.tecnico_id,
                COALESCE(
                    trim(t.nombre || ' ' || t.apellido), ''
                ) AS tecnico_nombre,
                COALESCE(o.costo_mano_obra, 0) AS costo_mano_obra,
                COALESCE(
                    (
                        SELECT SUM(r.cantidad * r.costo_unitario)
                        FROM repuestos_orden r
                        WHERE r.orden_id = o.id
                    ), 0
                ) AS costo_repuestos,
                COALESCE(o.observaciones, '') AS observaciones
            FROM ordenes_trabajo o
            JOIN equipos e ON e.id = o.equipo_id
            LEFT JOIN tecnicos t ON t.id = o.tecnico_id
        """
        conditions: list[str] = []
        params: list[object] = []

        if estado.strip():
            conditions.append("o.estado = ?")
            params.append(estado.strip())

        if search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                "(e.nombre LIKE ? OR o.descripcion LIKE ? OR o.observaciones LIKE ?)"
            )
            params.extend([term, term, term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY o.fecha_apertura DESC, o.id DESC"

        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            OrdenTrabajo(
                id=r[0], equipo_id=r[1], equipo_nombre=r[2], tipo=r[3],
                descripcion=r[4], fecha_apertura=r[5], fecha_cierre=r[6],
                estado=r[7], tecnico_id=r[8], tecnico_nombre=r[9],
                costo_mano_obra=float(r[10]), costo_repuestos=float(r[11]),
                observaciones=r[12],
            )
            for r in rows
        ]

    def get_by_id(self, orden_id: int) -> OrdenTrabajo | None:
        query = """
            SELECT
                o.id, o.equipo_id, e.nombre,
                o.tipo, COALESCE(o.descripcion, ''), COALESCE(o.fecha_apertura, ''),
                COALESCE(o.fecha_cierre, ''), o.estado, o.tecnico_id,
                COALESCE(trim(t.nombre || ' ' || t.apellido), ''),
                COALESCE(o.costo_mano_obra, 0),
                COALESCE(
                    (SELECT SUM(r.cantidad * r.costo_unitario)
                     FROM repuestos_orden r WHERE r.orden_id = o.id), 0
                ),
                COALESCE(o.observaciones, '')
            FROM ordenes_trabajo o
            JOIN equipos e ON e.id = o.equipo_id
            LEFT JOIN tecnicos t ON t.id = o.tecnico_id
            WHERE o.id = ?
        """
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(query, (orden_id,)).fetchone()
        if row is None:
            return None
        return OrdenTrabajo(
            id=row[0], equipo_id=row[1], equipo_nombre=row[2], tipo=row[3],
            descripcion=row[4], fecha_apertura=row[5], fecha_cierre=row[6],
            estado=row[7], tecnico_id=row[8], tecnico_nombre=row[9],
            costo_mano_obra=float(row[10]), costo_repuestos=float(row[11]),
            observaciones=row[12],
        )

    def create(self, data: OrdenTrabajoCreate) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO ordenes_trabajo
                    (equipo_id, tipo, descripcion, fecha_apertura, fecha_cierre,
                     estado, tecnico_id, costo_mano_obra, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.equipo_id, data.tipo, data.descripcion,
                    data.fecha_apertura, data.fecha_cierre, data.estado,
                    data.tecnico_id, data.costo_mano_obra, data.observaciones,
                ),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(self, orden_id: int, data: OrdenTrabajoCreate) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE ordenes_trabajo SET
                    equipo_id = ?, tipo = ?, descripcion = ?, fecha_apertura = ?,
                    fecha_cierre = ?, estado = ?, tecnico_id = ?, costo_mano_obra = ?,
                    observaciones = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    data.equipo_id, data.tipo, data.descripcion,
                    data.fecha_apertura, data.fecha_cierre, data.estado,
                    data.tecnico_id, data.costo_mano_obra, data.observaciones,
                    orden_id,
                ),
            )
            conn.commit()

    def delete(self, orden_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM repuestos_orden WHERE orden_id = ?", (orden_id,))
            conn.execute("DELETE FROM ordenes_trabajo WHERE id = ?", (orden_id,))
            conn.commit()

    def count_by_estado(self) -> dict[str, int]:
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(
                "SELECT estado, COUNT(*) FROM ordenes_trabajo GROUP BY estado"
            ).fetchall()
        return {r[0]: r[1] for r in rows}


class RepuestoOrdenRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_by_orden(self, orden_id: int) -> list[RepuestoOrden]:
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(
                """
                SELECT id, orden_id, descripcion, cantidad, costo_unitario
                FROM repuestos_orden
                WHERE orden_id = ?
                ORDER BY id
                """,
                (orden_id,),
            ).fetchall()
        return [
            RepuestoOrden(
                id=r[0], orden_id=r[1], descripcion=r[2],
                cantidad=float(r[3]), costo_unitario=float(r[4]),
            )
            for r in rows
        ]

    def create(
        self, orden_id: int, descripcion: str, cantidad: float, costo_unitario: float
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO repuestos_orden (orden_id, descripcion, cantidad, costo_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (orden_id, descripcion.strip(), cantidad, costo_unitario),
            )
            conn.commit()
            return cur.lastrowid or 0

    def delete(self, repuesto_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM repuestos_orden WHERE id = ?", (repuesto_id,))
            conn.commit()


class ProgramaMantenimientoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, *, solo_activos: bool = False) -> list[ProgramaMantenimiento]:
        query = """
            SELECT
                p.id,
                p.equipo_id,
                e.nombre AS equipo_nombre,
                COALESCE(p.descripcion, '') AS descripcion,
                p.frecuencia_dias,
                COALESCE(p.ultima_ejecucion, '') AS ultima_ejecucion,
                COALESCE(p.proxima_ejecucion, '') AS proxima_ejecucion,
                p.activo
            FROM programas_mantenimiento p
            JOIN equipos e ON e.id = p.equipo_id
        """
        if solo_activos:
            query += " WHERE p.activo = 1"
        query += " ORDER BY p.proxima_ejecucion, e.nombre"

        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query).fetchall()

        return [
            ProgramaMantenimiento(
                id=r[0], equipo_id=r[1], equipo_nombre=r[2], descripcion=r[3],
                frecuencia_dias=r[4], ultima_ejecucion=r[5], proxima_ejecucion=r[6],
                activo=bool(r[7]),
            )
            for r in rows
        ]

    def create(
        self,
        equipo_id: int,
        descripcion: str,
        frecuencia_dias: int,
        ultima_ejecucion: str,
        proxima_ejecucion: str,
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO programas_mantenimiento
                    (equipo_id, descripcion, frecuencia_dias,
                     ultima_ejecucion, proxima_ejecucion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (equipo_id, descripcion.strip(), frecuencia_dias,
                 ultima_ejecucion, proxima_ejecucion),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        programa_id: int,
        equipo_id: int,
        descripcion: str,
        frecuencia_dias: int,
        ultima_ejecucion: str,
        proxima_ejecucion: str,
        activo: bool,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE programas_mantenimiento SET
                    equipo_id = ?, descripcion = ?, frecuencia_dias = ?,
                    ultima_ejecucion = ?, proxima_ejecucion = ?, activo = ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    equipo_id, descripcion.strip(), frecuencia_dias,
                    ultima_ejecucion, proxima_ejecucion, int(activo), programa_id,
                ),
            )
            conn.commit()

    def delete(self, programa_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                "DELETE FROM programas_mantenimiento WHERE id = ?", (programa_id,)
            )
            conn.commit()


class AlertRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def get_snooze_date(self, key: str) -> str:
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(
                "SELECT avisar_nuevamente_desde FROM alertas_app WHERE clave = ?",
                (key,),
            ).fetchone()
        return row[0] if row else ""

    def set_snooze_date(self, key: str, date_str: str) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                INSERT INTO alertas_app (clave, avisar_nuevamente_desde)
                VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET
                    avisar_nuevamente_desde = excluded.avisar_nuevamente_desde,
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (key, date_str),
            )
            conn.commit()
