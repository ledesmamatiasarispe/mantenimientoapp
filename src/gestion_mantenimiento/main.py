from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

from gestion_mantenimiento import __version__
from gestion_mantenimiento.data.paths import get_app_data_dir


def _write_startup_error(error: BaseException) -> None:
    try:
        log_path = get_app_data_dir() / "startup-error.log"
    except Exception:
        log_path = Path.home() / "gestion-mantenimiento-startup-error.log"

    log_path.write_text(
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        encoding="utf-8",
    )


def main() -> int:
    if "--version" in sys.argv:
        print(__version__)
        return 0

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QStyleFactory

    from gestion_mantenimiento.data.paths import get_database_path, get_theme_path
    from gestion_mantenimiento.data.schema import initialize_database
    from gestion_mantenimiento.ui.main_window import MainWindow
    from gestion_mantenimiento.ui.theme import (
        build_app_palette,
        build_app_styles,
        get_theme,
        load_theme_colors,
        load_theme_mode,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Gestion Mantenimiento")
    app.setOrganizationName("Mantenimiento")
    app.setStyle(QStyleFactory.create("Fusion"))

    database_path = get_database_path()
    initialize_database(database_path, seed=False)

    theme_path = get_theme_path()
    mode = load_theme_mode(theme_path)
    theme = load_theme_colors(theme_path, get_theme(mode))
    app.setStyleSheet(build_app_styles(theme))
    app.setPalette(build_app_palette(theme))

    window = MainWindow(database_path, theme_mode=mode, initial_theme=theme)
    window.show()

    server_proc = _start_api_server(database_path)
    from gestion_mantenimiento.ui.server_console import ServerConsoleWindow
    console = ServerConsoleWindow(server_proc)  # muestra aunque proc sea None
    console.show()
    # Guardar en app para evitar garbage collection
    app._server_console = console  # type: ignore[attr-defined]

    return app.exec()


def _start_api_server(database_path: Path) -> "subprocess.Popen | None":
    """Arranca la API REST en background en el puerto 54321.

    Retorna el proceso para que el llamador pueda leer su stdout.
    """
    repo_root = Path(__file__).resolve().parents[2]

    if sys.platform == "win32":
        candidates = [
            repo_root / ".venv" / "Scripts" / "uvicorn.exe",
            Path(sys.executable).parent / "uvicorn.exe",
        ]
    else:
        candidates = [
            repo_root / ".venv" / "bin" / "uvicorn",
            Path(sys.executable).parent / "uvicorn",
        ]

    uvicorn_exe = next((p for p in candidates if p.exists()), None)
    if uvicorn_exe is None:
        return None

    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/IM", "uvicorn.exe", "/F"],
                capture_output=True, timeout=5,
            )
        except Exception:
            pass
    else:
        # Linux/Mac: matar instancias previas de uvicorn para liberar el puerto
        try:
            subprocess.run(
                ["pkill", "-f", "uvicorn api.main"],
                capture_output=True, timeout=3,
            )
            import time; time.sleep(0.8)  # esperar que libere el puerto
        except Exception:
            pass

    # PYTHONUNBUFFERED=1 garantiza output sin buffering
    env = {**os.environ, "DB_PATH": str(database_path), "PYTHONUNBUFFERED": "1"}
    try:
        return subprocess.Popen(
            [str(uvicorn_exe), "api.main:app", "--host", "0.0.0.0", "--port", "54321",
             "--log-level", "info"],
            cwd=str(repo_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # stderr va al mismo pipe que stdout
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except OSError:
        return None


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        _write_startup_error(exc)
        raise
