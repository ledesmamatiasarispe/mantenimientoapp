from __future__ import annotations

import subprocess
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class _OutputReader(QThread):
    """Lee stdout del proceso servidor línea a línea y emite señales al hilo principal."""

    line_received: Signal = Signal(str)

    def __init__(self, process: subprocess.Popen) -> None:
        super().__init__()
        self._process = process
        self.setDaemon(True)

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

    def __init__(self, process: "subprocess.Popen | None", port: int = 54321, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._process = process
        self.setWindowTitle(f"Servidor — Puerto {port}")
        self.resize(780, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de título
        header = QLabel(f"  \U0001f5a5  Servidor API  ·  http://0.0.0.0:{port}  ·  http://192.168.100.228:{port}")
        header.setStyleSheet(
            "background:#161b22;color:#58a6ff;padding:8px 12px;"
            "font-weight:bold;font-size:12px;border-bottom:1px solid #30363d;"
        )
        layout.addWidget(header)

        # Área de consola
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        font_family = "Consolas" if sys.platform == "win32" else "Monospace"
        self._console.setFont(QFont(font_family, 10))
        self._console.setStyleSheet(
            "QTextEdit {"
            "  background-color:#0d1117;"
            "  color:#c9d1d9;"
            "  border:none;"
            "  padding:8px 12px;"
            "  selection-background-color:#264f78;"
            "}"
        )
        layout.addWidget(self._console)

        if process is not None:
            self._reader: _OutputReader | None = _OutputReader(process)
            self._reader.line_received.connect(self._on_line)
            self._reader.start()
            self._append_system("Servidor iniciado — escuchando en el puerto " + str(port))
        else:
            self._reader = None
            self._append_error("No se encontró el ejecutable de uvicorn. Verificá que el entorno virtual esté instalado.")

    def _append_system(self, msg: str) -> None:
        self._console.append(f'<span style="color:#58a6ff">&#9654; {_esc(msg)}</span>')

    def _append_error(self, msg: str) -> None:
        self._console.append(f'<span style="color:#ff7b72">&#10006; {_esc(msg)}</span>')

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

    def closeEvent(self, event) -> None:  # type: ignore[override]
        # Cerrar la ventana no mata el servidor, solo la oculta
        event.ignore()
        self.hide()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
