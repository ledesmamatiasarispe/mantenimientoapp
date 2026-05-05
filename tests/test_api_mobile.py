from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from api.auth import hash_password
from api.main import create_app
from gestion_mantenimiento.data.schema import initialize_database


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"legajo": "20111111", "password": "secreto123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.sqlite3"
    initialize_database(database_path, seed=True)
    monkeypatch.setenv("DB_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE tecnicos SET password_hash = ? WHERE id = 1",
            (hash_password("secreto123"),),
        )
        connection.commit()

    client = TestClient(create_app())
    response = client.post(
        "/api/auth/login",
        json={"legajo": "20111111", "password": "secreto123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["legajo"] == "20111111"


def test_orden_flow_accept_note_complete(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.sqlite3"
    initialize_database(database_path, seed=True)
    monkeypatch.setenv("DB_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE tecnicos SET password_hash = ? WHERE id = 1",
            (hash_password("secreto123"),),
        )
        connection.execute(
            """
            INSERT INTO ordenes_trabajo
                (id, equipo_id, tipo, descripcion, fecha_apertura, estado, observaciones)
            VALUES
                (1, 1, 'CORRECTIVO', 'Falla eléctrica', '2026-05-01', 'PENDIENTE', '')
            """
        )
        connection.execute(
            """
            INSERT INTO programas_mantenimiento
                (id, equipo_id, descripcion, frecuencia_meses, ultima_ejecucion, proxima_ejecucion)
            VALUES
                (1, 1, 'Inspección mensual', 1, '2026-04-01', '2026-05-01')
            """
        )
        connection.execute(
            "INSERT INTO orden_programas (orden_id, programa_id) VALUES (1, 1)"
        )
        connection.execute(
            """
            INSERT INTO programa_adjuntos (programa_id, tipo, nombre, ruta)
            VALUES (1, 'PDF', 'manual.pdf', 'C:/tmp/manual.pdf')
            """
        )
        connection.commit()

    client = TestClient(create_app())
    headers = _auth_headers(client)

    listar = client.get("/api/ordenes", headers=headers)
    assert listar.status_code == 200
    assert len(listar.json()) == 1

    aceptar = client.post("/api/ordenes/1/aceptar", headers=headers)
    assert aceptar.status_code == 200
    assert aceptar.json()["estado"] == "EN_PROGRESO"

    nota = client.post(
        "/api/ordenes/1/observaciones",
        headers=headers,
        json={"texto": "Revisado tablero"},
    )
    assert nota.status_code == 200
    assert "Revisado tablero" in nota.json()["observaciones"]

    completar = client.post(
        "/api/ordenes/1/completar",
        headers=headers,
        json={"observaciones": "Trabajo terminado"},
    )
    assert completar.status_code == 200
    assert completar.json()["estado"] == "COMPLETADA"
    assert "Trabajo terminado" in completar.json()["observaciones"]


def test_biblioteca_endpoints(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "test.sqlite3"
    initialize_database(database_path, seed=True)
    monkeypatch.setenv("DB_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE tecnicos SET password_hash = ? WHERE id = 1",
            (hash_password("secreto123"),),
        )
        connection.execute(
            """
            INSERT INTO programas_mantenimiento
                (id, equipo_id, descripcion, frecuencia_meses, ultima_ejecucion, proxima_ejecucion)
            VALUES
                (1, 1, 'Cambio de filtro', 2, '2026-03-01', '2026-05-01')
            """
        )
        connection.commit()

    client = TestClient(create_app())
    headers = _auth_headers(client)

    equipos = client.get("/api/equipos", headers=headers)
    assert equipos.status_code == 200
    assert len(equipos.json()) >= 1

    equipo = client.get("/api/equipos/1", headers=headers)
    assert equipo.status_code == 200
    assert equipo.json()["id"] == 1

    programa = client.get("/api/programas/1", headers=headers)
    assert programa.status_code == 200
    assert programa.json()["descripcion"] == "Cambio de filtro"
