from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gestion_mantenimiento import __version__
from gestion_mantenimiento.data.models import (
    OrdenTrabajoCreate,
)
from gestion_mantenimiento.data.paths import get_database_path, get_theme_path
from gestion_mantenimiento.data.repositories import (
    AdjuntoRepository,
    EquipoRepository,
    OrdenProgramaRepository,
    OrdenTrabajoRepository,
    ProgramaMantenimientoRepository,
    RepuestoOrdenRepository,
    RepuestoRepository,
    TecnicoRepository,
    TipoEquipoRepository,
)
from gestion_mantenimiento.data.schema import initialize_database
from gestion_mantenimiento.ui.theme import (
    build_app_palette,
    build_app_styles,
    get_theme,
    save_theme_mode,
)

def _es_fecha_en_mes(fecha_str: str, mes: int, anio: int) -> bool:
    try:
        d = date.fromisoformat(fecha_str)
        return d.month == mes and d.year == anio
    except ValueError:
        return False


_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

_COLOR_VENCE_MES = QColor("#FFF3CD")   # amarillo suave
_COLOR_VENCIDO   = QColor("#FFD6D6")   # rojo suave (vencidos)

_NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Tipos de Máquina", "tipos_equipo"),
    ("Equipos", "equipos"),
    ("Repuestos", "repuestos"),
    ("Órdenes de Trabajo", "ordenes"),
    ("Programa Mantenimiento", "programa"),
    ("Técnicos", "tecnicos"),
]

_TIPOS_ORDEN = ["PREVENTIVO", "CORRECTIVO", "MEJORA"]
_ESTADOS_ORDEN = ["PENDIENTE", "EN_PROGRESO", "COMPLETADA", "CANCELADA"]
_ESTADOS_LABELS = {
    "PENDIENTE": "Pendiente",
    "EN_PROGRESO": "En progreso",
    "COMPLETADA": "Completada",
    "CANCELADA": "Cancelada",
}


