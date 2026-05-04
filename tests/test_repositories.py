from __future__ import annotations

from pathlib import Path

import pytest

from gestion_mantenimiento.data.models import OrdenTrabajoCreate
from gestion_mantenimiento.data.repositories import (
    EquipoRepository,
    OrdenTrabajoRepository,
    ProgramaMantenimientoRepository,
    TecnicoRepository,
    TipoEquipoRepository,
)
from gestion_mantenimiento.data.schema import initialize_database


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.sqlite3"
    initialize_database(path, seed=True)
    return path


def test_tipo_equipo_list(db_path: Path) -> None:
    repo = TipoEquipoRepository(db_path)
    tipos = repo.list_all()
    assert len(tipos) >= 5
    assert all(t.activo for t in tipos)


def test_tipo_equipo_create_update_delete(db_path: Path) -> None:
    repo = TipoEquipoRepository(db_path)
    tipo_id = repo.create("Neumático")
    tipos = repo.list_all()
    nombres = [t.nombre for t in tipos]
    assert "Neumático" in nombres

    repo.update(tipo_id, "Neumático v2", True)
    tipos = repo.list_all()
    assert any(t.nombre == "Neumático v2" for t in tipos)

    repo.delete(tipo_id)
    tipos = repo.list_all()
    assert not any(t.nombre == "Neumático v2" for t in tipos)


def test_equipo_create_and_list(db_path: Path) -> None:
    repo = EquipoRepository(db_path)
    tipo_repo = TipoEquipoRepository(db_path)
    tipo_id = tipo_repo.list_all()[0].id

    equipo_id = repo.create(
        "Bomba hidráulica", tipo_id, "SN-001", "Parker", "P31", "Planta A", "2024-01-01", ""
    )
    equipos = repo.list_all()
    assert any(e.id == equipo_id for e in equipos)


def test_equipo_search(db_path: Path) -> None:
    repo = EquipoRepository(db_path)
    results = repo.list_all(search="Compre")
    assert any("Compresor" in e.nombre for e in results)


def test_equipo_update(db_path: Path) -> None:
    repo = EquipoRepository(db_path)
    equipos = repo.list_all()
    eq = equipos[0]
    repo.update(eq.id, "Nuevo nombre", eq.tipo_id, eq.numero_serie, eq.marca,
                eq.modelo, eq.ubicacion, eq.fecha_adquisicion, eq.observaciones, True)
    updated = repo.get_by_id(eq.id)
    assert updated is not None
    assert updated.nombre == "Nuevo nombre"


def test_tecnico_create_and_list(db_path: Path) -> None:
    repo = TecnicoRepository(db_path)
    tecnico_id = repo.create("Ana", "Rodríguez", "30444444", "3516000099", "Soldadura")
    tecnicos = repo.list_all()
    assert any(t.id == tecnico_id for t in tecnicos)


def test_orden_create_and_list(db_path: Path) -> None:
    equipo_repo = EquipoRepository(db_path)
    orden_repo = OrdenTrabajoRepository(db_path)
    equipo = equipo_repo.list_all()[0]

    data = OrdenTrabajoCreate(
        equipo_id=equipo.id,
        tipo="PREVENTIVO",
        descripcion="Cambio de aceite",
        fecha_apertura="2026-05-01",
        fecha_cierre="",
        estado="PENDIENTE",
        tecnico_id=None,
        costo_mano_obra=15000.0,
        observaciones="",
    )
    orden_id = orden_repo.create(data)
    ordenes = orden_repo.list_all()
    assert any(o.id == orden_id for o in ordenes)


def test_orden_count_by_estado(db_path: Path) -> None:
    orden_repo = OrdenTrabajoRepository(db_path)
    counts = orden_repo.count_by_estado()
    assert isinstance(counts, dict)


def test_programa_create_and_list(db_path: Path) -> None:
    equipo_repo = EquipoRepository(db_path)
    prog_repo = ProgramaMantenimientoRepository(db_path)
    equipo = equipo_repo.list_all()[0]

    prog_id = prog_repo.create(equipo.id, "Lubricación mensual", 30, "2026-04-01", "2026-05-01")
    programas = prog_repo.list_all()
    assert any(p.id == prog_id for p in programas)
