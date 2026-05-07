from __future__ import annotations

import calendar
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from api.auth import AdminTecnicoDep, hash_password
from api.database import get_db, resolve_database_path
from api.models import (
    AdminEquipoItem,
    AdminEquipoRequest,
    AdminOrdenRequest,
    AdminPasoItem,
    AdminPasoRequest,
    AdminProgramaItem,
    AdminProgramaRequest,
    AdminRepuestoItem,
    AdminRepuestoRequest,
    AdminTecnicoCreate,
    AdminTecnicoItem,
    AdminTecnicoUpdate,
    OrdenCard,
    OrdenDetail,
    SetPasswordRequest,
    TipoEquipoItem,
    TipoEquipoRequest,
)
from api.routers.ordenes import (
    _base_query,
    _card_from_row,
    _get_orden_detail,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


def _calc_proxima(ultima: str, frecuencia_meses: int) -> str:
    try:
        d = date.fromisoformat(ultima)
    except ValueError:
        return ""
    m = d.month + frecuencia_meses
    y = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day).isoformat()


# ── Tipos de Equipo ───────────────────────────────────────────────────────────

@router.get("/tipos-equipo", response_model=list[TipoEquipoItem])
def list_tipos(_: AdminTecnicoDep, connection: ConnectionDep) -> list[TipoEquipoItem]:
    rows = connection.execute(
        "SELECT id, nombre, activo FROM tipos_equipo ORDER BY nombre"
    ).fetchall()
    return [TipoEquipoItem(id=int(r["id"]), nombre=str(r["nombre"]), activo=bool(r["activo"])) for r in rows]


