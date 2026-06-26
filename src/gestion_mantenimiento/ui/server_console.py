from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
)


class _OutputReader(QThread):
    """Lee stdout del proceso servidor línea a línea y emite señales al hilo principal."""

    line_received: Signal = Signal(str)

    def __init__(self, process: subprocess.Popen) -> None:
        super().__init__()
        self._process = process

    def run(self) -> None:
        try:
            assert self._process.stdout is not None
            for raw in iter(self._process.stdout.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip()
                if line:
                    self.line_received.emit(line)
        except Exception:
            pass


class ServerConsoleWindow(QWidget):
    """Ventana que muestra los logs del servidor uvicorn en tiempo real."""

    PORT = 54321

    def __init__(
        self,
        process: "subprocess.Popen | None",
        port: int = 54321,
        database_path: "Path | None" = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.PORT = port
        self._database_path = database_path
        self._reader: _OutputReader | None = None

        self.setWindowTitle(f"Servidor — Puerto {port}")
        self.resize(780, 460)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barra superior ────────────────────────────────────────────────────
        bar = QWidget()
        bar.setStyleSheet("background:#161b22;border-bottom:1px solid #30363d;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)

        self._status_label = QLabel(f"\U0001f5a5  Servidor API  ·  http://0.0.0.0:{port}  ·  http://192.168.100.228:{port}")
        self._status_label.setStyleSheet("color:#58a6ff;font-weight:bold;font-size:12px;background:transparent;")
        bar_layout.addWidget(self._status_label, stretch=1)

        btn_reload = QPushButton("↺  Reiniciar servidor")
        btn_reload.setStyleSheet(
            "QPushButton {"
            "  background:#21262d;color:#c9d1d9;border:1px solid #30363d;"
            "  border-radius:6px;padding:4px 14px;font-size:12px;"
            "}"
            "QPushButton:hover { background:#30363d; }"
            "QPushButton:pressed { background:#161b22; }"
        )
        btn_reload.clicked.connect(self._restart_server)
        bar_layout.addWidget(btn_reload)

        root.addWidget(bar)

        # ── Consola ───────────────────────────────────────────────────────────
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        font_family = "Consolas" if sys.platform == "win32" else "Monospace"
        self._console.setFont(QFont(font_family, 10))
        self._console.setStyleSheet(
            "QTextEdit {"
            "  background-color:#0d1117;color:#c9d1d9;"
            "  border:none;padding:8px 12px;"
            "  selection-background-color:#264f78;"
            "}"
        )
        root.addWidget(self._console)

        self._attach_process(process)

    # ── Proceso ───────────────────────────────────────────────────────────────

    def _attach_process(self, process: "subprocess.Popen | None") -> None:
        """Conecta un proceso al lector y arranca el hilo."""
        if process is not None:
            self._reader = _OutputReader(process)
            self._reader.line_received.connect(self._on_line)
            self._reader.start()
            self._append_system(f"Servidor iniciado — puerto {self.PORT}")
        else:
            self._reader = None
            self._append_error("No se encontró uvicorn. Verificá que el entorno virtual esté instalado.")

    def _restart_server(self) -> None:
        """Mata el proceso actual y arranca uno nuevo."""
        self._append_system("Reiniciando servidor…")

        # Detener lector anterior
        if self._reader is not None:
            self._reader.line_received.disconnect()
            self._reader.quit()
            self._reader.wait(2000)
            self._reader = None

        # Matar uvicorn anterior
        if sys.platform == "win32":
            try:
                subprocess.run(["taskkill", "/IM", "uvicorn.exe", "/F"], capture_output=True, timeout=5)
            except Exception:
                pass
        else:
            try:
                subprocess.run(["pkill", "-f", "uvicorn api.main"], capture_output=True, timeout=3)
                time.sleep(0.8)
            except Exception:
                pass

        # Arrancar proceso nuevo
        new_proc = _launch_uvicorn(self.PORT, self._database_path)
        self._console.clear()
        self._attach_process(new_proc)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_line(self, line: str) -> None:
        lower = line.lower()
        if "error" in lower or "exception" in lower or "critical" in lower:
            color = "#ff7b72"
        elif "warning" in lower or "warn" in lower:
            color = "#e3b341"
        elif "started" in lower or "application startup" in lower or "uvicorn running" in lower:
            color = "#7ee787"
        elif "info" in lower:
            color = "#79c0ff"
        else:
            color = "#c9d1d9"
        self._console.append(f'<span style="color:{color}">{_esc(line)}</span>')
        sb = self._console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _append_system(self, msg: str) -> None:
        self._console.append(f'<span style="color:#58a6ff">&#9654; {_esc(msg)}</span>')

    def _append_error(self, msg: str) -> None:
        self._console.append(f'<span style="color:#ff7b72">&#10006; {_esc(msg)}</span>')

    def closeEvent(self, event) -> None:  # type: ignore[override]
        event.ignore()
        self.hide()


# ── Helper para lanzar uvicorn ────────────────────────────────────────────────

def _launch_uvicorn(port: int = 54321, database_path: "Path | None" = None) -> "subprocess.Popen | None":
    """Encuentra y lanza uvicorn con stdout capturado. Retorna None si no lo encuentra."""
    repo_root = Path(__file__).resolve().parents[4]

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

    import os
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    if database_path is not None:
        env["DB_PATH"] = str(database_path)

    try:
        return subprocess.Popen(
            [str(uvicorn_exe), "api.main:app", "--host", "0.0.0.0",
             "--port", str(port), "--log-level", "info"],
            cwd=str(repo_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except OSError:
        return None


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
