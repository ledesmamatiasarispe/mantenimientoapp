from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from api.auth import CurrentTecnicoDep
from api.database import get_db
from api.models import AlertaItem, SnoozeRequest

router = APIRouter(prefix="/api/alertas", tags=["alertas"])

ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


def _compute_alertas(connection: sqlite3.Connection) -> list[AlertaItem]:
    hoy = date.today().isoformat()
    alertas: list[AlertaItem] = []

    # Leer llaves ya silenciadas
    snoozed: set[str] = set()
    rows = connection.execute(
        "SELECT clave, avisar_nuevamente_desde FROM alertas_app"
    ).fetchall()
    for row in rows:
        if row["avisar_nuevamente_desde"] and row["avisar_nuevamente_desde"] > hoy:
            snoozed.add(str(row["clave"]))

    # 1. Stock bajo (compara stock_actual vs suma de mínimos por equipo)
    for rep in connection.execute(
        """
        SELECT r.id, r.nombre, r.stock_actual, SUM(re.stock_minimo) AS suma_min
        FROM repuestos r
        JOIN repuestos_equipo re ON re.repuesto_id = r.id
        WHERE r.activo = 1
        GROUP BY r.id, r.nombre, r.stock_actual
        HAVING r.stock_actual <= SUM(re.stock_minimo)
        """
    ).fetchall():
        key = f"stock_bajo_{rep['id']}"
        if key not in snoozed:
            alertas.append(AlertaItem(
                key=key, tipo="STOCK_BAJO",
                mensaje=f"Stock bajo: {rep['nombre']} ({rep['stock_actual']} / mín total {rep['suma_min']})",
                severidad="alta" if rep["stock_actual"] == 0 else "media",
            ))

    # 2. Órdenes nuevas pendientes sin técnico
    for ord_ in connection.execute(
        "SELECT id, equipo_id FROM ordenes_trabajo WHERE estado='PENDIENTE' AND tecnico_id IS NULL"
    ).fetchall():
        key = f"orden_nueva_{ord_['id']}"
        if key not in snoozed:
            eq = connection.execute("SELECT nombre FROM equipos WHERE id=?", (ord_["equipo_id"],)).fetchone()
            nombre_eq = eq["nombre"] if eq else "?"
            alertas.append(AlertaItem(
                key=key, tipo="ORDEN_NUEVA",
                mensaje=f"Orden #{ord_['id']} pendiente sin asignar — {nombre_eq}",
                severidad="media",
            ))

    # 3. Mantenimientos vencidos
    for prog in connection.execute(
        "SELECT id, equipo_id, descripcion, proxima_ejecucion FROM programas_mantenimiento WHERE activo=1 AND proxima_ejecucion < ?",
        (hoy,),
    ).fetchall():
        key = f"mant_vencido_{prog['id']}"
        if key not in snoozed:
            eq = connection.execute("SELECT nombre FROM equipos WHERE id=?", (prog["equipo_id"],)).fetchone()
            nombre_eq = eq["nombre"] if eq else "?"
            alertas.append(AlertaItem(
                key=key, tipo="MANT_VENCIDO",
                mensaje=f"Mantenimiento vencido: {prog['descripcion']} — {nombre_eq} (desde {prog['proxima_ejecucion'][:10]})",
                severidad="alta",
            ))

    return alertas


@router.get("", response_model=list[AlertaItem])
def get_alertas(_: CurrentTecnicoDep, connection: ConnectionDep) -> list[AlertaItem]:
    return _compute_alertas(connection)


@router.post("/{key}/snooze", status_code=status.HTTP_204_NO_CONTENT)
def snooze_alerta(key: str, payload: SnoozeRequest, _: CurrentTecnicoDep, connection: ConnectionDep) -> Response:
    hasta = (date.today() + timedelta(days=payload.dias)).isoformat()
    connection.execute(
        "INSERT INTO alertas_app (clave, avisar_nuevamente_desde, actualizado_en) VALUES (?,?,?) "
        "ON CONFLICT(clave) DO UPDATE SET avisar_nuevamente_desde=excluded.avisar_nuevamente_desde, actualizado_en=excluded.actualizado_en",
        (key, hasta, date.today().isoformat()),
    )
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{key}/ignorar", status_code=status.HTTP_204_NO_CONTENT)
def ignorar_alerta(key: str, _: CurrentTecnicoDep, connection: ConnectionDep) -> Response:
    hasta = "9999-12-31"
    connection.execute(
        "INSERT INTO alertas_app (clave, avisar_nuevamente_desde, actualizado_en) VALUES (?,?,?) "
        "ON CONFLICT(clave) DO UPDATE SET avisar_nuevamente_desde=excluded.avisar_nuevamente_desde, actualizado_en=excluded.actualizado_en",
        (key, hasta, date.today().isoformat()),
    )
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