@router.post("/tipos-equipo", response_model=TipoEquipoItem, status_code=status.HTTP_201_CREATED)
def create_tipo(payload: TipoEquipoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> TipoEquipoItem:
    cur = connection.execute(
        "INSERT INTO tipos_equipo (nombre, activo) VALUES (?, ?)",
        (payload.nombre.strip(), int(payload.activo)),
    )
    connection.commit()
    row = connection.execute("SELECT id, nombre, activo FROM tipos_equipo WHERE id = ?", (cur.lastrowid,)).fetchone()
    return TipoEquipoItem(id=int(row["id"]), nombre=str(row["nombre"]), activo=bool(row["activo"]))


@router.put("/tipos-equipo/{tipo_id}", response_model=TipoEquipoItem)
def update_tipo(tipo_id: int, payload: TipoEquipoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> TipoEquipoItem:
    affected = connection.execute(
        "UPDATE tipos_equipo SET nombre = ?, activo = ? WHERE id = ?",
        (payload.nombre.strip(), int(payload.activo), tipo_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Tipo no encontrado.")
    connection.commit()
    row = connection.execute("SELECT id, nombre, activo FROM tipos_equipo WHERE id = ?", (tipo_id,)).fetchone()
    return TipoEquipoItem(id=int(row["id"]), nombre=str(row["nombre"]), activo=bool(row["activo"]))


@router.delete("/tipos-equipo/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo(tipo_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    affected = connection.execute("DELETE FROM tipos_equipo WHERE id = ?", (tipo_id,)).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Tipo no encontrado.")
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Equipos ───────────────────────────────────────────────────────────────────

def _equipo_row_to_item(row: sqlite3.Row) -> AdminEquipoItem:
    return AdminEquipoItem(
        id=int(row["id"]),
        nombre=str(row["nombre"] or ""),
        tipo_id=int(row["tipo_id"]) if row["tipo_id"] is not None else None,
        tipo_nombre=str(row["tipo_nombre"] or ""),
        numero_serie=str(row["numero_serie"] or ""),
        marca=str(row["marca"] or ""),
        modelo=str(row["modelo"] or ""),
        ubicacion=str(row["ubicacion"] or ""),
        fecha_adquisicion=str(row["fecha_adquisicion"] or ""),
        observaciones=str(row["observaciones"] or ""),
        activo=bool(row["activo"]),
    )

_EQUIPO_SELECT = """
    SELECT e.id, e.nombre, e.tipo_id, COALESCE(t.nombre,'') AS tipo_nombre,
           COALESCE(e.numero_serie,'') AS numero_serie, COALESCE(e.marca,'') AS marca,
           COALESCE(e.modelo,'') AS modelo, COALESCE(e.ubicacion,'') AS ubicacion,
           COALESCE(e.fecha_adquisicion,'') AS fecha_adquisicion,
           COALESCE(e.observaciones,'') AS observaciones, e.activo
    FROM equipos e LEFT JOIN tipos_equipo t ON t.id = e.tipo_id
"""


@router.get("/equipos", response_model=list[AdminEquipoItem])
def list_equipos_admin(_: AdminTecnicoDep, connection: ConnectionDep) -> list[AdminEquipoItem]:
    rows = connection.execute(_EQUIPO_SELECT + " ORDER BY e.nombre").fetchall()
    return [_equipo_row_to_item(r) for r in rows]


@router.post("/equipos", response_model=AdminEquipoItem, status_code=status.HTTP_201_CREATED)
def create_equipo(payload: AdminEquipoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminEquipoItem:
    cur = connection.execute(
        """INSERT INTO equipos (nombre, tipo_id, numero_serie, marca, modelo, ubicacion, fecha_adquisicion, observaciones, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (payload.nombre.strip(), payload.tipo_id, payload.numero_serie, payload.marca,
         payload.modelo, payload.ubicacion, payload.fecha_adquisicion, payload.observaciones, int(payload.activo)),
    )
    connection.commit()
    row = connection.execute(_EQUIPO_SELECT + " WHERE e.id = ?", (cur.lastrowid,)).fetchone()
    return _equipo_row_to_item(row)


@router.put("/equipos/{equipo_id}", response_model=AdminEquipoItem)
def update_equipo(equipo_id: int, payload: AdminEquipoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminEquipoItem:
    affected = connection.execute(
        """UPDATE equipos SET nombre=?, tipo_id=?, numero_serie=?, marca=?, modelo=?,
           ubicacion=?, fecha_adquisicion=?, observaciones=?, activo=?,
           actualizado_en=CURRENT_TIMESTAMP WHERE id=?""",
        (payload.nombre.strip(), payload.tipo_id, payload.numero_serie, payload.marca,
         payload.modelo, payload.ubicacion, payload.fecha_adquisicion, payload.observaciones,
         int(payload.activo), equipo_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")
    connection.commit()
    row = connection.execute(_EQUIPO_SELECT + " WHERE e.id = ?", (equipo_id,)).fetchone()
    return _equipo_row_to_item(row)


@router.delete("/equipos/{equipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipo(equipo_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    affected = connection.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,)).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Programas de Mantenimiento ────────────────────────────────────────────────

def _programa_row_to_item(row: sqlite3.Row) -> AdminProgramaItem:
    return AdminProgramaItem(
        id=int(row["id"]),
        equipo_id=int(row["equipo_id"]),
        equipo_nombre=str(row["equipo_nombre"] or ""),
        descripcion=str(row["descripcion"] or ""),
        frecuencia_meses=int(row["frecuencia_meses"] or 1),
        ultima_ejecucion=str(row["ultima_ejecucion"] or ""),
        proxima_ejecucion=str(row["proxima_ejecucion"] or ""),
        activo=bool(row["activo"]),
    )

_PROGRAMA_SELECT = """
    SELECT p.id, p.equipo_id, e.nombre AS equipo_nombre,
           COALESCE(p.descripcion,'') AS descripcion,
           COALESCE(p.frecuencia_meses,1) AS frecuencia_meses,
           COALESCE(p.ultima_ejecucion,'') AS ultima_ejecucion,
           COALESCE(p.proxima_ejecucion,'') AS proxima_ejecucion,
           p.activo
    FROM programas_mantenimiento p JOIN equipos e ON e.id = p.equipo_id
"""


@router.get("/programas", response_model=list[AdminProgramaItem])
def list_programas_admin(_: AdminTecnicoDep, connection: ConnectionDep) -> list[AdminProgramaItem]:
    rows = connection.execute(_PROGRAMA_SELECT + " ORDER BY e.nombre, p.descripcion").fetchall()
    return [_programa_row_to_item(r) for r in rows]


@router.post("/programas", response_model=AdminProgramaItem, status_code=status.HTTP_201_CREATED)
def create_programa(payload: AdminProgramaRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminProgramaItem:
    proxima = _calc_proxima(payload.ultima_ejecucion, payload.frecuencia_meses)
    cur = connection.execute(
        """INSERT INTO programas_mantenimiento (equipo_id, descripcion, frecuencia_meses, ultima_ejecucion, proxima_ejecucion, activo)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (payload.equipo_id, payload.descripcion.strip(), payload.frecuencia_meses,
         payload.ultima_ejecucion, proxima, int(payload.activo)),
    )
    connection.commit()
    row = connection.execute(_PROGRAMA_SELECT + " WHERE p.id = ?", (cur.lastrowid,)).fetchone()
    return _programa_row_to_item(row)


@router.put("/programas/{programa_id}", response_model=AdminProgramaItem)
def update_programa(programa_id: int, payload: AdminProgramaRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminProgramaItem:
    proxima = _calc_proxima(payload.ultima_ejecucion, payload.frecuencia_meses)
    affected = connection.execute(
        """UPDATE programas_mantenimiento SET equipo_id=?, descripcion=?, frecuencia_meses=?,
           ultima_ejecucion=?, proxima_ejecucion=?, activo=?, actualizado_en=CURRENT_TIMESTAMP
           WHERE id=?""",
        (payload.equipo_id, payload.descripcion.strip(), payload.frecuencia_meses,
         payload.ultima_ejecucion, proxima, int(payload.activo), programa_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    connection.commit()
    row = connection.execute(_PROGRAMA_SELECT + " WHERE p.id = ?", (programa_id,)).fetchone()
    return _programa_row_to_item(row)


@router.delete("/programas/{programa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_programa(programa_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    affected = connection.execute("DELETE FROM programas_mantenimiento WHERE id = ?", (programa_id,)).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Pasos de Programa ────────────────────────────────────────────────────────

def _paso_adjuntos_dir(paso_id: int) -> Path:
    folder = resolve_database_path().parent / "paso_adjuntos" / str(paso_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _paso_row_to_item(row: sqlite3.Row) -> AdminPasoItem:
    return AdminPasoItem(
        id=int(row["id"]),
        posicion=int(row["posicion"]),
        descripcion=str(row["descripcion"]),
        observaciones=str(row["observaciones"] or ""),
        adjunto_nombre=str(row["adjunto_nombre"] or ""),
        activo=bool(row["activo"]),
    )

_PASO_SELECT = """
    SELECT id, posicion, descripcion,
           COALESCE(observaciones,'') AS observaciones,
           COALESCE(adjunto_nombre,'') AS adjunto_nombre,
           COALESCE(adjunto_ruta,'') AS adjunto_ruta, activo
    FROM programa_pasos WHERE programa_id = ? AND activo = 1
    ORDER BY posicion, id
"""


@router.get("/programas/{programa_id}/pasos", response_model=list[AdminPasoItem])
def list_pasos(_: AdminTecnicoDep, programa_id: int, connection: ConnectionDep) -> list[AdminPasoItem]:
    rows = connection.execute(_PASO_SELECT, (programa_id,)).fetchall()
    return [_paso_row_to_item(r) for r in rows]


@router.post("/programas/{programa_id}/pasos", response_model=AdminPasoItem, status_code=status.HTTP_201_CREATED)
def create_paso(programa_id: int, payload: AdminPasoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminPasoItem:
    max_pos = connection.execute(
        "SELECT COALESCE(MAX(posicion),0) FROM programa_pasos WHERE programa_id = ? AND activo = 1",
        (programa_id,),
    ).fetchone()[0]
    cur = connection.execute(
        "INSERT INTO programa_pasos (programa_id, posicion, descripcion, observaciones) VALUES (?, ?, ?, ?)",
        (programa_id, int(max_pos) + 1, payload.descripcion.strip(), payload.observaciones),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id, posicion, descripcion, COALESCE(observaciones,'') AS observaciones, COALESCE(adjunto_nombre,'') AS adjunto_nombre, COALESCE(adjunto_ruta,'') AS adjunto_ruta, activo FROM programa_pasos WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    return _paso_row_to_item(row)


@router.put("/programas/{programa_id}/pasos/{paso_id}", response_model=AdminPasoItem)
def update_paso(programa_id: int, paso_id: int, payload: AdminPasoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminPasoItem:
    affected = connection.execute(
        "UPDATE programa_pasos SET descripcion = ?, posicion = ?, observaciones = ? WHERE id = ? AND programa_id = ?",
        (payload.descripcion.strip(), payload.posicion, payload.observaciones, paso_id, programa_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Paso no encontrado.")
    connection.commit()
    row = connection.execute(
        "SELECT id, posicion, descripcion, COALESCE(observaciones,'') AS observaciones, COALESCE(adjunto_nombre,'') AS adjunto_nombre, COALESCE(adjunto_ruta,'') AS adjunto_ruta, activo FROM programa_pasos WHERE id = ?",
        (paso_id,),
    ).fetchone()
    return _paso_row_to_item(row)


@router.delete("/programas/{programa_id}/pasos/{paso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paso(programa_id: int, paso_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    row = connection.execute(
        "SELECT adjunto_ruta FROM programa_pasos WHERE id = ? AND programa_id = ?",
        (paso_id, programa_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Paso no encontrado.")
    ruta = str(row["adjunto_ruta"] or "")
    if ruta:
        p = Path(ruta)
        if p.exists():
            p.unlink()
    connection.execute("DELETE FROM programa_pasos WHERE id = ?", (paso_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/programas/{programa_id}/pasos/{paso_id}/adjunto", response_model=AdminPasoItem)
async def upload_paso_adjunto(
    programa_id: int,
    paso_id: int,
    _: AdminTecnicoDep,
    connection: ConnectionDep,
    archivo: UploadFile = File(...),
) -> AdminPasoItem:
    row = connection.execute(
        "SELECT id, adjunto_ruta FROM programa_pasos WHERE id = ? AND programa_id = ?",
        (paso_id, programa_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Paso no encontrado.")
    ruta_vieja = str(row["adjunto_ruta"] or "")
    if ruta_vieja:
        p = Path(ruta_vieja)
        if p.exists():
            p.unlink()
    folder = _paso_adjuntos_dir(paso_id)
    nombre = archivo.filename or f"adjunto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ruta = folder / nombre
    with ruta.open("wb") as f:
        shutil.copyfileobj(archivo.file, f)
    connection.execute(
        "UPDATE programa_pasos SET adjunto_nombre = ?, adjunto_ruta = ? WHERE id = ?",
        (nombre, str(ruta), paso_id),
    )
    connection.commit()
    updated = connection.execute(
        "SELECT id, posicion, descripcion, COALESCE(observaciones,'') AS observaciones, COALESCE(adjunto_nombre,'') AS adjunto_nombre, COALESCE(adjunto_ruta,'') AS adjunto_ruta, activo FROM programa_pasos WHERE id = ?",
        (paso_id,),
    ).fetchone()
    return _paso_row_to_item(updated)


@router.delete("/programas/{programa_id}/pasos/{paso_id}/adjunto", response_model=AdminPasoItem)
def delete_paso_adjunto(programa_id: int, paso_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminPasoItem:
    row = connection.execute(
        "SELECT id, adjunto_ruta FROM programa_pasos WHERE id = ? AND programa_id = ?",
        (paso_id, programa_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Paso no encontrado.")
    ruta = str(row["adjunto_ruta"] or "")
    if ruta:
        p = Path(ruta)
        if p.exists():
            p.unlink()
    connection.execute(
        "UPDATE programa_pasos SET adjunto_nombre = '', adjunto_ruta = '' WHERE id = ?",
        (paso_id,),
    )
    connection.commit()
    updated = connection.execute(
        "SELECT id, posicion, descripcion, COALESCE(observaciones,'') AS observaciones, COALESCE(adjunto_nombre,'') AS adjunto_nombre, COALESCE(adjunto_ruta,'') AS adjunto_ruta, activo FROM programa_pasos WHERE id = ?",
        (paso_id,),
    ).fetchone()
    return _paso_row_to_item(updated)


@router.get("/programas/{programa_id}/pasos/{paso_id}/adjunto")
def ver_paso_adjunto(programa_id: int, paso_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> FileResponse:
    row = connection.execute(
        "SELECT adjunto_nombre, adjunto_ruta FROM programa_pasos WHERE id = ? AND programa_id = ?",
        (paso_id, programa_id),
    ).fetchone()
    if row is None or not str(row["adjunto_ruta"] or ""):
        raise HTTPException(status_code=404, detail="Sin adjunto.")
    path = Path(str(row["adjunto_ruta"]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="El archivo no existe en disco.")
    return FileResponse(path, filename=str(row["adjunto_nombre"] or path.name))


# ── Repuestos ─────────────────────────────────────────────────────────────────

def _repuesto_row_to_item(row: sqlite3.Row) -> AdminRepuestoItem:
    return AdminRepuestoItem(
        id=int(row["id"]),
        nombre=str(row["nombre"] or ""),
        observaciones=str(row["observaciones"] or ""),
        stock_actual=float(row["stock_actual"] or 0),
        stock_minimo=float(row["stock_minimo"] or 0),
        activo=bool(row["activo"]),
    )


@router.get("/repuestos", response_model=list[AdminRepuestoItem])
def list_repuestos_admin(_: AdminTecnicoDep, connection: ConnectionDep) -> list[AdminRepuestoItem]:
    rows = connection.execute(
        "SELECT id, nombre, COALESCE(observaciones,'') AS observaciones, stock_actual, stock_minimo, activo FROM repuestos ORDER BY nombre"
    ).fetchall()
    return [_repuesto_row_to_item(r) for r in rows]


@router.post("/repuestos", response_model=AdminRepuestoItem, status_code=status.HTTP_201_CREATED)
def create_repuesto(payload: AdminRepuestoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminRepuestoItem:
    cur = connection.execute(
        "INSERT INTO repuestos (nombre, observaciones, stock_actual, stock_minimo, activo) VALUES (?, ?, ?, ?, ?)",
        (payload.nombre.strip(), payload.observaciones, payload.stock_actual, payload.stock_minimo, int(payload.activo)),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id, nombre, COALESCE(observaciones,'') AS observaciones, stock_actual, stock_minimo, activo FROM repuestos WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    return _repuesto_row_to_item(row)


@router.put("/repuestos/{repuesto_id}", response_model=AdminRepuestoItem)
def update_repuesto(repuesto_id: int, payload: AdminRepuestoRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminRepuestoItem:
    affected = connection.execute(
        """UPDATE repuestos SET nombre=?, observaciones=?, stock_actual=?, stock_minimo=?, activo=?,
           actualizado_en=CURRENT_TIMESTAMP WHERE id=?""",
        (payload.nombre.strip(), payload.observaciones, payload.stock_actual, payload.stock_minimo,
         int(payload.activo), repuesto_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado.")
    connection.commit()
    row = connection.execute(
        "SELECT id, nombre, COALESCE(observaciones,'') AS observaciones, stock_actual, stock_minimo, activo FROM repuestos WHERE id = ?",
        (repuesto_id,),
    ).fetchone()
    return _repuesto_row_to_item(row)


@router.delete("/repuestos/{repuesto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repuesto(repuesto_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    affected = connection.execute("DELETE FROM repuestos WHERE id = ?", (repuesto_id,)).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado.")
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Técnicos ──────────────────────────────────────────────────────────────────

def _tecnico_row_to_item(row: sqlite3.Row) -> AdminTecnicoItem:
    return AdminTecnicoItem(
        id=int(row["id"]),
        nombre=str(row["nombre"] or ""),
        apellido=str(row["apellido"] or ""),
        legajo=str(row["legajo"] or ""),
        telefono=str(row["telefono"] or ""),
        especialidad=str(row["especialidad"] or ""),
        activo=bool(row["activo"]),
    )

_TECNICO_SELECT = "SELECT id, nombre, apellido, legajo, telefono, especialidad, activo FROM tecnicos"


@router.get("/tecnicos", response_model=list[AdminTecnicoItem])
def list_tecnicos_admin(_: AdminTecnicoDep, connection: ConnectionDep) -> list[AdminTecnicoItem]:
    rows = connection.execute(_TECNICO_SELECT + " ORDER BY apellido, nombre").fetchall()
    return [_tecnico_row_to_item(r) for r in rows]


@router.post("/tecnicos", response_model=AdminTecnicoItem, status_code=status.HTTP_201_CREATED)
def create_tecnico(payload: AdminTecnicoCreate, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminTecnicoItem:
    cur = connection.execute(
        "INSERT INTO tecnicos (nombre, apellido, legajo, telefono, especialidad, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (payload.nombre.strip(), payload.apellido.strip(), payload.legajo.strip(),
         payload.telefono, payload.especialidad, hash_password(payload.password)),
    )
    connection.commit()
    row = connection.execute(_TECNICO_SELECT + " WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _tecnico_row_to_item(row)


@router.put("/tecnicos/{tecnico_id}", response_model=AdminTecnicoItem)
def update_tecnico(tecnico_id: int, payload: AdminTecnicoUpdate, _: AdminTecnicoDep, connection: ConnectionDep) -> AdminTecnicoItem:
    affected = connection.execute(
        "UPDATE tecnicos SET nombre=?, apellido=?, legajo=?, telefono=?, especialidad=?, activo=? WHERE id=?",
        (payload.nombre.strip(), payload.apellido.strip(), payload.legajo.strip(),
         payload.telefono, payload.especialidad, int(payload.activo), tecnico_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Técnico no encontrado.")
    connection.commit()
    row = connection.execute(_TECNICO_SELECT + " WHERE id = ?", (tecnico_id,)).fetchone()
    return _tecnico_row_to_item(row)


@router.delete("/tecnicos/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tecnico(tecnico_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    affected = connection.execute("DELETE FROM tecnicos WHERE id = ?", (tecnico_id,)).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Técnico no encontrado.")
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tecnicos/{tecnico_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def set_tecnico_password(tecnico_id: int, payload: SetPasswordRequest, current: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    row = connection.execute(
        "SELECT id, es_admin FROM tecnicos WHERE id = ?", (tecnico_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Técnico no encontrado.")
    if bool(row["es_admin"]) and tecnico_id != current.id:
        raise HTTPException(status_code=403, detail="No podés cambiar la contraseña de otro administrador.")
    connection.execute(
        "UPDATE tecnicos SET password_hash = ? WHERE id = ?",
        (hash_password(payload.password), tecnico_id),
    )
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Órdenes de Trabajo ────────────────────────────────────────────────────────

@router.get("/ordenes", response_model=list[OrdenCard])
def list_ordenes_admin(_: AdminTecnicoDep, connection: ConnectionDep) -> list[OrdenCard]:
    query = _base_query() + """
        ORDER BY
            CASE o.estado WHEN 'PENDIENTE' THEN 0 WHEN 'EN_PROGRESO' THEN 1 ELSE 2 END,
            o.fecha_apertura DESC, o.id DESC
    """
    rows = connection.execute(query).fetchall()
    return [_card_from_row(r) for r in rows]


@router.put("/ordenes/{orden_id}", response_model=OrdenDetail)
def update_orden_admin(orden_id: int, payload: AdminOrdenRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> OrdenDetail:
    affected = connection.execute(
        """UPDATE ordenes_trabajo SET equipo_id=?, tipo=?, descripcion=?, fecha_apertura=?,
           fecha_cierre=?, estado=?, tecnico_id=?, costo_mano_obra=?, observaciones=?,
           actualizado_en=CURRENT_TIMESTAMP WHERE id=?""",
        (payload.equipo_id, payload.tipo, payload.descripcion, payload.fecha_apertura,
         payload.fecha_cierre, payload.estado, payload.tecnico_id, payload.costo_mano_obra,
         payload.observaciones, orden_id),
    ).rowcount
    if not affected:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    connection.commit()
    orden = _get_orden_detail(connection, orden_id)
    if orden is None:
        raise HTTPException(status_code=500, detail="Error interno al recuperar la orden.")
    return orden


@router.delete("/ordenes/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_orden_admin(orden_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    row = connection.execute("SELECT id FROM ordenes_trabajo WHERE id = ?", (orden_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    # Restaurar stock de repuestos antes de eliminar
    rep_rows = connection.execute(
        "SELECT repuesto_id, cantidad FROM repuestos_orden WHERE orden_id = ? AND repuesto_id IS NOT NULL",
        (orden_id,),
    ).fetchall()
    for rep in rep_rows:
        connection.execute(
            "UPDATE repuestos SET stock_actual = stock_actual + ? WHERE id = ?",
            (float(rep["cantidad"]), int(rep["repuesto_id"])),
        )
    connection.execute("DELETE FROM ordenes_trabajo WHERE id = ?", (orden_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
