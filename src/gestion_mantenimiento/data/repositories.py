from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

from gestion_mantenimiento.data.models import (
    Alerta,
    AppAlert,
    Equipo,
    OrdenPrograma,
    OrdenTrabajo,
    OrdenTrabajoCreate,
    ProgramaAdjunto,
    ProgramaMantenimiento,
    Repuesto,
    RepuestoOrden,
    Tecnico,
    TipoEquipo,
)


class RepuestoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_all(self, search: str = "", *, solo_activos: bool = False) -> list[Repuesto]:
        query = """
            SELECT id, nombre, COALESCE(observaciones, ''), stock_actual, stock_minimo, activo
            FROM repuestos
        """
        conditions: list[str] = []
        params: list[object] = []
        if solo_activos:
            conditions.append("activo = 1")
        if search.strip():
            term = f"%{search.strip()}%"
            conditions.append("(nombre LIKE ? OR observaciones LIKE ?)")
            params.extend([term, term])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY nombre"
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            Repuesto(
                id=r[0], nombre=r[1], observaciones=r[2],
                stock_actual=float(r[3]), stock_minimo=float(r[4]), activo=bool(r[5]),
            )
            for r in rows
        ]

    def get_by_id(self, repuesto_id: int) -> Repuesto | None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(
                "SELECT id, nombre, COALESCE(observaciones,''), stock_actual, stock_minimo, activo"
                " FROM repuestos WHERE id = ?",
                (repuesto_id,),
            ).fetchone()
        if row is None:
            return None
        return Repuesto(
            id=row[0], nombre=row[1], observaciones=row[2],
            stock_actual=float(row[3]), stock_minimo=float(row[4]), activo=bool(row[5]),
        )

    def create(
        self, nombre: str, observaciones: str, stock_actual: float, stock_minimo: float
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                "INSERT INTO repuestos (nombre, observaciones, stock_actual, stock_minimo)"
                " VALUES (?, ?, ?, ?)",
                (nombre.strip(), observaciones.strip(), stock_actual, stock_minimo),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        repuesto_id: int,
        nombre: str,
        observaciones: str,
        stock_actual: float,
        stock_minimo: float,
        activo: bool,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE repuestos SET
                    nombre = ?, observaciones = ?, stock_actual = ?, stock_minimo = ?,
                    activo = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (nombre.strip(), observaciones.strip(), stock_actual, stock_minimo,
                 int(activo), repuesto_id),
            )
            conn.commit()

    def delete(self, repuesto_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM repuestos WHERE id = ?", (repuesto_id,))
            conn.commit()

    def ajustar_stock(self, repuesto_id: int, delta: float) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                "UPDATE repuestos SET stock_actual = stock_actual + ?,"
                " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                (delta, repuesto_id),
            )
            conn.commit()


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
            SELECT id, nombre, apellido, COALESCE(legajo, ''), COALESCE(telefono, ''),
                   COALESCE(especialidad, ''), activo, COALESCE(es_admin, 0)
            FROM tecnicos
        """
        conditions: list[str] = []
        params: list[object] = []

        if solo_activos:
            conditions.append("activo = 1")

        if search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                "(nombre LIKE ? OR apellido LIKE ? OR legajo LIKE ? OR especialidad LIKE ?)"
            )
            params.extend([term, term, term, term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY apellido, nombre"

        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Tecnico(
                id=r[0], nombre=r[1], apellido=r[2], legajo=r[3],
                telefono=r[4], especialidad=r[5], activo=bool(r[6]), es_admin=bool(r[7]),
            )
            for r in rows
        ]

    def create(
        self, nombre: str, apellido: str, legajo: str, telefono: str, especialidad: str,
        *, es_admin: bool = False,
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO tecnicos (nombre, apellido, legajo, telefono, especialidad, es_admin)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nombre.strip(), apellido.strip(), legajo.strip(),
                 telefono.strip(), especialidad.strip(), int(es_admin)),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        tecnico_id: int,
        nombre: str,
        apellido: str,
        legajo: str,
        telefono: str,
        especialidad: str,
        activo: bool,
        *,
        es_admin: bool = False,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE tecnicos SET
                    nombre = ?, apellido = ?, legajo = ?, telefono = ?,
                    especialidad = ?, activo = ?, es_admin = ?
                WHERE id = ?
                """,
                (
                    nombre.strip(), apellido.strip(), legajo.strip(),
                    telefono.strip(), especialidad.strip(), int(activo), int(es_admin), tecnico_id,
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
            rows = conn.execute(
                "SELECT repuesto_id, cantidad FROM repuestos_orden WHERE orden_id = ?",
                (orden_id,),
            ).fetchall()
            for repuesto_id, cantidad in rows:
                if repuesto_id is not None:
                    conn.execute(
                        "UPDATE repuestos SET stock_actual = stock_actual + ?,"
                        " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                        (cantidad, repuesto_id),
                    )
            conn.execute("DELETE FROM repuestos_orden WHERE orden_id = ?", (orden_id,))
            conn.execute("DELETE FROM orden_colaboradores WHERE orden_id = ?", (orden_id,))
            conn.execute("DELETE FROM orden_programas WHERE orden_id = ?", (orden_id,))
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
                SELECT
                    ro.id, ro.orden_id, ro.repuesto_id,
                    COALESCE(r.nombre, ro.descripcion) AS descripcion,
                    ro.cantidad, ro.costo_unitario
                FROM repuestos_orden ro
                LEFT JOIN repuestos r ON r.id = ro.repuesto_id
                WHERE ro.orden_id = ?
                ORDER BY ro.id
                """,
                (orden_id,),
            ).fetchall()
        return [
            RepuestoOrden(
                id=r[0], orden_id=r[1], repuesto_id=r[2], descripcion=r[3],
                cantidad=float(r[4]), costo_unitario=float(r[5]),
            )
            for r in rows
        ]

    def create(
        self,
        orden_id: int,
        repuesto_id: int,
        descripcion: str,
        cantidad: float,
        costo_unitario: float,
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO repuestos_orden
                    (orden_id, repuesto_id, descripcion, cantidad, costo_unitario)
                VALUES (?, ?, ?, ?, ?)
                """,
                (orden_id, repuesto_id, descripcion.strip(), cantidad, costo_unitario),
            )
            # Deduct from stock
            conn.execute(
                "UPDATE repuestos SET stock_actual = stock_actual - ?,"
                " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                (cantidad, repuesto_id),
            )
            conn.commit()
            return cur.lastrowid or 0

    def delete(self, rep_orden_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(
                "SELECT repuesto_id, cantidad FROM repuestos_orden WHERE id = ?",
                (rep_orden_id,),
            ).fetchone()
            conn.execute("DELETE FROM repuestos_orden WHERE id = ?", (rep_orden_id,))
            # Restore stock
            if row and row[0] is not None:
                conn.execute(
                    "UPDATE repuestos SET stock_actual = stock_actual + ?,"
                    " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                    (row[1], row[0]),
                )
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
                p.frecuencia_meses,
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
                frecuencia_meses=r[4], ultima_ejecucion=r[5], proxima_ejecucion=r[6],
                activo=bool(r[7]),
            )
            for r in rows
        ]

    def create(
        self,
        equipo_id: int,
        descripcion: str,
        frecuencia_meses: int,
        ultima_ejecucion: str,
        proxima_ejecucion: str,
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                """
                INSERT INTO programas_mantenimiento
                    (equipo_id, descripcion, frecuencia_meses,
                     ultima_ejecucion, proxima_ejecucion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (equipo_id, descripcion.strip(), frecuencia_meses,
                 ultima_ejecucion, proxima_ejecucion),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        programa_id: int,
        equipo_id: int,
        descripcion: str,
        frecuencia_meses: int,
        ultima_ejecucion: str,
        proxima_ejecucion: str,
        activo: bool,
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE programas_mantenimiento SET
                    equipo_id = ?, descripcion = ?, frecuencia_meses = ?,
                    ultima_ejecucion = ?, proxima_ejecucion = ?, activo = ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    equipo_id, descripcion.strip(), frecuencia_meses,
                    ultima_ejecucion, proxima_ejecucion, int(activo), programa_id,
                ),
            )
            conn.commit()

    def advance_proxima(self, programa_id: int, desde: str, frecuencia_meses: int) -> str:
        """Avanza proxima_ejecucion en frecuencia_meses meses y devuelve la nueva fecha."""
        try:
            d = date.fromisoformat(desde)
        except ValueError:
            return desde
        # Calcular nueva fecha respetando fin de mes
        new_month = d.month + frecuencia_meses
        new_year  = d.year + (new_month - 1) // 12
        new_month = ((new_month - 1) % 12) + 1
        # Preservar día o truncar al fin del mes destino
        import calendar
        last_day = calendar.monthrange(new_year, new_month)[1]
        nueva = d.replace(year=new_year, month=new_month, day=min(d.day, last_day))
        nueva_str = nueva.isoformat()
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                UPDATE programas_mantenimiento
                SET proxima_ejecucion = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (nueva_str, programa_id),
            )
            conn.commit()
        return nueva_str

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


class OrdenProgramaRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_by_orden(self, orden_id: int) -> list[OrdenPrograma]:
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(
                """
                SELECT op.id, op.orden_id, op.programa_id,
                       COALESCE(p.descripcion, '') AS descripcion
                FROM orden_programas op
                LEFT JOIN programas_mantenimiento p ON p.id = op.programa_id
                WHERE op.orden_id = ?
                ORDER BY op.id
                """,
                (orden_id,),
            ).fetchall()
        return [
            OrdenPrograma(id=r[0], orden_id=r[1], programa_id=r[2], programa_descripcion=r[3])
            for r in rows
        ]

    def link(self, orden_id: int, programa_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO orden_programas (orden_id, programa_id) VALUES (?, ?)",
                (orden_id, programa_id),
            )
            conn.commit()

    def find_orden_pendiente(self, equipo_id: int, programa_ids: list[int]) -> int | None:
        """Devuelve el id de una orden PENDIENTE/EN_PROGRESO ya vinculada a alguno de esos programas."""
        if not programa_ids:
            return None
        placeholders = ",".join("?" * len(programa_ids))
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(
                f"""
                SELECT o.id
                FROM ordenes_trabajo o
                JOIN orden_programas op ON op.orden_id = o.id
                WHERE o.equipo_id = ?
                  AND o.estado IN ('PENDIENTE', 'EN_PROGRESO')
                  AND op.programa_id IN ({placeholders})
                LIMIT 1
                """,
                (equipo_id, *programa_ids),
            ).fetchone()
        return row[0] if row else None

    def find_orden_completada_desde(
        self, equipo_id: int, programa_ids: list[int], desde: str
    ) -> int | None:
        """Devuelve el id de una orden COMPLETADA vinculada al programa con fecha_cierre >= desde."""
        if not programa_ids:
            return None
        placeholders = ",".join("?" * len(programa_ids))
        with closing(sqlite3.connect(self.database_path)) as conn:
            row = conn.execute(
                f"""
                SELECT o.id
                FROM ordenes_trabajo o
                JOIN orden_programas op ON op.orden_id = o.id
                WHERE o.equipo_id = ?
                  AND o.estado = 'COMPLETADA'
                  AND o.fecha_cierre >= ?
                  AND op.programa_id IN ({placeholders})
                LIMIT 1
                """,
                (equipo_id, desde, *programa_ids),
            ).fetchone()
        return row[0] if row else None


class AdjuntoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_by_programa(self, programa_id: int) -> list[ProgramaAdjunto]:
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(
                """
                SELECT id, programa_id, tipo, nombre, ruta
                FROM programa_adjuntos
                WHERE programa_id = ?
                ORDER BY tipo, nombre
                """,
                (programa_id,),
            ).fetchall()
        return [
            ProgramaAdjunto(id=r[0], programa_id=r[1], tipo=r[2], nombre=r[3], ruta=r[4])
            for r in rows
        ]

    def create(self, programa_id: int, tipo: str, nombre: str, ruta: str) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                "INSERT INTO programa_adjuntos (programa_id, tipo, nombre, ruta)"
                " VALUES (?, ?, ?, ?)",
                (programa_id, tipo, nombre, ruta),
            )
            conn.commit()
            return cur.lastrowid or 0

    def delete(self, adjunto_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM programa_adjuntos WHERE id = ?", (adjunto_id,))
            conn.commit()


class AlertaRepository:
    """Computa alertas activas y gestiona snooze/ignorar en alertas_app."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def compute(self) -> list[Alerta]:
        hoy = date.today().isoformat()
        alertas: list[Alerta] = []

        with closing(sqlite3.connect(self.database_path)) as conn:
            # Keys actualmente en snooze (no mostrar)
            snoozed = {
                row[0]
                for row in conn.execute(
                    "SELECT clave FROM alertas_app WHERE avisar_nuevamente_desde > ?",
                    (hoy,),
                ).fetchall()
            }

            # ── Repuestos en stock mínimo o por debajo ─────────────────────
            for r in conn.execute(
                "SELECT id, nombre, stock_actual, stock_minimo"
                " FROM repuestos WHERE stock_actual <= stock_minimo AND activo = 1"
            ).fetchall():
                key = f"stock_bajo_{r[0]}"
                if key not in snoozed:
                    alertas.append(Alerta(
                        key=key, tipo="STOCK_BAJO",
                        titulo=f"Stock bajo: {r[1]}",
                        mensaje=f"Actual {r[2]:g} ≤ mínimo {r[3]:g}",
                        entidad_id=r[0],
                    ))

            # ── Órdenes de trabajo pendientes ──────────────────────────────
            for r in conn.execute(
                """
                SELECT o.id, e.nombre, COALESCE(o.descripcion,''), o.fecha_apertura
                FROM ordenes_trabajo o
                JOIN equipos e ON e.id = o.equipo_id
                WHERE o.estado = 'PENDIENTE'
                ORDER BY o.id DESC
                """
            ).fetchall():
                key = f"orden_nueva_{r[0]}"
                if key not in snoozed:
                    desc = r[2][:60] + ("…" if len(r[2]) > 60 else "")
                    alertas.append(Alerta(
                        key=key, tipo="ORDEN_NUEVA",
                        titulo=f"Orden pendiente — {r[1]}",
                        mensaje=f"#{r[0]}  {desc}  ({r[3]})",
                        entidad_id=r[0],
                    ))

            # ── Mantenimientos vencidos ────────────────────────────────────
            for r in conn.execute(
                """
                SELECT p.id, e.nombre, p.descripcion, p.proxima_ejecucion
                FROM programas_mantenimiento p
                JOIN equipos e ON e.id = p.equipo_id
                WHERE p.proxima_ejecucion < ? AND p.proxima_ejecucion != '' AND p.activo = 1
                ORDER BY p.proxima_ejecucion
                """,
                (hoy,),
            ).fetchall():
                key = f"mant_vencido_{r[0]}"
                if key not in snoozed:
                    alertas.append(Alerta(
                        key=key, tipo="MANT_VENCIDO",
                        titulo=f"Mantenimiento vencido — {r[1]}",
                        mensaje=f"{r[2]}  (venció el {r[3]})",
                        entidad_id=r[0],
                    ))

        return alertas

    def snooze(self, key: str, dias: int = 7) -> None:
        hasta = (date.today() + timedelta(days=dias)).isoformat()
        self._upsert(key, hasta)

    def ignorar(self, key: str) -> None:
        self._upsert(key, "9999-12-31")

    def _upsert(self, key: str, hasta: str) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """
                INSERT INTO alertas_app (clave, avisar_nuevamente_desde)
                VALUES (?, ?)
                ON CONFLICT(clave) DO UPDATE SET
                    avisar_nuevamente_desde = excluded.avisar_nuevamente_desde,
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (key, hasta),
            )
            conn.commit()


class PasoRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def list_for_programa(
        self, programa_id: int
    ) -> list[tuple[int, int, str, bool, str, str, str]]:
        """Returns list of (id, posicion, descripcion, activo, observaciones, adjunto_nombre, adjunto_ruta)."""
        with closing(sqlite3.connect(self.database_path)) as conn:
            rows = conn.execute(
                """
                SELECT id, posicion, descripcion, activo,
                       COALESCE(observaciones,'') AS observaciones,
                       COALESCE(adjunto_nombre,'') AS adjunto_nombre,
                       COALESCE(adjunto_ruta,'') AS adjunto_ruta
                FROM programa_pasos
                WHERE programa_id = ?
                ORDER BY posicion, id
                """,
                (programa_id,),
            ).fetchall()
        return [
            (int(r[0]), int(r[1]), str(r[2]), bool(r[3]), str(r[4]), str(r[5]), str(r[6]))
            for r in rows
        ]

    def create(
        self, programa_id: int, descripcion: str, posicion: int, observaciones: str = ""
    ) -> int:
        with closing(sqlite3.connect(self.database_path)) as conn:
            cur = conn.execute(
                "INSERT INTO programa_pasos (programa_id, descripcion, posicion, observaciones) VALUES (?, ?, ?, ?)",
                (programa_id, descripcion.strip(), posicion, observaciones),
            )
            conn.commit()
            return cur.lastrowid or 0

    def update(
        self,
        paso_id: int,
        descripcion: str,
        posicion: int,
        observaciones: str = "",
        adjunto_nombre: str = "",
        adjunto_ruta: str = "",
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute(
                """UPDATE programa_pasos
                   SET descripcion=?, posicion=?, observaciones=?,
                       adjunto_nombre=?, adjunto_ruta=?
                   WHERE id=?""",
                (descripcion.strip(), posicion, observaciones,
                 adjunto_nombre, adjunto_ruta, paso_id),
            )
            conn.commit()

    def delete(self, paso_id: int) -> None:
        with closing(sqlite3.connect(self.database_path)) as conn:
            conn.execute("DELETE FROM programa_pasos WHERE id = ?", (paso_id,))
            conn.commit()
