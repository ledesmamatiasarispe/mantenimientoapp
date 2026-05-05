from __future__ import annotations

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
    theme = get_theme(mode)
    app.setStyleSheet(build_app_styles(theme))
    app.setPalette(build_app_palette(theme))

    window = MainWindow(database_path, theme_mode=mode)
    window.show()

    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        _write_startup_error(exc)
        raise
