from __future__ import annotations

import calendar
import sqlite3
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from api.auth import CurrentTecnicoDep
from api.database import get_db
from api.models import (
    CronogramaFila,
    EquipoCard,
    RepuestoDisponible,
)

router = APIRouter(tags=["biblioteca"])
ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


@router.get("/api/equipos", response_model=list[EquipoCard])
def list_equipos(_: CurrentTecnicoDep, connection: ConnectionDep) -> list[EquipoCard]:
    rows = connection.execute(
        """
        SELECT
            e.id,
            e.nombre,
            e.tipo_id,
            COALESCE(t.nombre, '') AS tipo_nombre,
            COALESCE(e.numero_serie, '') AS numero_serie,
            COALESCE(e.marca, '') AS marca,
            COALESCE(e.modelo, '') AS modelo,
            COALESCE(e.ubicacion, '') AS ubicacion,
            COALESCE(e.observaciones, '') AS observaciones,
            (
                SELECT COUNT(*)
                FROM programas_mantenimiento p
                WHERE p.equipo_id = e.id AND p.activo = 1
            ) AS programas_activos_count
        FROM equipos e
        LEFT JOIN tipos_equipo t ON t.id = e.tipo_id
        WHERE e.activo = 1
        ORDER BY e.nombre
        """
    ).fetchall()
    return [
        EquipoCard(
            id=int(row["id"]),
            nombre=str(row["nombre"] or ""),
            tipo_id=int(row["tipo_id"]) if row["tipo_id"] is not None else None,
            tipo_nombre=str(row["tipo_nombre"] or ""),
            numero_serie=str(row["numero_serie"] or ""),
            marca=str(row["marca"] or ""),
            modelo=str(row["modelo"] or ""),
            ubicacion=str(row["ubicacion"] or ""),
            observaciones=str(row["observaciones"] or ""),
            programas_activos_count=int(row["programas_activos_count"] or 0),
        )
        for row in rows
    ]


@router.get("/api/pasos/{paso_id}/adjunto")
def ver_adjunto_paso(paso_id: int, _: CurrentTecnicoDep, connection: ConnectionDep) -> FileResponse:
    row = connection.execute(
        "SELECT adjunto_nombre, adjunto_ruta FROM programa_pasos WHERE id = ? AND activo = 1",
        (paso_id,),
    ).fetchone()
    if row is None or not str(row["adjunto_ruta"] or ""):
        raise HTTPException(status_code=404, detail="Sin adjunto.")
    path = Path(str(row["adjunto_ruta"]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="El archivo no existe en disco.")
    return FileResponse(path, filename=str(row["adjunto_nombre"] or path.name))


@router.get("/api/repuestos", response_model=list[RepuestoDisponible])
def list_repuestos(_: CurrentTecnicoDep, connection: ConnectionDep) -> list[RepuestoDisponible]:
    rows = connection.execute(
        """
        SELECT id, nombre, COALESCE(descripcion,'') AS descripcion,
               stock_actual, COALESCE(imagen_nombre,'') AS imagen_nombre
        FROM repuestos
        WHERE activo = 1
        ORDER BY nombre
        """
    ).fetchall()
    return [
        RepuestoDisponible(
            id=int(r["id"]),
            nombre=str(r["nombre"]),
            descripcion=str(r["descripcion"]),
            stock_actual=float(r["stock_actual"] or 0),
            tiene_imagen=bool(r["imagen_nombre"]),
        )
        for r in rows
    ]


@router.get("/api/cronograma", response_model=list[CronogramaFila])
def get_cronograma(
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
    anio: int = Query(default=0),
) -> list[CronogramaFila]:
    if anio == 0:
        anio = date.today().year
    anio_str = str(anio)

    programas = connection.execute(
        """
        SELECT p.id, p.equipo_id, p.frecuencia_meses, p.proxima_ejecucion,
               e.nombre AS equipo_nombre,
               COALESCE(p.descripcion, '') AS descripcion
        FROM programas_mantenimiento p
        JOIN equipos e ON e.id = p.equipo_id
        WHERE p.activo = 1
        ORDER BY e.nombre, p.descripcion
        """
    ).fetchall()

    # Órdenes del año vinculadas a programas
    orden_rows = connection.execute(
        """
        SELECT
            op.programa_id,
            o.estado,
            CAST(strftime('%m', o.fecha_apertura) AS INTEGER) AS mes_ap,
            CAST(strftime('%m',
                COALESCE(NULLIF(o.fecha_cierre,''), o.fecha_apertura)) AS INTEGER) AS mes_ci
        FROM ordenes_trabajo o
        JOIN orden_programas op ON op.orden_id = o.id
        WHERE strftime('%Y', o.fecha_apertura) = ?
           OR strftime('%Y', o.fecha_cierre)   = ?
        """,
        (anio_str, anio_str),
    ).fetchall()

    from collections import defaultdict
    activas:     dict[int, set[int]] = defaultdict(set)
    completadas: dict[int, set[int]] = defaultdict(set)
    for prog_id, estado, mes_ap, mes_ci in orden_rows:
        if estado == "COMPLETADA":
            if mes_ci:
                completadas[int(prog_id)].add(int(mes_ci))
        elif estado in ("PENDIENTE", "EN_PROGRESO"):
            if mes_ap:
                activas[int(prog_id)].add(int(mes_ap))

    def _planned_months(proxima_str: str, freq: int) -> set[int]:
        try:
            proxima = date.fromisoformat(proxima_str)
        except ValueError:
            return set()
        freq = max(1, freq)
        cur = proxima
        while True:
            pm = cur.month - freq
            py = cur.year + (pm - 1) // 12
            pm = ((pm - 1) % 12) + 1
            last = calendar.monthrange(py, pm)[1]
            prev = cur.replace(year=py, month=pm, day=min(cur.day, last))
            if prev.year < anio:
                break
            cur = prev
        result: set[int] = set()
        while cur.year <= anio:
            if cur.year == anio:
                result.add(cur.month)
            nm = cur.month + freq
            ny = cur.year + (nm - 1) // 12
            nm = ((nm - 1) % 12) + 1
            last = calendar.monthrange(ny, nm)[1]
            cur = cur.replace(year=ny, month=nm, day=min(cur.day, last))
        return result

    filas: list[CronogramaFila] = []
    for row in programas:
        prog_id      = int(row["id"])
        equipo_id    = int(row["equipo_id"])
        equipo_nombre = str(row["equipo_nombre"] or "")
        freq     = int(row["frecuencia_meses"] or 1)
        proxima  = str(row["proxima_ejecucion"] or "")
        planned  = _planned_months(proxima, freq)

        meses: dict[str, str] = {}
        for mes in range(1, 13):
            if mes in completadas.get(prog_id, set()):
                meses[str(mes)] = "completada"
            elif mes in activas.get(prog_id, set()):
                meses[str(mes)] = "activa"
            elif mes in planned:
                meses[str(mes)] = "planned"

        etiqueta = f"{equipo_nombre} — {row['descripcion']}"
        filas.append(CronogramaFila(
            programa_id=prog_id, equipo_id=equipo_id,
            equipo_nombre=equipo_nombre, etiqueta=etiqueta, meses=meses,
        ))

    return filas