def _panel(parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("panel")
    return frame


def _page_title(text: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("pageTitle")
    return label


def _section_title(text: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("sectionTitle")
    return label


def _metric_widget(title: str, value: str, parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("metric")
    frame.setFixedHeight(100)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    title_label = QLabel(title, frame)
    title_label.setObjectName("muted")
    value_label = QLabel(value, frame)
    value_label.setObjectName("metricValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    layout.addStretch()
    return frame


def _primary_button(text: str, parent: QWidget | None = None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("primaryButton")
    return btn


def _danger_button(text: str, parent: QWidget | None = None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("dangerButton")
    return btn


def _make_table(headers: list[str], parent: QWidget | None = None) -> QTableWidget:
    table = QTableWidget(0, len(headers), parent)
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    return table


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path, theme_mode: str = "light") -> None:
        super().__init__()
        self._db = database_path
        self._theme_mode = theme_mode
        self._equipo_repo = EquipoRepository(database_path)
        self._tecnico_repo = TecnicoRepository(database_path)
        self._tipo_repo = TipoEquipoRepository(database_path)
        self._orden_repo = OrdenTrabajoRepository(database_path)
        self._repuesto_repo = RepuestoOrdenRepository(database_path)
        self._repuesto_catalog_repo = RepuestoRepository(database_path)
        self._programa_repo = ProgramaMantenimientoRepository(database_path)
        self._orden_programa_repo = OrdenProgramaRepository(database_path)
        self._adjunto_repo = AdjuntoRepository(database_path)

        self.setWindowTitle(f"Gestión Mantenimiento v{__version__}")
        self.resize(1280, 800)
        self._build_ui()
        self._navigate("dashboard")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = self._build_sidebar()
        root.addWidget(sidebar)

        self._stack = QStackedWidget()
        self._pages: dict[str, QWidget] = {}
        for _, key in _NAV_ITEMS:
            page = self._build_page(key)
            self._pages[key] = page
            self._stack.addWidget(page)

        root.addWidget(self._stack, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        brand = QLabel("Mantenimiento", sidebar)
        brand.setObjectName("brand")
        layout.addWidget(brand)

        subtitle = QLabel("Sistema de gestión", sidebar)
        subtitle.setObjectName("sidebarSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        self._nav_buttons: dict[str, QPushButton] = {}
        for label, key in _NAV_ITEMS:
            btn = QPushButton(label, sidebar)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn

        layout.addStretch()

        self._theme_btn = QPushButton(sidebar)
        self._theme_btn.setObjectName("navButton")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_btn_label()
        layout.addWidget(self._theme_btn)

        version_label = QLabel(f"v{__version__}", sidebar)
        version_label.setObjectName("muted")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        return sidebar

    def _update_theme_btn_label(self) -> None:
        if self._theme_mode == "dark":
            self._theme_btn.setText("Modo diurno")
        else:
            self._theme_btn.setText("Modo nocturno")

    def _toggle_theme(self) -> None:
        self._theme_mode = "dark" if self._theme_mode == "light" else "light"
        self._apply_theme(self._theme_mode)
        self._update_theme_btn_label()

    def _apply_theme(self, mode: str) -> None:
        from PySide6.QtWidgets import QApplication
        from gestion_mantenimiento.data.paths import get_theme_path
        theme = get_theme(mode)
        app = QApplication.instance()
        if app is None:
            return
        palette = build_app_palette(theme)
        stylesheet = build_app_styles(theme)
        # Clear first so Qt re-evaluates all rules
        app.setStyleSheet("")
        app.setStyleSheet(stylesheet)
        app.setPalette(palette)
        # Force every visible widget to repaint with new palette+stylesheet
        for widget in app.allWidgets():
            widget.setPalette(palette)
            widget.update()
        save_theme_mode(get_theme_path(), mode)

    def _navigate(self, key: str) -> None:
        for k, btn in self._nav_buttons.items():
            btn.setObjectName("navButtonActive" if k == key else "navButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        page = self._pages[key]
        self._stack.setCurrentWidget(page)
        if hasattr(page, "_refresh"):
            page._refresh()  # type: ignore[attr-defined]

    def _build_page(self, key: str) -> QWidget:
        builders = {
            "dashboard": self._build_dashboard_page,
            "tipos_equipo": self._build_tipos_equipo_page,
            "equipos": self._build_equipos_page,
            "repuestos": self._build_repuestos_page,
            "ordenes": self._build_ordenes_page,
            "programa": self._build_programa_page,
            "tecnicos": self._build_tecnicos_page,
        }
        return builders[key]()

    # ── Dashboard ────────────────────────────────────────────────────────────

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Dashboard"))

        self._dash_metrics_row = QHBoxLayout()
        self._dash_metrics_row.setSpacing(12)
        layout.addLayout(self._dash_metrics_row)

        layout.addWidget(_section_title("Próximos mantenimientos programados"))

        self._dash_tabla_proximos = _make_table(
            ["Equipo", "Descripción", "Próxima ejecución", "Días restantes"]
        )
        layout.addWidget(self._dash_tabla_proximos)

        layout.addWidget(_section_title("Órdenes abiertas recientes"))
        self._dash_tabla_ordenes = _make_table(
            ["#", "Equipo", "Tipo", "Estado", "Fecha apertura", "Técnico"]
        )
        layout.addWidget(self._dash_tabla_ordenes)

        layout.addStretch()

        def refresh() -> None:
            self._refresh_dashboard()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_dashboard(self) -> None:
        # Metrics
        while self._dash_metrics_row.count():
            item = self._dash_metrics_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        counts = self._orden_repo.count_by_estado()
        total_equipos = len(self._equipo_repo.list_all(solo_activos=True))
        pendientes = counts.get("PENDIENTE", 0) + counts.get("EN_PROGRESO", 0)
        completadas = counts.get("COMPLETADA", 0)

        for title, value in [
            ("Equipos activos", str(total_equipos)),
            ("Órdenes abiertas", str(pendientes)),
            ("Completadas (total)", str(completadas)),
        ]:
            self._dash_metrics_row.addWidget(_metric_widget(title, value))
        self._dash_metrics_row.addStretch()

        # Próximos mantenimientos
        programas = self._programa_repo.list_all(solo_activos=True)
        hoy = date.today()
        tabla = self._dash_tabla_proximos
        tabla.setRowCount(0)
        for p in programas[:20]:
            row = tabla.rowCount()
            tabla.insertRow(row)
            try:
                proxima = date.fromisoformat(p.proxima_ejecucion)
                dias = (proxima - hoy).days
                dias_str = str(dias) if dias >= 0 else f"{dias} (vencido)"
            except ValueError:
                dias_str = "-"
            tabla.setItem(row, 0, QTableWidgetItem(p.equipo_nombre))
            tabla.setItem(row, 1, QTableWidgetItem(p.descripcion))
            tabla.setItem(row, 2, QTableWidgetItem(p.proxima_ejecucion))
            tabla.setItem(row, 3, QTableWidgetItem(dias_str))

        # Órdenes abiertas
        ordenes = self._orden_repo.list_all(estado="PENDIENTE")
        ordenes += self._orden_repo.list_all(estado="EN_PROGRESO")
        tabla2 = self._dash_tabla_ordenes
        tabla2.setRowCount(0)
        for o in sorted(ordenes, key=lambda x: x.fecha_apertura, reverse=True)[:20]:
            row = tabla2.rowCount()
            tabla2.insertRow(row)
            tabla2.setItem(row, 0, QTableWidgetItem(str(o.id)))
            tabla2.setItem(row, 1, QTableWidgetItem(o.equipo_nombre))
            tabla2.setItem(row, 2, QTableWidgetItem(o.tipo))
            tabla2.setItem(row, 3, QTableWidgetItem(_ESTADOS_LABELS.get(o.estado, o.estado)))
            tabla2.setItem(row, 4, QTableWidgetItem(o.fecha_apertura))
            tabla2.setItem(row, 5, QTableWidgetItem(o.tecnico_nombre))

    # ── Tipos de Máquina ──────────────────────────────────────────────────────

    def _build_tipos_equipo_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Tipos de Máquina"))

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._te_search = QLineEdit()
        self._te_search.setPlaceholderText("Buscar tipo...")
        self._te_search.textChanged.connect(lambda: self._refresh_tipos_equipo())

        self._te_show_inactive = QCheckBox("Mostrar inactivos")
        self._te_show_inactive.stateChanged.connect(lambda: self._refresh_tipos_equipo())

        btn_nuevo = _primary_button("+ Nuevo tipo")
        btn_nuevo.clicked.connect(lambda: self._open_tipo_equipo_dialog())

        tb_layout.addWidget(self._te_search, 1)
        tb_layout.addWidget(self._te_show_inactive)
        tb_layout.addWidget(btn_nuevo)
        layout.addWidget(topbar)

        self._te_table = _make_table(["ID", "Nombre", "Estado"])
        self._te_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._te_table.doubleClicked.connect(self._edit_selected_tipo_equipo)
        layout.addWidget(self._te_table)

        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_selected_tipo_equipo)
        btn_delete = _danger_button("Eliminar")
        btn_delete.clicked.connect(self._delete_selected_tipo_equipo)
        act_layout.addStretch()
        act_layout.addWidget(btn_edit)
        act_layout.addWidget(btn_delete)
        layout.addWidget(actions)

        layout.addStretch()

        def refresh() -> None:
            self._refresh_tipos_equipo()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_tipos_equipo(self) -> None:
        search = self._te_search.text().strip().lower()
        solo_activos = not self._te_show_inactive.isChecked()
        tipos = self._tipo_repo.list_all(solo_activos=solo_activos)
        if search:
            tipos = [t for t in tipos if search in t.nombre.lower()]
        tabla = self._te_table
        tabla.setRowCount(0)
        for t in tipos:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(t.id)))
            tabla.setItem(row, 1, QTableWidgetItem(t.nombre))
            tabla.setItem(row, 2, QTableWidgetItem("Activo" if t.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, t.id)

    def _open_tipo_equipo_dialog(self, tipo_id: int | None = None) -> None:
        dlg = TipoEquipoDialog(self._db, tipo_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_tipos_equipo()

    def _edit_selected_tipo_equipo(self) -> None:
        tipo_id = self._selected_id(self._te_table)
        if tipo_id is None:
            return
        self._open_tipo_equipo_dialog(tipo_id)

    def _delete_selected_tipo_equipo(self) -> None:
        tipo_id = self._selected_id(self._te_table)
        if tipo_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar el tipo seleccionado?\n"
            "No se puede eliminar si hay equipos que lo usan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._tipo_repo.delete(tipo_id)
                self._refresh_tipos_equipo()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    # ── Equipos ──────────────────────────────────────────────────────────────

    def _build_equipos_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Equipos"))

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._eq_search = QLineEdit()
        self._eq_search.setPlaceholderText("Buscar equipo...")
        self._eq_search.textChanged.connect(lambda: self._refresh_equipos())

        self._eq_show_inactive = QCheckBox("Mostrar inactivos")
        self._eq_show_inactive.stateChanged.connect(lambda: self._refresh_equipos())

        btn_nuevo = _primary_button("+ Nuevo equipo")
        btn_nuevo.clicked.connect(lambda: self._open_equipo_dialog())

        tb_layout.addWidget(self._eq_search, 1)
        tb_layout.addWidget(self._eq_show_inactive)
        tb_layout.addWidget(btn_nuevo)
        layout.addWidget(topbar)

        self._eq_table = _make_table(
            ["ID", "Nombre", "Tipo", "Marca", "Modelo", "N° Serie", "Ubicación", "Estado"]
        )
        self._eq_table.doubleClicked.connect(self._edit_selected_equipo)
        layout.addWidget(self._eq_table)

        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_selected_equipo)
        btn_delete = _danger_button("Eliminar")
        btn_delete.clicked.connect(self._delete_selected_equipo)
        act_layout.addStretch()
        act_layout.addWidget(btn_edit)
        act_layout.addWidget(btn_delete)
        layout.addWidget(actions)

        def refresh() -> None:
            self._refresh_equipos()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_equipos(self) -> None:
        search = self._eq_search.text()
        solo_activos = not self._eq_show_inactive.isChecked()
        equipos = self._equipo_repo.list_all(search=search, solo_activos=solo_activos)
        tabla = self._eq_table
        tabla.setRowCount(0)
        for eq in equipos:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(eq.id)))
            tabla.setItem(row, 1, QTableWidgetItem(eq.nombre))
            tabla.setItem(row, 2, QTableWidgetItem(eq.tipo_nombre))
            tabla.setItem(row, 3, QTableWidgetItem(eq.marca))
            tabla.setItem(row, 4, QTableWidgetItem(eq.modelo))
            tabla.setItem(row, 5, QTableWidgetItem(eq.numero_serie))
            tabla.setItem(row, 6, QTableWidgetItem(eq.ubicacion))
            tabla.setItem(row, 7, QTableWidgetItem("Activo" if eq.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, eq.id)

    def _open_equipo_dialog(self, equipo_id: int | None = None) -> None:
        dlg = EquipoDialog(self._db, equipo_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_equipos()

    def _edit_selected_equipo(self) -> None:
        equipo_id = self._selected_id(self._eq_table)
        if equipo_id is None:
            return
        self._open_equipo_dialog(equipo_id)

    def _delete_selected_equipo(self) -> None:
        equipo_id = self._selected_id(self._eq_table)
        if equipo_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar el equipo seleccionado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._equipo_repo.delete(equipo_id)
                self._refresh_equipos()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    # ── Repuestos ─────────────────────────────────────────────────────────────

    def _build_repuestos_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Repuestos"))

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._rep_search = QLineEdit()
        self._rep_search.setPlaceholderText("Buscar repuesto...")
        self._rep_search.textChanged.connect(lambda: self._refresh_repuestos())

        self._rep_show_inactive = QCheckBox("Mostrar inactivos")
        self._rep_show_inactive.stateChanged.connect(lambda: self._refresh_repuestos())

        btn_nuevo = _primary_button("+ Nuevo repuesto")
        btn_nuevo.clicked.connect(lambda: self._open_repuesto_dialog())

        tb_layout.addWidget(self._rep_search, 1)
        tb_layout.addWidget(self._rep_show_inactive)
        tb_layout.addWidget(btn_nuevo)
        layout.addWidget(topbar)

        self._rep_catalog_table = _make_table(
            ["ID", "Nombre", "Stock actual", "Stock mínimo", "Estado stock", "Observaciones", "Activo"]
        )
        self._rep_catalog_table.doubleClicked.connect(self._edit_selected_repuesto)
        layout.addWidget(self._rep_catalog_table)

        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_selected_repuesto)
        btn_delete = _danger_button("Eliminar")
        btn_delete.clicked.connect(self._delete_selected_repuesto)
        act_layout.addStretch()
        act_layout.addWidget(btn_edit)
        act_layout.addWidget(btn_delete)
        layout.addWidget(actions)

        def refresh() -> None:
            self._refresh_repuestos()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_repuestos(self) -> None:
        search = self._rep_search.text()
        solo_activos = not self._rep_show_inactive.isChecked()
        repuestos = self._repuesto_catalog_repo.list_all(search=search, solo_activos=solo_activos)
        tabla = self._rep_catalog_table
        tabla.setRowCount(0)
        for r in repuestos:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(r.id)))
            tabla.setItem(row, 1, QTableWidgetItem(r.nombre))
            tabla.setItem(row, 2, QTableWidgetItem(f"{r.stock_actual:g}"))
            tabla.setItem(row, 3, QTableWidgetItem(f"{r.stock_minimo:g}"))
            estado_stock = "BAJO STOCK" if r.bajo_stock else "OK"
            tabla.setItem(row, 4, QTableWidgetItem(estado_stock))
            tabla.setItem(row, 5, QTableWidgetItem(r.observaciones))
            tabla.setItem(row, 6, QTableWidgetItem("Activo" if r.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, r.id)

    def _open_repuesto_dialog(self, repuesto_id: int | None = None) -> None:
        dlg = RepuestoCatalogDialog(self._db, repuesto_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_repuestos()

    def _edit_selected_repuesto(self) -> None:
        repuesto_id = self._selected_id(self._rep_catalog_table)
        if repuesto_id is None:
            return
        self._open_repuesto_dialog(repuesto_id)

    def _delete_selected_repuesto(self) -> None:
        repuesto_id = self._selected_id(self._rep_catalog_table)
        if repuesto_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar el repuesto seleccionado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._repuesto_catalog_repo.delete(repuesto_id)
                self._refresh_repuestos()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    # ── Órdenes de Trabajo ───────────────────────────────────────────────────

    def _build_ordenes_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Órdenes de Trabajo"))

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._ot_search = QLineEdit()
        self._ot_search.setPlaceholderText("Buscar...")
        self._ot_search.textChanged.connect(lambda: self._refresh_ordenes())

        self._ot_estado_filter = QComboBox()
        self._ot_estado_filter.addItem("Todos los estados", "")
        for k, v in _ESTADOS_LABELS.items():
            self._ot_estado_filter.addItem(v, k)
        self._ot_estado_filter.currentIndexChanged.connect(lambda: self._refresh_ordenes())

        btn_nuevo = _primary_button("+ Nueva orden")
        btn_nuevo.clicked.connect(lambda: self._open_orden_dialog())

        tb_layout.addWidget(self._ot_search, 1)
        tb_layout.addWidget(self._ot_estado_filter)
        tb_layout.addWidget(btn_nuevo)
        layout.addWidget(topbar)

        self._ot_table = _make_table(
            ["#", "Equipo", "Tipo", "Estado", "Apertura", "Cierre", "Técnico", "Costo total"]
        )
        self._ot_table.doubleClicked.connect(self._edit_selected_orden)
        layout.addWidget(self._ot_table)

        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_selected_orden)
        btn_delete = _danger_button("Eliminar")
        btn_delete.clicked.connect(self._delete_selected_orden)
        act_layout.addStretch()
        act_layout.addWidget(btn_edit)
        act_layout.addWidget(btn_delete)
        layout.addWidget(actions)

        def refresh() -> None:
            self._refresh_ordenes()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_ordenes(self) -> None:
        search = self._ot_search.text()
        estado = self._ot_estado_filter.currentData() or ""
        ordenes = self._orden_repo.list_all(search=search, estado=estado)
        tabla = self._ot_table
        tabla.setRowCount(0)
        for o in ordenes:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(o.id)))
            tabla.setItem(row, 1, QTableWidgetItem(o.equipo_nombre))
            tabla.setItem(row, 2, QTableWidgetItem(o.tipo))
            tabla.setItem(row, 3, QTableWidgetItem(_ESTADOS_LABELS.get(o.estado, o.estado)))
            tabla.setItem(row, 4, QTableWidgetItem(o.fecha_apertura))
            tabla.setItem(row, 5, QTableWidgetItem(o.fecha_cierre))
            tabla.setItem(row, 6, QTableWidgetItem(o.tecnico_nombre))
            tabla.setItem(
                row, 7, QTableWidgetItem(f"$ {o.costo_total:,.2f}")
            )
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, o.id)

    def _open_orden_dialog(self, orden_id: int | None = None) -> None:
        dlg = OrdenTrabajoDialog(self._db, orden_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_ordenes()

    def _edit_selected_orden(self) -> None:
        orden_id = self._selected_id(self._ot_table)
        if orden_id is None:
            return
        self._open_orden_dialog(orden_id)

    def _delete_selected_orden(self) -> None:
        orden_id = self._selected_id(self._ot_table)
        if orden_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar la orden seleccionada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._orden_repo.delete(orden_id)
                self._refresh_ordenes()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    # ── Programa Mantenimiento ───────────────────────────────────────────────

    def _build_programa_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Programa de Mantenimiento"))

        # ── Selector de mes ──────────────────────────────────────────────────
        mes_bar = QFrame()
        mes_bar.setObjectName("panel")
        mes_layout = QHBoxLayout(mes_bar)
        mes_layout.setContentsMargins(16, 10, 16, 10)

        mes_layout.addWidget(QLabel("Ver mes:"))

        self._prog_mes = QComboBox()
        for nombre in _MESES:
            self._prog_mes.addItem(nombre)
        self._prog_mes.setCurrentIndex(date.today().month - 1)
        self._prog_mes.setFixedWidth(130)
        self._prog_mes.currentIndexChanged.connect(lambda: self._refresh_programas())

        self._prog_anio = QSpinBox()
        self._prog_anio.setRange(2000, 2100)
        self._prog_anio.setValue(date.today().year)
        self._prog_anio.setFixedWidth(80)
        self._prog_anio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prog_anio.valueChanged.connect(lambda: self._refresh_programas())

        leyenda_amarilla = QLabel("■ vence este mes")
        leyenda_amarilla.setStyleSheet("color: #b8860b; font-size: 12px;")
        leyenda_roja = QLabel("■ vencido")
        leyenda_roja.setStyleSheet("color: #b42318; font-size: 12px;")

        mes_layout.addWidget(self._prog_mes)
        mes_layout.addWidget(self._prog_anio)
        mes_layout.addSpacing(24)
        mes_layout.addWidget(leyenda_amarilla)
        mes_layout.addSpacing(12)
        mes_layout.addWidget(leyenda_roja)
        mes_layout.addStretch()
        layout.addWidget(mes_bar)

        # ── Barra de acciones ────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._prog_show_inactive = QCheckBox("Mostrar máquinas inactivas")
        self._prog_show_inactive.stateChanged.connect(lambda: self._refresh_programas())

        btn_generar = _primary_button("Generar órdenes del mes")
        btn_generar.clicked.connect(lambda: self._generar_ordenes_mes())

        tb_layout.addStretch()
        tb_layout.addWidget(self._prog_show_inactive)
        tb_layout.addWidget(btn_generar)
        layout.addWidget(topbar)

        # ── Tabla (una fila por máquina) ─────────────────────────────────────
        self._prog_table = _make_table(
            ["Máquina", "Tipo", "Programas activos", "Próxima ejecución", "Días restantes"]
        )
        self._prog_table.doubleClicked.connect(self._open_mantenimientos_equipo)
        layout.addWidget(self._prog_table)

        # ── Botón inferior ───────────────────────────────────────────────────
        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)

        btn_editar = _primary_button("Editar mantenimientos")
        btn_editar.clicked.connect(self._open_mantenimientos_equipo)

        act_layout.addStretch()
        act_layout.addWidget(btn_editar)
        layout.addWidget(actions)

        def refresh() -> None:
            self._refresh_programas()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_programas(self) -> None:
        mes_sel  = self._prog_mes.currentIndex() + 1
        anio_sel = self._prog_anio.value()
        hoy = date.today()

        solo_activos = not self._prog_show_inactive.isChecked()
        equipos = self._equipo_repo.list_all(solo_activos=solo_activos)

        # Agrupar todos los programas por equipo_id
        todos_programas = self._programa_repo.list_all()
        por_equipo: dict[int, list] = {}
        for p in todos_programas:
            por_equipo.setdefault(p.equipo_id, []).append(p)

        tabla = self._prog_table
        tabla.setRowCount(0)

        for eq in equipos:
            progs = por_equipo.get(eq.id, [])
            activos = [p for p in progs if p.activo]

            # Fecha más próxima entre todos los programas de esta máquina
            proximas: list[date] = []
            for p in progs:
                try:
                    proximas.append(date.fromisoformat(p.proxima_ejecucion))
                except ValueError:
                    pass

            proxima_str   = min(proximas).isoformat() if proximas else "—"
            dias_restantes = ""
            if proximas:
                delta = (min(proximas) - hoy).days
                if delta < 0:
                    dias_restantes = f"{abs(delta)} días vencido"
                elif delta == 0:
                    dias_restantes = "Hoy"
                else:
                    dias_restantes = f"{delta} días"

            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(eq.nombre))
            tabla.setItem(row, 1, QTableWidgetItem(eq.tipo_nombre))
            tabla.setItem(row, 2, QTableWidgetItem(str(len(activos)) if activos else "Sin programas"))
            tabla.setItem(row, 3, QTableWidgetItem(proxima_str))
            tabla.setItem(row, 4, QTableWidgetItem(dias_restantes))

            # Guardar equipo_id en UserRole de la primera celda
            item0 = tabla.item(row, 0)
            if item0:
                item0.setData(Qt.ItemDataRole.UserRole, eq.id)

            # Color de fila según la fecha más próxima
            color: QColor | None = None
            if proximas:
                nearest = min(proximas)
                if nearest < hoy:
                    color = _COLOR_VENCIDO
                elif nearest.year == anio_sel and nearest.month == mes_sel:
                    color = _COLOR_VENCE_MES

            if color is not None:
                brush = QBrush(color)
                for col in range(tabla.columnCount()):
                    it = tabla.item(row, col)
                    if it:
                        it.setBackground(brush)

    def _open_mantenimientos_equipo(self) -> None:
        selected = self._prog_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Sin selección", "Seleccione una máquina de la lista.")
            return
        row = self._prog_table.row(selected[0])
        item = self._prog_table.item(row, 0)
        if item is None:
            return
        equipo_id = item.data(Qt.ItemDataRole.UserRole)
        equipo_nombre = item.text()
        if equipo_id is None:
            return
        dlg = MantenimientosEquipoDialog(self._db, equipo_id, equipo_nombre, parent=self)
        dlg.exec()
        self._refresh_programas()

    def _generar_ordenes_mes(self) -> None:
        mes_sel  = self._prog_mes.currentIndex() + 1
        anio_sel = self._prog_anio.value()
        hoy      = date.today()

        equipos = self._equipo_repo.list_all(solo_activos=True)
        todos   = self._programa_repo.list_all()
        por_equipo: dict[int, list] = {}
        for p in todos:
            por_equipo.setdefault(p.equipo_id, []).append(p)

        creadas     = 0
        ya_existian = 0

        for eq in equipos:
            progs_mes = [
                p for p in por_equipo.get(eq.id, [])
                if _es_fecha_en_mes(p.proxima_ejecucion, mes_sel, anio_sel)
            ]
            if not progs_mes:
                continue

            existing = self._orden_programa_repo.find_orden_pendiente(
                eq.id, [p.id for p in progs_mes]
            )
            if existing is not None:
                ya_existian += 1
                continue

            orden_data = OrdenTrabajoCreate(
                equipo_id=eq.id,
                tipo="PREVENTIVO",
                descripcion=f"Mantenimiento preventivo — {_MESES[mes_sel - 1]} {anio_sel}",
                fecha_apertura=hoy.isoformat(),
                fecha_cierre="",
                estado="PENDIENTE",
                tecnico_id=None,
                costo_mano_obra=0.0,
                observaciones=(
                    f"Generada automáticamente por {len(progs_mes)} "
                    f"programa(s): {', '.join(p.descripcion for p in progs_mes)}"
                ),
            )
            orden_id = self._orden_repo.create(orden_data)
            for p in progs_mes:
                self._orden_programa_repo.link(orden_id, p.id)
            creadas += 1

        partes = [f"Órdenes creadas: {creadas}"]
        if ya_existian:
            partes.append(f"Ya tenían orden pendiente: {ya_existian}")
        if creadas == 0 and ya_existian == 0:
            partes = ["No hay máquinas con mantenimientos que venzan este mes."]
        QMessageBox.information(self, "Generar órdenes", "\n".join(partes))
        self._refresh_programas()

    # ── Técnicos ─────────────────────────────────────────────────────────────

    def _build_tecnicos_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Técnicos"))

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        self._tec_search = QLineEdit()
        self._tec_search.setPlaceholderText("Buscar técnico...")
        self._tec_search.textChanged.connect(lambda: self._refresh_tecnicos())

        self._tec_show_inactive = QCheckBox("Mostrar inactivos")
        self._tec_show_inactive.stateChanged.connect(lambda: self._refresh_tecnicos())

        btn_nuevo = _primary_button("+ Nuevo técnico")
        btn_nuevo.clicked.connect(lambda: self._open_tecnico_dialog())

        tb_layout.addWidget(self._tec_search, 1)
        tb_layout.addWidget(self._tec_show_inactive)
        tb_layout.addWidget(btn_nuevo)
        layout.addWidget(topbar)

        self._tec_table = _make_table(
            ["ID", "Apellido", "Nombre", "DNI", "Teléfono", "Especialidad", "Estado"]
        )
        self._tec_table.doubleClicked.connect(self._edit_selected_tecnico)
        layout.addWidget(self._tec_table)

        actions = QWidget()
        actions.setObjectName("actionButtons")
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self._edit_selected_tecnico)
        btn_delete = _danger_button("Eliminar")
        btn_delete.clicked.connect(self._delete_selected_tecnico)
        act_layout.addStretch()
        act_layout.addWidget(btn_edit)
        act_layout.addWidget(btn_delete)
        layout.addWidget(actions)

        def refresh() -> None:
            self._refresh_tecnicos()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _refresh_tecnicos(self) -> None:
        search = self._tec_search.text()
        solo_activos = not self._tec_show_inactive.isChecked()
        tecnicos = self._tecnico_repo.list_all(search=search, solo_activos=solo_activos)
        tabla = self._tec_table
        tabla.setRowCount(0)
        for t in tecnicos:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(t.id)))
            tabla.setItem(row, 1, QTableWidgetItem(t.apellido))
            tabla.setItem(row, 2, QTableWidgetItem(t.nombre))
            tabla.setItem(row, 3, QTableWidgetItem(t.dni))
            tabla.setItem(row, 4, QTableWidgetItem(t.telefono))
            tabla.setItem(row, 5, QTableWidgetItem(t.especialidad))
            tabla.setItem(row, 6, QTableWidgetItem("Activo" if t.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, t.id)

    def _open_tecnico_dialog(self, tecnico_id: int | None = None) -> None:
        dlg = TecnicoDialog(self._db, tecnico_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_tecnicos()

    def _edit_selected_tecnico(self) -> None:
        tecnico_id = self._selected_id(self._tec_table)
        if tecnico_id is None:
            return
        self._open_tecnico_dialog(tecnico_id)

    def _delete_selected_tecnico(self) -> None:
        tecnico_id = self._selected_id(self._tec_table)
        if tecnico_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar el técnico seleccionado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._tecnico_repo.delete(tecnico_id)
                self._refresh_tecnicos()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_id(self, table: QTableWidget) -> int | None:
        selected = table.selectedItems()
        if not selected:
            return None
        row = table.row(selected[0])
        item = table.item(row, 0)
        if item is None:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        return int(val) if val is not None else None


# ── Dialogs ───────────────────────────────────────────────────────────────────

class EquipoDialog(QDialog):
    def __init__(
        self, database_path: Path, equipo_id: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._equipo_id = equipo_id
        self._repo = EquipoRepository(database_path)
        self._tipo_repo = TipoEquipoRepository(database_path)
        self.setWindowTitle("Equipo")
        self.setMinimumWidth(480)
        self._build()
        if equipo_id is not None:
            self._load(equipo_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._nombre = QLineEdit()
        self._tipo = QComboBox()
        self._tipo.addItem("(sin tipo)", None)
        for t in self._tipo_repo.list_all():
            self._tipo.addItem(t.nombre, t.id)

        self._numero_serie = QLineEdit()
        self._marca = QLineEdit()
        self._modelo = QLineEdit()
        self._ubicacion = QLineEdit()
        self._fecha_adq = QDateEdit()
        self._fecha_adq.setCalendarPopup(True)
        self._fecha_adq.setDate(QDate.currentDate())
        self._observaciones = QTextEdit()
        self._observaciones.setFixedHeight(80)
        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Nombre *", self._nombre)
        form.addRow("Tipo", self._tipo)
        form.addRow("N° Serie", self._numero_serie)
        form.addRow("Marca", self._marca)
        form.addRow("Modelo", self._modelo)
        form.addRow("Ubicación", self._ubicacion)
        form.addRow("Fecha adquisición", self._fecha_adq)
        form.addRow("Observaciones", self._observaciones)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, equipo_id: int) -> None:
        eq = self._repo.get_by_id(equipo_id)
        if eq is None:
            return
        self._nombre.setText(eq.nombre)
        idx = self._tipo.findData(eq.tipo_id)
        if idx >= 0:
            self._tipo.setCurrentIndex(idx)
        self._numero_serie.setText(eq.numero_serie)
        self._marca.setText(eq.marca)
        self._modelo.setText(eq.modelo)
        self._ubicacion.setText(eq.ubicacion)
        if eq.fecha_adquisicion:
            try:
                d = date.fromisoformat(eq.fecha_adquisicion)
                self._fecha_adq.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass
        self._observaciones.setPlainText(eq.observaciones)
        self._activo.setChecked(eq.activo)

    def _save(self) -> None:
        nombre = self._nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre es requerido.")
            return

        tipo_id = self._tipo.currentData()
        numero_serie = self._numero_serie.text().strip()
        marca = self._marca.text().strip()
        modelo = self._modelo.text().strip()
        ubicacion = self._ubicacion.text().strip()
        fecha_adq = self._fecha_adq.date().toString("yyyy-MM-dd")
        observaciones = self._observaciones.toPlainText().strip()
        activo = self._activo.isChecked()

        try:
            if self._equipo_id is None:
                self._repo.create(
                    nombre, tipo_id, numero_serie, marca, modelo,
                    ubicacion, fecha_adq, observaciones,
                )
            else:
                self._repo.update(
                    self._equipo_id, nombre, tipo_id, numero_serie, marca, modelo,
                    ubicacion, fecha_adq, observaciones, activo,
                )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class TecnicoDialog(QDialog):
    def __init__(
        self, database_path: Path, tecnico_id: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._tecnico_id = tecnico_id
        self._repo = TecnicoRepository(database_path)
        self.setWindowTitle("Técnico")
        self.setMinimumWidth(400)
        self._build()
        if tecnico_id is not None:
            self._load(tecnico_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._nombre = QLineEdit()
        self._apellido = QLineEdit()
        self._dni = QLineEdit()
        self._telefono = QLineEdit()
        self._especialidad = QLineEdit()
        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Nombre *", self._nombre)
        form.addRow("Apellido *", self._apellido)
        form.addRow("DNI", self._dni)
        form.addRow("Teléfono", self._telefono)
        form.addRow("Especialidad", self._especialidad)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, tecnico_id: int) -> None:
        tecnicos = self._repo.list_all()
        tec = next((t for t in tecnicos if t.id == tecnico_id), None)
        if tec is None:
            return
        self._nombre.setText(tec.nombre)
        self._apellido.setText(tec.apellido)
        self._dni.setText(tec.dni)
        self._telefono.setText(tec.telefono)
        self._especialidad.setText(tec.especialidad)
        self._activo.setChecked(tec.activo)

    def _save(self) -> None:
        nombre = self._nombre.text().strip()
        apellido = self._apellido.text().strip()
        if not nombre or not apellido:
            QMessageBox.warning(self, "Validación", "Nombre y apellido son requeridos.")
            return

        try:
            if self._tecnico_id is None:
                self._repo.create(
                    nombre, apellido, self._dni.text().strip(),
                    self._telefono.text().strip(), self._especialidad.text().strip(),
                )
            else:
                self._repo.update(
                    self._tecnico_id, nombre, apellido,
                    self._dni.text().strip(), self._telefono.text().strip(),
                    self._especialidad.text().strip(), self._activo.isChecked(),
                )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class OrdenTrabajoDialog(QDialog):
    def __init__(
        self, database_path: Path, orden_id: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._orden_id = orden_id
        self._repo = OrdenTrabajoRepository(database_path)
        self._repuesto_repo = RepuestoOrdenRepository(database_path)
        self._repuesto_catalog_repo = RepuestoRepository(database_path)
        self._orden_programa_repo = OrdenProgramaRepository(database_path)
        self._equipo_repo = EquipoRepository(database_path)
        self._tecnico_repo = TecnicoRepository(database_path)
        self.setWindowTitle("Orden de Trabajo")
        self.setMinimumWidth(620)
        self.resize(660, 740)
        self._build()
        if orden_id is not None:
            self._load(orden_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._equipo = QComboBox()
        for eq in self._equipo_repo.list_all(solo_activos=True):
            self._equipo.addItem(eq.etiqueta, eq.id)

        self._tipo = QComboBox()
        for t in _TIPOS_ORDEN:
            self._tipo.addItem(t, t)

        self._estado = QComboBox()
        for k, v in _ESTADOS_LABELS.items():
            self._estado.addItem(v, k)

        self._descripcion = QTextEdit()
        self._descripcion.setFixedHeight(80)

        self._fecha_apertura = QDateEdit()
        self._fecha_apertura.setCalendarPopup(True)
        self._fecha_apertura.setDate(QDate.currentDate())

        self._fecha_cierre = QDateEdit()
        self._fecha_cierre.setCalendarPopup(True)
        self._fecha_cierre.setDate(QDate.currentDate())

        self._tecnico = QComboBox()
        self._tecnico.addItem("(sin asignar)", None)
        for t in self._tecnico_repo.list_all(solo_activos=True):
            self._tecnico.addItem(t.nombre_completo, t.id)

        self._costo_mano_obra = QDoubleSpinBox()
        self._costo_mano_obra.setRange(0, 999_999_999)
        self._costo_mano_obra.setDecimals(2)
        self._costo_mano_obra.setSuffix(" $")
        self._costo_mano_obra.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._observaciones = QTextEdit()
        self._observaciones.setFixedHeight(60)

        form.addRow("Equipo *", self._equipo)
        form.addRow("Tipo", self._tipo)
        form.addRow("Estado", self._estado)
        form.addRow("Descripción", self._descripcion)
        form.addRow("Fecha apertura", self._fecha_apertura)
        form.addRow("Fecha cierre", self._fecha_cierre)
        form.addRow("Técnico", self._tecnico)
        form.addRow("Costo mano de obra", self._costo_mano_obra)
        form.addRow("Observaciones", self._observaciones)

        layout.addLayout(form)

        # ── Mantenimientos que activaron esta orden ──────────────────────────
        self._vinc_section = QFrame()
        self._vinc_section.setObjectName("panel")
        vinc_layout = QVBoxLayout(self._vinc_section)
        vinc_layout.setContentsMargins(12, 8, 12, 8)
        vinc_layout.setSpacing(6)

        vinc_title = _section_title("Mantenimientos que activaron esta orden")
        vinc_layout.addWidget(vinc_title)

        self._vinc_table = _make_table(
            ["Descripción", "Frecuencia", "Última ejecución", "Próxima ejecución"]
        )
        self._vinc_table.setFixedHeight(120)
        vinc_layout.addWidget(self._vinc_table)

        btn_ver_mant = QPushButton("Ver mantenimiento")
        btn_ver_mant.clicked.connect(self._ver_mantenimiento_vinculado)
        vinc_btn_row = QHBoxLayout()
        vinc_btn_row.addStretch()
        vinc_btn_row.addWidget(btn_ver_mant)
        vinc_layout.addLayout(vinc_btn_row)

        self._vinc_section.setVisible(False)
        layout.addWidget(self._vinc_section)

        # Repuestos section
        layout.addWidget(_section_title("Repuestos utilizados"))

        self._rep_table = _make_table(
            ["Repuesto", "Stock disp.", "Cantidad", "Costo unit.", "Subtotal"]
        )
        self._rep_table.setFixedHeight(160)
        layout.addWidget(self._rep_table)

        rep_actions = QHBoxLayout()
        btn_add_rep = QPushButton("+ Agregar repuesto")
        btn_del_rep = _danger_button("Quitar")
        btn_add_rep.clicked.connect(self._add_repuesto)
        btn_del_rep.clicked.connect(self._del_repuesto)
        rep_actions.addStretch()
        rep_actions.addWidget(btn_add_rep)
        rep_actions.addWidget(btn_del_rep)
        layout.addLayout(rep_actions)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, orden_id: int) -> None:
        orden = self._repo.get_by_id(orden_id)
        if orden is None:
            return

        idx = self._equipo.findData(orden.equipo_id)
        if idx >= 0:
            self._equipo.setCurrentIndex(idx)

        idx = self._tipo.findData(orden.tipo)
        if idx >= 0:
            self._tipo.setCurrentIndex(idx)

        idx = self._estado.findData(orden.estado)
        if idx >= 0:
            self._estado.setCurrentIndex(idx)

        self._descripcion.setPlainText(orden.descripcion)

        if orden.fecha_apertura:
            try:
                d = date.fromisoformat(orden.fecha_apertura)
                self._fecha_apertura.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass

        if orden.fecha_cierre:
            try:
                d = date.fromisoformat(orden.fecha_cierre)
                self._fecha_cierre.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass

        idx = self._tecnico.findData(orden.tecnico_id)
        if idx >= 0:
            self._tecnico.setCurrentIndex(idx)

        self._costo_mano_obra.setValue(orden.costo_mano_obra)
        self._observaciones.setPlainText(orden.observaciones)

        # Poblar tabla de mantenimientos vinculados
        vinculados = self._orden_programa_repo.list_by_orden(orden_id)
        if vinculados:
            prog_repo = ProgramaMantenimientoRepository(self._db)
            todos_progs = {p.id: p for p in prog_repo.list_all()}
            self._vinc_table.setRowCount(0)
            for v in vinculados:
                prog = todos_progs.get(v.programa_id)
                row = self._vinc_table.rowCount()
                self._vinc_table.insertRow(row)
                self._vinc_table.setItem(row, 0, QTableWidgetItem(v.programa_descripcion))
                self._vinc_table.setItem(
                    row, 1,
                    QTableWidgetItem(f"{prog.frecuencia_meses} mes(es)" if prog else "—")
                )
                self._vinc_table.setItem(
                    row, 2, QTableWidgetItem(prog.ultima_ejecucion if prog else "—")
                )
                self._vinc_table.setItem(
                    row, 3, QTableWidgetItem(prog.proxima_ejecucion if prog else "—")
                )
                item = self._vinc_table.item(row, 0)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, v.programa_id)
            self._vinc_section.setVisible(True)

        for rep in self._repuesto_repo.list_by_orden(orden_id):
            self._add_rep_row(
                rep.descripcion, rep.cantidad, rep.costo_unitario,
                rep_orden_id=rep.id, repuesto_id=rep.repuesto_id,
            )

    def _ver_mantenimiento_vinculado(self) -> None:
        selected = self._vinc_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Sin selección", "Seleccione un mantenimiento de la lista.")
            return
        row = self._vinc_table.row(selected[0])
        item = self._vinc_table.item(row, 0)
        if item is None:
            return
        programa_id = item.data(Qt.ItemDataRole.UserRole)
        if programa_id is None:
            return
        dlg = VerMantenimientoDialog(self._db, programa_id, parent=self)
        dlg.exec()

    def _add_repuesto(self) -> None:
        dlg = AgregarRepuestoOrdenDialog(self._db, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            repuesto_id, nombre, stock_disp, qty, costo = dlg.result_data()
            self._add_rep_row(
                nombre, qty, costo,
                rep_orden_id=None, repuesto_id=repuesto_id, stock_disp=stock_disp,
            )

    def _add_rep_row(
        self,
        descripcion: str,
        cantidad: float,
        costo_unitario: float,
        *,
        rep_orden_id: int | None,
        repuesto_id: int | None,
        stock_disp: float | None = None,
    ) -> None:
        # When loading existing rows, look up current stock if not supplied
        if stock_disp is None and repuesto_id is not None:
            rep = self._repuesto_catalog_repo.get_by_id(repuesto_id)
            stock_disp = rep.stock_actual if rep else 0.0

        row = self._rep_table.rowCount()
        self._rep_table.insertRow(row)

        item_desc = QTableWidgetItem(descripcion)
        # UserRole = rep_orden_id, UserRole+1 = repuesto_id
        item_desc.setData(Qt.ItemDataRole.UserRole, rep_orden_id)
        item_desc.setData(Qt.ItemDataRole.UserRole + 1, repuesto_id)
        self._rep_table.setItem(row, 0, item_desc)
        self._rep_table.setItem(
            row, 1, QTableWidgetItem(f"{stock_disp:g}" if stock_disp is not None else "-")
        )
        self._rep_table.setItem(row, 2, QTableWidgetItem(f"{cantidad:g}"))
        self._rep_table.setItem(row, 3, QTableWidgetItem(f"{costo_unitario:,.2f}"))
        self._rep_table.setItem(row, 4, QTableWidgetItem(f"{cantidad * costo_unitario:,.2f}"))

    def _del_repuesto(self) -> None:
        selected = self._rep_table.selectedItems()
        if not selected:
            return
        row = self._rep_table.row(selected[0])
        item = self._rep_table.item(row, 0)
        rep_orden_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        # If already saved to DB, delete it and restore stock
        if rep_orden_id is not None:
            self._repuesto_repo.delete(rep_orden_id)
        self._rep_table.removeRow(row)

    def _save(self) -> None:
        equipo_id = self._equipo.currentData()
        if equipo_id is None:
            QMessageBox.warning(self, "Validación", "Seleccione un equipo.")
            return

        data = OrdenTrabajoCreate(
            equipo_id=equipo_id,
            tipo=self._tipo.currentData() or "CORRECTIVO",
            descripcion=self._descripcion.toPlainText().strip(),
            fecha_apertura=self._fecha_apertura.date().toString("yyyy-MM-dd"),
            fecha_cierre=self._fecha_cierre.date().toString("yyyy-MM-dd"),
            estado=self._estado.currentData() or "PENDIENTE",
            tecnico_id=self._tecnico.currentData(),
            costo_mano_obra=self._costo_mano_obra.value(),
            observaciones=self._observaciones.toPlainText().strip(),
        )

        try:
            if self._orden_id is None:
                orden_id = self._repo.create(data)
            else:
                self._repo.update(self._orden_id, data)
                orden_id = self._orden_id

            # Save repuestos that don't have a rep_orden_id yet (new rows added in this session)
            for row in range(self._rep_table.rowCount()):
                item = self._rep_table.item(row, 0)
                if item is None:
                    continue
                rep_orden_id = item.data(Qt.ItemDataRole.UserRole)
                repuesto_id = item.data(Qt.ItemDataRole.UserRole + 1)
                if rep_orden_id is None and repuesto_id is not None:
                    desc = item.text()
                    try:
                        qty = float(
                            (self._rep_table.item(row, 2) or QTableWidgetItem("1")).text()
                        )
                        costo = float(
                            (self._rep_table.item(row, 3) or QTableWidgetItem("0"))
                            .text()
                            .replace(",", "")
                        )
                    except ValueError:
                        qty, costo = 1.0, 0.0
                    self._repuesto_repo.create(orden_id, repuesto_id, desc, qty, costo)

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class AgregarRepuestoOrdenDialog(QDialog):
    """Selector de repuesto del catálogo para agregar a una orden de trabajo."""

    def __init__(self, database_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repo = RepuestoRepository(database_path)
        self.setWindowTitle("Agregar repuesto a la orden")
        self.setMinimumWidth(420)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._repuesto_combo = QComboBox()
        self._stock_label = QLabel("-")
        self._stock_label.setObjectName("muted")

        for r in self._repo.list_all(solo_activos=True):
            self._repuesto_combo.addItem(f"{r.nombre}  (stock: {r.stock_actual:g})", r.id)

        self._repuesto_combo.currentIndexChanged.connect(self._on_repuesto_changed)

        self._cantidad = QDoubleSpinBox()
        self._cantidad.setRange(0.001, 99999)
        self._cantidad.setDecimals(3)
        self._cantidad.setValue(1)
        self._cantidad.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._costo_unitario = QDoubleSpinBox()
        self._costo_unitario.setRange(0, 999_999_999)
        self._costo_unitario.setDecimals(2)
        self._costo_unitario.setSuffix(" $")
        self._costo_unitario.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        form.addRow("Repuesto *", self._repuesto_combo)
        form.addRow("Stock disponible", self._stock_label)
        form.addRow("Cantidad a usar *", self._cantidad)
        form.addRow("Costo unitario", self._costo_unitario)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_repuesto_changed()

    def _on_repuesto_changed(self) -> None:
        repuesto_id = self._repuesto_combo.currentData()
        if repuesto_id is None:
            self._stock_label.setText("-")
            return
        rep = self._repo.get_by_id(repuesto_id)
        if rep:
            self._stock_label.setText(f"{rep.stock_actual:g}")

    def _validate_and_accept(self) -> None:
        if self._repuesto_combo.currentData() is None:
            QMessageBox.warning(self, "Validación", "Seleccione un repuesto.")
            return
        if self._cantidad.value() <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0.")
            return
        self.accept()

    def result_data(self) -> tuple[int, str, float, float, float]:
        """Returns (repuesto_id, nombre, stock_disp, cantidad, costo_unitario)."""
        repuesto_id = self._repuesto_combo.currentData()
        nombre = self._repuesto_combo.currentText().split("  (stock:")[0].strip()
        rep = self._repo.get_by_id(repuesto_id)
        stock_disp = rep.stock_actual if rep else 0.0
        return (repuesto_id, nombre, stock_disp, self._cantidad.value(), self._costo_unitario.value())


class RepuestoCatalogDialog(QDialog):
    """CRUD dialog para el catálogo de repuestos."""

    def __init__(
        self, database_path: Path, repuesto_id: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = RepuestoRepository(database_path)
        self._repuesto_id = repuesto_id
        self.setWindowTitle("Repuesto")
        self.setMinimumWidth(400)
        self._build()
        if repuesto_id is not None:
            self._load(repuesto_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._nombre = QLineEdit()

        self._observaciones = QTextEdit()
        self._observaciones.setFixedHeight(70)

        self._stock_actual = QDoubleSpinBox()
        self._stock_actual.setRange(0, 999_999)
        self._stock_actual.setDecimals(3)
        self._stock_actual.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._stock_minimo = QDoubleSpinBox()
        self._stock_minimo.setRange(0, 999_999)
        self._stock_minimo.setDecimals(3)
        self._stock_minimo.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Nombre *", self._nombre)
        form.addRow("Observaciones", self._observaciones)
        form.addRow("Cantidad en stock", self._stock_actual)
        form.addRow("Stock mínimo", self._stock_minimo)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, repuesto_id: int) -> None:
        rep = self._repo.get_by_id(repuesto_id)
        if rep is None:
            return
        self._nombre.setText(rep.nombre)
        self._observaciones.setPlainText(rep.observaciones)
        self._stock_actual.setValue(rep.stock_actual)
        self._stock_minimo.setValue(rep.stock_minimo)
        self._activo.setChecked(rep.activo)

    def _save(self) -> None:
        nombre = self._nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre es requerido.")
            return
        try:
            if self._repuesto_id is None:
                self._repo.create(
                    nombre,
                    self._observaciones.toPlainText().strip(),
                    self._stock_actual.value(),
                    self._stock_minimo.value(),
                )
            else:
                self._repo.update(
                    self._repuesto_id,
                    nombre,
                    self._observaciones.toPlainText().strip(),
                    self._stock_actual.value(),
                    self._stock_minimo.value(),
                    self._activo.isChecked(),
                )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class TipoEquipoDialog(QDialog):
    def __init__(
        self, database_path: Path, tipo_id: int | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = TipoEquipoRepository(database_path)
        self._tipo_id = tipo_id
        self.setWindowTitle("Tipo de Máquina")
        self.setMinimumWidth(360)
        self._build()
        if tipo_id is not None:
            self._load(tipo_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._nombre = QLineEdit()
        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Nombre *", self._nombre)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, tipo_id: int) -> None:
        tipos = self._repo.list_all(solo_activos=False)
        tipo = next((t for t in tipos if t.id == tipo_id), None)
        if tipo is None:
            return
        self._nombre.setText(tipo.nombre)
        self._activo.setChecked(tipo.activo)

    def _save(self) -> None:
        nombre = self._nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre es requerido.")
            return
        try:
            if self._tipo_id is None:
                self._repo.create(nombre)
            else:
                self._repo.update(self._tipo_id, nombre, self._activo.isChecked())
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class VerMantenimientoDialog(QDialog):
    """Vista de solo lectura de un programa de mantenimiento con sus adjuntos."""

    def __init__(
        self,
        database_path: Path,
        programa_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._programa_id = programa_id
        self._prog_repo   = ProgramaMantenimientoRepository(database_path)
        self._adjunto_repo = AdjuntoRepository(database_path)
        self.setWindowTitle("Detalle de mantenimiento")
        self.setMinimumWidth(580)
        self.resize(620, 460)
        self._build()
        self._load()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Datos del programa ───────────────────────────────────────────────
        self._form = QFormLayout()

        self._lbl_equipo   = QLabel()
        self._lbl_desc     = QLabel()
        self._lbl_desc.setWordWrap(True)
        self._lbl_frec     = QLabel()
        self._lbl_ultima   = QLabel()
        self._lbl_proxima  = QLabel()

        for lbl in (self._lbl_equipo, self._lbl_desc, self._lbl_frec,
                    self._lbl_ultima, self._lbl_proxima):
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._form.addRow("Equipo:", self._lbl_equipo)
        self._form.addRow("Descripción:", self._lbl_desc)
        self._form.addRow("Frecuencia:", self._lbl_frec)
        self._form.addRow("Última ejecución:", self._lbl_ultima)
        self._form.addRow("Próxima ejecución:", self._lbl_proxima)
        layout.addLayout(self._form)

        # ── Adjuntos ─────────────────────────────────────────────────────────
        layout.addWidget(_section_title("Adjuntos"))

        self._adj_table = _make_table(["Tipo", "Nombre", "Ruta"])
        self._adj_table.setFixedHeight(140)
        self._adj_table.doubleClicked.connect(self._ver_adjunto)
        layout.addWidget(self._adj_table)

        btn_row = QHBoxLayout()
        btn_ver = _primary_button("Ver archivo")
        btn_ver.clicked.connect(self._ver_adjunto)
        btn_row.addStretch()
        btn_row.addWidget(btn_ver)
        layout.addLayout(btn_row)

        btn_cerrar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_cerrar.rejected.connect(self.reject)
        layout.addWidget(btn_cerrar)

    def _load(self) -> None:
        todos = self._prog_repo.list_all()
        prog  = next((p for p in todos if p.id == self._programa_id), None)
        if prog is None:
            return

        self.setWindowTitle(f"Mantenimiento — {prog.descripcion}")
        self._lbl_equipo.setText(prog.equipo_nombre)
        self._lbl_desc.setText(prog.descripcion)
        self._lbl_frec.setText(f"{prog.frecuencia_meses} mes(es)")
        self._lbl_ultima.setText(prog.ultima_ejecucion or "—")
        self._lbl_proxima.setText(prog.proxima_ejecucion or "—")

        adjuntos = self._adjunto_repo.list_by_programa(self._programa_id)
        self._adj_table.setRowCount(0)
        for a in adjuntos:
            row = self._adj_table.rowCount()
            self._adj_table.insertRow(row)
            self._adj_table.setItem(row, 0, QTableWidgetItem(a.tipo))
            self._adj_table.setItem(row, 1, QTableWidgetItem(a.nombre))
            self._adj_table.setItem(row, 2, QTableWidgetItem(a.ruta))
            item = self._adj_table.item(row, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, a.ruta)

    def _ver_adjunto(self) -> None:
        selected = self._adj_table.selectedItems()
        if not selected:
            return
        row = self._adj_table.row(selected[0])
        item = self._adj_table.item(row, 0)
        if item is None:
            return
        ruta = Path(item.data(Qt.ItemDataRole.UserRole) or "")
        if not ruta.exists():
            QMessageBox.warning(self, "Archivo no encontrado",
                                f"El archivo ya no existe en:\n{ruta}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta)))


class AdjuntosDialog(QDialog):
    """Gestiona fotos y PDFs adjuntos a un programa de mantenimiento."""

    def __init__(
        self,
        database_path: Path,
        programa_id: int,
        programa_desc: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._programa_id = programa_id
        self._repo = AdjuntoRepository(database_path)
        self.setWindowTitle(f"Adjuntos — {programa_desc}")
        self.setMinimumWidth(620)
        self.resize(680, 380)
        self._build()
        self._refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._tabla = _make_table(["Tipo", "Nombre", "Ruta"])
        self._tabla.doubleClicked.connect(self._ver)
        layout.addWidget(self._tabla)

        btn_bar = QHBoxLayout()
        btn_foto = _primary_button("+ Agregar foto")
        btn_pdf  = _primary_button("+ Agregar PDF")
        btn_ver  = QPushButton("Ver")
        btn_elim = _danger_button("Eliminar")
        btn_cerrar = QPushButton("Cerrar")

        btn_foto.clicked.connect(lambda: self._agregar("FOTO"))
        btn_pdf.clicked.connect(lambda: self._agregar("PDF"))
        btn_ver.clicked.connect(self._ver)
        btn_elim.clicked.connect(self._eliminar)
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_foto)
        btn_bar.addWidget(btn_pdf)
        btn_bar.addWidget(btn_ver)
        btn_bar.addWidget(btn_elim)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cerrar)
        layout.addLayout(btn_bar)

    def _refresh(self) -> None:
        adjuntos = self._repo.list_by_programa(self._programa_id)
        self._tabla.setRowCount(0)
        for a in adjuntos:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(a.tipo))
            self._tabla.setItem(row, 1, QTableWidgetItem(a.nombre))
            self._tabla.setItem(row, 2, QTableWidgetItem(a.ruta))
            item = self._tabla.item(row, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, a.id)

    def _agregar(self, tipo: str) -> None:
        if tipo == "FOTO":
            filtro = "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        else:
            filtro = "PDF (*.pdf)"

        ruta, _ = QFileDialog.getOpenFileName(self, f"Seleccionar {tipo}", "", filtro)
        if not ruta:
            return

        nombre = Path(ruta).name
        self._repo.create(self._programa_id, tipo, nombre, ruta)
        self._refresh()

    def _selected_adjunto_id(self) -> int | None:
        selected = self._tabla.selectedItems()
        if not selected:
            return None
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _ver(self) -> None:
        selected = self._tabla.selectedItems()
        if not selected:
            return
        row = self._tabla.row(selected[0])
        ruta_item = self._tabla.item(row, 2)
        if ruta_item is None:
            return
        ruta = Path(ruta_item.text())
        if not ruta.exists():
            QMessageBox.warning(self, "Archivo no encontrado",
                                f"El archivo ya no existe en:\n{ruta}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta)))

    def _eliminar(self) -> None:
        adj_id = self._selected_adjunto_id()
        if adj_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un adjunto.")
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Quitar el acceso directo? (El archivo original no se toca.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._repo.delete(adj_id)
        self._refresh()


class MantenimientosEquipoDialog(QDialog):
    """Sub-ventana que lista y gestiona todos los programas de mantenimiento de un equipo."""

    def __init__(
        self,
        database_path: Path,
        equipo_id: int,
        equipo_nombre: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._equipo_id = equipo_id
        self._repo = ProgramaMantenimientoRepository(database_path)
        self.setWindowTitle(f"Mantenimientos — {equipo_nombre}")
        self.setMinimumWidth(750)
        self.resize(800, 480)
        self._build()
        self._refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._tabla = _make_table(
            ["#", "Descripción", "Frecuencia (meses)",
             "Última ejecución", "Próxima ejecución", "Estado"]
        )
        self._tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self._tabla)

        btn_bar = QHBoxLayout()
        btn_crear  = _primary_button("+ Crear")
        btn_editar = QPushButton("Editar")
        btn_elim   = _danger_button("Eliminar")
        btn_cerrar = QPushButton("Cerrar")

        btn_crear.clicked.connect(lambda: self._crear())
        btn_editar.clicked.connect(self._editar)
        btn_elim.clicked.connect(self._eliminar)

        btn_adjuntos = QPushButton("Adjuntos")
        btn_adjuntos.clicked.connect(self._abrir_adjuntos)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_crear)
        btn_bar.addWidget(btn_editar)
        btn_bar.addWidget(btn_elim)
        btn_bar.addWidget(btn_adjuntos)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cerrar)
        layout.addLayout(btn_bar)

    def _refresh(self) -> None:
        todos = self._repo.list_all()
        programas = [p for p in todos if p.equipo_id == self._equipo_id]
        tabla = self._tabla
        tabla.setRowCount(0)
        hoy = date.today()
        for p in programas:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(p.id)))
            tabla.setItem(row, 1, QTableWidgetItem(p.descripcion))
            tabla.setItem(row, 2, QTableWidgetItem(str(p.frecuencia_meses)))
            tabla.setItem(row, 3, QTableWidgetItem(p.ultima_ejecucion))
            tabla.setItem(row, 4, QTableWidgetItem(p.proxima_ejecucion))
            tabla.setItem(row, 5, QTableWidgetItem("Activo" if p.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, p.id)
            # Colorear vencidos
            try:
                proxima = date.fromisoformat(p.proxima_ejecucion)
                if proxima < hoy:
                    brush = QBrush(_COLOR_VENCIDO)
                    for col in range(tabla.columnCount()):
                        it = tabla.item(row, col)
                        if it:
                            it.setBackground(brush)
            except ValueError:
                pass

    def _selected_prog_id(self) -> int | None:
        selected = self._tabla.selectedItems()
        if not selected:
            return None
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        if item is None:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        return int(val) if val is not None else None

    def _abrir_adjuntos(self) -> None:
        prog_id = self._selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa primero.")
            return
        # Obtener descripción del programa seleccionado
        selected = self._tabla.selectedItems()
        row = self._tabla.row(selected[0])
        desc = (self._tabla.item(row, 1) or QTableWidgetItem("")).text()
        dlg = AdjuntosDialog(self._db, prog_id, desc, parent=self)
        dlg.exec()

    def _crear(self) -> None:
        dlg = ProgramaDialog(self._db, None, equipo_id_fijo=self._equipo_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh()

    def _editar(self) -> None:
        prog_id = self._selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        dlg = ProgramaDialog(self._db, prog_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh()

    def _eliminar(self) -> None:
        prog_id = self._selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar este programa de mantenimiento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.delete(prog_id)
            self._refresh()


class ProgramaDialog(QDialog):
    def __init__(
        self,
        database_path: Path,
        programa_id: int | None = None,
        *,
        equipo_id_fijo: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._programa_id = programa_id
        self._equipo_id_fijo = equipo_id_fijo
        self._repo = ProgramaMantenimientoRepository(database_path)
        self._equipo_repo = EquipoRepository(database_path)
        self.setWindowTitle("Programa de Mantenimiento")
        self.setMinimumWidth(460)
        self._build()
        if programa_id is not None:
            self._load(programa_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._equipo = QComboBox()
        for eq in self._equipo_repo.list_all(solo_activos=True):
            self._equipo.addItem(eq.etiqueta, eq.id)

        # Si se abre desde MantenimientosEquipoDialog, bloquear el combo al equipo
        if self._equipo_id_fijo is not None:
            idx = self._equipo.findData(self._equipo_id_fijo)
            if idx >= 0:
                self._equipo.setCurrentIndex(idx)
            self._equipo.setEnabled(False)

        self._descripcion = QLineEdit()

        self._frecuencia = QSpinBox()
        self._frecuencia.setRange(1, 120)
        self._frecuencia.setValue(1)
        self._frecuencia.setSuffix(" meses")
        self._frecuencia.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._ultima = QDateEdit()
        self._ultima.setCalendarPopup(True)
        self._ultima.setDate(QDate.currentDate())

        self._proxima = QDateEdit()
        self._proxima.setCalendarPopup(True)
        hoy = date.today()
        proxima_default = hoy + timedelta(days=30)
        self._proxima.setDate(QDate(proxima_default.year, proxima_default.month, proxima_default.day))

        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Equipo *", self._equipo)
        form.addRow("Descripción *", self._descripcion)
        form.addRow("Frecuencia", self._frecuencia)
        form.addRow("Última ejecución", self._ultima)
        form.addRow("Próxima ejecución", self._proxima)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, programa_id: int) -> None:
        programas = self._repo.list_all()
        prog = next((p for p in programas if p.id == programa_id), None)
        if prog is None:
            return

        idx = self._equipo.findData(prog.equipo_id)
        if idx >= 0:
            self._equipo.setCurrentIndex(idx)

        self._descripcion.setText(prog.descripcion)
        self._frecuencia.setValue(prog.frecuencia_meses)

        if prog.ultima_ejecucion:
            try:
                d = date.fromisoformat(prog.ultima_ejecucion)
                self._ultima.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass

        if prog.proxima_ejecucion:
            try:
                d = date.fromisoformat(prog.proxima_ejecucion)
                self._proxima.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass

        self._activo.setChecked(prog.activo)

    def _save(self) -> None:
        equipo_id = self._equipo.currentData()
        descripcion = self._descripcion.text().strip()

        if equipo_id is None or not descripcion:
            QMessageBox.warning(self, "Validación", "Equipo y descripción son requeridos.")
            return

        try:
            if self._programa_id is None:
                self._repo.create(
                    equipo_id,
                    descripcion,
                    self._frecuencia.value(),
                    self._ultima.date().toString("yyyy-MM-dd"),
                    self._proxima.date().toString("yyyy-MM-dd"),
                )
            else:
                self._repo.update(
                    self._programa_id,
                    equipo_id,
                    descripcion,
                    self._frecuencia.value(),
                    self._ultima.date().toString("yyyy-MM-dd"),
                    self._proxima.date().toString("yyyy-MM-dd"),
                    self._activo.isChecked(),
                )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
