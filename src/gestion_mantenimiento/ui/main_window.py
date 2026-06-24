from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSlice,
    QPieSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import QDate, QMargins, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QDesktopServices, QPainter, QPalette
from PySide6.QtWidgets import QToolTip
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
    QStyle,
    QStyledItemDelegate,
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
    FacturaElectricaRepository,
    MedidorRepository,
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
    ("Electricidad", "electricidad"),
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


class _ColorItemDelegate(QStyledItemDelegate):
    """Pinta el BackgroundRole sobre el fondo CSS. Si la fila está seleccionada,
    deja que Qt muestre el resaltado de selección normal."""
    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)
        bg = index.data(Qt.ItemDataRole.BackgroundRole)
        if not (isinstance(bg, QBrush) and bg.style() != Qt.BrushStyle.NoBrush):
            return
        if option.state & QStyle.StateFlag.State_Selected:
            return
        painter.save()
        painter.fillRect(option.rect, bg)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            fg = index.data(Qt.ItemDataRole.ForegroundRole)
            color = fg.color() if isinstance(fg, QBrush) else option.palette.color(QPalette.ColorRole.Text)
            painter.setPen(color)
            a = index.data(Qt.ItemDataRole.TextAlignmentRole)
            align = Qt.AlignmentFlag(a) if a else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            painter.drawText(option.rect.adjusted(4, 0, -4, 0), align, str(text))
        painter.restore()


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
        self._medidor_repo = MedidorRepository(database_path)
        self._factura_repo = FacturaElectricaRepository(database_path)

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
        self._nav_container = QWidget(sidebar)
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(0, 0, 0, 0)
        self._nav_layout.setSpacing(4)
        layout.addWidget(self._nav_container)
        self._rebuild_nav_buttons()

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
        if hasattr(self, "_dash_chart_tipo_view"):
            self._refresh_chart_tipo()
            self._refresh_chart_mes()

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

    # ── Nav settings (order + visibility) ────────────────────────────────────

    def _load_nav_settings(self) -> list[tuple[str, bool]]:
        """Returns ordered list of (key, visible). Missing keys appended at end as visible."""
        from gestion_mantenimiento.data.paths import get_settings_path
        import json as _json
        path = get_settings_path()
        saved: list[dict] = []
        if path.exists():
            try:
                data = _json.loads(path.read_text(encoding="utf-8"))
                saved = data.get("nav_items", [])
            except Exception:
                pass
        saved_keys = {item["key"] for item in saved if isinstance(item, dict)}
        result = [
            (item["key"], bool(item.get("visible", True)))
            for item in saved
            if isinstance(item, dict) and item.get("key") in {k for _, k in _NAV_ITEMS}
        ]
        for _, key in _NAV_ITEMS:
            if key not in saved_keys:
                result.append((key, True))
        return result

    def _save_nav_settings(self, items: list[tuple[str, bool]]) -> None:
        from gestion_mantenimiento.data.paths import get_settings_path
        import json as _json
        path = get_settings_path()
        try:
            data: dict = _json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            data = {}
        data["nav_items"] = [{"key": k, "visible": v} for k, v in items]
        path.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _rebuild_nav_buttons(self) -> None:
        """Clears and rebuilds sidebar nav buttons from saved order/visibility settings."""
        _labels = {key: label for label, key in _NAV_ITEMS}
        # Remove all widgets from nav layout
        while self._nav_layout.count():
            item = self._nav_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._nav_buttons.clear()

        for key, visible in self._load_nav_settings():
            label = _labels.get(key, key)
            btn = QPushButton(label, self._nav_container)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            btn.setVisible(visible)
            self._nav_layout.addWidget(btn)
            self._nav_buttons[key] = btn

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
            "electricidad": self._build_electricidad_page,
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

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self._dash_chart_tipo_view = QChartView()
        self._dash_chart_tipo_view.setMinimumHeight(220)
        self._dash_chart_tipo_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._dash_chart_mes_view = QChartView()
        self._dash_chart_mes_view.setMinimumHeight(220)
        self._dash_chart_mes_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        charts_row.addWidget(self._dash_chart_tipo_view, 1)
        charts_row.addWidget(self._dash_chart_mes_view, 2)
        layout.addLayout(charts_row)

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

        self._refresh_chart_tipo()
        self._refresh_chart_mes()

    def _refresh_chart_tipo(self) -> None:
        theme = self._current_theme
        bg = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))

        conteos = self._orden_repo.count_by_tipo()
        series = QPieSeries()
        tipo_colors = {
            "PREVENTIVO": "#0e6b52",
            "CORRECTIVO": "#d97706",
            "MEJORA": "#3b82f6",
        }
        tipo_labels = {
            "PREVENTIVO": "Preventivo",
            "CORRECTIVO": "Correctivo",
            "MEJORA": "Mejora",
        }
        for tipo, color in tipo_colors.items():
            count = conteos.get(tipo, 0)
            slc = series.append(f"{tipo_labels[tipo]}\n{count}", count if count > 0 else 0)
            slc.setColor(QColor(color))
            slc.setLabelColor(text_color)
        series.setHoleSize(0.45)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSlice.LabelPosition.LabelOutside)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Órdenes por tipo")
        chart.setBackgroundBrush(QBrush(bg))
        chart.setTitleBrush(QBrush(text_color))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(text_color)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._dash_chart_tipo_view.setChart(chart)
        self._dash_chart_tipo_view.setBackgroundBrush(QBrush(bg))

    def _refresh_chart_mes(self) -> None:
        theme = self._current_theme
        bg = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))
        accent = str(theme.get("accent_color", "#0e6b52"))

        data = self._orden_repo.count_by_month(12)
        months_map: dict[str, int] = dict(data)
        today = date.today()
        labels: list[str] = []
        values: list[int] = []
        for i in range(11, -1, -1):
            m = today.month - i
            y = today.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            key = f"{y}-{m:02d}"
            labels.append(f"{m:02d}/{str(y)[2:]}")
            values.append(months_map.get(key, 0))

        bar_set = QBarSet("Órdenes")
        bar_set.setColor(QColor(accent))
        for v in values:
            bar_set.append(v)

        series = QBarSeries()
        series.append(bar_set)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(text_color)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(text_color)
        axis_y.setTickCount(5)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Órdenes por mes (últimos 12 meses)")
        chart.setBackgroundBrush(QBrush(bg))
        chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._dash_chart_mes_view.setChart(chart)
        self._dash_chart_mes_view.setBackgroundBrush(QBrush(bg))

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
        self._prog_table.setItemDelegate(_ColorItemDelegate(self._prog_table))
        self._prog_table.doubleClicked.connect(self._prog_editar)
        layout.addWidget(self._prog_table)

        # ── Barra de acciones ────────────────────────────────────────────────
        act_layout = QHBoxLayout()
        btn_crear    = _primary_button("+ Nuevo")
        btn_editar   = QPushButton("Editar")
        btn_elim     = _danger_button("Eliminar")
        btn_pasos    = QPushButton("Pasos")
        btn_generar  = _primary_button("Generar órdenes del mes")

        btn_crear.clicked.connect(lambda: self._prog_crear())
        btn_editar.clicked.connect(self._prog_editar)
        btn_elim.clicked.connect(self._prog_eliminar)
        btn_pasos.clicked.connect(self._prog_pasos)
        btn_generar.clicked.connect(lambda: self._generar_ordenes_mes())

        act_layout.addWidget(btn_crear)
        act_layout.addWidget(btn_editar)
        act_layout.addWidget(btn_elim)
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
        """Genera automáticamente órdenes preventivas para programas que vencen hoy o están vencidos."""
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
                continue

            # Ya hay una orden abierta para este programa — no crear otra
            if self._orden_programa_repo.find_orden_pendiente(p.equipo_id, [p.id]) is not None:
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

        # Selector de año y equipo
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Año:"))
        self._crono_year_combo = QComboBox()
        anio_actual = date.today().year
        for y in range(anio_actual - 2, anio_actual + 5):
            self._crono_year_combo.addItem(str(y), y)
        self._crono_year_combo.setCurrentText(str(anio_actual))
        self._crono_year_combo.currentIndexChanged.connect(self._refresh_cronograma)
        top_bar.addWidget(self._crono_year_combo)
        top_bar.addSpacing(16)

        top_bar.addWidget(QLabel("Equipo:"))
        self._crono_equipo_combo = QComboBox()
        self._crono_equipo_combo.setMinimumWidth(200)
        self._crono_equipo_combo.addItem("Todos", None)
        for eq in self._equipo_repo.list_all(solo_activos=True):
            self._crono_equipo_combo.addItem(eq.etiqueta, eq.id)
        self._crono_equipo_combo.currentIndexChanged.connect(self._refresh_cronograma)
        top_bar.addWidget(self._crono_equipo_combo)
        top_bar.addSpacing(16)

        for color, texto in [
            ("#BDD7EE", "Planificado"),
            ("#FFE699", "Orden abierta"),
            ("#C6EFCE", "Completado"),
        ]:
            lbl = QLabel(f"■ {texto}")
            lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
            top_bar.addWidget(lbl)
            top_bar.addSpacing(8)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Tabla de cronograma
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._crono_tabla = QTableWidget()
        self._crono_tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._crono_tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._crono_tabla.verticalHeader().setVisible(False)
        self._crono_tabla.setItemDelegate(_ColorItemDelegate(self._crono_tabla))
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

        from collections import defaultdict
        import sqlite3 as _sqlite3
        from contextlib import closing as _closing

        equipo_id_filtro = self._crono_equipo_combo.currentData()
        programas = self._programa_repo.list_all(solo_activos=True)
        if equipo_id_filtro is not None:
            programas = [p for p in programas if p.equipo_id == equipo_id_filtro]
        anio_str  = str(anio)

        # ── Proyección de meses planificados por frecuencia ──────────────────
        # programa_id → set[month]
        planned: dict[int, set[int]] = defaultdict(set)
        for prog in programas:
            if not prog.proxima_ejecucion:
                continue
            try:
                proxima = date.fromisoformat(prog.proxima_ejecucion)
            except ValueError:
                continue
            freq = max(1, prog.frecuencia_meses)
            cur = proxima
            while True:
                pm = cur.month - freq
                py = cur.year + (pm - 1) // 12
                pm = ((pm - 1) % 12) + 1
                prev = cur.replace(year=py, month=pm, day=min(cur.day, 28))
                if prev.year < anio:
                    break
                cur = prev
            while cur.year <= anio:
                if cur.year == anio:
                    planned[prog.id].add(cur.month)
                nm = cur.month + freq
                ny = cur.year + (nm - 1) // 12
                nm = ((nm - 1) % 12) + 1
                try:
                    cur = cur.replace(year=ny, month=nm)
                except ValueError:
                    cur = cur.replace(year=ny, month=nm, day=28)

        # ── Órdenes reales del año vinculadas a cada programa ─────────────────
        # programa_id → set[month]
        activas:     dict[int, set[int]] = defaultdict(set)
        completadas: dict[int, set[int]] = defaultdict(set)

        with _closing(_sqlite3.connect(self._db)) as conn:
            rows = conn.execute(
                """
                SELECT
                    op.programa_id,
                    o.estado,
                    CAST(strftime('%m', o.fecha_apertura) AS INTEGER) AS mes_ap,
                    CAST(strftime('%m', COALESCE(NULLIF(o.fecha_cierre,''), o.fecha_apertura))
                         AS INTEGER) AS mes_ci
                FROM ordenes_trabajo o
                JOIN orden_programas op ON op.orden_id = o.id
                WHERE strftime('%Y', o.fecha_apertura) = ?
                   OR strftime('%Y', o.fecha_cierre)   = ?
                """,
                (anio_str, anio_str),
            ).fetchall()

        for prog_id, estado, mes_ap, mes_ci in rows:
            if estado == "COMPLETADA":
                if mes_ci:
                    completadas[prog_id].add(mes_ci)
            elif estado in ("PENDIENTE", "EN_PROGRESO"):
                if mes_ap:
                    activas[prog_id].add(mes_ap)

        # ── Construir tabla ───────────────────────────────────────────────────
        COLOR_PLANNED    = QColor("#BDD7EE")  # azul claro  — planificado
        COLOR_ACTIVA     = QColor("#FFE699")  # amarillo    — orden abierta
        COLOR_COMPLETADA = QColor("#C6EFCE")  # verde claro — completada
        COLOR_COMP_HOY   = QColor("#70AD47")  # verde oscuro — completada mes actual
        COLOR_SEP        = QColor("#4A4A4A")  # gris oscuro  — separador entre máquinas
        hoy = date.today()

        equipos_map = {e.id: e for e in self._equipo_repo.list_all()}

        # Agrupar programas por equipo para insertar separadores
        grupos: list[list] = []  # lista de grupos, cada grupo es lista de programas
        for prog in programas:
            if not grupos or grupos[-1][0].equipo_id != prog.equipo_id:
                grupos.append([])
            grupos[-1].append(prog)

        # Calcular número total de filas (programas + separadores entre grupos)
        n_separadores = max(0, len(grupos) - 1)
        total_rows = len(programas) + n_separadores

        tabla = self._crono_tabla
        tabla.clear()
        tabla.setColumnCount(13)
        tabla.setRowCount(total_rows)
        tabla.setHorizontalHeaderLabels(["Máquina — Mantenimiento"] + _MESES)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 13):
            tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        tabla_row = 0
        for g_idx, grupo in enumerate(grupos):
            # Separador entre máquinas (excepto antes del primer grupo)
            if g_idx > 0:
                tabla.setRowHeight(tabla_row, 5)
                for col in range(13):
                    sep_item = QTableWidgetItem("")
                    sep_item.setBackground(QBrush(COLOR_SEP))
                    sep_item.setFlags(Qt.ItemFlag.NoItemFlags)
                    tabla.setItem(tabla_row, col, sep_item)
                tabla_row += 1

            for p_idx, prog in enumerate(grupo):
                etiqueta = f"{prog.equipo_nombre}  —  {prog.descripcion}"
                if p_idx == 0:
                    equipo = equipos_map.get(prog.equipo_id)
                    if equipo is not None and equipo.horas_trabajo_activo:
                        etiqueta += f"\nHoras de trabajo: {equipo.horas_trabajo_actual:g} hs"
                tabla.setItem(tabla_row, 0, QTableWidgetItem(etiqueta))

                for mes in range(1, 13):
                    es_hoy = (anio == hoy.year and mes == hoy.month)
                    if mes in completadas.get(prog.id, set()):
                        color = COLOR_COMP_HOY if es_hoy else COLOR_COMPLETADA
                        label = "✔"
                    elif mes in activas.get(prog.id, set()):
                        color = COLOR_ACTIVA
                        label = "⏳"
                    elif mes in planned.get(prog.id, set()):
                        color = COLOR_PLANNED
                        label = "·"
                    else:
                        tabla.setItem(tabla_row, mes, QTableWidgetItem(""))
                        continue
                    item = QTableWidgetItem(label)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QBrush(color))
                    tabla.setItem(tabla_row, mes, item)

                tabla.resizeRowToContents(tabla_row)
                tabla_row += 1

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

    # ── Electricidad ──────────────────────────────────────────────────────────

    def _build_electricidad_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(_page_title("Control de Gasto Eléctrico — EDESUR"))

        # ── Barra superior ────────────────────────────────────────────────────
        top = QFrame()
        top.setObjectName("topbar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(12, 8, 12, 8)

        top_layout.addWidget(QLabel("Medidor:"))
        self._elec_medidor_combo = QComboBox()
        self._elec_medidor_combo.setMinimumWidth(220)
        self._elec_medidor_combo.currentIndexChanged.connect(lambda: self._refresh_electricidad())
        top_layout.addWidget(self._elec_medidor_combo)

        top_layout.addSpacing(16)
        top_layout.addWidget(QLabel("Año:"))
        self._elec_anio_combo = QComboBox()
        from datetime import date as _date
        _anio_actual = _date.today().year
        for y in range(_anio_actual - 4, _anio_actual + 2):
            self._elec_anio_combo.addItem(str(y), y)
        self._elec_anio_combo.setCurrentText(str(_anio_actual))
        self._elec_anio_combo.currentIndexChanged.connect(lambda: self._refresh_electricidad())
        top_layout.addWidget(self._elec_anio_combo)
        top_layout.addStretch()
        btn_descargar = _primary_button("Descargar de EDESUR")
        btn_descargar.setToolTip("Descarga la última factura directamente desde el portal EDESUR")
        btn_descargar.clicked.connect(self._elec_descargar_edesur)
        top_layout.addWidget(btn_descargar)

        btn_config_edesur = QPushButton("Acceso EDESUR")
        btn_config_edesur.setToolTip("Configurar usuario y contraseña del portal EDESUR")
        btn_config_edesur.clicked.connect(self._elec_configurar_edesur)
        top_layout.addWidget(btn_config_edesur)

        btn_medidores = QPushButton("Gestionar medidores")
        btn_medidores.clicked.connect(self._gestionar_medidores)
        top_layout.addWidget(btn_medidores)
        layout.addWidget(top)

        # ── Métricas ──────────────────────────────────────────────────────────
        self._elec_metrics_row = QHBoxLayout()
        self._elec_metrics_row.setSpacing(12)
        layout.addLayout(self._elec_metrics_row)

        # ── Gráfico de barras ─────────────────────────────────────────────────
        self._elec_chart_view = QChartView()
        self._elec_chart_view.setMinimumHeight(190)
        self._elec_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self._elec_chart_view)

        # ── Tabla ─────────────────────────────────────────────────────────────
        layout.addWidget(_section_title("Facturas registradas"))
        self._elec_table = _make_table([
            "ID", "Período", "Tarifa", "N° Factura",
            "kWh total", "kVAR", "cos φ", "Subtotal", "IVA + IIBB", "Total",
            "Vto 1", "Vto 2",
        ])
        self._elec_table.setColumnHidden(0, True)
        hdr = self._elec_table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setStretchLastSection(True)  # última columna (Vto 2) absorbe el espacio sobrante
        # altura para ver 12 filas sin scroll interno
        self._elec_table.setMinimumHeight(12 * 28 + 32)
        self._elec_table.doubleClicked.connect(self._elec_editar)
        layout.addWidget(self._elec_table)

        # ── Análisis comparativo ───────────────────────────────────────────────
        layout.addWidget(_section_title("Análisis comparativo — todos los meses registrados"))

        for attr, titulo in [
            ("_elec_chart_energia", "Consumo energético (kWh)"),
            ("_elec_chart_demanda", "Demanda máxima 15 min (kW)"),
            ("_elec_chart_cosphi",  "Factor de potencia cos φ"),
            ("_elec_chart_kvar",    "Energía reactiva (kVAR)"),
        ]:
            cv = QChartView()
            cv.setFixedHeight(220)
            cv.setRenderHint(QPainter.RenderHint.Antialiasing)
            setattr(self, attr, cv)
            layout.addWidget(cv)

        # ── Acciones ──────────────────────────────────────────────────────────
        act_layout = QHBoxLayout()
        btn_nueva = _primary_button("+ Nueva factura")
        btn_editar = QPushButton("Editar")
        btn_elim = _danger_button("Eliminar")
        btn_bulk = QPushButton("Importar varios PDFs...")
        btn_nueva.clicked.connect(self._elec_nueva)
        btn_editar.clicked.connect(self._elec_editar)
        btn_elim.clicked.connect(self._elec_eliminar)
        btn_bulk.clicked.connect(self._elec_importar_masivo)
        act_layout.addWidget(btn_nueva)
        act_layout.addWidget(btn_editar)
        act_layout.addWidget(btn_bulk)
        act_layout.addStretch()
        act_layout.addWidget(btn_elim)
        layout.addLayout(act_layout)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        def refresh() -> None:
            self._reload_elec_medidor_combo()

        page._refresh = refresh  # type: ignore[attr-defined]
        return page

    def _reload_elec_medidor_combo(self) -> None:
        prev_id = self._elec_medidor_combo.currentData()
        self._elec_medidor_combo.blockSignals(True)
        self._elec_medidor_combo.clear()
        for m in self._medidor_repo.list_all():
            label = m.nombre if m.activo else f"{m.nombre} (inactivo)"
            self._elec_medidor_combo.addItem(label, m.id)
        if prev_id is not None:
            idx = self._elec_medidor_combo.findData(prev_id)
            if idx >= 0:
                self._elec_medidor_combo.setCurrentIndex(idx)
        self._elec_medidor_combo.blockSignals(False)
        self._refresh_electricidad()

    def _refresh_electricidad(self) -> None:
        medidor_id: int | None = self._elec_medidor_combo.currentData()
        anio: int = self._elec_anio_combo.currentData() or 0

        while self._elec_metrics_row.count():
            item = self._elec_metrics_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if medidor_id is None:
            self._elec_table.setRowCount(0)
            self._elec_chart_view.setChart(QChart())
            return

        totales = self._factura_repo.totales_anio(medidor_id, anio)
        for titulo, valor in [
            ("kWh total año", f"{totales['kwh']:,.1f}"),
            ("kWh máx. mensual", f"{totales['max_kwh_mes']:,.1f}"),
            ("DRP máx. año", f"{totales['max_drp_kw']:,.1f} kW"),
            ("DRFP máx. año", f"{totales['max_drfp_kw']:,.1f} kW"),
            ("Total facturado", f"$ {totales['importe']:,.2f}"),
            ("Costo promedio", f"$ {totales['costo_kwh']:,.4f}/kWh"),
        ]:
            self._elec_metrics_row.addWidget(_metric_widget(titulo, valor))
        self._elec_metrics_row.addStretch()

        # Tabla
        facturas = self._factura_repo.list_by_medidor(medidor_id, anio)
        tabla = self._elec_table
        tabla.setRowCount(0)
        from datetime import date as _date
        hoy = _date.today().isoformat()
        for f in facturas:
            row = tabla.rowCount()
            tabla.insertRow(row)
            anio_f, mes_f = f.periodo.split("-")
            periodo_label = f"{_MESES[int(mes_f) - 1]} {anio_f}"
            tabla.setItem(row, 0, QTableWidgetItem(str(f.id)))
            tabla.setItem(row, 1, QTableWidgetItem(periodo_label))
            tabla.setItem(row, 2, QTableWidgetItem(f.tipo_tarifa))
            tabla.setItem(row, 3, QTableWidgetItem(f.nro_lsp))
            tabla.setItem(row, 4, QTableWidgetItem(f"{f.kwh_total:,.1f} kWh"))
            # kVAR y cos φ — solo si tienen datos
            kvar_txt = f"{f.kvar_reactiva:,.0f}" if f.kvar_reactiva else "—"
            tabla.setItem(row, 5, QTableWidgetItem(kvar_txt))
            cos_txt = f"{f.cos_phi:.4f}" if f.tangente_fi else "—"
            item_cos = QTableWidgetItem(cos_txt)
            # Resaltar en rojo si cos φ < 0.85 (límite típico de penalización EDESUR)
            if f.tangente_fi and f.cos_phi < 0.85:
                item_cos.setForeground(QBrush(QColor("#e53e3e")))
            tabla.setItem(row, 6, item_cos)
            tabla.setItem(row, 7, QTableWidgetItem(f"$ {f.subtotal_neto:,.2f}"))
            tabla.setItem(row, 8, QTableWidgetItem(f"$ {f.subtotal_impuestos:,.2f}"))
            item_total = QTableWidgetItem(f"$ {f.importe:,.2f}")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tabla.setItem(row, 9, item_total)
            # Vencimientos — resaltar si ya venció
            for col, vto in [(10, f.fecha_vto1), (11, f.fecha_vto2)]:
                it = QTableWidgetItem(vto)
                if vto and vto < hoy:
                    it.setForeground(QBrush(QColor("#e53e3e")))
                tabla.setItem(row, col, it)
            item_id = tabla.item(row, 0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole, f.id)

        self._refresh_elec_chart(medidor_id, anio)
        self._refresh_elec_chart_energia(medidor_id)
        self._refresh_elec_chart_demanda(medidor_id)
        self._refresh_elec_chart_cosphi(medidor_id)
        self._refresh_elec_chart_kvar(medidor_id)

    def _refresh_elec_chart(self, medidor_id: int, anio: int) -> None:
        theme = self._current_theme
        bg = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))

        por_mes = self._factura_repo.por_mes(medidor_id, anio)

        set_subtotal = QBarSet("Subtotal s/imp.")
        set_subtotal.setColor(QColor("#3b82f6"))
        set_impuestos = QBarSet("Impuestos")
        set_impuestos.setColor(QColor("#f87171"))
        labels: list[str] = []
        for mes in range(1, 13):
            f = por_mes.get(mes)
            set_subtotal.append(f.subtotal_neto if f else 0.0)
            set_impuestos.append(f.subtotal_impuestos if f else 0.0)
            labels.append(_MESES[mes - 1][:3])

        series = QBarSeries()
        series.append(set_subtotal)
        series.append(set_impuestos)
        self._hover_barras(series, labels, self._elec_chart_view, "$")

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(text_color)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("$%.0f")
        axis_y.setLabelsColor(text_color)
        axis_y.setTickCount(5)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Composición del gasto mensual — {anio}")
        chart.setBackgroundBrush(QBrush(bg))
        chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(text_color)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._elec_chart_view.setChart(chart)
        self._elec_chart_view.setBackgroundBrush(QBrush(bg))

    def _refresh_elec_chart_energia(self, medidor_id: int) -> None:
        """Barras apiladas de kWh (punta / valle / restantes) — todos los meses."""
        theme = self._current_theme
        bg = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))

        todas = self._factura_repo.list_by_medidor(medidor_id)
        if not todas:
            self._elec_chart_energia.setChart(QChart())
            return

        set_punta    = QBarSet("Punta");    set_punta.setColor(QColor("#f87171"))
        set_valle    = QBarSet("Valle Noc."); set_valle.setColor(QColor("#60a5fa"))
        set_rest     = QBarSet("Restantes"); set_rest.setColor(QColor("#34d399"))
        labels: list[str] = []

        for f in todas:
            anio_f, mes_f = f.periodo.split("-")
            labels.append(f"{_MESES[int(mes_f)-1][:3]}\n{anio_f[2:]}")
            set_punta.append(f.kwh_punta)
            set_valle.append(f.kwh_valle_noc)
            set_rest.append(f.kwh_restantes)

        series = QBarSeries()
        series.append(set_punta)
        series.append(set_valle)
        series.append(set_rest)
        self._hover_barras(series, labels, self._elec_chart_energia, "kWh")

        axis_x = QBarCategoryAxis(); axis_x.append(labels); axis_x.setLabelsColor(text_color)
        axis_y = QValueAxis(); axis_y.setLabelFormat("%.0f kWh"); axis_y.setLabelsColor(text_color); axis_y.setTickCount(5)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Consumo energético mensual (kWh)")
        chart.setBackgroundBrush(QBrush(bg)); chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x); series.attachAxis(axis_y)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(text_color)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._elec_chart_energia.setChart(chart)
        self._elec_chart_energia.setBackgroundBrush(QBrush(bg))

    def _refresh_elec_chart_demanda(self, medidor_id: int) -> None:
        """Barras de DRP y DRFP — demanda máxima en 15 min por mes."""
        theme = self._current_theme
        bg = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))

        todas = self._factura_repo.list_by_medidor(medidor_id)
        con_datos = [f for f in todas if f.drp_kw > 0 or f.drfp_kw > 0]
        if not con_datos:
            self._elec_chart_demanda.setChart(QChart())
            return

        set_drp  = QBarSet("DRP — En punta");       set_drp.setColor(QColor("#f59e0b"))
        set_drfp = QBarSet("DRFP — Fuera de punta"); set_drfp.setColor(QColor("#8b5cf6"))
        labels: list[str] = []

        for f in con_datos:
            anio_f, mes_f = f.periodo.split("-")
            labels.append(f"{_MESES[int(mes_f)-1][:3]}\n{anio_f[2:]}")
            set_drp.append(f.drp_kw)
            set_drfp.append(f.drfp_kw)

        series = QBarSeries()
        series.append(set_drp)
        series.append(set_drfp)
        self._hover_barras(series, labels, self._elec_chart_demanda, "kW")

        axis_x = QBarCategoryAxis(); axis_x.append(labels); axis_x.setLabelsColor(text_color)
        axis_y = QValueAxis(); axis_y.setLabelFormat("%.0f kW"); axis_y.setLabelsColor(text_color); axis_y.setTickCount(5)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Demanda máxima en 15 min (kW)")
        chart.setBackgroundBrush(QBrush(bg)); chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x); series.attachAxis(axis_y)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(text_color)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._elec_chart_demanda.setChart(chart)
        self._elec_chart_demanda.setBackgroundBrush(QBrush(bg))

    def _refresh_elec_chart_cosphi(self, medidor_id: int) -> None:
        """Línea de cos φ mensual con umbral de penalización en 0.85."""
        theme = self._current_theme
        bg         = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))
        accent     = str(theme.get("accent_color", "#0e6b52"))

        todas = [f for f in self._factura_repo.list_by_medidor(medidor_id)
                 if f.tangente_fi > 0]
        if not todas:
            self._elec_chart_cosphi.setChart(QChart())
            return

        serie = QLineSeries()
        serie.setName("cos φ")
        serie.setColor(QColor(accent))
        p = serie.pen(); p.setWidth(2); serie.setPen(p)

        umbral = QLineSeries()
        umbral.setName("Límite 0.85")
        umbral.setColor(QColor("#ef4444"))
        p2 = umbral.pen(); p2.setWidth(1); p2.setStyle(Qt.PenStyle.DashLine); umbral.setPen(p2)

        labels: list[str] = []
        vals_phi: list[float] = []
        for i, f in enumerate(todas):
            anio_f, mes_f = f.periodo.split("-")
            labels.append(f"{mes_f}/{anio_f[2:]}")
            vals_phi.append(f.cos_phi)
            serie.append(i, f.cos_phi)
            umbral.append(i, 0.85)

        # se conecta DESPUÉS de construir el chart (más abajo)

        # Un solo eje X de categorías adjuntado a ambas series
        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(text_color)
        axis_x.setLabelsAngle(-45)

        vals = [f.cos_phi for f in todas]
        ymin = max(0.5, min(vals) - 0.03)
        ymax = min(1.01, max(vals) + 0.02)
        axis_y = QValueAxis()
        axis_y.setRange(ymin, ymax)
        axis_y.setTickCount(6)
        axis_y.setLabelFormat("%.4f")
        axis_y.setLabelsColor(text_color)

        chart = QChart()
        chart.addSeries(serie)
        chart.addSeries(umbral)
        chart.setTitle("Factor de potencia  cos φ")
        chart.setBackgroundBrush(QBrush(bg))
        chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        serie.attachAxis(axis_x)
        serie.attachAxis(axis_y)
        umbral.attachAxis(axis_x)
        umbral.attachAxis(axis_y)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.legend().setLabelColor(text_color)
        chart.setMargins(QMargins(8, 8, 8, 4))
        self._elec_chart_cosphi.setChart(chart)
        self._elec_chart_cosphi.setBackgroundBrush(QBrush(bg))
        self._hover_linea(serie, labels, vals_phi, self._elec_chart_cosphi, ".4f")

    def _refresh_elec_chart_kvar(self, medidor_id: int) -> None:
        """Barras de energía reactiva (kVAR) por mes."""
        theme = self._current_theme
        bg         = QColor(str(theme.get("panel_background", "#ffffff")))
        text_color = QColor(str(theme.get("text_color", "#182026")))

        todas = [f for f in self._factura_repo.list_by_medidor(medidor_id)
                 if f.kvar_reactiva > 0]
        if not todas:
            self._elec_chart_kvar.setChart(QChart())
            return

        bar_set = QBarSet("kVAR reactiva")
        bar_set.setColor(QColor("#a78bfa"))
        labels: list[str] = []
        for f in todas:
            anio_f, mes_f = f.periodo.split("-")
            labels.append(f"{_MESES[int(mes_f)-1][:3]}\n{anio_f[2:]}")
            bar_set.append(f.kvar_reactiva)

        series = QBarSeries()
        series.append(bar_set)
        self._hover_barras(series, labels, self._elec_chart_kvar, "kVAR")

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(text_color)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        axis_y.setLabelsColor(text_color)
        axis_y.setTickCount(5)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Energía reactiva (kVAR)")
        chart.setBackgroundBrush(QBrush(bg))
        chart.setTitleBrush(QBrush(text_color))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        chart.setMargins(QMargins(4, 4, 4, 4))
        self._elec_chart_kvar.setChart(chart)
        self._elec_chart_kvar.setBackgroundBrush(QBrush(bg))

    def _elec_selected_id(self) -> int | None:
        return self._selected_id(self._elec_table)

    def _elec_importar_masivo(self) -> None:
        medidor_id: int | None = self._elec_medidor_combo.currentData()
        if medidor_id is None:
            QMessageBox.information(
                self, "Sin medidor",
                "Seleccioná un medidor antes de importar facturas."
            )
            return

        from pathlib import Path as _Path
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar facturas EDESUR (PDF)",
            str(_Path.home()),
            "Archivos PDF (*.pdf *.PDF)",
        )
        if not paths:
            return

        dlg = _BulkImportDialog(
            self._db, medidor_id, paths, parent=self
        )
        dlg.exec()
        self._refresh_electricidad()

    def _elec_nueva(self) -> None:
        medidor_id: int | None = self._elec_medidor_combo.currentData()
        if medidor_id is None:
            QMessageBox.information(self, "Sin medidor", "Primero seleccioná o creá un medidor.")
            return
        anio: int = self._elec_anio_combo.currentData() or 0
        dlg = FacturaElectricaDialog(self._db, medidor_id, anio, None, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_electricidad()

    def _elec_editar(self) -> None:
        factura_id = self._elec_selected_id()
        if factura_id is None:
            return
        medidor_id: int | None = self._elec_medidor_combo.currentData()
        anio: int = self._elec_anio_combo.currentData() or 0
        dlg = FacturaElectricaDialog(self._db, medidor_id or 0, anio, factura_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_electricidad()

    def _elec_eliminar(self) -> None:
        factura_id = self._elec_selected_id()
        if factura_id is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar esta factura?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._factura_repo.delete(factura_id)
            self._refresh_electricidad()

    def _elec_configurar_edesur(self) -> None:
        dlg = EdesurCredencialesDialog(parent=self)
        dlg.exec()

    def _elec_descargar_edesur(self) -> None:
        from gestion_mantenimiento.services.edesur_scraper import cargar_credenciales

        creds = cargar_credenciales()
        if not creds.get("usuario") or not creds.get("clave"):
            QMessageBox.information(
                self, "Acceso EDESUR",
                "Ingresá usuario y contraseña del portal EDESUR primero."
            )
            self._elec_configurar_edesur()
            creds = cargar_credenciales()
            if not creds.get("usuario"):
                return

        medidor_id: int | None = self._elec_medidor_combo.currentData()
        anio: int = self._elec_anio_combo.currentData() or 0

        # Diálogo de progreso
        self._edesur_dlg = QDialog(self)
        self._edesur_dlg.setWindowTitle("Obteniendo datos de EDESUR")
        self._edesur_dlg.setMinimumWidth(460)
        self._edesur_dlg.setWindowFlags(
            self._edesur_dlg.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        vl = QVBoxLayout(self._edesur_dlg)
        info = QLabel(
            "Conectando al portal y descargando datos de factura\n"
            "y consumo directamente desde la API de EDESUR..."
        )
        info.setWordWrap(True)
        info.setObjectName("muted")
        vl.addWidget(info)
        self._edesur_status = QLabel("Iniciando...")
        self._edesur_status.setWordWrap(True)
        vl.addWidget(self._edesur_status)
        btn_cancel = QPushButton("Cancelar")
        vl.addWidget(btn_cancel)

        self._edesur_worker = _DescargaEdesurWorker(
            creds["usuario"], creds["clave"], parent=self
        )
        self._edesur_worker.progreso.connect(self._edesur_status.setText)
        self._edesur_worker.listo.connect(
            lambda res: self._on_edesur_ok(res, medidor_id, anio)
        )
        self._edesur_worker.fallo.connect(self._on_edesur_error)
        btn_cancel.clicked.connect(self._edesur_worker.terminate)
        btn_cancel.clicked.connect(self._edesur_dlg.reject)
        self._edesur_worker.start()
        self._edesur_dlg.exec()

    def _on_edesur_ok(self, resultado, medidor_id: int | None, anio: int) -> None:
        self._edesur_dlg.accept()
        # Mostrar historial con links antes de abrir el formulario
        hist_dlg = EdesurHistorialDialog(resultado, parent=self)
        factura_elegida = hist_dlg.exec_get_choice()  # devuelve índice o None

        indice = factura_elegida if factura_elegida is not None else 0
        facturas = resultado.todas_facturas
        if indice >= len(facturas):
            return

        # Si el usuario eligió una factura distinta a la ya cargada, recargar
        if indice == 0:
            r = resultado.resultado
        else:
            # Para facturas históricas, construir resultado minimal desde la lista
            from gestion_mantenimiento.services.edesur_parser import FacturaParseResult
            inv = facturas[indice]
            def dmy(s: str) -> str:
                try:
                    d, m, y = s.strip().split("/")
                    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                except Exception:
                    return ""
            fecha = dmy(inv.get("issueDate", ""))
            r = FacturaParseResult(
                tipo_tarifa   = resultado.tipo_tarifa_api,
                nro_lsp       = inv.get("number", ""),
                nro_cliente   = resultado.nro_cliente,
                nro_medidor   = resultado.nro_medidor_api,
                periodo       = fecha[:7],
                fecha_factura = fecha,
                fecha_vto1    = dmy(inv.get("firstDueDate", "") or ""),
                importe       = float(inv.get("totalAmount", 0)),
                advertencias  = ["Desglose no disponible por API — importá el PDF para completarlo."],
            )

        dlg = FacturaElectricaDialog(self._db, medidor_id or 0, anio, None, parent=self)
        dlg._cargar_desde_api(r)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_electricidad()

    def _on_edesur_error(self, mensaje: str) -> None:
        self._edesur_dlg.accept()
        QMessageBox.critical(self, "Error al descargar factura EDESUR", mensaje)

    def _gestionar_medidores(self) -> None:
        dlg = MedidoresDialog(self._db, parent=self)
        dlg.exec()
        self._reload_elec_medidor_combo()

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

        layout.addWidget(_page_title("Opciones"))

        # ── Pestañas del menú ────────────────────────────────────────────────
        layout.addWidget(_section_title("Pestañas del menú lateral"))

        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        self._nav_list_widget = QListWidget()
        self._nav_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._nav_list_widget.setMinimumHeight(len(_NAV_ITEMS) * 30 + 8)
        self._nav_list_widget.setToolTip("Arrastrá para reordenar · Tildá para mostrar u ocultar")
        self._reload_nav_list_widget()

        nav_btn_row = QHBoxLayout()
        btn_nav_up   = QPushButton("↑ Subir")
        btn_nav_down = QPushButton("↓ Bajar")
        btn_nav_save = _primary_button("Aplicar")

        def _nav_move(delta: int) -> None:
            lw = self._nav_list_widget
            row = lw.currentRow()
            if row < 0:
                return
            target = row + delta
            if target < 0 or target >= lw.count():
                return
            item = lw.takeItem(row)
            lw.insertItem(target, item)
            lw.setCurrentRow(target)

        btn_nav_up.clicked.connect(lambda: _nav_move(-1))
        btn_nav_down.clicked.connect(lambda: _nav_move(1))
        btn_nav_save.clicked.connect(self._opciones_save_nav)

        nav_btn_row.addWidget(btn_nav_up)
        nav_btn_row.addWidget(btn_nav_down)
        nav_btn_row.addStretch()
        nav_btn_row.addWidget(btn_nav_save)

        layout.addWidget(self._nav_list_widget)
        layout.addLayout(nav_btn_row)

        # ── Apariencia ───────────────────────────────────────────────────────
        layout.addWidget(_section_title("Apariencia"))

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

        def _refresh_opciones() -> None:
            self._reload_nav_list_widget()

        page._refresh = _refresh_opciones  # type: ignore[attr-defined]

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _reload_nav_list_widget(self) -> None:
        from PySide6.QtWidgets import QListWidgetItem
        lw = self._nav_list_widget
        lw.clear()
        _labels = {key: label for label, key in _NAV_ITEMS}
        for key, visible in self._load_nav_settings():
            item = QListWidgetItem(_labels.get(key, key))
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
            )
            item.setCheckState(Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked)
            lw.addItem(item)

    def _opciones_save_nav(self) -> None:
        lw = self._nav_list_widget
        items: list[tuple[str, bool]] = []
        for i in range(lw.count()):
            item = lw.item(i)
            if item is None:
                continue
            key = item.data(Qt.ItemDataRole.UserRole)
            visible = item.checkState() == Qt.CheckState.Checked
            items.append((key, visible))
        self._save_nav_settings(items)
        self._rebuild_nav_buttons()
        # Navegar a la primera pestaña visible para no quedar en una oculta
        for key, visible in items:
            if visible:
                self._navigate(key)
                break

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

    @staticmethod
    def _make_overlay(chart_view: "QChartView") -> "QLabel":
        lbl = QLabel(chart_view)
        lbl.setStyleSheet(
            "QLabel{background:rgba(20,20,20,210);color:#f0f0f0;"
            "padding:5px 10px;border-radius:5px;font-size:12px;}"
        )
        lbl.hide()
        return lbl

    @staticmethod
    def _hover_barras(series, labels: list[str], chart_view: "QChartView",
                      unidad: str = "") -> None:
        """Overlay persistente con el valor de la barra hovered."""
        overlay = MainWindow._make_overlay(chart_view)

        def _on(status: bool, index: int, barset,
                _l=labels, _ov=overlay, _u=unidad) -> None:
            if status and 0 <= index < len(_l):
                val = barset.at(index)
                txt = f"{_l[index]}  —  {barset.label()}: {val:,.1f}"
                if _u:
                    txt += f" {_u}"
                _ov.setText(txt)
                _ov.adjustSize()
                _ov.move(10, 10)
                _ov.show()
                _ov.raise_()
            else:
                _ov.hide()

        series.hovered.connect(_on)

    @staticmethod
    def _hover_linea(serie, labels: list[str], valores: list[float],
                     chart_view: "QChartView",
                     fmt: str = ".4f", unidad: str = "") -> None:
        """Overlay persistente con el valor real del punto hovered."""
        overlay = MainWindow._make_overlay(chart_view)

        def _on(point, state: bool,
                _l=labels, _v=valores, _ov=overlay,
                _f=fmt, _u=unidad) -> None:
            if state:
                idx = int(round(point.x()))
                if 0 <= idx < len(_l):
                    val_txt = format(_v[idx], _f)
                    txt = f"{_l[idx]}  —  {val_txt}"
                    if _u:
                        txt += f" {_u}"
                    _ov.setText(txt)
                    _ov.adjustSize()
                    _ov.move(10, 10)
                    _ov.show()
                    _ov.raise_()
            else:
                _ov.hide()

        serie.hovered.connect(_on)

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

        self._horas_trabajo_check = QCheckBox("Controlar horas de trabajo")
        self._horas_trabajo_actual = QDoubleSpinBox()
        self._horas_trabajo_actual.setRange(0, 9_999_999)
        self._horas_trabajo_actual.setDecimals(1)
        self._horas_trabajo_actual.setSuffix(" hs")

        form.addRow("Nombre *", self._nombre)
        form.addRow("Tipo", self._tipo)
        form.addRow("N° Serie", self._numero_serie)
        form.addRow("Marca", self._marca)
        form.addRow("Modelo", self._modelo)
        form.addRow("Ubicación", self._ubicacion)
        form.addRow("Fecha adquisición", self._fecha_adq)
        form.addRow("Observaciones", self._observaciones)
        form.addRow("", self._activo)
        form.addRow("", self._horas_trabajo_check)
        self._horas_row_label = "Horas actuales"
        form.addRow(self._horas_row_label, self._horas_trabajo_actual)

        self._form = form
        self._horas_trabajo_check.toggled.connect(self._on_horas_trabajo_toggled)
        self._on_horas_trabajo_toggled(self._horas_trabajo_check.isChecked())

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_horas_trabajo_toggled(self, checked: bool) -> None:
        row, _ = self._form.getWidgetPosition(self._horas_trabajo_actual)
        if row >= 0:
            self._form.setRowVisible(row, checked)

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
        self._horas_trabajo_check.setChecked(eq.horas_trabajo_activo)
        self._horas_trabajo_actual.setValue(eq.horas_trabajo_actual)
        self._on_horas_trabajo_toggled(self._horas_trabajo_check.isChecked())

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
        horas_trabajo_activo = self._horas_trabajo_check.isChecked()
        horas_trabajo_actual = self._horas_trabajo_actual.value()

        try:
            if self._equipo_id is None:
                self._repo.create(
                    nombre, tipo_id, numero_serie, marca, modelo,
                    ubicacion, fecha_adq, observaciones,
                    horas_trabajo_activo, horas_trabajo_actual,
                )
            else:
                self._repo.update(
                    self._equipo_id, nombre, tipo_id, numero_serie, marca, modelo,
                    ubicacion, fecha_adq, observaciones, activo,
                    horas_trabajo_activo, horas_trabajo_actual,
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
        self._es_admin = QCheckBox("Administrador web")

        form.addRow("Nombre *", self._nombre)
        form.addRow("Apellido *", self._apellido)
        form.addRow("Legajo", self._legajo)
        form.addRow("Teléfono", self._telefono)
        form.addRow("Especialidad", self._especialidad)
        form.addRow("", self._activo)
        form.addRow("", self._es_admin)

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
        self._es_admin.setChecked(tec.es_admin)
        if tec.es_admin:
            self._es_admin.setEnabled(False)

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
                    es_admin=self._es_admin.isChecked(),
                )
            else:
                self._repo.update(
                    self._tecnico_id, nombre, apellido,
                    self._legajo.text().strip(), self._telefono.text().strip(),
                    self._especialidad.text().strip(), self._activo.isChecked(),
                    es_admin=self._es_admin.isChecked(),
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
        self._initial_estado: str = ""
        self._horas_trabajo_baseline: float = 0.0
        self._repo = OrdenTrabajoRepository(database_path)
        self._repuesto_repo = RepuestoOrdenRepository(database_path)
        self._repuesto_catalog_repo = RepuestoRepository(database_path)
        self._orden_programa_repo = OrdenProgramaRepository(database_path)
        self._programa_repo = ProgramaMantenimientoRepository(database_path)
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

        self._equipos_map = {e.id: e for e in self._equipo_repo.list_all()}

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

        self._horas_trabajo_input = QDoubleSpinBox()
        self._horas_trabajo_input.setRange(0, 9_999_999)
        self._horas_trabajo_input.setDecimals(1)
        self._horas_trabajo_input.setSuffix(" hs")

        form.addRow("Equipo *", self._equipo)
        form.addRow("Tipo", self._tipo)
        form.addRow("Estado", self._estado)
        form.addRow("Descripción", self._descripcion)
        form.addRow("Fecha apertura", self._fecha_apertura)
        form.addRow("Fecha cierre", self._fecha_cierre)
        form.addRow("Técnico", self._tecnico)
        form.addRow("Costo mano de obra", self._costo_mano_obra)
        form.addRow("Horas de trabajo actuales", self._horas_trabajo_input)
        form.addRow("Observaciones", self._observaciones)

        self._form = form
        self._equipo.currentIndexChanged.connect(self._on_equipo_changed)
        self._on_equipo_changed()

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

    def _on_equipo_changed(self) -> None:
        equipo = self._equipos_map.get(self._equipo.currentData())
        activo = bool(equipo and equipo.horas_trabajo_activo)
        row, _ = self._form.getWidgetPosition(self._horas_trabajo_input)
        if row >= 0:
            self._form.setRowVisible(row, activo)
        if activo and equipo is not None:
            self._horas_trabajo_baseline = equipo.horas_trabajo_actual
            if self._orden_id is None:
                self._horas_trabajo_input.setValue(equipo.horas_trabajo_actual)

    def _load(self, orden_id: int) -> None:
        orden = self._repo.get_by_id(orden_id)
        if orden is None:
            return

        self._initial_estado = orden.estado

        idx = self._equipo.findData(orden.equipo_id)
        if idx >= 0:
            self._equipo.setCurrentIndex(idx)
        self._on_equipo_changed()

        equipo = self._equipos_map.get(orden.equipo_id)
        if equipo and equipo.horas_trabajo_activo:
            valor = orden.horas_trabajo if orden.horas_trabajo is not None else equipo.horas_trabajo_actual
            self._horas_trabajo_input.setValue(valor)

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

        equipo = self._equipos_map.get(equipo_id)
        usa_horas = bool(equipo and equipo.horas_trabajo_activo)
        estado = self._estado.currentData() or "PENDIENTE"
        horas_trabajo = self._horas_trabajo_input.value() if usa_horas else None

        if (
            usa_horas
            and estado == "COMPLETADA"
            and self._initial_estado != "COMPLETADA"
            and (horas_trabajo is None or horas_trabajo <= self._horas_trabajo_baseline)
        ):
            QMessageBox.warning(
                self, "Validación",
                "Debe actualizar las horas de trabajo del equipo para completar esta orden."
            )
            return

        data = OrdenTrabajoCreate(
            equipo_id=equipo_id,
            tipo=self._tipo.currentData() or "CORRECTIVO",
            descripcion=self._descripcion.toPlainText().strip(),
            fecha_apertura=self._fecha_apertura.date().toString("yyyy-MM-dd"),
            fecha_cierre=self._fecha_cierre.date().toString("yyyy-MM-dd"),
            estado=estado,
            tecnico_id=self._tecnico.currentData(),
            costo_mano_obra=self._costo_mano_obra.value(),
            observaciones=self._observaciones.toPlainText().strip(),
            horas_trabajo=horas_trabajo,
        )

        try:
            if self._orden_id is None:
                orden_id = self._repo.create(data)
            else:
                self._repo.update(self._orden_id, data)
                orden_id = self._orden_id

            # Al completar la orden, avanzar proxima_ejecucion de cada programa vinculado
            if (
                data.estado == "COMPLETADA"
                and self._initial_estado != "COMPLETADA"
                and self._orden_id is not None
            ):
                vinculos = self._orden_programa_repo.list_by_orden(self._orden_id)
                for v in vinculos:
                    programas = self._programa_repo.list_all()
                    prog = next((p for p in programas if p.id == v.programa_id), None)
                    if prog and prog.proxima_ejecucion:
                        self._programa_repo.advance_proxima(
                            prog.id, prog.proxima_ejecucion, prog.frecuencia_meses
                        )

            # Al completar la orden, actualizar las horas de trabajo del equipo
            if (
                usa_horas
                and data.estado == "COMPLETADA"
                and self._initial_estado != "COMPLETADA"
                and data.horas_trabajo is not None
            ):
                self._equipo_repo.actualizar_horas_trabajo(equipo_id, data.horas_trabajo)

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

        btn_pasos = QPushButton("Pasos")
        btn_pasos.clicked.connect(self._abrir_pasos)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_crear)
        btn_bar.addWidget(btn_editar)
        btn_bar.addWidget(btn_elim)
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

        self._tabla = _make_table(["#", "Pos.", "Descripción", "Observaciones", "Adjunto"])
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self._tabla)

        btn_bar = QHBoxLayout()
        btn_nuevo = _primary_button("+ Agregar paso")
        btn_editar = QPushButton("Editar")
        btn_elim  = _danger_button("Eliminar")
        btn_cerrar = QPushButton("Cerrar")

        btn_nuevo.clicked.connect(self._agregar)
        btn_editar.clicked.connect(self._editar)
        btn_elim.clicked.connect(self._eliminar)
        btn_cerrar.clicked.connect(self.accept)

        btn_bar.addWidget(btn_nuevo)
        btn_bar.addWidget(btn_editar)
        btn_bar.addWidget(btn_elim)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cerrar)
        layout.addLayout(btn_bar)

    def _refresh(self) -> None:
        pasos = self._repo.list_for_programa(self._programa_id)
        self._tabla.setRowCount(0)
        for paso_id, posicion, descripcion, activo, observaciones, adjunto_nombre, _adjunto_ruta in pasos:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(str(paso_id)))
            self._tabla.setItem(row, 1, QTableWidgetItem(str(posicion)))
            self._tabla.setItem(row, 2, QTableWidgetItem(descripcion))
            self._tabla.setItem(row, 3, QTableWidgetItem(observaciones))
            self._tabla.setItem(row, 4, QTableWidgetItem(adjunto_nombre or ""))
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

    def _paso_dialog(
        self,
        titulo: str,
        desc: str = "",
        pos: int = 0,
        obs: str = "",
        adj_nombre: str = "",
        adj_ruta: str = "",
    ) -> tuple[str, int, str, str, str] | None:
        """Abre el diálogo de edición de paso. Retorna (desc, pos, obs, adj_nombre, adj_ruta) o None."""
        dlg = QDialog(self)
        dlg.setWindowTitle(titulo)
        dlg.setMinimumWidth(460)
        dlg.resize(480, 340)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        desc_edit = QLineEdit(desc)
        pos_spin = QSpinBox()
        pos_spin.setRange(0, 9999)
        pos_spin.setValue(pos)
        obs_edit = QLineEdit()
        obs_edit.setText(obs)

        adj_label = QLabel(adj_nombre or "Sin adjunto")
        adj_label.setStyleSheet("color: gray;")
        adj_path_holder: list[str] = [adj_ruta]
        adj_name_holder: list[str] = [adj_nombre]

        btn_adj = QPushButton("Seleccionar archivo…")

        def _pick_file() -> None:
            ruta, _ = QFileDialog.getOpenFileName(dlg, "Seleccionar adjunto")
            if ruta:
                adj_path_holder[0] = ruta
                adj_name_holder[0] = Path(ruta).name
                adj_label.setText(adj_name_holder[0])

        btn_ver_adj = QPushButton("Ver")
        btn_ver_adj.setEnabled(bool(adj_ruta and Path(adj_ruta).exists()))

        def _ver_adjunto() -> None:
            ruta = adj_path_holder[0]
            if ruta and Path(ruta).exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
            else:
                QMessageBox.warning(dlg, "Adjunto", "El archivo no existe en disco.")

        btn_adj.clicked.connect(_pick_file)
        btn_ver_adj.clicked.connect(_ver_adjunto)

        def _on_file_picked() -> None:
            _pick_file()
            btn_ver_adj.setEnabled(bool(adj_path_holder[0] and Path(adj_path_holder[0]).exists()))

        btn_adj.clicked.disconnect(_pick_file)
        btn_adj.clicked.connect(_on_file_picked)

        adj_row = QHBoxLayout()
        adj_row.addWidget(adj_label)
        adj_row.addWidget(btn_ver_adj)
        adj_row.addWidget(btn_adj)

        form.addRow("Descripción *", desc_edit)
        form.addRow("Posición", pos_spin)
        form.addRow("Observaciones", obs_edit)
        form.addRow("Adjunto", adj_row)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        d = desc_edit.text().strip()
        if not d:
            QMessageBox.warning(self, "Error", "La descripción no puede estar vacía.")
            return None
        return d, pos_spin.value(), obs_edit.text().strip(), adj_name_holder[0], adj_path_holder[0]

    def _agregar(self) -> None:
        next_pos = max((p[1] for p in self._repo.list_for_programa(self._programa_id)), default=-1) + 1
        result = self._paso_dialog("Nuevo paso", pos=next_pos)
        if result is None:
            return
        desc, pos, obs, adj_nombre, adj_ruta = result
        self._repo.create(self._programa_id, desc, pos, obs)
        self._refresh()

    def _editar(self) -> None:
        paso_id = self._selected_paso_id()
        if paso_id is None:
            QMessageBox.information(self, "Sin selección", "Seleccione un paso.")
            return
        pasos = self._repo.list_for_programa(self._programa_id)
        data = next((p for p in pasos if p[0] == paso_id), None)
        if data is None:
            return
        _id, pos, desc, _activo, obs, adj_nombre, adj_ruta = data
        result = self._paso_dialog("Editar paso", desc, pos, obs, adj_nombre, adj_ruta)
        if result is None:
            return
        new_desc, new_pos, new_obs, new_adj_nombre, new_adj_ruta = result

        # Si se seleccionó un nuevo archivo, copiarlo al directorio de adjuntos
        if new_adj_ruta and new_adj_ruta != adj_ruta:
            import shutil as _shutil
            dest_dir = self._db.parent / "paso_adjuntos" / str(paso_id)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / new_adj_nombre
            _shutil.copy2(new_adj_ruta, dest)
            new_adj_ruta = str(dest)

        self._repo.update(paso_id, new_desc, new_pos, new_obs, new_adj_nombre, new_adj_ruta)
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
    _last_frecuencia: int = 1

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
        self._frecuencia.setValue(ProgramaDialog._last_frecuencia if self._programa_id is None else 1)
        self._frecuencia.setSuffix(" meses")
        self._frecuencia.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self._ultima = QDateEdit()
        self._ultima.setCalendarPopup(True)
        self._ultima.setDate(QDate.currentDate())

        self._proxima_label = QLabel()
        self._proxima_label.setStyleSheet("color: gray; padding: 2px 0;")

        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)

        form.addRow("Equipo *", self._equipo)
        form.addRow("Descripción *", self._descripcion)
        form.addRow("Frecuencia", self._frecuencia)
        form.addRow("Última ejecución", self._ultima)
        form.addRow("Próxima ejecución", self._proxima_label)
        form.addRow("", self._activo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        if self._programa_id is None:
            self._btn_otra = buttons.addButton("Cargar otra", QDialogButtonBox.ButtonRole.ActionRole)
            self._btn_otra.clicked.connect(self._guardar_y_nueva)

        layout.addWidget(buttons)

        self._ultima.dateChanged.connect(self._actualizar_proxima)
        self._frecuencia.valueChanged.connect(self._actualizar_proxima)
        self._actualizar_proxima()

    def _guardar_y_nueva(self) -> None:
        equipo_id = self._equipo.currentData()
        descripcion = self._descripcion.text().strip()
        if equipo_id is None or not descripcion:
            QMessageBox.warning(self, "Validación", "Equipo y descripción son requeridos.")
            return
        ProgramaDialog._last_frecuencia = self._frecuencia.value()
        try:
            self._repo.create(
                equipo_id,
                descripcion,
                self._frecuencia.value(),
                self._ultima.date().toString("yyyy-MM-dd"),
                self._proxima_label.text(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self._descripcion.clear()
        self._descripcion.setFocus()

    def _actualizar_proxima(self) -> None:
        ultima = self._ultima.date()
        meses = self._frecuencia.value()
        m = ultima.month() + meses
        y = ultima.year() + (m - 1) // 12
        m = (m - 1) % 12 + 1
        d = min(ultima.day(), QDate(y, m, 1).daysInMonth())
        self._proxima_label.setText(QDate(y, m, d).toString("yyyy-MM-dd"))

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

        self._activo.setChecked(prog.activo)

    def _save(self) -> None:
        equipo_id = self._equipo.currentData()
        descripcion = self._descripcion.text().strip()

        if equipo_id is None or not descripcion:
            QMessageBox.warning(self, "Validación", "Equipo y descripción son requeridos.")
            return

        proxima_str = self._proxima_label.text()
        ProgramaDialog._last_frecuencia = self._frecuencia.value()
        try:
            if self._programa_id is None:
                self._repo.create(
                    equipo_id,
                    descripcion,
                    self._frecuencia.value(),
                    self._ultima.date().toString("yyyy-MM-dd"),
                    proxima_str,
                )
            else:
                self._repo.update(
                    self._programa_id,
                    equipo_id,
                    descripcion,
                    self._frecuencia.value(),
                    self._ultima.date().toString("yyyy-MM-dd"),
                    proxima_str,
                    self._activo.isChecked(),
                )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


# ── Importación masiva de PDFs ────────────────────────────────────────────────

# (worker eliminado — la importación ahora usa QTimer en el diálogo)


class _BulkImportDialog(QDialog):
    """
    Importa múltiples PDFs usando ProcessPoolExecutor (proceso separado = sin GIL).
    Un QTimer sondea cada 150 ms si el proceso terminó y actualiza la UI.
    """

    def __init__(
        self, db: Path, medidor_id: int, paths: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db         = db
        self._medidor_id = medidor_id
        self._paths      = paths
        self._total      = len(paths)
        self._done       = 0
        self._resultados: list[dict] = []

        self.setWindowTitle(f"Importar {self._total} factura(s) PDF")
        self.setMinimumWidth(600)
        self.resize(640, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self._build()

        # src/ path para que el subproceso pueda importar gestion_mantenimiento
        src_path = str(Path(__file__).resolve().parent.parent.parent)

        from concurrent.futures import ProcessPoolExecutor
        from gestion_mantenimiento.services.edesur_parser import parse_pdf_worker

        self._executor = ProcessPoolExecutor(max_workers=1)
        self._futures = [
            (Path(p).name, self._executor.submit(parse_pdf_worker, p, src_path))
            for p in paths
        ]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._sondear)
        self._timer.start(150)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        self._lbl = QLabel(f"Iniciando... 0 / {self._total}")
        layout.addWidget(self._lbl)

        from PySide6.QtWidgets import QProgressBar as _PBar
        self._bar = _PBar()
        self._bar.setRange(0, self._total)
        layout.addWidget(self._bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(180)
        self._log.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self._log)

        self._tabla = _make_table(["Archivo", "Período", "N° Factura", "Total", "Estado"])
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, w in [(1, 90), (2, 160), (3, 110), (4, 90)]:
            self._tabla.setColumnWidth(col, w)
        self._tabla.horizontalHeader().setStretchLastSection(False)
        layout.addWidget(self._tabla)

        self._btn = QPushButton("Procesando...")
        self._btn.setEnabled(False)
        self._btn.clicked.connect(self.accept)
        layout.addWidget(self._btn)

    # ── sondeo de futuros ─────────────────────────────────────────────────────

    def _sondear(self) -> None:
        """Llamado cada 150 ms. Procesa futuros completados sin bloquear Qt."""
        while self._done < len(self._futures):
            nombre, future = self._futures[self._done]
            if not future.done():
                break
            try:
                d = future.result()
            except Exception as exc:
                d = {"ok": False, "error": str(exc)}
            self._aplicar_resultado(nombre, d)
            self._done += 1
            self._bar.setValue(self._done)
            self._lbl.setText(f"Procesando {self._done} / {self._total}...")

        if self._done >= len(self._futures):
            self._timer.stop()
            self._executor.shutdown(wait=False)
            self._finalizar()

    def _aplicar_resultado(self, nombre: str, d: dict) -> None:
        from gestion_mantenimiento.data.repositories import FacturaElectricaRepository

        self._log.append(f"\n── {nombre}")
        if not d.get("ok"):
            self._log.append(f"   ERROR: {d.get('error', '?')}")
            self._resultados.append({"archivo": nombre, "ok": False,
                                     "error": d.get("error", "")})
            self._scroll_log()
            return

        periodo = d.get("periodo", "")
        if not periodo:
            self._log.append("   ERROR: no se encontró el período")
            self._resultados.append({"archivo": nombre, "ok": False,
                                     "error": "período no encontrado"})
            self._scroll_log()
            return

        anio_f, mes_f = periodo.split("-")
        kwh = d["kwh_punta"] + d["kwh_valle_noc"] + d["kwh_restantes"]
        self._log.append(f"   Período  : {_MESES[int(mes_f)-1]} {anio_f}")
        self._log.append(f"   LSP N°   : {d.get('nro_lsp','')}")
        self._log.append(f"   kWh total: {kwh:,.1f}  "
                         f"(P:{d['kwh_punta']:,.0f} VN:{d['kwh_valle_noc']:,.0f} "
                         f"R:{d['kwh_restantes']:,.0f})")
        if d.get("drp_kw") or d.get("drfp_kw"):
            self._log.append(f"   Demanda  : DRP={d['drp_kw']:.0f} kW  "
                             f"DRFP={d['drfp_kw']:.0f} kW")
        if d.get("cargo_fijo"):
            sub = (d["cargo_fijo"] + d["importe_cap_convenida"] + d["importe_cap_adquirida"]
                   + d["importe_kwh_punta"] + d["importe_kwh_valle_noc"] + d["importe_kwh_restantes"])
            imp = d["ley_7290"] + d["iva_27"] + d["contrib_art34"] + d["contrib_provincial"] + d["percep_iva"]
            self._log.append(f"   Subtotal : $ {sub:,.2f}   Impuestos: $ {imp:,.2f}")
        self._log.append(f"   TOTAL    : $ {d['importe']:,.2f}")

        try:
            repo = FacturaElectricaRepository(self._db)
            _, creada = repo.create_or_update(
                medidor_id=self._medidor_id,
                periodo=d["periodo"], tipo_tarifa=d["tipo_tarifa"], nro_lsp=d["nro_lsp"],
                fecha_factura=d["fecha_factura"], fecha_vto1=d["fecha_vto1"], fecha_vto2=d["fecha_vto2"],
                cap_convenida_kw=d["cap_convenida_kw"], cap_adquirida_kw=d["cap_adquirida_kw"],
                tangente_fi=d["tangente_fi"],
                kwh_punta=d["kwh_punta"], kwh_valle_noc=d["kwh_valle_noc"],
                kwh_restantes=d["kwh_restantes"], kvar_reactiva=d["kvar_reactiva"],
                drp_kw=d["drp_kw"], drfp_kw=d["drfp_kw"],
                cargo_fijo=d["cargo_fijo"],
                importe_cap_convenida=d["importe_cap_convenida"],
                importe_cap_adquirida=d["importe_cap_adquirida"],
                importe_kwh_punta=d["importe_kwh_punta"],
                importe_kwh_valle_noc=d["importe_kwh_valle_noc"],
                importe_kwh_restantes=d["importe_kwh_restantes"],
                recargo_reactiva=d["recargo_reactiva"],
                ley_7290=d["ley_7290"], iva_27=d["iva_27"], contrib_art34=d["contrib_art34"],
                contrib_provincial=d["contrib_provincial"], percep_iva=d["percep_iva"],
                cestab=d["cestab"], tasa_mun_ap=d["tasa_mun_ap"],
                bonificaciones=d["bonificaciones"], acpot=d["acpot"], iva_otros=d["iva_otros"],
                importe=d["importe"], observaciones="",
            )
            label = "✓ Nueva" if creada else "↻ Actualizada"
            self._log.append(f"   Estado   : {label}")
            self._resultados.append({"archivo": nombre, "ok": True, "nueva": creada,
                                     "periodo": periodo, "lsp": d["nro_lsp"],
                                     "total": d["importe"]})
        except Exception as exc:
            self._log.append(f"   ERROR DB : {exc}")
            self._resultados.append({"archivo": nombre, "ok": False, "error": str(exc)})

        self._scroll_log()

    def _scroll_log(self) -> None:
        self._log.verticalScrollBar().setValue(self._log.verticalScrollBar().maximum())

    # ── cierre ────────────────────────────────────────────────────────────────

    def _finalizar(self) -> None:
        self._bar.setValue(self._total)
        nuevas       = sum(1 for r in self._resultados if r.get("ok") and r.get("nueva"))
        actualizadas = sum(1 for r in self._resultados if r.get("ok") and not r.get("nueva"))
        errores      = sum(1 for r in self._resultados if not r.get("ok"))
        partes = [f"{nuevas} nueva(s)"]
        if actualizadas:
            partes.append(f"{actualizadas} actualizada(s)")
        if errores:
            partes.append(f"{errores} con error")
        resumen = "Completado: " + ", ".join(partes) + "."
        self._lbl.setText(resumen)
        self._log.append(f"\n{'─'*44}\n{resumen}")
        self._scroll_log()

        for res in self._resultados:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(res["archivo"]))
            if res["ok"]:
                anio_f, mes_f = res["periodo"].split("-")
                self._tabla.setItem(row, 1, QTableWidgetItem(f"{_MESES[int(mes_f)-1]} {anio_f}"))
                self._tabla.setItem(row, 2, QTableWidgetItem(res["lsp"]))
                self._tabla.setItem(row, 3, QTableWidgetItem(f"$ {res['total']:,.2f}"))
                lbl = "Nueva" if res.get("nueva") else "Actualizada"
                it = QTableWidgetItem(lbl)
                it.setForeground(QBrush(QColor("#22c55e" if res.get("nueva") else "#f59e0b")))
                self._tabla.setItem(row, 4, it)
            else:
                for col in [1, 2, 3]:
                    self._tabla.setItem(row, col, QTableWidgetItem("—"))
                it = QTableWidgetItem("Error")
                it.setForeground(QBrush(QColor("#ef4444")))
                it.setToolTip(res["error"])
                self._tabla.setItem(row, 4, it)

        self._btn.setText("Cerrar")
        self._btn.setEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        self.show()


# ── Worker de descarga EDESUR ─────────────────────────────────────────────────

class _DescargaEdesurWorker(QThread):
    progreso = Signal(str)
    listo    = Signal(object)   # ResultadoAPI
    fallo    = Signal(str)

    def __init__(self, usuario: str, clave: str, parent=None) -> None:
        super().__init__(parent)
        self._usuario = usuario
        self._clave   = clave

    def run(self) -> None:
        try:
            from gestion_mantenimiento.services.edesur_scraper import obtener_datos_factura
            resultado = obtener_datos_factura(
                self._usuario, self._clave,
                on_status=self.progreso.emit,
            )
            self.listo.emit(resultado)
        except Exception as exc:
            self.fallo.emit(str(exc))


# ── Diálogos de electricidad ──────────────────────────────────────────────────

class MedidoresDialog(QDialog):
    """CRUD de medidores eléctricos."""

    def __init__(self, database_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = database_path
        self._repo = MedidorRepository(database_path)
        self.setWindowTitle("Gestionar medidores")
        self.setMinimumWidth(500)
        self.resize(520, 400)
        self._build()
        self._load()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        self._tabla = _make_table(["ID", "Nombre", "N° Medidor", "N° Cliente", "Descripción", "Estado"])
        self._tabla.setColumnHidden(0, True)
        self._tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self._tabla)

        btn_row = QHBoxLayout()
        btn_nuevo = _primary_button("+ Nuevo")
        btn_editar = QPushButton("Editar")
        btn_elim = _danger_button("Eliminar")
        btn_cerrar = QPushButton("Cerrar")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar.clicked.connect(self._editar)
        btn_elim.clicked.connect(self._eliminar)
        btn_cerrar.clicked.connect(self.accept)
        btn_row.addWidget(btn_nuevo)
        btn_row.addWidget(btn_editar)
        btn_row.addWidget(btn_elim)
        btn_row.addStretch()
        btn_row.addWidget(btn_cerrar)
        layout.addLayout(btn_row)

    def _load(self) -> None:
        medidores = self._repo.list_all()
        self._tabla.setRowCount(0)
        for m in medidores:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)
            self._tabla.setItem(row, 0, QTableWidgetItem(str(m.id)))
            self._tabla.setItem(row, 1, QTableWidgetItem(m.nombre))
            self._tabla.setItem(row, 2, QTableWidgetItem(m.nro_medidor))
            self._tabla.setItem(row, 3, QTableWidgetItem(m.nro_cliente))
            self._tabla.setItem(row, 4, QTableWidgetItem(m.descripcion))
            self._tabla.setItem(row, 5, QTableWidgetItem("Activo" if m.activo else "Inactivo"))
            item = self._tabla.item(row, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, m.id)

    def _selected_id(self) -> int | None:
        selected = self._tabla.selectedItems()
        if not selected:
            return None
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        if item is None:
            return None
        val = item.data(Qt.ItemDataRole.UserRole)
        return int(val) if val is not None else None

    def _nuevo(self) -> None:
        dlg = MedidorDialog(self._db, None, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load()

    def _editar(self) -> None:
        mid = self._selected_id()
        if mid is None:
            return
        dlg = MedidorDialog(self._db, mid, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load()

    def _eliminar(self) -> None:
        mid = self._selected_id()
        if mid is None:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Eliminar este medidor?\nSe eliminarán también sus facturas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._repo.delete(mid)
                self._load()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))


class MedidorDialog(QDialog):
    def __init__(
        self, database_path: Path, medidor_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._medidor_id = medidor_id
        self._repo = MedidorRepository(database_path)
        self.setWindowTitle("Medidor")
        self.setMinimumWidth(380)
        self._build()
        if medidor_id is not None:
            self._load(medidor_id)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("ej: Tablero principal planta")
        self._nro_medidor = QLineEdit()
        self._nro_medidor.setPlaceholderText("ej: 36110637")
        self._nro_cliente = QLineEdit()
        self._nro_cliente.setPlaceholderText("ej: 80035433")
        self._descripcion = QLineEdit()
        self._activo = QCheckBox("Activo")
        self._activo.setChecked(True)
        form.addRow("Nombre *", self._nombre)
        form.addRow("N° Medidor (físico)", self._nro_medidor)
        form.addRow("N° Cliente EDESUR", self._nro_cliente)
        form.addRow("Descripción", self._descripcion)
        form.addRow("", self._activo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, medidor_id: int) -> None:
        m = self._repo.get_by_id(medidor_id)
        if m is None:
            return
        self._nombre.setText(m.nombre)
        self._nro_medidor.setText(m.nro_medidor)
        self._nro_cliente.setText(m.nro_cliente)
        self._descripcion.setText(m.descripcion)
        self._activo.setChecked(m.activo)

    def _save(self) -> None:
        nombre = self._nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre es requerido.")
            return
        try:
            if self._medidor_id is None:
                self._repo.create(nombre, self._nro_medidor.text().strip(),
                                  self._nro_cliente.text().strip(),
                                  self._descripcion.text().strip())
            else:
                self._repo.update(self._medidor_id, nombre,
                                  self._nro_medidor.text().strip(),
                                  self._nro_cliente.text().strip(),
                                  self._descripcion.text().strip(),
                                  self._activo.isChecked())
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class FacturaElectricaDialog(QDialog):
    """Carga/edición de factura EDESUR con estructura real (T1 / T2 / T3)."""

    def __init__(
        self,
        database_path: Path,
        medidor_id: int,
        anio_default: int,
        factura_id: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db = database_path
        self._medidor_id = medidor_id
        self._factura_id = factura_id
        self._repo = FacturaElectricaRepository(database_path)
        self.setWindowTitle("Factura eléctrica — EDESUR")
        self.setMinimumWidth(520)
        self._anio_default = anio_default
        self._build()
        if factura_id is not None:
            self._load(factura_id)
        self._on_tarifa_changed()

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _money_spin(maximo: float = 99_999_999.0) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(0, maximo)
        sb.setDecimals(2)
        sb.setPrefix("$ ")
        sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sb.setMinimumWidth(140)
        return sb

    @staticmethod
    def _kwh_spin() -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(0, 9_999_999)
        sb.setDecimals(1)
        sb.setSuffix(" kWh")
        sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sb.setMinimumWidth(140)
        return sb

    @staticmethod
    def _date_edit() -> QDateEdit:
        de = QDateEdit()
        de.setCalendarPopup(True)
        de.setDate(QDate.currentDate())
        de.setDisplayFormat("dd/MM/yyyy")
        return de

    @staticmethod
    def _parse_date(s: str) -> QDate | None:
        if not s:
            return None
        try:
            p = s.split("-")
            return QDate(int(p[0]), int(p[1]), int(p[2]))
        except (ValueError, IndexError):
            return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        from PySide6.QtWidgets import QGroupBox, QScrollArea
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Barra de importación ──────────────────────────────────────────────
        import_bar = QFrame()
        import_bar.setObjectName("topbar")
        ib_layout = QHBoxLayout(import_bar)
        ib_layout.setContentsMargins(12, 6, 12, 6)
        lbl_import = QLabel("Cargá el PDF de EDESUR para completar el formulario automáticamente:")
        lbl_import.setObjectName("muted")
        btn_import = _primary_button("Importar PDF")
        btn_import.clicked.connect(self._importar_pdf)
        ib_layout.addWidget(lbl_import, 1)
        ib_layout.addWidget(btn_import)
        outer.addWidget(import_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(10)

        # ── 1. Identificación ──────────────────────────────────────────────────
        grp1 = QGroupBox("Identificación de la factura")
        f1 = QFormLayout(grp1)
        f1.setSpacing(7)

        self._tarifa_combo = QComboBox()
        for label, key in [("T1 — Residencial", "T1"),
                            ("T2 — Comercial / Pequeña industria", "T2"),
                            ("T3 MT — Gran demanda / Media tensión", "T3")]:
            self._tarifa_combo.addItem(label, key)
        self._tarifa_combo.setCurrentIndex(2)   # T3 por defecto
        self._tarifa_combo.currentIndexChanged.connect(self._on_tarifa_changed)
        f1.addRow("Tipo de tarifa *", self._tarifa_combo)

        periodo_row = QHBoxLayout()
        self._mes_combo = QComboBox()
        for nombre in _MESES:
            self._mes_combo.addItem(nombre)
        from datetime import date as _date
        self._mes_combo.setCurrentIndex(_date.today().month - 1)
        self._anio_spin = QSpinBox()
        self._anio_spin.setRange(2000, 2100)
        self._anio_spin.setValue(self._anio_default)
        self._anio_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._anio_spin.setFixedWidth(76)
        periodo_row.addWidget(self._mes_combo)
        periodo_row.addWidget(self._anio_spin)
        f1.addRow("Período *", periodo_row)

        self._nro_lsp = QLineEdit()
        self._nro_lsp.setPlaceholderText("ej: A 9904-02665225 17")
        f1.addRow("LSP N°", self._nro_lsp)

        self._fecha_factura = self._date_edit()
        f1.addRow("Fecha de emisión", self._fecha_factura)

        vto_row = QHBoxLayout()
        self._fecha_vto1 = self._date_edit()
        self._fecha_vto2 = self._date_edit()
        vto_row.addWidget(QLabel("1° vto:"))
        vto_row.addWidget(self._fecha_vto1)
        vto_row.addSpacing(8)
        vto_row.addWidget(QLabel("2° vto:"))
        vto_row.addWidget(self._fecha_vto2)
        f1.addRow("Vencimientos", vto_row)
        layout.addWidget(grp1)

        # ── 2. Datos técnicos y consumo ────────────────────────────────────────
        self._grp_consumo = QGroupBox("Consumo y datos técnicos")
        f2 = QFormLayout(self._grp_consumo)
        f2.setSpacing(7)

        # Capacidades (T2/T3)
        cap_row = QHBoxLayout()
        self._cap_convenida = self._kw_spin()
        self._cap_adquirida = self._kw_spin()
        cap_row.addWidget(QLabel("Conv:"))
        cap_row.addWidget(self._cap_convenida)
        cap_row.addSpacing(8)
        cap_row.addWidget(QLabel("Adquirida:"))
        cap_row.addWidget(self._cap_adquirida)
        self._lbl_cap = QLabel("Cap. Suministro (kW)")
        f2.addRow(self._lbl_cap, cap_row)

        self._tangente_fi = QDoubleSpinBox()
        self._tangente_fi.setRange(0, 10)
        self._tangente_fi.setDecimals(7)
        self._tangente_fi.setSingleStep(0.01)
        self._tangente_fi.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._tangente_fi.setMinimumWidth(140)
        self._lbl_tg = QLabel("Tangente fi (cos φ)")
        f2.addRow(self._lbl_tg, self._tangente_fi)

        # Energía — 3 períodos (T2/T3) o 1 total (T1)
        self._kwh_punta = self._kwh_spin()
        self._kwh_punta.valueChanged.connect(self._recalcular_kwh_total)
        self._lbl_punta = QLabel("kWh Hrs. Punta")
        f2.addRow(self._lbl_punta, self._kwh_punta)

        self._kwh_valle_noc = self._kwh_spin()
        self._kwh_valle_noc.valueChanged.connect(self._recalcular_kwh_total)
        self._lbl_valle = QLabel("kWh Hrs. Valle Noc.")
        f2.addRow(self._lbl_valle, self._kwh_valle_noc)

        self._kwh_restantes = self._kwh_spin()
        self._kwh_restantes.valueChanged.connect(self._recalcular_kwh_total)
        self._lbl_rest = QLabel("kWh Hrs. Restantes")
        f2.addRow(self._lbl_rest, self._kwh_restantes)

        self._lbl_kwh_total = QLabel("kWh Total")
        self._kwh_total_lbl = QLabel("0,0 kWh")
        self._kwh_total_lbl.setObjectName("metricValue")
        f2.addRow(self._lbl_kwh_total, self._kwh_total_lbl)

        self._kvar_reactiva = self._kwh_spin()
        self._kvar_reactiva.setSuffix(" kVAR")
        self._lbl_reactiva = QLabel("Energía Reactiva")
        f2.addRow(self._lbl_reactiva, self._kvar_reactiva)

        sep_dem = QFrame(); sep_dem.setFrameShape(QFrame.Shape.HLine)
        f2.addRow(sep_dem)

        self._drp_kw = QDoubleSpinBox()
        self._drp_kw.setRange(0, 99999); self._drp_kw.setDecimals(1)
        self._drp_kw.setSuffix(" kW"); self._drp_kw.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._drp_kw.setMinimumWidth(130)
        self._lbl_drp = QLabel("DRP — Dem. Reg. Punta (15 min)")
        f2.addRow(self._lbl_drp, self._drp_kw)

        self._drfp_kw = QDoubleSpinBox()
        self._drfp_kw.setRange(0, 99999); self._drfp_kw.setDecimals(1)
        self._drfp_kw.setSuffix(" kW"); self._drfp_kw.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._drfp_kw.setMinimumWidth(130)
        self._lbl_drfp = QLabel("DRFP — Dem. Reg. Fuera Punta (15 min)")
        f2.addRow(self._lbl_drfp, self._drfp_kw)

        # T1: campo simple de kWh
        self._kwh_t1 = self._kwh_spin()
        self._lbl_kwh_t1 = QLabel("kWh consumidos *")
        f2.addRow(self._lbl_kwh_t1, self._kwh_t1)

        layout.addWidget(self._grp_consumo)

        # ── 3. Cargos netos ────────────────────────────────────────────────────
        self._grp_cargos = QGroupBox("Cargos netos del mes")
        f3 = QFormLayout(self._grp_cargos)
        f3.setSpacing(7)

        self._cargo_fijo = self._money_spin()
        self._cargo_fijo.valueChanged.connect(self._recalcular_subtotal)
        f3.addRow("a) Cargo fijo T3", self._cargo_fijo)

        self._imp_cap_conv = self._money_spin()
        self._imp_cap_conv.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_cap_conv = QLabel("b) Cap. Suministro Convenida")
        f3.addRow(self._lbl_cap_conv, self._imp_cap_conv)

        self._imp_cap_adq = self._money_spin()
        self._imp_cap_adq.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_cap_adq = QLabel("c) Cap. Suministro Adquirida")
        f3.addRow(self._lbl_cap_adq, self._imp_cap_adq)

        self._imp_punta = self._money_spin()
        self._imp_punta.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_imp_punta = QLabel("d) Energ. Hrs. Punta")
        f3.addRow(self._lbl_imp_punta, self._imp_punta)

        self._imp_valle_noc = self._money_spin()
        self._imp_valle_noc.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_imp_valle = QLabel("d) Energ. Hrs. Valle Noc.")
        f3.addRow(self._lbl_imp_valle, self._imp_valle_noc)

        self._imp_restantes = self._money_spin()
        self._imp_restantes.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_imp_rest = QLabel("d) Energ. Hrs. Restantes")
        f3.addRow(self._lbl_imp_rest, self._imp_restantes)

        self._recargo_reactiva = self._money_spin()
        self._recargo_reactiva.valueChanged.connect(self._recalcular_subtotal)
        self._lbl_rec_react = QLabel("Recargo Energía Reactiva")
        f3.addRow(self._lbl_rec_react, self._recargo_reactiva)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.Shape.HLine)
        f3.addRow(sep1)
        self._lbl_subtotal_neto = QLabel("$ 0,00")
        self._lbl_subtotal_neto.setObjectName("metricValue")
        f3.addRow("Subtotal cargos netos:", self._lbl_subtotal_neto)

        layout.addWidget(self._grp_cargos)

        # ── 4. Impuestos sobre subtotal neto ──────────────────────────────────
        grp4 = QGroupBox("Contribuciones e impuestos (sobre subtotal neto)")
        f4 = QFormLayout(grp4)
        f4.setSpacing(7)

        self._ley_7290 = self._money_spin()
        self._ley_7290.valueChanged.connect(self._recalcular_subtotal)
        f4.addRow("Ley 7290/67  (1 %)", self._ley_7290)

        self._iva_27 = self._money_spin()
        self._iva_27.valueChanged.connect(self._recalcular_subtotal)
        f4.addRow("IVA  (27 %)", self._iva_27)

        self._contrib_art34 = self._money_spin()
        self._contrib_art34.valueChanged.connect(self._recalcular_subtotal)
        f4.addRow("Contrib. Art. 34  (6.424 %)", self._contrib_art34)

        self._contrib_prov = self._money_spin()
        self._contrib_prov.valueChanged.connect(self._recalcular_subtotal)
        f4.addRow("Contrib. Provincial  (0.001 %)", self._contrib_prov)

        self._percep_iva = self._money_spin()
        self._percep_iva.valueChanged.connect(self._recalcular_subtotal)
        f4.addRow("Percep. IVA RG2408/08  (3 %)", self._percep_iva)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        f4.addRow(sep2)
        self._lbl_subtotal_imp = QLabel("$ 0,00")
        self._lbl_subtotal_imp.setObjectName("metricValue")
        f4.addRow("Subtotal impuestos:", self._lbl_subtotal_imp)
        layout.addWidget(grp4)

        # ── 5. Otros cargos y ajustes ─────────────────────────────────────────
        grp5 = QGroupBox("Otros cargos y ajustes")
        f5 = QFormLayout(grp5)
        f5.setSpacing(7)

        self._cestab = self._money_spin()
        self._cestab.valueChanged.connect(self._recalcular_subtotal)
        f5.addRow("CESTAB  (Res. SE 976-23)", self._cestab)

        self._tasa_mun_ap = self._money_spin()
        self._tasa_mun_ap.valueChanged.connect(self._recalcular_subtotal)
        f5.addRow("Tasa Municipal AP", self._tasa_mun_ap)

        self._bonificaciones = QDoubleSpinBox()
        self._bonificaciones.setRange(-99_999_999, 0)
        self._bonificaciones.setDecimals(2)
        self._bonificaciones.setPrefix("$ ")
        self._bonificaciones.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._bonificaciones.setMinimumWidth(140)
        self._bonificaciones.valueChanged.connect(self._recalcular_subtotal)
        f5.addRow("Bonificaciones (negativo)", self._bonificaciones)

        self._acpot = QDoubleSpinBox()
        self._acpot.setRange(-99_999_999, 0)
        self._acpot.setDecimals(2)
        self._acpot.setPrefix("$ ")
        self._acpot.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._acpot.setMinimumWidth(140)
        self._acpot.valueChanged.connect(self._recalcular_subtotal)
        f5.addRow("ACPOT  (Res. SE 976-23, negativo)", self._acpot)

        self._iva_otros = self._money_spin()
        self._iva_otros.valueChanged.connect(self._recalcular_subtotal)
        f5.addRow("IVA  (21 %)  s/otros cargos", self._iva_otros)

        layout.addWidget(grp5)

        # ── 6. Total ──────────────────────────────────────────────────────────
        grp6 = QGroupBox("Total")
        f6 = QFormLayout(grp6)
        f6.setSpacing(7)
        self._importe_total = self._money_spin()
        self._importe_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        f6.addRow("TOTAL A PAGAR *", self._importe_total)
        layout.addWidget(grp6)

        # ── 7. Observaciones ──────────────────────────────────────────────────
        grp7 = QGroupBox("Observaciones")
        obs_lay = QVBoxLayout(grp7)
        self._observaciones = QTextEdit()
        self._observaciones.setFixedHeight(55)
        obs_lay.addWidget(self._observaciones)
        layout.addWidget(grp7)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        btn_wrap = QWidget()
        bl = QHBoxLayout(btn_wrap)
        bl.setContentsMargins(16, 8, 16, 12)
        bl.addStretch()
        bl.addWidget(buttons)
        outer.addWidget(btn_wrap)

    @staticmethod
    def _kw_spin() -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(0, 9_999_999)
        sb.setDecimals(2)
        sb.setSuffix(" kW")
        sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sb.setMinimumWidth(130)
        return sb

    # ── cargar desde API EDESUR ───────────────────────────────────────────────

    def _cargar_desde_api(self, r) -> None:
        """Rellena el formulario con datos obtenidos de la API de EDESUR."""
        from gestion_mantenimiento.services.edesur_parser import FacturaParseResult
        if not isinstance(r, FacturaParseResult):
            return
        idx = self._tarifa_combo.findData(r.tipo_tarifa)
        if idx >= 0:
            self._tarifa_combo.setCurrentIndex(idx)
        if r.periodo and len(r.periodo) == 7:
            anio_str, mes_str = r.periodo.split("-")
            self._mes_combo.setCurrentIndex(int(mes_str) - 1)
            self._anio_spin.setValue(int(anio_str))
        self._nro_lsp.setText(r.nro_lsp)
        for src, widget in [(r.fecha_factura, self._fecha_factura),
                            (r.fecha_vto1,    self._fecha_vto1)]:
            d = self._parse_date(src)
            if d:
                widget.setDate(d)
        self._kwh_punta.setValue(r.kwh_punta)
        self._kwh_valle_noc.setValue(r.kwh_valle_noc)
        self._kwh_restantes.setValue(r.kwh_restantes)
        self._kwh_t1.setValue(r.kwh_punta)
        self._importe_total.setValue(r.importe)
        self._recalcular_kwh_total()
        self._recalcular_subtotal()
        if r.advertencias:
            QMessageBox.information(
                self, "Datos importados desde EDESUR",
                "Datos de factura y consumo cargados correctamente.\n\n"
                + "\n".join(f"• {a}" for a in r.advertencias)
            )

    # ── importar PDF ──────────────────────────────────────────────────────────

    def _importar_pdf(self, pdf_path: str | None = None) -> None:
        from pathlib import Path as _Path
        if pdf_path is None:
            pdf_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar factura EDESUR (PDF)",
                str(_Path.home()),
                "Archivos PDF (*.pdf *.PDF)",
            )
        if not pdf_path:
            return
        path = pdf_path
        try:
            from gestion_mantenimiento.services.edesur_parser import parse_factura_edesur
            r = parse_factura_edesur(_Path(path))
        except ImportError as exc:
            QMessageBox.critical(self, "Módulo faltante", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Error al leer el PDF", str(exc))
            return

        # ── Rellenar formulario ───────────────────────────────────────────────
        idx = self._tarifa_combo.findData(r.tipo_tarifa)
        if idx >= 0:
            self._tarifa_combo.setCurrentIndex(idx)

        if r.periodo and len(r.periodo) == 7:
            anio, mes = r.periodo.split("-")
            self._mes_combo.setCurrentIndex(int(mes) - 1)
            self._anio_spin.setValue(int(anio))

        self._nro_lsp.setText(r.nro_lsp)

        for src, widget in [(r.fecha_factura, self._fecha_factura),
                            (r.fecha_vto1,    self._fecha_vto1),
                            (r.fecha_vto2,    self._fecha_vto2)]:
            d = self._parse_date(src)
            if d:
                widget.setDate(d)

        self._cap_convenida.setValue(r.cap_convenida_kw)
        self._cap_adquirida.setValue(r.cap_adquirida_kw)
        self._tangente_fi.setValue(r.tangente_fi)
        self._kwh_punta.setValue(r.kwh_punta)
        self._kwh_valle_noc.setValue(r.kwh_valle_noc)
        self._kwh_restantes.setValue(r.kwh_restantes)
        self._kvar_reactiva.setValue(r.kvar_reactiva)
        self._drp_kw.setValue(r.drp_kw)
        self._drfp_kw.setValue(r.drfp_kw)
        self._kwh_t1.setValue(r.kwh_punta)

        self._cargo_fijo.setValue(r.cargo_fijo)
        self._imp_cap_conv.setValue(r.importe_cap_convenida)
        self._imp_cap_adq.setValue(r.importe_cap_adquirida)
        self._imp_punta.setValue(r.importe_kwh_punta)
        self._imp_valle_noc.setValue(r.importe_kwh_valle_noc)
        self._imp_restantes.setValue(r.importe_kwh_restantes)
        self._recargo_reactiva.setValue(r.recargo_reactiva)

        self._ley_7290.setValue(r.ley_7290)
        self._iva_27.setValue(r.iva_27)
        self._contrib_art34.setValue(r.contrib_art34)
        self._contrib_prov.setValue(r.contrib_provincial)
        self._percep_iva.setValue(r.percep_iva)

        self._cestab.setValue(r.cestab)
        self._tasa_mun_ap.setValue(r.tasa_mun_ap)
        self._bonificaciones.setValue(r.bonificaciones)
        self._acpot.setValue(r.acpot)
        self._iva_otros.setValue(r.iva_otros)
        self._importe_total.setValue(r.importe)

        self._recalcular_kwh_total()
        self._recalcular_subtotal()

        # ── Resumen de la importación ─────────────────────────────────────────
        lineas = [
            f"Factura {r.nro_lsp}  —  {r.tipo_tarifa}  —  período {r.periodo}",
            f"Total importado: $ {r.importe:,.2f}",
        ]
        if r.nro_medidor:
            lineas.append(f"Medidor: {r.nro_medidor}  |  Cliente: {r.nro_cliente}")
        if r.advertencias:
            lineas.append("")
            lineas.append("Advertencias (revisar manualmente):")
            lineas.extend(f"  • {a}" for a in r.advertencias)

        QMessageBox.information(self, "PDF importado", "\n".join(lineas))

    # ── lógica dinámica ───────────────────────────────────────────────────────

    def _on_tarifa_changed(self) -> None:
        tarifa = self._tarifa_combo.currentData() or "T3"
        es_t1 = tarifa == "T1"

        t23_widgets = [
            self._lbl_cap, self._cap_convenida, self._cap_adquirida,
            self._lbl_tg, self._tangente_fi,
            self._lbl_punta, self._kwh_punta,
            self._lbl_valle, self._kwh_valle_noc,
            self._lbl_rest, self._kwh_restantes,
            self._lbl_kwh_total, self._kwh_total_lbl,
            self._lbl_reactiva, self._kvar_reactiva,
            self._lbl_cap_conv, self._imp_cap_conv,
            self._lbl_cap_adq, self._imp_cap_adq,
            self._lbl_imp_punta, self._imp_punta,
            self._lbl_imp_valle, self._imp_valle_noc,
            self._lbl_imp_rest, self._imp_restantes,
            self._lbl_rec_react, self._recargo_reactiva,
        ]
        for w in t23_widgets:
            w.setVisible(not es_t1)
        self._lbl_kwh_t1.setVisible(es_t1)
        self._kwh_t1.setVisible(es_t1)
        # DRP/DRFP solo en T2/T3
        for w in (self._lbl_drp, self._drp_kw, self._lbl_drfp, self._drfp_kw):
            w.setVisible(not es_t1)

    def _recalcular_kwh_total(self) -> None:
        total = self._kwh_punta.value() + self._kwh_valle_noc.value() + self._kwh_restantes.value()
        self._kwh_total_lbl.setText(f"{total:,.1f} kWh")

    def _recalcular_subtotal(self) -> None:
        sub_neto = (self._cargo_fijo.value() + self._imp_cap_conv.value()
                    + self._imp_cap_adq.value() + self._imp_punta.value()
                    + self._imp_valle_noc.value() + self._imp_restantes.value()
                    + self._recargo_reactiva.value())
        sub_imp = (self._ley_7290.value() + self._iva_27.value()
                   + self._contrib_art34.value() + self._contrib_prov.value()
                   + self._percep_iva.value())
        otros = (self._cestab.value() + self._tasa_mun_ap.value()
                 + self._bonificaciones.value() + self._acpot.value()
                 + self._iva_otros.value())
        total = sub_neto + sub_imp + otros
        self._lbl_subtotal_neto.setText(f"$ {sub_neto:,.2f}")
        self._lbl_subtotal_imp.setText(f"$ {sub_imp:,.2f}")
        self._importe_total.blockSignals(True)
        self._importe_total.setValue(total)
        self._importe_total.blockSignals(False)

    # ── load / save ───────────────────────────────────────────────────────────

    def _load(self, factura_id: int) -> None:
        f = self._repo.get_by_id(factura_id)
        if f is None:
            return
        idx = self._tarifa_combo.findData(f.tipo_tarifa)
        if idx >= 0:
            self._tarifa_combo.setCurrentIndex(idx)
        anio_f, mes_f = f.periodo.split("-")
        self._mes_combo.setCurrentIndex(int(mes_f) - 1)
        self._anio_spin.setValue(int(anio_f))
        self._nro_lsp.setText(f.nro_lsp)
        for src, widget in [(f.fecha_factura, self._fecha_factura),
                            (f.fecha_vto1, self._fecha_vto1),
                            (f.fecha_vto2, self._fecha_vto2)]:
            d = self._parse_date(src)
            if d:
                widget.setDate(d)
        self._cap_convenida.setValue(f.cap_convenida_kw)
        self._cap_adquirida.setValue(f.cap_adquirida_kw)
        self._tangente_fi.setValue(f.tangente_fi)
        self._kwh_punta.setValue(f.kwh_punta)
        self._kwh_valle_noc.setValue(f.kwh_valle_noc)
        self._kwh_restantes.setValue(f.kwh_restantes)
        self._kvar_reactiva.setValue(f.kvar_reactiva)
        self._drp_kw.setValue(f.drp_kw)
        self._drfp_kw.setValue(f.drfp_kw)
        self._kwh_t1.setValue(f.kwh_punta)   # T1 usa kwh_punta como total
        self._cargo_fijo.setValue(f.cargo_fijo)
        self._imp_cap_conv.setValue(f.importe_cap_convenida)
        self._imp_cap_adq.setValue(f.importe_cap_adquirida)
        self._imp_punta.setValue(f.importe_kwh_punta)
        self._imp_valle_noc.setValue(f.importe_kwh_valle_noc)
        self._imp_restantes.setValue(f.importe_kwh_restantes)
        self._recargo_reactiva.setValue(f.recargo_reactiva)
        self._ley_7290.setValue(f.ley_7290)
        self._iva_27.setValue(f.iva_27)
        self._contrib_art34.setValue(f.contrib_art34)
        self._contrib_prov.setValue(f.contrib_provincial)
        self._percep_iva.setValue(f.percep_iva)
        self._cestab.setValue(f.cestab)
        self._tasa_mun_ap.setValue(f.tasa_mun_ap)
        self._bonificaciones.setValue(f.bonificaciones)
        self._acpot.setValue(f.acpot)
        self._iva_otros.setValue(f.iva_otros)
        self._importe_total.setValue(f.importe)
        self._observaciones.setPlainText(f.observaciones)
        self._recalcular_kwh_total()
        self._recalcular_subtotal()

    def _save(self) -> None:
        tarifa = self._tarifa_combo.currentData() or "T3"
        mes = self._mes_combo.currentIndex() + 1
        anio = self._anio_spin.value()
        periodo = f"{anio}-{mes:02d}"
        importe = self._importe_total.value()

        if tarifa == "T1":
            kwh_p = self._kwh_t1.value()
            kwh_v = kwh_r = 0.0
        else:
            kwh_p = self._kwh_punta.value()
            kwh_v = self._kwh_valle_noc.value()
            kwh_r = self._kwh_restantes.value()

        if (kwh_p + kwh_v + kwh_r) <= 0:
            QMessageBox.warning(self, "Validación", "Ingresá al menos un valor de consumo (kWh).")
            return
        if importe <= 0:
            QMessageBox.warning(self, "Validación", "El total a pagar debe ser mayor a 0.")
            return

        args = dict(
            periodo=periodo, tipo_tarifa=tarifa,
            nro_lsp=self._nro_lsp.text().strip(),
            fecha_factura=self._fecha_factura.date().toString("yyyy-MM-dd"),
            fecha_vto1=self._fecha_vto1.date().toString("yyyy-MM-dd"),
            fecha_vto2=self._fecha_vto2.date().toString("yyyy-MM-dd"),
            cap_convenida_kw=self._cap_convenida.value(),
            cap_adquirida_kw=self._cap_adquirida.value(),
            tangente_fi=self._tangente_fi.value(),
            kwh_punta=kwh_p, kwh_valle_noc=kwh_v, kwh_restantes=kwh_r,
            kvar_reactiva=self._kvar_reactiva.value(),
            drp_kw=self._drp_kw.value(),
            drfp_kw=self._drfp_kw.value(),
            cargo_fijo=self._cargo_fijo.value(),
            importe_cap_convenida=self._imp_cap_conv.value(),
            importe_cap_adquirida=self._imp_cap_adq.value(),
            importe_kwh_punta=self._imp_punta.value(),
            importe_kwh_valle_noc=self._imp_valle_noc.value(),
            importe_kwh_restantes=self._imp_restantes.value(),
            recargo_reactiva=self._recargo_reactiva.value(),
            ley_7290=self._ley_7290.value(),
            iva_27=self._iva_27.value(),
            contrib_art34=self._contrib_art34.value(),
            contrib_provincial=self._contrib_prov.value(),
            percep_iva=self._percep_iva.value(),
            cestab=self._cestab.value(),
            tasa_mun_ap=self._tasa_mun_ap.value(),
            bonificaciones=self._bonificaciones.value(),
            acpot=self._acpot.value(),
            iva_otros=self._iva_otros.value(),
            importe=importe,
            observaciones=self._observaciones.toPlainText().strip(),
        )
        try:
            if self._factura_id is None:
                self._repo.create(medidor_id=self._medidor_id, **args)
            else:
                self._repo.update(factura_id=self._factura_id, **args)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


# ── Diálogo de historial EDESUR ───────────────────────────────────────────────

class EdesurHistorialDialog(QDialog):
    """
    Muestra el historial de facturas EDESUR obtenido por API.
    El usuario elige qué factura cargar y tiene links directos a los PDFs.
    """

    def __init__(self, resultado, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._resultado = resultado
        self._elegido: int | None = 0
        self.setWindowTitle("Historial de facturas EDESUR")
        self.setMinimumWidth(640)
        self.resize(680, 480)
        self._build()

    def exec_get_choice(self) -> int | None:
        self.exec()
        return self._elegido

    def _build(self) -> None:
        layout = QVBoxLayout(self)

        info = QLabel(
            f"Se encontraron <b>{len(self._resultado.todas_facturas)}</b> facturas en tu cuenta EDESUR.<br>"
            "Seleccioná cuál cargar y usá el link para descargar el PDF si necesitás el desglose completo."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabla de facturas
        tabla = _make_table(["#", "Período", "N° Factura", "Total", "Vto 1", "PDF"])
        tabla.setColumnWidth(0, 35)
        tabla.setColumnWidth(1, 90)
        tabla.setColumnWidth(2, 165)
        tabla.setColumnWidth(3, 110)
        tabla.setColumnWidth(4, 90)
        tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        tabla.setSelectionBehavior(tabla.SelectionBehavior.SelectRows)
        tabla.doubleClicked.connect(self._elegir_seleccionado)

        facturas = self._resultado.todas_facturas
        for i, inv in enumerate(facturas):
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            # Período desde issueDate (DD/MM/YYYY → Mes YYYY)
            issue = inv.get("issueDate", "")
            try:
                d, m, y = issue.split("/")
                from datetime import date as _date
                periodo_lbl = f"{_MESES[int(m)-1]} {y}"
            except Exception:
                periodo_lbl = issue
            tabla.setItem(row, 1, QTableWidgetItem(periodo_lbl))
            tabla.setItem(row, 2, QTableWidgetItem(inv.get("number", "")))
            tabla.setItem(row, 3, QTableWidgetItem(f"$ {float(inv.get('totalAmount', 0)):,.2f}"))
            tabla.setItem(row, 4, QTableWidgetItem(inv.get("firstDueDate", "")))

            # Link al PDF
            url_pdf = inv.get("invoiceAccess", "")
            if url_pdf:
                btn_link = QPushButton("Abrir PDF")
                btn_link.setFlat(True)
                btn_link.setStyleSheet("color: #3b82f6; text-decoration: underline;")
                btn_link.setToolTip(f"Abre el PDF en el navegador (requiere verificación)")
                btn_link.clicked.connect(lambda _, u=url_pdf: QDesktopServices.openUrl(QUrl(u)))
                tabla.setCellWidget(row, 5, btn_link)
            else:
                tabla.setItem(row, 5, QTableWidgetItem("No disponible"))

            item0 = tabla.item(row, 0)
            if item0:
                item0.setData(Qt.ItemDataRole.UserRole, i)

        tabla.selectRow(0)
        layout.addWidget(tabla)
        self._tabla = tabla

        nota = QLabel(
            "<i>Los links de PDF abren el portal de descarga de EDESUR en el navegador.<br>"
            "En la página verás un botón 'Descargá tu factura digital' — hacé clic para bajarlo.<br>"
            "Luego usá 'Importar PDF' en el formulario para completar el desglose de cargos.</i>"
        )
        nota.setWordWrap(True)
        nota.setObjectName("muted")
        layout.addWidget(nota)

        btn_row = QHBoxLayout()
        btn_cargar = _primary_button("Cargar factura seleccionada")
        btn_cargar.clicked.connect(self._elegir_seleccionado)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancelar)
        btn_row.addWidget(btn_cargar)
        layout.addLayout(btn_row)

    def _elegir_seleccionado(self) -> None:
        selected = self._tabla.selectedItems()
        if not selected:
            return
        row = self._tabla.row(selected[0])
        item = self._tabla.item(row, 0)
        if item:
            self._elegido = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


# ── Diálogo de credenciales EDESUR ────────────────────────────────────────────

class EdesurCredencialesDialog(QDialog):
    """Guarda usuario y contraseña del portal EDESUR de forma local."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Acceso portal EDESUR")
        self.setMinimumWidth(420)
        self._build()
        self._load()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        aviso = QLabel(
            "Las credenciales se guardan <b>solo en este equipo</b>, "
            "en un archivo local fuera del repositorio.\n"
            "No se comparten con ningún servicio externo."
        )
        aviso.setWordWrap(True)
        aviso.setObjectName("muted")
        layout.addWidget(aviso)

        form = QFormLayout()
        self._usuario = QLineEdit()
        self._usuario.setPlaceholderText("email o usuario EDESUR")
        self._clave = QLineEdit()
        self._clave.setEchoMode(QLineEdit.EchoMode.Password)
        self._clave.setPlaceholderText("contraseña")
        form.addRow("Usuario:", self._usuario)
        form.addRow("Contraseña:", self._clave)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        from gestion_mantenimiento.services.edesur_scraper import cargar_credenciales
        creds = cargar_credenciales()
        self._usuario.setText(creds.get("usuario", ""))
        self._clave.setText(creds.get("clave", ""))

    def _save(self) -> None:
        from gestion_mantenimiento.services.edesur_scraper import guardar_credenciales
        usuario = self._usuario.text().strip()
        clave = self._clave.text()
        if not usuario or not clave:
            QMessageBox.warning(self, "Validación", "Completá usuario y contraseña.")
            return
        guardar_credenciales(usuario, clave)
        self.accept()
