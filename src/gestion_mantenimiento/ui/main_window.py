from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QTimer, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import QColorDialog, QFileDialog
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
    AlertaRepository,
    EquipoRepository,
    OrdenProgramaRepository,
    OrdenTrabajoRepository,
    PasoRepository,
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
    save_theme_colors,
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

# Colores de fila usados en tablas — se leen desde self._current_theme en runtime
_COLOR_VENCE_MES_DEFAULT = "#FFF3CD"
_COLOR_VENCIDO_DEFAULT   = "#FFD6D6"

_COLOR_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("General", [
        ("app_background",        "Fondo general"),
        ("text_color",            "Texto principal"),
        ("muted_text",            "Texto secundario"),
        ("disabled_text",         "Texto deshabilitado"),
        ("menu_background",       "Fondo de menú"),
    ]),
    ("Paneles e inputs", [
        ("panel_background",         "Paneles"),
        ("panel_header_background",  "Cabecera de panel"),
        ("input_background",         "Campos de texto"),
        ("border_color",             "Bordes"),
    ]),
    ("Acento y acciones", [
        ("accent_color",          "Color de acento"),
        ("primary_button_text",   "Texto en botón primario"),
        ("danger_color",          "Color de peligro"),
    ]),
    ("Sidebar", [
        ("sidebar_background",    "Fondo del sidebar"),
        ("brand_text",            "Texto de marca"),
        ("sidebar_subtitle_text", "Subtítulo"),
        ("nav_text",              "Ítems de navegación"),
        ("nav_active_text",       "Ítem activo — texto"),
        ("nav_active_background", "Ítem activo — fondo"),
    ]),
    ("Tabla", [
        ("table_alt_background",    "Filas alternas"),
        ("table_header_background", "Cabecera"),
        ("table_header_text",       "Texto de cabecera"),
    ]),
    ("Títulos", [
        ("page_title_text",     "Título de página"),
        ("section_title_text",  "Título de sección"),
        ("metric_value_text",   "Valor de métricas"),
    ]),
    ("Programa de mantenimiento", [
        ("color_vence_mes", "Vence este mes (resaltado)"),
        ("color_vencido",   "Vencido (resaltado)"),
    ]),
]

_NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Tipos de Máquina", "tipos_equipo"),
    ("Equipos", "equipos"),
    ("Repuestos", "repuestos"),
    ("Órdenes de Trabajo", "ordenes"),
    ("Programa Mantenimiento", "programa"),
    ("Cronograma", "cronograma"),
    ("Técnicos", "tecnicos"),
    ("Opciones", "opciones"),
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
    def __init__(
        self, database_path: Path, theme_mode: str = "light",
        initial_theme: dict | None = None,
    ) -> None:
        super().__init__()
        self._db = database_path
        self._theme_mode = theme_mode
        self._current_theme: dict = dict(initial_theme) if initial_theme else get_theme(theme_mode)
        self._opciones_btns: dict[str, QPushButton] = {}
        self._opciones_font_size: QSpinBox | None = None
        self._equipo_repo = EquipoRepository(database_path)
        self._tecnico_repo = TecnicoRepository(database_path)
        self._tipo_repo = TipoEquipoRepository(database_path)
        self._orden_repo = OrdenTrabajoRepository(database_path)
        self._repuesto_repo = RepuestoOrdenRepository(database_path)
        self._repuesto_catalog_repo = RepuestoRepository(database_path)
        self._programa_repo = ProgramaMantenimientoRepository(database_path)
        self._orden_programa_repo = OrdenProgramaRepository(database_path)
        self._adjunto_repo = AdjuntoRepository(database_path)
        self._alerta_repo = AlertaRepository(database_path)

        self.setWindowTitle(f"Gestión Mantenimiento v{__version__}")
        self.resize(1280, 800)
        self._build_ui()
        self._navigate("dashboard")
        # Alertas: refresco inicial + timer cada 5 minutos
        self._refresh_alertas_badge()
        self._alertas_timer = QTimer(self)
        self._alertas_timer.timeout.connect(self._refresh_alertas_badge)
        self._alertas_timer.start(5 * 60 * 1000)
        # Generación automática: al inicio y luego cada 24 horas
        self._auto_generar_ordenes()
        self._auto_gen_timer = QTimer(self)
        self._auto_gen_timer.timeout.connect(self._auto_generar_ordenes)
        self._auto_gen_timer.start(24 * 60 * 60 * 1000)

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

        # Badge de alertas
        self._alertas_btn = QPushButton(sidebar)
        self._alertas_btn.setObjectName("navButton")
        self._alertas_btn.clicked.connect(self._open_alertas)
        layout.addWidget(self._alertas_btn)

        self._theme_btn = QPushButton(sidebar)
        self._theme_btn.setObjectName("navButton")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_btn_label()
        layout.addWidget(self._theme_btn)

        api_label = QLabel("App técnicos:", sidebar)
        api_label.setObjectName("muted")
        api_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(api_label)

        api_url_label = QLabel("mantenimiento:54321", sidebar)
        api_url_label.setObjectName("muted")
        api_url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        api_url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(api_url_label)

        version_label = QLabel(f"v{__version__}", sidebar)
        version_label.setObjectName("muted")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        return sidebar

    def _refresh_alertas_badge(self) -> None:
        alertas = self._alerta_repo.compute()
        n = len(alertas)
        if n == 0:
            self._alertas_btn.setText("Sin alertas")
            self._alertas_btn.setStyleSheet("")
        else:
            self._alertas_btn.setText(f"⚠ Alertas ({n})")
            # Resaltar en rojo si hay alertas
            self._alertas_btn.setStyleSheet(
                "QPushButton { color: #f87171; font-weight: 700; }"
            )

    def _open_alertas(self) -> None:
        dlg = AlertasDialog(self._db, parent=self)
        dlg.exec()
        self._refresh_alertas_badge()

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
        from gestion_mantenimiento.data.paths import get_theme_path
        theme = get_theme(mode)
        self._apply_theme_dict(theme)
        save_theme_mode(get_theme_path(), mode)

    def _apply_theme_dict(self, theme: dict) -> None:
        from PySide6.QtWidgets import QApplication
        self._current_theme = dict(theme)
        app = QApplication.instance()
        if app is None:
            return
        palette = build_app_palette(theme)
        app.setStyleSheet("")
        app.setStyleSheet(build_app_styles(theme))
        app.setPalette(palette)
        for widget in app.allWidgets():
            widget.setPalette(palette)
            widget.update()
        self._update_opciones_colors()

    def _update_opciones_colors(self) -> None:
        for key, btn in self._opciones_btns.items():
            color = str(self._current_theme.get(key, "#000000"))
            _set_color_btn_style(btn, color)
        if self._opciones_font_size is not None:
            self._opciones_font_size.setValue(
                int(self._current_theme.get("base_font_size", 14))
            )

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
            "cronograma": self._build_cronograma_page,
            "tecnicos": self._build_tecnicos_page,
            "opciones": self._build_opciones_page,
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
        btn_historial = QPushButton("Ver historial")
        btn_historial.clicked.connect(self._open_historial_equipo)

        act_layout.addWidget(btn_historial)
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

    def _open_historial_equipo(self) -> None:
        equipo_id = self._selected_id(self._eq_table)
        if equipo_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un equipo de la lista.")
            return
        row = self._eq_table.currentRow()
        nombre = (self._eq_table.item(row, 1) or QTableWidgetItem("")).text()
        dlg = HistorialEquipoDialog(self._db, equipo_id, nombre, parent=self)
        dlg.exec()

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

        # ── Selector de máquina ──────────────────────────────────────────────
        top_panel = QFrame()
        top_panel.setObjectName("panel")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(16, 10, 16, 10)

        top_layout.addWidget(QLabel("Máquina:"))
        self._prog_equipo_combo = QComboBox()
        self._prog_equipo_combo.setMinimumWidth(260)
        self._prog_equipo_combo.currentIndexChanged.connect(lambda: self._refresh_programas())
        top_layout.addWidget(self._prog_equipo_combo)

        top_layout.addSpacing(24)
        top_layout.addWidget(QLabel("Mes ref.:"))

        self._prog_mes = QComboBox()
        for nombre in _MESES:
            self._prog_mes.addItem(nombre)
        self._prog_mes.setCurrentIndex(date.today().month - 1)
        self._prog_mes.setFixedWidth(120)
        self._prog_mes.currentIndexChanged.connect(lambda: self._refresh_programas())
        top_layout.addWidget(self._prog_mes)

        self._prog_anio = QSpinBox()
        self._prog_anio.setRange(2000, 2100)
        self._prog_anio.setValue(date.today().year)
        self._prog_anio.setFixedWidth(76)
        self._prog_anio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._prog_anio.valueChanged.connect(lambda: self._refresh_programas())
        top_layout.addWidget(self._prog_anio)

        top_layout.addSpacing(20)
        leyenda_amarilla = QLabel("■ vence este mes")
        leyenda_amarilla.setStyleSheet("color: #b8860b; font-size: 12px;")
        leyenda_roja = QLabel("■ vencido")
        leyenda_roja.setStyleSheet("color: #b42318; font-size: 12px;")
        top_layout.addWidget(leyenda_amarilla)
        top_layout.addSpacing(10)
        top_layout.addWidget(leyenda_roja)
        top_layout.addStretch()

        self._prog_show_inactive = QCheckBox("Ver inactivas")
        self._prog_show_inactive.stateChanged.connect(lambda: self._reload_equipo_combo())
        top_layout.addWidget(self._prog_show_inactive)
        layout.addWidget(top_panel)

        # ── Tabla de programas de la máquina seleccionada ────────────────────
        self._prog_table = _make_table(
            ["#", "Descripción", "Frecuencia (meses)", "Última ejecución", "Próxima ejecución", "Estado"]
        )
        self._prog_table.doubleClicked.connect(self._prog_editar)
        layout.addWidget(self._prog_table)

        # ── Barra de acciones ────────────────────────────────────────────────
        act_layout = QHBoxLayout()
        btn_crear    = _primary_button("+ Nuevo")
        btn_editar   = QPushButton("Editar")
        btn_elim     = _danger_button("Eliminar")
        btn_adjuntos = QPushButton("Adjuntos")
        btn_pasos    = QPushButton("Pasos")
        btn_generar  = _primary_button("Generar órdenes del mes")

        btn_crear.clicked.connect(lambda: self._prog_crear())
        btn_editar.clicked.connect(self._prog_editar)
        btn_elim.clicked.connect(self._prog_eliminar)
        btn_adjuntos.clicked.connect(self._prog_adjuntos)
        btn_pasos.clicked.connect(self._prog_pasos)
        btn_generar.clicked.connect(lambda: self._generar_ordenes_mes())

        act_layout.addWidget(btn_crear)
        act_layout.addWidget(btn_editar)
        act_layout.addWidget(btn_elim)
        act_layout.addWidget(btn_adjuntos)
        act_layout.addWidget(btn_pasos)
        act_layout.addStretch()
        act_layout.addWidget(btn_generar)
        layout.addLayout(act_layout)

        def refresh() -> None:
            self._reload_equipo_combo()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _reload_equipo_combo(self) -> None:
        solo_activos = not self._prog_show_inactive.isChecked()
        equipos = self._equipo_repo.list_all(solo_activos=solo_activos)
        prev_id = self._prog_equipo_combo.currentData()
        self._prog_equipo_combo.blockSignals(True)
        self._prog_equipo_combo.clear()
        for eq in equipos:
            self._prog_equipo_combo.addItem(f"{eq.nombre}  ({eq.tipo_nombre})", eq.id)
        # Restaurar selección anterior si sigue existiendo
        if prev_id is not None:
            idx = self._prog_equipo_combo.findData(prev_id)
            if idx >= 0:
                self._prog_equipo_combo.setCurrentIndex(idx)
        self._prog_equipo_combo.blockSignals(False)
        self._refresh_programas()

    def _prog_selected_equipo_id(self) -> int | None:
        data = self._prog_equipo_combo.currentData()
        return int(data) if data is not None else None

    def _prog_selected_prog_id(self) -> int | None:
        selected = self._prog_table.selectedItems()
        if not selected:
            return None
        row = self._prog_table.row(selected[0])
        item = self._prog_table.item(row, 0)
        if item is None:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        return int(val) if val is not None else None

    def _refresh_programas(self) -> None:
        equipo_id = self._prog_selected_equipo_id()
        mes_sel   = self._prog_mes.currentIndex() + 1
        anio_sel  = self._prog_anio.value()
        hoy = date.today()

        tabla = self._prog_table
        tabla.setRowCount(0)

        if equipo_id is None:
            return

        todos = self._programa_repo.list_all()
        programas = [p for p in todos if p.equipo_id == equipo_id]

        for p in programas:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(p.id)))
            tabla.setItem(row, 1, QTableWidgetItem(p.descripcion))
            tabla.setItem(row, 2, QTableWidgetItem(str(p.frecuencia_meses)))
            tabla.setItem(row, 3, QTableWidgetItem(p.ultima_ejecucion))
            tabla.setItem(row, 4, QTableWidgetItem(p.proxima_ejecucion))
            tabla.setItem(row, 5, QTableWidgetItem("Activo" if p.activo else "Inactivo"))

            item0 = tabla.item(row, 0)
            if item0:
                item0.setData(Qt.ItemDataRole.UserRole, p.id)

            # Coloreado
            color: QColor | None = None
            try:
                proxima = date.fromisoformat(p.proxima_ejecucion)
                if proxima < hoy:
                    color = QColor(str(self._current_theme.get("color_vencido", _COLOR_VENCIDO_DEFAULT)))
                elif proxima.year == anio_sel and proxima.month == mes_sel:
                    color = QColor(str(self._current_theme.get("color_vence_mes", _COLOR_VENCE_MES_DEFAULT)))
            except ValueError:
                pass

            if color is not None:
                brush = QBrush(color)
                for col in range(tabla.columnCount()):
                    it = tabla.item(row, col)
                    if it:
                        it.setBackground(brush)

    def _prog_crear(self) -> None:
        equipo_id = self._prog_selected_equipo_id()
        if equipo_id is None:
            QMessageBox.information(self, "Sin máquina", "Seleccione una máquina primero.")
            return
        dlg = ProgramaDialog(self._db, None, equipo_id_fijo=equipo_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_programas()

    def _prog_editar(self) -> None:
        prog_id = self._prog_selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        dlg = ProgramaDialog(self._db, prog_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_programas()

    def _prog_eliminar(self) -> None:
        prog_id = self._prog_selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar este programa de mantenimiento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._programa_repo.delete(prog_id)
            self._refresh_programas()

    def _prog_adjuntos(self) -> None:
        prog_id = self._prog_selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        selected = self._prog_table.selectedItems()
        row = self._prog_table.row(selected[0])
        desc = (self._prog_table.item(row, 1) or QTableWidgetItem("")).text()
        dlg = AdjuntosDialog(self._db, prog_id, desc, parent=self)
        dlg.exec()

    def _prog_pasos(self) -> None:
        prog_id = self._prog_selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa.")
            return
        selected = self._prog_table.selectedItems()
        row = self._prog_table.row(selected[0])
        desc = (self._prog_table.item(row, 1) or QTableWidgetItem("")).text()
        dlg = PasosDialog(self._db, prog_id, desc, parent=self)
        dlg.exec()

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

    def _auto_generar_ordenes(self) -> None:
        """Genera automáticamente órdenes preventivas para programas vencidos o que vencen hoy."""
        hoy = date.today()
        programas = self._programa_repo.list_all(solo_activos=True)
        creadas = 0

        for p in programas:
            if not p.proxima_ejecucion:
                continue
            try:
                proxima = date.fromisoformat(p.proxima_ejecucion)
            except ValueError:
                continue
            if proxima > hoy:
                continue  # Aún no vence

            # ¿Ya existe una orden pendiente o en progreso?
            if self._orden_programa_repo.find_orden_pendiente(p.equipo_id, [p.id]) is not None:
                # Hay una orden abierta — solo avanzar fecha si ya venció
                if proxima < hoy:
                    self._programa_repo.advance_proxima(p.id, p.proxima_ejecucion, p.frecuencia_meses)
                continue

            # ¿Ya existe una orden COMPLETADA que cubre este ciclo?
            if self._orden_programa_repo.find_orden_completada_desde(
                p.equipo_id, [p.id], p.proxima_ejecucion
            ) is not None:
                # El trabajo ya fue hecho — solo avanzar la fecha al siguiente ciclo
                self._programa_repo.advance_proxima(p.id, p.proxima_ejecucion, p.frecuencia_meses)
                continue

            orden_data = OrdenTrabajoCreate(
                equipo_id=p.equipo_id,
                tipo="PREVENTIVO",
                descripcion=f"Mantenimiento preventivo — {p.descripcion}",
                fecha_apertura=hoy.isoformat(),
                fecha_cierre="",
                estado="PENDIENTE",
                tecnico_id=None,
                costo_mano_obra=0.0,
                observaciones=(
                    f"Generada automáticamente. Programa: {p.descripcion} "
                    f"(frecuencia: {p.frecuencia_meses} meses)"
                ),
            )
            orden_id = self._orden_repo.create(orden_data)
            self._orden_programa_repo.link(orden_id, p.id)
            self._programa_repo.advance_proxima(p.id, p.proxima_ejecucion, p.frecuencia_meses)
            creadas += 1

        if creadas > 0:
            self._refresh_alertas_badge()

    # ── Cronograma ───────────────────────────────────────────────────────────

    def _build_cronograma_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Cronograma de mantenimiento"))

        # Selector de año
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Año:"))
        self._crono_year_combo = QComboBox()
        anio_actual = date.today().year
        for y in range(anio_actual - 2, anio_actual + 5):
            self._crono_year_combo.addItem(str(y), y)
        self._crono_year_combo.setCurrentText(str(anio_actual))
        self._crono_year_combo.currentIndexChanged.connect(self._refresh_cronograma)
        top_bar.addWidget(self._crono_year_combo)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Tabla de cronograma
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._crono_tabla = QTableWidget()
        self._crono_tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._crono_tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._crono_tabla.verticalHeader().setVisible(False)
        scroll.setWidget(self._crono_tabla)
        layout.addWidget(scroll)

        def _refresh(self_page: QWidget = page) -> None:
            self._refresh_cronograma()

        page._refresh = _refresh  # type: ignore[attr-defined]
        return page

    def _refresh_cronograma(self) -> None:
        anio = self._crono_year_combo.currentData()
        if anio is None:
            return

        equipo_repo = EquipoRepository(self._db)
        prog_repo   = ProgramaMantenimientoRepository(self._db)

        equipos  = [e for e in equipo_repo.list_all() if e.activo]
        programas = prog_repo.list_all(solo_activos=True)

        # Agrupar programas por equipo y por mes de proxima_ejecucion dentro del año
        # Un programa aparece en el mes de su proxima_ejecucion si cae en el año seleccionado.
        # También calculamos recurrencias: a partir de proxima_ejecucion cada frecuencia_meses.
        from collections import defaultdict
        # equipo_id → set of month numbers (1-12) with planned maintenance
        planned: dict[int, set[int]] = defaultdict(set)

        for prog in programas:
            if not prog.proxima_ejecucion:
                continue
            try:
                proxima = date.fromisoformat(prog.proxima_ejecucion)
            except ValueError:
                continue
            freq = max(1, prog.frecuencia_meses)
            # Proyectar desde la proxima hacia adelante para todo el año
            # También proyectar hacia atrás desde proxima para cubrir meses anteriores
            # Rango: buscar cuál es la primera ocurrencia que cae dentro del año
            # Retroceder hasta el inicio del año
            cur = proxima
            # Retroceder mientras aún estemos dentro o antes del año
            while True:
                prev_month = cur.month - freq
                prev_year  = cur.year + (prev_month - 1) // 12
                prev_month = ((prev_month - 1) % 12) + 1
                prev = cur.replace(year=prev_year, month=prev_month, day=min(cur.day, 28))
                if prev.year < anio:
                    break
                cur = prev
            # Ahora avanzar por el año seleccionado
            while cur.year <= anio:
                if cur.year == anio:
                    planned[prog.equipo_id].add(cur.month)
                next_month = cur.month + freq
                next_year  = cur.year + (next_month - 1) // 12
                next_month = ((next_month - 1) % 12) + 1
                try:
                    cur = cur.replace(year=next_year, month=next_month)
                except ValueError:
                    cur = cur.replace(year=next_year, month=next_month, day=28)

        # Construir tabla
        tabla = self._crono_tabla
        tabla.clear()
        tabla.setColumnCount(13)  # col 0 = equipo, col 1-12 = meses
        tabla.setRowCount(len(equipos))

        headers = ["Equipo"] + _MESES
        tabla.setHorizontalHeaderLabels(headers)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 13):
            tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        color_ok  = QColor("#C6EFCE")   # verde claro
        color_none = QColor(0, 0, 0, 0)  # transparente

        hoy = date.today()

        for row, equipo in enumerate(equipos):
            nombre_item = QTableWidgetItem(equipo.nombre)
            tabla.setItem(row, 0, nombre_item)
            meses_planificados = planned.get(equipo.id, set())
            for mes in range(1, 13):
                if mes in meses_planificados:
                    # Resaltar el mes actual con un tono más oscuro
                    if anio == hoy.year and mes == hoy.month:
                        cell_color = QColor("#70AD47")
                    else:
                        cell_color = color_ok
                    item = QTableWidgetItem("✔")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QBrush(cell_color))
                else:
                    item = QTableWidgetItem("")
                    item.setBackground(QBrush(color_none))
                tabla.setItem(row, mes, item)

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
            ["ID", "Apellido", "Nombre", "Legajo", "Teléfono", "Especialidad", "Estado"]
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
        btn_pass = QPushButton("Cambiar contraseña")
        btn_pass.clicked.connect(self._cambiar_password_tecnico)

        act_layout.addWidget(btn_pass)
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
            tabla.setItem(row, 3, QTableWidgetItem(t.legajo))
            tabla.setItem(row, 4, QTableWidgetItem(t.telefono))
            tabla.setItem(row, 5, QTableWidgetItem(t.especialidad))
            tabla.setItem(row, 6, QTableWidgetItem("Activo" if t.activo else "Inactivo"))
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, t.id)

    def _cambiar_password_tecnico(self) -> None:
        tecnico_id = self._selected_id(self._tec_table)
        if tecnico_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un técnico de la lista.")
            return
        row = self._tec_table.currentRow()
        nombre = (self._tec_table.item(row, 1) or QTableWidgetItem("")).text()
        apellido = (self._tec_table.item(row, 0) or QTableWidgetItem("")).text()
        dlg = CambiarPasswordDialog(self._db, tecnico_id, f"{nombre} {apellido}".strip(), parent=self)
        dlg.exec()

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

    # ── Opciones ──────────────────────────────────────────────────────────────

    def _build_opciones_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 32)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Opciones de apariencia"))

        # ── Tipografía ───────────────────────────────────────────────────────
        layout.addWidget(_section_title("Tipografía"))
        tipo_form = QFormLayout()
        self._opciones_font_size = QSpinBox()
        self._opciones_font_size.setRange(10, 22)
        self._opciones_font_size.setValue(int(self._current_theme.get("base_font_size", 14)))
        self._opciones_font_size.setSuffix(" px")
        self._opciones_font_size.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._opciones_font_size.setFixedWidth(90)
        self._opciones_font_size.valueChanged.connect(self._opciones_change_font_size)
        tipo_form.addRow("Tamaño de fuente:", self._opciones_font_size)
        layout.addLayout(tipo_form)

        # ── Grupos de colores ────────────────────────────────────────────────
        self._opciones_btns = {}
        for group_name, keys in _COLOR_GROUPS:
            layout.addWidget(_section_title(group_name))
            form = QFormLayout()
            for key, label in keys:
                color = str(self._current_theme.get(key, "#000000"))
                btn = QPushButton()
                _set_color_btn_style(btn, color)
                btn.clicked.connect(lambda checked, k=key: self._opciones_pick_color(k))
                self._opciones_btns[key] = btn
                form.addRow(label + ":", btn)
            layout.addLayout(form)

        layout.addStretch()

        # ── Botones ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_restore = QPushButton("Restaurar predeterminados")
        btn_save = _primary_button("Guardar colores")
        btn_restore.clicked.connect(self._opciones_restore)
        btn_save.clicked.connect(self._opciones_save)
        btn_row.addWidget(btn_restore)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _opciones_pick_color(self, key: str) -> None:
        current = QColor(str(self._current_theme.get(key, "#000000")))
        color = QColorDialog.getColor(current, self, "Elegir color")
        if not color.isValid():
            return
        self._current_theme[key] = color.name()
        btn = self._opciones_btns.get(key)
        if btn:
            _set_color_btn_style(btn, color.name())
        self._apply_theme_dict(self._current_theme)

    def _opciones_change_font_size(self, value: int) -> None:
        self._current_theme["base_font_size"] = value
        self._apply_theme_dict(self._current_theme)

    def _opciones_restore(self) -> None:
        base = get_theme(self._theme_mode)
        self._apply_theme_dict(base)

    def _opciones_save(self) -> None:
        from gestion_mantenimiento.data.paths import get_theme_path
        save_theme_colors(get_theme_path(), self._current_theme)
        QMessageBox.information(self, "Opciones", "Colores guardados correctamente.")

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


