from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from api.auth import CurrentTecnicoDep
from api.database import get_db, resolve_database_path
from api.models import (
    AgregarRepuestoOrdenRequest,
    ColaboradorItem,
    CompletarOrdenRequest,
    CrearOrdenRequest,
    FotoOrdenItem,
    ObservacionRequest,
    OrdenCard,
    OrdenDetail,
    PasoItem,
    ProgramaAdjuntoItem,
    ProgramaResumen,
    RepuestoOrdenItem,
)


def _fotos_dir(orden_id: int) -> Path:
    db_path = resolve_database_path()
    folder = db_path.parent / "orden_fotos" / str(orden_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder

router = APIRouter(prefix="/api/ordenes", tags=["ordenes"])
ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


def _card_from_row(row: sqlite3.Row) -> OrdenCard:
    return OrdenCard(
        id=int(row["id"]),
        equipo_id=int(row["equipo_id"]),
        equipo_nombre=str(row["equipo_nombre"] or ""),
        equipo_tipo_nombre=str(row["equipo_tipo_nombre"] or ""),
        equipo_marca=str(row["equipo_marca"] or ""),
        equipo_modelo=str(row["equipo_modelo"] or ""),
        equipo_ubicacion=str(row["equipo_ubicacion"] or ""),
        equipo_horas_trabajo_activo=bool(row["equipo_horas_trabajo_activo"]),
        equipo_horas_trabajo_actual=float(row["equipo_horas_trabajo_actual"] or 0),
        tipo=str(row["tipo"] or ""),
        descripcion=str(row["descripcion"] or ""),
        fecha_apertura=str(row["fecha_apertura"] or ""),
        fecha_cierre=str(row["fecha_cierre"] or ""),
        estado=str(row["estado"] or ""),
        tecnico_id=int(row["tecnico_id"]) if row["tecnico_id"] is not None else None,
        tecnico_nombre=str(row["tecnico_nombre"] or ""),
        costo_mano_obra=float(row["costo_mano_obra"] or 0),
        observaciones=str(row["observaciones"] or ""),
        horas_trabajo=float(row["horas_trabajo"]) if row["horas_trabajo"] is not None else None,
    )


def _base_query() -> str:
    return """
        SELECT
            o.id,
            o.equipo_id,
            e.nombre AS equipo_nombre,
            COALESCE(te.nombre, '') AS equipo_tipo_nombre,
            COALESCE(e.marca, '') AS equipo_marca,
            COALESCE(e.modelo, '') AS equipo_modelo,
            COALESCE(e.ubicacion, '') AS equipo_ubicacion,
            COALESCE(e.horas_trabajo_activo, 0) AS equipo_horas_trabajo_activo,
            COALESCE(e.horas_trabajo_actual, 0) AS equipo_horas_trabajo_actual,
            o.tipo,
            COALESCE(o.descripcion, '') AS descripcion,
            COALESCE(o.fecha_apertura, '') AS fecha_apertura,
            COALESCE(o.fecha_cierre, '') AS fecha_cierre,
            o.estado,
            o.tecnico_id,
            COALESCE(trim(t.nombre || ' ' || t.apellido), '') AS tecnico_nombre,
            COALESCE(o.costo_mano_obra, 0) AS costo_mano_obra,
            COALESCE(o.observaciones, '') AS observaciones,
            o.horas_trabajo AS horas_trabajo
        FROM ordenes_trabajo o
        JOIN equipos e ON e.id = o.equipo_id
        LEFT JOIN tipos_equipo te ON te.id = e.tipo_id
        LEFT JOIN tecnicos t ON t.id = o.tecnico_id
    """


def _colaboradores_for_orden(
    connection: sqlite3.Connection, orden_id: int
) -> list[ColaboradorItem]:
    rows = connection.execute(
        """
        SELECT t.id, t.nombre, t.apellido
        FROM orden_colaboradores oc
        JOIN tecnicos t ON t.id = oc.tecnico_id
        WHERE oc.orden_id = ?
        ORDER BY oc.creado_en
        """,
        (orden_id,),
    ).fetchall()
    return [
        ColaboradorItem(id=int(r["id"]), nombre=str(r["nombre"]), apellido=str(r["apellido"]))
        for r in rows
    ]


def _programas_for_orden(connection: sqlite3.Connection, orden_id: int) -> list[ProgramaResumen]:
    program_rows = connection.execute(
        """
        SELECT
            p.id,
            COALESCE(p.descripcion, '') AS descripcion,
            COALESCE(p.frecuencia_meses, 0) AS frecuencia_meses,
            COALESCE(p.ultima_ejecucion, '') AS ultima_ejecucion,
            COALESCE(p.proxima_ejecucion, '') AS proxima_ejecucion
        FROM orden_programas op
        JOIN programas_mantenimiento p ON p.id = op.programa_id
        WHERE op.orden_id = ?
        ORDER BY p.proxima_ejecucion, p.id
        """,
        (orden_id,),
    ).fetchall()
    programas: list[ProgramaResumen] = []
    for row in program_rows:
        programa_id = int(row["id"])
        adjuntos = connection.execute(
            """
            SELECT id, tipo, nombre
            FROM programa_adjuntos
            WHERE programa_id = ?
            ORDER BY tipo, nombre
            """,
            (programa_id,),
        ).fetchall()
        paso_rows = connection.execute(
            """
            SELECT
                pp.id,
                pp.posicion,
                pp.descripcion,
                COALESCE(pp.adjunto_nombre, '') AS adjunto_nombre,
                COALESCE(pp.observaciones, '') AS observaciones,
                COALESCE(ope.completado, 0) AS completado
            FROM programa_pasos pp
            LEFT JOIN orden_paso_estado ope
                ON ope.paso_id = pp.id AND ope.orden_id = ?
            WHERE pp.programa_id = ? AND pp.activo = 1
            ORDER BY pp.posicion, pp.id
            """,
            (orden_id, programa_id),
        ).fetchall()
        programas.append(
            ProgramaResumen(
                id=programa_id,
                descripcion=str(row["descripcion"] or ""),
                frecuencia_meses=int(row["frecuencia_meses"] or 0),
                ultima_ejecucion=str(row["ultima_ejecucion"] or ""),
                proxima_ejecucion=str(row["proxima_ejecucion"] or ""),
                adjuntos=[
                    ProgramaAdjuntoItem(
                        id=int(adjunto["id"]),
                        tipo=str(adjunto["tipo"]),
                        nombre=str(adjunto["nombre"] or ""),
                    )
                    for adjunto in adjuntos
                ],
                pasos=[
                    PasoItem(
                        id=int(paso["id"]),
                        posicion=int(paso["posicion"]),
                        descripcion=str(paso["descripcion"]),
                        completado=bool(paso["completado"]),
                        adjunto_nombre=str(paso["adjunto_nombre"]),
                        observaciones=str(paso["observaciones"]),
                    )
                    for paso in paso_rows
                ],
            )
        )
    return programas


def _get_orden_detail(connection: sqlite3.Connection, orden_id: int) -> OrdenDetail | None:
    row = connection.execute(_base_query() + " WHERE o.id = ?", (orden_id,)).fetchone()
    if row is None:
        return None
    repuestos = connection.execute(
        """
        SELECT
            ro.id,
            ro.repuesto_id,
            COALESCE(r.nombre, ro.descripcion) AS descripcion,
            COALESCE(ro.cantidad, 0) AS cantidad,
            COALESCE(ro.costo_unitario, 0) AS costo_unitario
        FROM repuestos_orden ro
        LEFT JOIN repuestos r ON r.id = ro.repuesto_id
        WHERE ro.orden_id = ?
        ORDER BY ro.id
        """,
        (orden_id,),
    ).fetchall()
    fotos = connection.execute(
        "SELECT id, nombre FROM orden_adjuntos WHERE orden_id = ? ORDER BY id",
        (orden_id,),
    ).fetchall()
    return OrdenDetail(
        **_card_from_row(row).model_dump(),
        repuestos=[
            RepuestoOrdenItem(
                id=int(item["id"]),
                repuesto_id=int(item["repuesto_id"]) if item["repuesto_id"] is not None else None,
                descripcion=str(item["descripcion"] or ""),
                cantidad=float(item["cantidad"] or 0),
                costo_unitario=float(item["costo_unitario"] or 0),
            )
            for item in repuestos
        ],
        programas=_programas_for_orden(connection, orden_id),
        colaboradores=_colaboradores_for_orden(connection, orden_id),
        fotos=[
            FotoOrdenItem(id=int(f["id"]), nombre=str(f["nombre"] or ""))
            for f in fotos
        ],
    )


@router.post("", response_model=OrdenDetail, status_code=201)
def create_orden(
    payload: CrearOrdenRequest,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    if payload.tipo not in ("PREVENTIVO", "CORRECTIVO", "MEJORA"):
        raise HTTPException(status_code=400, detail="Tipo de orden inválido.")
    equipo = connection.execute(
        "SELECT id FROM equipos WHERE id = ? AND activo = 1", (payload.equipo_id,)
    ).fetchone()
    if equipo is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")
    cursor = connection.execute(
        """
        INSERT INTO ordenes_trabajo
            (equipo_id, tipo, descripcion, fecha_apertura, observaciones, estado)
        VALUES (?, ?, ?, date('now'), ?, 'PENDIENTE')
        """,
        (
            payload.equipo_id,
            payload.tipo,
            payload.descripcion.strip(),
            payload.observaciones.strip(),
        ),
    )
    orden_id = cursor.lastrowid
    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.get("", response_model=list[OrdenCard])
def list_ordenes(
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
    estado: str | None = Query(default=None),
    equipo_id: int | None = Query(default=None),
    solo_mis: bool = Query(default=False),
) -> list[OrdenCard]:
    query = _base_query()
    clauses: list[str] = []
    params: list[object] = []
    if solo_mis:
        query += " JOIN orden_colaboradores _oc ON _oc.orden_id = o.id AND _oc.tecnico_id = ?"
        params.insert(0, current_tecnico.id)
        clauses.append("o.estado NOT IN ('COMPLETADA', 'CANCELADA')")
    if estado:
        clauses.append("o.estado = ?")
        params.append(estado)
    if equipo_id is not None:
        clauses.append("o.equipo_id = ?")
        params.append(equipo_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += """
        ORDER BY
            CASE o.estado
                WHEN 'PENDIENTE' THEN 0
                WHEN 'EN_PROGRESO' THEN 1
                ELSE 2
            END,
            o.fecha_apertura DESC,
            o.id DESC
    """
    rows = connection.execute(query, tuple(params)).fetchall()
    return [_card_from_row(row) for row in rows]


@router.get("/{orden_id}", response_model=OrdenDetail)
def get_orden(
    orden_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    return orden


@router.post("/{orden_id}/aceptar", response_model=OrdenDetail)
def aceptar_orden(
    orden_id: int,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT id, estado FROM ordenes_trabajo WHERE id = ?",
        (orden_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in ("COMPLETADA", "CANCELADA"):
        raise HTTPException(status_code=409, detail="La orden ya está cerrada.")

    # Verificar si ya es colaborador
    ya_colabora = connection.execute(
        "SELECT 1 FROM orden_colaboradores WHERE orden_id = ? AND tecnico_id = ?",
        (orden_id, current_tecnico.id),
    ).fetchone()
    if ya_colabora:
        raise HTTPException(status_code=409, detail="Ya sos colaborador de esta orden.")

    # Registrar como colaborador
    connection.execute(
        "INSERT OR IGNORE INTO orden_colaboradores (orden_id, tecnico_id) VALUES (?, ?)",
        (orden_id, current_tecnico.id),
    )

    # Si estaba PENDIENTE → cambiar estado y asignar técnico principal
    if str(row["estado"]) == "PENDIENTE":
        connection.execute(
            """
            UPDATE ordenes_trabajo
            SET estado = 'EN_PROGRESO', tecnico_id = ?, actualizado_en = CURRENT_TIMESTAMP
            WHERE id = ? AND estado = 'PENDIENTE'
            """,
            (current_tecnico.id, orden_id),
        )

    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/cancelar-aceptacion", response_model=OrdenDetail)
def cancelar_aceptacion(
    orden_id: int,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT id, estado, tecnico_id FROM ordenes_trabajo WHERE id = ?",
        (orden_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in ("COMPLETADA", "CANCELADA"):
        raise HTTPException(status_code=409, detail="La orden ya está cerrada.")

    ya_colabora = connection.execute(
        "SELECT 1 FROM orden_colaboradores WHERE orden_id = ? AND tecnico_id = ?",
        (orden_id, current_tecnico.id),
    ).fetchone()
    if not ya_colabora:
        raise HTTPException(status_code=409, detail="No sos colaborador de esta orden.")

    connection.execute(
        "DELETE FROM orden_colaboradores WHERE orden_id = ? AND tecnico_id = ?",
        (orden_id, current_tecnico.id),
    )

    siguiente = connection.execute(
        "SELECT tecnico_id FROM orden_colaboradores WHERE orden_id = ? ORDER BY creado_en LIMIT 1",
        (orden_id,),
    ).fetchone()

    if siguiente is None:
        connection.execute(
            """
            UPDATE ordenes_trabajo
            SET estado = 'PENDIENTE', tecnico_id = NULL, actualizado_en = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (orden_id,),
        )
    elif int(row["tecnico_id"] or 0) == current_tecnico.id:
        connection.execute(
            """
            UPDATE ordenes_trabajo
            SET tecnico_id = ?, actualizado_en = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(siguiente["tecnico_id"]), orden_id),
        )

    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/completar", response_model=OrdenDetail)
def completar_orden(
    orden_id: int,
    payload: CompletarOrdenRequest,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        """
        SELECT o.id, o.estado, o.tecnico_id, o.observaciones, o.equipo_id,
               COALESCE(e.horas_trabajo_activo, 0) AS horas_trabajo_activo,
               COALESCE(e.horas_trabajo_actual, 0) AS horas_trabajo_actual
        FROM ordenes_trabajo o
        JOIN equipos e ON e.id = o.equipo_id
        WHERE o.id = ?
        """,
        (orden_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) != "EN_PROGRESO":
        raise HTTPException(status_code=409, detail="La orden no está en EN_PROGRESO.")
    if row["tecnico_id"] is not None and int(row["tecnico_id"]) != current_tecnico.id:
        raise HTTPException(status_code=403, detail="El técnico no es el asignado.")

    horas_trabajo_activo = bool(row["horas_trabajo_activo"])
    horas_trabajo_actual = float(row["horas_trabajo_actual"] or 0)
    if horas_trabajo_activo:
        if payload.horas_trabajo is None or payload.horas_trabajo <= horas_trabajo_actual:
            raise HTTPException(
                status_code=400,
                detail="Debe actualizar las horas de trabajo del equipo para completar esta orden.",
            )

    nueva_obs = payload.observaciones.strip()
    observaciones = str(row["observaciones"] or "")
    merged = observaciones
    if nueva_obs:
        merged = f"{observaciones}\n---\n{nueva_obs}" if observaciones else nueva_obs

    connection.execute(
        """
        UPDATE ordenes_trabajo
        SET
            estado = 'COMPLETADA',
            fecha_cierre = datetime('now', 'localtime'),
            observaciones = ?,
            horas_trabajo = ?,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE id = ? AND estado = 'EN_PROGRESO'
        """,
        (merged, payload.horas_trabajo, orden_id),
    )
    if horas_trabajo_activo:
        connection.execute(
            """
            UPDATE equipos
            SET horas_trabajo_actual = ?, actualizado_en = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (payload.horas_trabajo, int(row["equipo_id"])),
        )
    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/repuestos", response_model=OrdenDetail)
def agregar_repuesto_a_orden(
    orden_id: int,
    payload: AgregarRepuestoOrdenRequest,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT estado FROM ordenes_trabajo WHERE id = ?", (orden_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in ("COMPLETADA", "CANCELADA"):
        raise HTTPException(status_code=409, detail="No se pueden agregar repuestos a una orden cerrada.")
    if payload.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0.")

    rep = connection.execute(
        "SELECT id, nombre, stock_actual FROM repuestos WHERE id = ? AND activo = 1",
        (payload.repuesto_id,),
    ).fetchone()
    if rep is None:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado.")

    connection.execute(
        """
        INSERT INTO repuestos_orden (orden_id, repuesto_id, descripcion, cantidad, costo_unitario)
        VALUES (?, ?, ?, ?, 0)
        """,
        (orden_id, payload.repuesto_id, str(rep["nombre"]), payload.cantidad),
    )
    connection.execute(
        "UPDATE repuestos SET stock_actual = stock_actual - ?,"
        " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
        (payload.cantidad, payload.repuesto_id),
    )
    connection.commit()

    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.delete("/{orden_id}/repuestos/{item_id}", response_model=OrdenDetail)
def quitar_repuesto_de_orden(
    orden_id: int,
    item_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT repuesto_id, cantidad FROM repuestos_orden WHERE id = ? AND orden_id = ?",
        (item_id, orden_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado en la orden.")

    connection.execute("DELETE FROM repuestos_orden WHERE id = ?", (item_id,))
    if row["repuesto_id"] is not None:
        connection.execute(
            "UPDATE repuestos SET stock_actual = stock_actual + ?,"
            " actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
            (row["cantidad"], row["repuesto_id"]),
        )
    connection.commit()

    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/observaciones", response_model=OrdenDetail)
def agregar_observacion(
    orden_id: int,
    payload: ObservacionRequest,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT estado, observaciones FROM ordenes_trabajo WHERE id = ?",
        (orden_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in {"COMPLETADA", "CANCELADA"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pueden agregar observaciones en este estado.",
        )

    texto = payload.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="La observación no puede estar vacía.")
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M")
    bloque = f"[{marca_tiempo}] {current_tecnico.nombre_completo}: {texto}"
    observaciones = str(row["observaciones"] or "")
    merged = f"{observaciones}\n---\n{bloque}" if observaciones else bloque

    connection.execute(
        """
        UPDATE ordenes_trabajo
        SET observaciones = ?, actualizado_en = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (merged, orden_id),
    )
    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/fotos", response_model=OrdenDetail, status_code=201)
async def subir_foto(
    orden_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
    foto: UploadFile = File(...),
) -> OrdenDetail:
    row = connection.execute(
        "SELECT estado FROM ordenes_trabajo WHERE id = ?", (orden_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in ("COMPLETADA", "CANCELADA"):
        raise HTTPException(status_code=409, detail="No se pueden agregar fotos a una orden cerrada.")

    folder = _fotos_dir(orden_id)
    suffix = Path(foto.filename or "foto.jpg").suffix or ".jpg"
    # Nombre único con timestamp para evitar colisiones
    nombre = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.filename or 'foto'}"
    ruta = folder / nombre
    with ruta.open("wb") as f:
        shutil.copyfileobj(foto.file, f)

    connection.execute(
        "INSERT INTO orden_adjuntos (orden_id, nombre, ruta) VALUES (?, ?, ?)",
        (orden_id, foto.filename or nombre, str(ruta)),
    )
    connection.commit()

    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.get("/{orden_id}/fotos/{foto_id}")
def ver_foto(
    orden_id: int,
    foto_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> FileResponse:
    row = connection.execute(
        "SELECT nombre, ruta FROM orden_adjuntos WHERE id = ? AND orden_id = ?",
        (foto_id, orden_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Foto no encontrada.")
    path = Path(str(row["ruta"]))
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="El archivo no existe en disco.")
    return FileResponse(path, media_type="image/jpeg", filename=str(row["nombre"] or path.name))


@router.delete("/{orden_id}/fotos/{foto_id}", response_model=OrdenDetail)
def eliminar_foto(
    orden_id: int,
    foto_id: int,
    _: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT nombre, ruta FROM orden_adjuntos WHERE id = ? AND orden_id = ?",
        (foto_id, orden_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Foto no encontrada.")
    path = Path(str(row["ruta"]))
    if path.exists() and path.is_file():
        path.unlink()
    connection.execute("DELETE FROM orden_adjuntos WHERE id = ?", (foto_id,))
    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.post("/{orden_id}/pasos/{paso_id}/toggle", response_model=OrdenDetail)
def toggle_paso(
    orden_id: int,
    paso_id: int,
    current_tecnico: CurrentTecnicoDep,
    connection: ConnectionDep,
) -> OrdenDetail:
    row = connection.execute(
        "SELECT estado FROM ordenes_trabajo WHERE id = ?", (orden_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    if str(row["estado"]) in ("COMPLETADA", "CANCELADA"):
        raise HTTPException(status_code=409, detail="La orden ya está cerrada.")

    paso = connection.execute(
        "SELECT id FROM programa_pasos WHERE id = ? AND activo = 1", (paso_id,)
    ).fetchone()
    if paso is None:
        raise HTTPException(status_code=404, detail="Paso no encontrado.")

    existing = connection.execute(
        "SELECT completado FROM orden_paso_estado WHERE orden_id = ? AND paso_id = ?",
        (orden_id, paso_id),
    ).fetchone()

    if existing is None:
        connection.execute(
            """
            INSERT INTO orden_paso_estado (orden_id, paso_id, completado, tecnico_id, actualizado_en)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
            """,
            (orden_id, paso_id, current_tecnico.id),
        )
    else:
        nuevo = 0 if int(existing["completado"]) else 1
        connection.execute(
            """
            UPDATE orden_paso_estado
            SET completado = ?, tecnico_id = ?, actualizado_en = CURRENT_TIMESTAMP
            WHERE orden_id = ? AND paso_id = ?
            """,
            (nuevo, current_tecnico.id, orden_id, paso_id),
        )
    connection.commit()

    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden

