from __future__ import annotations

from getpass import getpass

from api.auth import hash_password
from api.database import create_connection, initialize_api_database, resolve_database_path


def main() -> int:
    database_path = initialize_api_database()
    print(f"Base de datos: {database_path}")
    connection = create_connection()
    try:
        rows = connection.execute(
            """
            SELECT id, nombre, apellido, legajo
            FROM tecnicos
            WHERE activo = 1
            ORDER BY apellido, nombre
            """
        ).fetchall()
        if not rows:
            print("No hay técnicos activos.")
            return 0
        for row in rows:
            nombre = f'{row["nombre"]} {row["apellido"]}'.strip()
            print(f'\nTécnico #{row["id"]} - {nombre} (DNI {row["legajo"]})')
            while True:
                password = getpass("Nueva contraseña: ").strip()
                if not password:
                    print("La contraseña no puede estar vacía.")
                    continue
                confirm = getpass("Confirmar contraseña: ").strip()
                if password != confirm:
                    print("Las contraseñas no coinciden.")
                    continue
                connection.execute(
                    "UPDATE tecnicos SET password_hash = ? WHERE id = ?",
                    (hash_password(password), row["id"]),
                )
                connection.commit()
                break
    finally:
        connection.close()
    print(f"\nContraseñas actualizadas en {resolve_database_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