def _set_color_btn_style(btn: QPushButton, color: str) -> None:
    btn.setStyleSheet(
        f"QPushButton {{ background-color: {color}; border: 2px solid #666;"
        f" border-radius: 4px; min-width: 60px; min-height: 28px; }}"
        f"QPushButton:hover {{ border-color: #aaa; }}"
    )


# ── Dialogs ───────────────────────────────────────────────────────────────────

class HistorialEquipoDialog(QDialog):
    """Historial completo de mantenimientos realizados en un equipo."""

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
        self.setWindowTitle(f"Historial — {equipo_nombre}")
        self.setMinimumWidth(800)
        self.resize(860, 520)
        self._build()
        self._load()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._tabla = _make_table(
            ["Fecha cierre", "Tipo", "Descripción", "Técnico(s)", "Estado"]
        )
        self._tabla.doubleClicked.connect(self._ver_observaciones)
        layout.addWidget(self._tabla)

        btn_row = QHBoxLayout()
        btn_obs = QPushButton("Ver observaciones")
        btn_obs.clicked.connect(self._ver_observaciones)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_row.addWidget(btn_obs)
        btn_row.addStretch()
        btn_row.addWidget(btn_cerrar)
        layout.addLayout(btn_row)

    def _load(self) -> None:
        import sqlite3 as _sqlite3
        from contextlib import closing as _closing

        with _closing(_sqlite3.connect(self._db)) as conn:
            conn.row_factory = _sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    o.id,
                    o.tipo,
                    COALESCE(o.descripcion, '')    AS descripcion,
                    COALESCE(o.fecha_cierre, '')   AS fecha_cierre,
                    COALESCE(o.fecha_apertura, '') AS fecha_apertura,
                    o.estado,
                    COALESCE(o.observaciones, '')  AS observaciones,
                    COALESCE(trim(t.nombre || ' ' || t.apellido), '') AS tecnico_nombre
                FROM ordenes_trabajo o
                LEFT JOIN tecnicos t ON t.id = o.tecnico_id
                WHERE o.equipo_id = ?
                ORDER BY
                    CASE WHEN o.fecha_cierre = '' OR o.fecha_cierre IS NULL THEN 1 ELSE 0 END,
                    o.fecha_cierre DESC,
                    o.id DESC
                """,
                (self._equipo_id,),
            ).fetchall()

            # Colaboradores por orden
            colab_by_orden: dict[int, list[str]] = {}
            for r in rows:
                colab_rows = conn.execute(
                    """
                    SELECT trim(t2.nombre || ' ' || t2.apellido)
                    FROM orden_colaboradores oc
                    JOIN tecnicos t2 ON t2.id = oc.tecnico_id
                    WHERE oc.orden_id = ?
                    ORDER BY oc.creado_en
                    """,
                    (int(r["id"]),),
                ).fetchall()
                colab_by_orden[int(r["id"])] = [c[0] for c in colab_rows]

        self._tabla.setRowCount(0)
        for r in rows:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            fecha = r["fecha_cierre"] or r["fecha_apertura"]
            tecnicos = colab_by_orden.get(int(r["id"]), [])
            tecnico_str = ", ".join(tecnicos) if tecnicos else str(r["tecnico_nombre"])
            self._tabla.setItem(row, 0, QTableWidgetItem(fecha))
            self._tabla.setItem(row, 1, QTableWidgetItem(str(r["tipo"])))
            self._tabla.setItem(row, 2, QTableWidgetItem(str(r["descripcion"])))
            self._tabla.setItem(row, 3, QTableWidgetItem(tecnico_str))
            self._tabla.setItem(row, 4, QTableWidgetItem(str(r["estado"])))
            item = self._tabla.item(row, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, str(r["observaciones"]))

    def _ver_observaciones(self) -> None:
        selected = self._tabla.selectedItems()
        if not selected:
            return
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        obs = item.data(Qt.ItemDataRole.UserRole) if item else ""
        if not obs:
            QMessageBox.information(self, "Observaciones", "Esta orden no tiene observaciones.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Observaciones")
        dlg.setMinimumWidth(500)
        v = QVBoxLayout(dlg)
        txt = QTextEdit()
        txt.setPlainText(obs)
        txt.setReadOnly(True)
        v.addWidget(txt)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(dlg.accept)
        v.addWidget(bb)
        dlg.exec()


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


class CambiarPasswordDialog(QDialog):
    """Dialog para configurar la contraseña de acceso web de un técnico."""

    def __init__(
        self,
        database_path: Path,
        tecnico_id: int,
        tecnico_nombre: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._tecnico_id = tecnico_id
        self.setWindowTitle(f"Contraseña — {tecnico_nombre}")
        self.setMinimumWidth(360)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        info = QLabel("Esta contraseña se usa para ingresar a la app web desde el celular.")
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self._pass1 = QLineEdit()
        self._pass1.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass1.setPlaceholderText("Nueva contraseña")
        self._pass2 = QLineEdit()
        self._pass2.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass2.setPlaceholderText("Confirmar contraseña")

        form.addRow("Nueva contraseña:", self._pass1)
        form.addRow("Confirmar:", self._pass2)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        p1 = self._pass1.text()
        p2 = self._pass2.text()
        if not p1:
            QMessageBox.warning(self, "Validación", "La contraseña no puede estar vacía.")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Validación", "Las contraseñas no coinciden.")
            return
        try:
            from api.auth import hash_password
            hashed = hash_password(p1)
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(self._db)) as conn:
                conn.execute(
                    "UPDATE tecnicos SET password_hash = ? WHERE id = ?",
                    (hashed, self._tecnico_id),
                )
                conn.commit()
            QMessageBox.information(self, "Listo", "Contraseña actualizada correctamente.")
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
        self._legajo = QLineEdit()
        self._telefono = QLineEdit()
        self._especialidad = QLineEdit()
        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Nombre *", self._nombre)
        form.addRow("Apellido *", self._apellido)
        form.addRow("Legajo", self._legajo)
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
        self._legajo.setText(tec.legajo)
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
                    nombre, apellido, self._legajo.text().strip(),
                    self._telefono.text().strip(), self._especialidad.text().strip(),
                )
            else:
                self._repo.update(
                    self._tecnico_id, nombre, apellido,
                    self._legajo.text().strip(), self._telefono.text().strip(),
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

        # ── Técnicos colaboradores ────────────────────────────────────────────
        self._colab_section = QFrame()
        self._colab_section.setObjectName("panel")
        colab_layout = QVBoxLayout(self._colab_section)
        colab_layout.setContentsMargins(12, 8, 12, 8)
        colab_layout.setSpacing(4)
        colab_layout.addWidget(_section_title("Técnicos que trabajaron en esta orden"))
        self._colab_list = QLabel()
        self._colab_list.setWordWrap(True)
        colab_layout.addWidget(self._colab_list)
        self._colab_section.setVisible(False)
        layout.addWidget(self._colab_section)

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

        # Colaboradores (técnicos que aceptaron la orden)
        import sqlite3 as _sqlite3
        from contextlib import closing as _closing
        with _closing(_sqlite3.connect(self._db)) as _conn:
            _conn.row_factory = _sqlite3.Row
            colab_rows = _conn.execute(
                """
                SELECT trim(t.nombre || ' ' || t.apellido) AS nombre_completo,
                       oc.creado_en
                FROM orden_colaboradores oc
                JOIN tecnicos t ON t.id = oc.tecnico_id
                WHERE oc.orden_id = ?
                ORDER BY oc.creado_en
                """,
                (orden_id,),
            ).fetchall()
        if colab_rows:
            lineas = []
            for i, c in enumerate(colab_rows):
                rol = "Principal" if i == 0 else "Colaborador"
                lineas.append(f"  {rol}: {c['nombre_completo']}")
            self._colab_list.setText("\n".join(lineas))
            self._colab_section.setVisible(True)

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


_TIPO_LABEL = {
    "STOCK_BAJO":  "Stock bajo",
    "ORDEN_NUEVA": "Orden nueva",
    "MANT_VENCIDO": "Mant. vencido",
}
_TIPO_COLOR = {
    "STOCK_BAJO":  "#f59e0b",   # naranja
    "ORDEN_NUEVA": "#3b82f6",   # azul
    "MANT_VENCIDO": "#ef4444",  # rojo
}


class AlertasDialog(QDialog):
    """Centro de alertas: muestra alertas activas con opciones de snooze/ignorar."""

    def __init__(self, database_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db   = database_path
        self._repo = AlertaRepository(database_path)
        self.setWindowTitle("Centro de alertas")
        self.setMinimumWidth(700)
        self.resize(780, 480)
        self._build()
        self._refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._tabla = _make_table(["Tipo", "Título", "Descripción"])
        self._tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._tabla)

        # Leyenda
        leyenda = QLabel(
            "  ⚠ Stock bajo    ●  Orden nueva    ✕  Mantenimiento vencido"
        )
        leyenda.setObjectName("muted")
        layout.addWidget(leyenda)

        btn_bar = QHBoxLayout()
        self._btn_snooze  = QPushButton("Posponer 7 días")
        self._btn_ignorar = _danger_button("Ignorar siempre")
        btn_cerrar        = QPushButton("Cerrar")

        self._btn_snooze.clicked.connect(lambda: self._accion("snooze"))
        self._btn_ignorar.clicked.connect(lambda: self._accion("ignorar"))
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(self._btn_snooze)
        btn_bar.addWidget(self._btn_ignorar)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cerrar)
        layout.addLayout(btn_bar)

        self._no_alertas_lbl = QLabel("No hay alertas activas.")
        self._no_alertas_lbl.setObjectName("muted")
        self._no_alertas_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_alertas_lbl.setVisible(False)
        layout.addWidget(self._no_alertas_lbl)

    def _refresh(self) -> None:
        alertas = self._repo.compute()
        self._tabla.setRowCount(0)

        if not alertas:
            self._tabla.setVisible(False)
            self._no_alertas_lbl.setVisible(True)
            self._btn_snooze.setEnabled(False)
            self._btn_ignorar.setEnabled(False)
            return

        self._tabla.setVisible(True)
        self._no_alertas_lbl.setVisible(False)
        self._btn_snooze.setEnabled(True)
        self._btn_ignorar.setEnabled(True)

        for a in alertas:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)

            tipo_item = QTableWidgetItem(_TIPO_LABEL.get(a.tipo, a.tipo))
            color = _TIPO_COLOR.get(a.tipo, "#888888")
            tipo_item.setForeground(QBrush(QColor(color)))
            tipo_item.setData(Qt.ItemDataRole.UserRole, a.key)
            self._tabla.setItem(row, 0, tipo_item)
            self._tabla.setItem(row, 1, QTableWidgetItem(a.titulo))
            self._tabla.setItem(row, 2, QTableWidgetItem(a.mensaje))

    def _selected_key(self) -> str | None:
        selected = self._tabla.selectedItems()
        if not selected:
            return None
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _accion(self, accion: str) -> None:
        key = self._selected_key()
        if key is None:
            QMessageBox.information(self, "Sin selección", "Seleccione una alerta de la lista.")
            return
        if accion == "snooze":
            self._repo.snooze(key, dias=7)
        else:
            self._repo.ignorar(key)
        self._refresh()


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
        color_vencido: str = _COLOR_VENCIDO_DEFAULT,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._equipo_id = equipo_id
        self._color_vencido = QColor(color_vencido)
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

        btn_pasos = QPushButton("Pasos")
        btn_pasos.clicked.connect(self._abrir_pasos)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_crear)
        btn_bar.addWidget(btn_editar)
        btn_bar.addWidget(btn_elim)
        btn_bar.addWidget(btn_adjuntos)
        btn_bar.addWidget(btn_pasos)
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
                    brush = QBrush(self._color_vencido)
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

    def _abrir_pasos(self) -> None:
        prog_id = self._selected_prog_id()
        if prog_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un programa primero.")
            return
        selected = self._tabla.selectedItems()
        row = self._tabla.row(selected[0])
        desc = (self._tabla.item(row, 1) or QTableWidgetItem("")).text()
        dlg = PasosDialog(self._db, prog_id, desc, parent=self)
        dlg.exec()


class PasosDialog(QDialog):
    """Gestiona la lista de pasos (checklist) de un programa de mantenimiento."""

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
        self._repo = PasoRepository(database_path)
        self.setWindowTitle(f"Pasos — {programa_desc}")
        self.setMinimumWidth(500)
        self.resize(560, 400)
        self._build()
        self._refresh()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._tabla = _make_table(["#", "Posición", "Descripción", "Activo"])
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._tabla)

        btn_bar = QHBoxLayout()
        btn_nuevo = _primary_button("+ Agregar paso")
        btn_elim  = _danger_button("Eliminar")
        btn_cerrar = QPushButton("Cerrar")

        btn_nuevo.clicked.connect(self._agregar)
        btn_elim.clicked.connect(self._eliminar)
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_nuevo)
        btn_bar.addWidget(btn_elim)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cerrar)
        layout.addLayout(btn_bar)

    def _refresh(self) -> None:
        pasos = self._repo.list_for_programa(self._programa_id)
        self._tabla.setRowCount(0)
        for paso_id, posicion, descripcion, activo in pasos:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(str(paso_id)))
            self._tabla.setItem(row, 1, QTableWidgetItem(str(posicion)))
            self._tabla.setItem(row, 2, QTableWidgetItem(descripcion))
            self._tabla.setItem(row, 3, QTableWidgetItem("Sí" if activo else "No"))
            item_id = self._tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, paso_id)

    def _selected_paso_id(self) -> int | None:
        selected = self._tabla.selectedItems()
        if not selected:
            return None
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        if item is None:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        return int(val) if val is not None else None

    def _agregar(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Nuevo paso")
        dlg.resize(400, 160)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        desc_edit = QLineEdit()
        pos_spin = QSpinBox()
        pos_spin.setRange(0, 9999)
        pos_spin.setValue(
            max((p[1] for p in self._repo.list_for_programa(self._programa_id)), default=-1) + 1
        )
        form.addRow("Descripción *", desc_edit)
        form.addRow("Posición", pos_spin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            desc = desc_edit.text().strip()
            if not desc:
                QMessageBox.warning(self, "Error", "La descripción no puede estar vacía.")
                return
            self._repo.create(self._programa_id, desc, pos_spin.value())
            self._refresh()

    def _eliminar(self) -> None:
        paso_id = self._selected_paso_id()
        if paso_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un paso.")
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar este paso?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repo.delete(paso_id)
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
