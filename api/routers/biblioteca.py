from __future__ import annotations

import mimetypes
import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.auth import CurrentTecnicoDep
from api.database import get_db
from api.models import (
    EquipoCard,
    EquipoDetail,
    HistorialOrdenItem,
    PasoItem,
    ProgramaAdjuntoItem,
    ProgramaDetail,
    ProgramaResumen,
    RepuestoDisponible,
)

router = APIRouter(tags=["biblioteca"])
ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


def _pasos_for_programa(
    connection: sqlite3.Connection,
    programa_id: int,
) -> list[PasoItem]:
    rows = connection.execute(
        """
        SELECT id, posicion, descripcion
        FROM programa_pasos
        WHERE programa_id = ? AND activo = 1
        ORDER BY posicion, id
        """,
        (programa_id,),
    ).fetchall()
    return [
        PasoItem(
            id=int(row["id"]),
            posicion=int(row["posicion"]),
            descripcion=str(row["descripcion"]),
            completado=False,
        )
        for row in rows
    ]


def _adjuntos_for_programa(
    connection: sqlite3.Connection,
    programa_id: int,
) -> list[ProgramaAdjuntoItem]:
    rows = connection.execute(
        """
        SELECT id, tipo, nombre
        FROM programa_adjuntos
        WHERE programa_id = ?
        ORDER BY tipo, nombre
        """,
        (programa_id,),
    ).fetchall()
    return [
        ProgramaAdjuntoItem(
            id=int(row["id"]),
            tipo=str(row["tipo"]),
            nombre=str(row["nombre"] or ""),
        )
        for row in rows
    ]


