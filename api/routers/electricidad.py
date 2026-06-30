from __future__ import annotations

import sqlite3
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.auth import AdminTecnicoDep
from api.database import get_db
from api.models import (
    FacturaElectricaItem,
    FacturaElectricaRequest,
    GraficoElectricidad,
    GraficoPunto,
    MedidorItem,
    MedidorRequest,
)

router = APIRouter(prefix="/api/admin/electricidad", tags=["electricidad"])

ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


# ── Medidores ─────────────────────────────────────────────────────────────────

def _medidor_row(row: sqlite3.Row) -> MedidorItem:
    return MedidorItem(
        id=int(row["id"]),
        nombre=str(row["nombre"]),
        nro_medidor=str(row["nro_medidor"] or ""),
        nro_cliente=str(row["nro_cliente"] or ""),
        descripcion=str(row["descripcion"] or ""),
        activo=bool(row["activo"]),
    )


@router.get("/medidores", response_model=list[MedidorItem])
def list_medidores(_: AdminTecnicoDep, connection: ConnectionDep) -> list[MedidorItem]:
    rows = connection.execute("SELECT * FROM medidores ORDER BY nombre").fetchall()
    return [_medidor_row(r) for r in rows]


@router.post("/medidores", response_model=MedidorItem, status_code=status.HTTP_201_CREATED)
def create_medidor(payload: MedidorRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> MedidorItem:
    hoy = date.today().isoformat()
    connection.execute(
        "INSERT INTO medidores (nombre, nro_medidor, nro_cliente, descripcion, activo, creado_en) VALUES (?,?,?,?,?,?)",
        (payload.nombre, payload.nro_medidor, payload.nro_cliente, payload.descripcion, 1 if payload.activo else 0, hoy),
    )
    row_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.commit()
    row = connection.execute("SELECT * FROM medidores WHERE id=?", (row_id,)).fetchone()
    return _medidor_row(row)


@router.put("/medidores/{medidor_id}", response_model=MedidorItem)
def update_medidor(medidor_id: int, payload: MedidorRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> MedidorItem:
    if not connection.execute("SELECT id FROM medidores WHERE id=?", (medidor_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Medidor no encontrado.")
    connection.execute(
        "UPDATE medidores SET nombre=?, nro_medidor=?, nro_cliente=?, descripcion=?, activo=? WHERE id=?",
        (payload.nombre, payload.nro_medidor, payload.nro_cliente, payload.descripcion, 1 if payload.activo else 0, medidor_id),
    )
    connection.commit()
    return _medidor_row(connection.execute("SELECT * FROM medidores WHERE id=?", (medidor_id,)).fetchone())


@router.delete("/medidores/{medidor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medidor(medidor_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    connection.execute("DELETE FROM medidores WHERE id=?", (medidor_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Facturas ──────────────────────────────────────────────────────────────────

def _factura_row(row: sqlite3.Row) -> FacturaElectricaItem:
    return FacturaElectricaItem(
        id=int(row["id"]),
        medidor_id=int(row["medidor_id"]),
        periodo=str(row["periodo"] or ""),
        tipo_tarifa=str(row["tipo_tarifa"] or ""),
        fecha_factura=str(row["fecha_factura"] or ""),
        kwh_punta=float(row["kwh_punta"] or 0),
        kwh_valle_noc=float(row["kwh_valle_noc"] or 0),
        kwh_restantes=float(row["kwh_restantes"] or 0),
        kvar_reactiva=float(row["kvar_reactiva"] or 0),
        drp_kw=float(row["drp_kw"] or 0),
        drfp_kw=float(row["drfp_kw"] or 0),
        importe=float(row["importe"] or 0),
        observaciones=str(row["observaciones"] or ""),
    )


@router.get("/medidores/{medidor_id}/facturas", response_model=list[FacturaElectricaItem])
def list_facturas(medidor_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> list[FacturaElectricaItem]:
    rows = connection.execute(
        "SELECT * FROM facturas_electricas WHERE medidor_id=? ORDER BY periodo DESC",
        (medidor_id,),
    ).fetchall()
    return [_factura_row(r) for r in rows]


@router.post("/medidores/{medidor_id}/facturas", response_model=FacturaElectricaItem, status_code=status.HTTP_201_CREATED)
def create_factura(medidor_id: int, payload: FacturaElectricaRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> FacturaElectricaItem:
    hoy = date.today().isoformat()
    connection.execute(
        """INSERT INTO facturas_electricas
           (medidor_id, periodo, tipo_tarifa, fecha_factura,
            kwh_punta, kwh_valle_noc, kwh_restantes, kvar_reactiva,
            drp_kw, drfp_kw, cap_convenida_kw, cap_adquirida_kw,
            tangente_fi, cargo_fijo, importe, observaciones,
            creado_en, actualizado_en)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (medidor_id, payload.periodo, payload.tipo_tarifa, payload.fecha_factura,
         payload.kwh_punta, payload.kwh_valle_noc, payload.kwh_restantes, payload.kvar_reactiva,
         payload.drp_kw, payload.drfp_kw, payload.cap_convenida_kw, payload.cap_adquirida_kw,
         payload.tangente_fi, payload.cargo_fijo, payload.importe, payload.observaciones,
         hoy, hoy),
    )
    row_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.commit()
    return _factura_row(connection.execute("SELECT * FROM facturas_electricas WHERE id=?", (row_id,)).fetchone())


@router.put("/medidores/{medidor_id}/facturas/{factura_id}", response_model=FacturaElectricaItem)
def update_factura(medidor_id: int, factura_id: int, payload: FacturaElectricaRequest, _: AdminTecnicoDep, connection: ConnectionDep) -> FacturaElectricaItem:
    if not connection.execute("SELECT id FROM facturas_electricas WHERE id=? AND medidor_id=?", (factura_id, medidor_id)).fetchone():
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    hoy = date.today().isoformat()
    connection.execute(
        """UPDATE facturas_electricas SET
           periodo=?, tipo_tarifa=?, fecha_factura=?,
           kwh_punta=?, kwh_valle_noc=?, kwh_restantes=?, kvar_reactiva=?,
           drp_kw=?, drfp_kw=?, cap_convenida_kw=?, cap_adquirida_kw=?,
           tangente_fi=?, cargo_fijo=?, importe=?, observaciones=?, actualizado_en=?
           WHERE id=?""",
        (payload.periodo, payload.tipo_tarifa, payload.fecha_factura,
         payload.kwh_punta, payload.kwh_valle_noc, payload.kwh_restantes, payload.kvar_reactiva,
         payload.drp_kw, payload.drfp_kw, payload.cap_convenida_kw, payload.cap_adquirida_kw,
         payload.tangente_fi, payload.cargo_fijo, payload.importe, payload.observaciones, hoy,
         factura_id),
    )
    connection.commit()
    return _factura_row(connection.execute("SELECT * FROM facturas_electricas WHERE id=?", (factura_id,)).fetchone())


@router.delete("/medidores/{medidor_id}/facturas/{factura_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_factura(medidor_id: int, factura_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> Response:
    connection.execute("DELETE FROM facturas_electricas WHERE id=? AND medidor_id=?", (factura_id, medidor_id))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Gráficos ──────────────────────────────────────────────────────────────────

@router.get("/medidores/{medidor_id}/graficos", response_model=GraficoElectricidad)
def get_graficos(medidor_id: int, _: AdminTecnicoDep, connection: ConnectionDep) -> GraficoElectricidad:
    rows = connection.execute(
        """SELECT periodo,
                  kwh_punta + kwh_valle_noc + kwh_restantes AS kwh_total,
                  drp_kw,
                  CASE WHEN tangente_fi > 0
                       THEN ROUND(1.0 / SQRT(1 + tangente_fi * tangente_fi), 3)
                       ELSE 1.0 END AS cos_fi,
                  kvar_reactiva,
                  importe
           FROM facturas_electricas
           WHERE medidor_id=?
           ORDER BY periodo""",
        (medidor_id,),
    ).fetchall()

    return GraficoElectricidad(
        consumo_kwh=[GraficoPunto(periodo=r["periodo"], valor=float(r["kwh_total"] or 0)) for r in rows],
        demanda_kw=[GraficoPunto(periodo=r["periodo"], valor=float(r["drp_kw"] or 0)) for r in rows],
        factor_potencia=[GraficoPunto(periodo=r["periodo"], valor=float(r["cos_fi"] or 1)) for r in rows],
        energia_reactiva=[GraficoPunto(periodo=r["periodo"], valor=float(r["kvar_reactiva"] or 0)) for r in rows],
        costo_total=[GraficoPunto(periodo=r["periodo"], valor=float(r["importe"] or 0)) for r in rows],
    )
