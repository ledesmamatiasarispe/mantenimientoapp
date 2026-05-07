from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.database import get_db
from api.models import LoginRequest, TecnicoPublic, TokenResponse

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8
JWT_SECRET = os.environ.get("JWT_SECRET", "gestion-mantenimiento-dev-secret")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
router = APIRouter(prefix="/api/auth", tags=["auth"])

TokenDep = Annotated[str, Depends(oauth2_scheme)]
ConnectionDep = Annotated[sqlite3.Connection, Depends(get_db)]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash.strip():
        return False
    return pwd_context.verify(plain_password, password_hash)


def _serialize_tecnico(row: sqlite3.Row) -> TecnicoPublic:
    return TecnicoPublic(
        id=int(row["id"]),
        nombre=str(row["nombre"]),
        apellido=str(row["apellido"]),
        legajo=str(row["legajo"] or ""),
        telefono=str(row["telefono"] or ""),
        especialidad=str(row["especialidad"] or ""),
        es_admin=bool(row["es_admin"]) if "es_admin" in row.keys() else False,
    )


def authenticate_tecnico(
    connection: sqlite3.Connection,
    *,
    legajo: str,
    password: str,
) -> TecnicoPublic | None:
    row = connection.execute(
        """
        SELECT
            id,
            nombre,
            apellido,
            legajo,
            telefono,
            especialidad,
            es_admin,
            password_hash,
            activo
        FROM tecnicos
        WHERE legajo = ?
        """,
        (legajo.strip(),),
    ).fetchone()
    if row is None or not bool(row["activo"]):
        return None
    if not verify_password(password, str(row["password_hash"] or "")):
        return None
    return _serialize_tecnico(row)


def create_access_token(*, tecnico: TecnicoPublic) -> str:
    expires_at = datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(tecnico.id),
        "nombre_completo": tecnico.nombre_completo,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_current_tecnico(token: TokenDep, connection: ConnectionDep) -> TecnicoPublic:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        tecnico_id = int(payload.get("sub", ""))
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc

    row = connection.execute(
        """
        SELECT id, nombre, apellido, legajo, telefono, especialidad, es_admin, activo
        FROM tecnicos
        WHERE id = ?
        """,
        (tecnico_id,),
    ).fetchone()
    if row is None or not bool(row["activo"]):
        raise credentials_error
    return _serialize_tecnico(row)


CurrentTecnicoDep = Annotated[TecnicoPublic, Depends(get_current_tecnico)]


def _require_admin(current: CurrentTecnicoDep) -> TecnicoPublic:
    if not current.es_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso de administrador requerido.",
        )
    return current


AdminTecnicoDep = Annotated[TecnicoPublic, Depends(_require_admin)]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, connection: ConnectionDep) -> TokenResponse:
    tecnico = authenticate_tecnico(
        connection,
        legajo=payload.legajo,
        password=payload.password,
    )
    if tecnico is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    if not tecnico.es_admin:
        hay_admins = connection.execute(
            "SELECT 1 FROM tecnicos WHERE es_admin = 1 AND activo = 1 LIMIT 1"
        ).fetchone()
        if hay_admins is None:
            connection.execute(
                "UPDATE tecnicos SET es_admin = 1 WHERE id = ?", (tecnico.id,)
            )
            connection.commit()
            tecnico = tecnico.model_copy(update={"es_admin": True})
    return TokenResponse(
        access_token=create_access_token(tecnico=tecnico),
        token_type="bearer",
        tecnico=tecnico,
    )


@router.get("/me", response_model=TecnicoPublic)
def me(current_tecnico: CurrentTecnicoDep) -> TecnicoPublic:
    return current_tecnico