def _programa_detail(connection: sqlite3.Connection, programa_id: int) -> ProgramaDetail | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.equipo_id,
            e.nombre AS equipo_nombre,
            COALESCE(p.descripcion, '') AS descripcion,
            COALESCE(p.frecuencia_meses, 0) AS frecuencia_meses,
            COALESCE(p.ultima_ejecucion, '') AS ultima_ejecucion,
            COALESCE(p.proxima_ejecucion, '') AS proxima_ejecucion
        FROM programas_mantenimiento p
        JOIN equipos e ON e.id = p.equipo_id
        WHERE p.id = ?
        """,
        (programa_id,),
    ).fetchone()
    if row is None:
        return None
    return ProgramaDetail(
        id=int(row["id"]),
        equipo_id=int(row["equipo_id"]),
        equipo_nombre=str(row["equipo_nombre"] or ""),
        descripcion=str(row["descripcion"] or ""),
        frecuencia_meses=int(row["frecuencia_meses"] or 0),
        ultima_ejecucion=str(row["ultima_ejecucion"] or ""),
        proxima_ejecucion=str(row["proxima_ejecucion"] or ""),
        adjuntos=_adjuntos_for_programa(connection, programa_id),
        pasos=_pasos_for_programa(connection, programa_id),
    )


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


@router.get("/api/equipos/{equipo_id}", response_model=EquipoDetail)
def get_equipo(
    equipo_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> EquipoDetail:
    row = connection.execute(
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
            COALESCE(e.fecha_adquisicion, '') AS fecha_adquisicion,
            (
                SELECT COUNT(*)
                FROM programas_mantenimiento p
                WHERE p.equipo_id = e.id AND p.activo = 1
            ) AS programas_activos_count
        FROM equipos e
        LEFT JOIN tipos_equipo t ON t.id = e.tipo_id
        WHERE e.id = ? AND e.activo = 1
        """,
        (equipo_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    programas_rows = connection.execute(
        """
        SELECT
            id,
            COALESCE(descripcion, '') AS descripcion,
            COALESCE(frecuencia_meses, 0) AS frecuencia_meses,
            COALESCE(ultima_ejecucion, '') AS ultima_ejecucion,
            COALESCE(proxima_ejecucion, '') AS proxima_ejecucion
        FROM programas_mantenimiento
        WHERE equipo_id = ? AND activo = 1
        ORDER BY proxima_ejecucion, id
        """,
        (equipo_id,),
    ).fetchall()

    return EquipoDetail(
        id=int(row["id"]),
        nombre=str(row["nombre"] or ""),
        tipo_id=int(row["tipo_id"]) if row["tipo_id"] is not None else None,
        tipo_nombre=str(row["tipo_nombre"] or ""),
        numero_serie=str(row["numero_serie"] or ""),
        marca=str(row["marca"] or ""),
        modelo=str(row["modelo"] or ""),
        ubicacion=str(row["ubicacion"] or ""),
        observaciones=str(row["observaciones"] or ""),
        fecha_adquisicion=str(row["fecha_adquisicion"] or ""),
        programas_activos_count=int(row["programas_activos_count"] or 0),
        programas=[
            ProgramaResumen(
                id=int(item["id"]),
                descripcion=str(item["descripcion"] or ""),
                frecuencia_meses=int(item["frecuencia_meses"] or 0),
                ultima_ejecucion=str(item["ultima_ejecucion"] or ""),
                proxima_ejecucion=str(item["proxima_ejecucion"] or ""),
                adjuntos=_adjuntos_for_programa(connection, int(item["id"])),
                pasos=_pasos_for_programa(connection, int(item["id"])),
            )
            for item in programas_rows
        ],
    )


@router.get("/api/programas/{programa_id}", response_model=ProgramaDetail)
def get_programa(
    programa_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> ProgramaDetail:
    programa = _programa_detail(connection, programa_id)
    if programa is None:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    return programa


@router.get("/api/adjuntos/{adjunto_id}")
def get_adjunto(
    adjunto_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> FileResponse:
    row = connection.execute(
        "SELECT tipo, nombre, ruta FROM programa_adjuntos WHERE id = ?",
        (adjunto_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado.")
    path = Path(str(row["ruta"] or ""))
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="El archivo no existe en disco.")
    media_type, _ = mimetypes.guess_type(path.name)
    if str(row["tipo"]) == "PDF":
        media_type = media_type or "application/pdf"
    else:
        media_type = media_type or "image/jpeg"
    return FileResponse(path, media_type=media_type, filename=str(row["nombre"] or path.name))


@router.get("/api/repuestos", response_model=list[RepuestoDisponible])
def list_repuestos(_: CurrentTecnicoDep, connection: ConnectionDep) -> list[RepuestoDisponible]:
    rows = connection.execute(
        """
        SELECT id, nombre, stock_actual, stock_minimo
        FROM repuestos
        WHERE activo = 1
        ORDER BY nombre
        """
    ).fetchall()
    return [
        RepuestoDisponible(
            id=int(r["id"]),
            nombre=str(r["nombre"]),
            stock_actual=float(r["stock_actual"] or 0),
            stock_minimo=float(r["stock_minimo"] or 0),
        )
        for r in rows
    ]


@router.get("/api/equipos/{equipo_id}/historial", response_model=list[HistorialOrdenItem])
def get_historial_equipo(
    equipo_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> list[HistorialOrdenItem]:
    rows = connection.execute(
        """
        SELECT
            o.id,
            o.tipo,
            COALESCE(o.descripcion, '')    AS descripcion,
            COALESCE(o.fecha_apertura, '') AS fecha_apertura,
            COALESCE(o.fecha_cierre, '')   AS fecha_cierre,
            o.estado,
            COALESCE(o.observaciones, '')  AS observaciones,
            COALESCE(trim(t.nombre || ' ' || t.apellido), '') AS tecnico_nombre
        FROM ordenes_trabajo o
        LEFT JOIN tecnicos t ON t.id = o.tecnico_id
        WHERE o.equipo_id = ?
        ORDER BY
            CASE WHEN o.fecha_cierre = '' OR o.fecha_cierre IS NULL THEN 1 ELSE 0 END,
            o.fecha_cierre DESC,
            o.id DESC
        """,
        (equipo_id,),
    ).fetchall()

    items = []
    for r in rows:
        orden_id = int(r["id"])
        colab_rows = connection.execute(
            """
            SELECT trim(t.nombre || ' ' || t.apellido) AS nombre_completo
            FROM orden_colaboradores oc
            JOIN tecnicos t ON t.id = oc.tecnico_id
            WHERE oc.orden_id = ?
            ORDER BY oc.creado_en
            """,
            (orden_id,),
        ).fetchall()
        items.append(
            HistorialOrdenItem(
                id=orden_id,
                tipo=str(r["tipo"] or ""),
                descripcion=str(r["descripcion"]),
                fecha_apertura=str(r["fecha_apertura"]),
                fecha_cierre=str(r["fecha_cierre"]),
                estado=str(r["estado"] or ""),
                observaciones=str(r["observaciones"]),
                tecnico_nombre=str(r["tecnico_nombre"]),
                colaboradores=[str(c["nombre_completo"]) for c in colab_rows],
            )
        )
    return items
