from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TipoEquipo:
    id: int
    nombre: str
    activo: bool


@dataclass(frozen=True)
class Equipo:
    id: int
    nombre: str
    tipo_id: int | None
    tipo_nombre: str
    numero_serie: str
    marca: str
    modelo: str
    ubicacion: str
    fecha_adquisicion: str
    observaciones: str
    activo: bool
    horas_trabajo_activo: bool = False
    horas_trabajo_actual: float = 0.0

    @property
    def etiqueta(self) -> str:
        partes = [self.nombre]
        if self.marca:
            partes.append(self.marca)
        if self.modelo:
            partes.append(self.modelo)
        return " - ".join(partes)


@dataclass(frozen=True)
class Tecnico:
    id: int
    nombre: str
    apellido: str
    legajo: str
    telefono: str
    especialidad: str
    activo: bool
    es_admin: bool = False

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


@dataclass(frozen=True)
class OrdenTrabajo:
    id: int
    equipo_id: int
    equipo_nombre: str
    tipo: str
    descripcion: str
    fecha_apertura: str
    fecha_cierre: str
    estado: str
    tecnico_id: int | None
    tecnico_nombre: str
    costo_mano_obra: float
    costo_repuestos: float
    observaciones: str
    horas_trabajo: float | None = None

    @property
    def costo_total(self) -> float:
        return self.costo_mano_obra + self.costo_repuestos


@dataclass(frozen=True)
class OrdenTrabajoCreate:
    equipo_id: int
    tipo: str
    descripcion: str
    fecha_apertura: str
    fecha_cierre: str
    estado: str
    tecnico_id: int | None
    costo_mano_obra: float
    observaciones: str
    horas_trabajo: float | None = None


@dataclass(frozen=True)
class Repuesto:
    id: int
    nombre: str
    observaciones: str
    stock_actual: float
    stock_minimo: float
    activo: bool

    @property
    def bajo_stock(self) -> bool:
        return self.stock_actual <= self.stock_minimo


@dataclass(frozen=True)
class RepuestoOrden:
    id: int
    orden_id: int
    repuesto_id: int | None
    descripcion: str
    cantidad: float
    costo_unitario: float

    @property
    def costo_total(self) -> float:
        return self.cantidad * self.costo_unitario


@dataclass(frozen=True)
class ProgramaMantenimiento:
    id: int
    equipo_id: int
    equipo_nombre: str
    descripcion: str
    frecuencia_meses: int
    ultima_ejecucion: str
    proxima_ejecucion: str
    activo: bool


@dataclass(frozen=True)
class OrdenPrograma:
    id: int
    orden_id: int
    programa_id: int
    programa_descripcion: str


@dataclass(frozen=True)
class ProgramaAdjunto:
    id: int
    programa_id: int
    tipo: str
    nombre: str
    ruta: str


@dataclass(frozen=True)
class Alerta:
    key: str
    tipo: str        # "STOCK_BAJO" | "ORDEN_NUEVA" | "MANT_VENCIDO"
    titulo: str
    mensaje: str
    entidad_id: int


@dataclass(frozen=True)
class AppAlert:
    key: str
    source: str
    title: str
    message: str
    entity_id: int
    due_date: str


@dataclass(frozen=True)
class Medidor:
    id: int
    nombre: str
    nro_medidor: str    # número de serie del medidor físico (ej: 36110637)
    nro_cliente: str    # número de cliente EDESUR (ej: 80035433)
    descripcion: str
    activo: bool


@dataclass(frozen=True)
class FacturaElectrica:
    # ── Identificación ────────────────────────────────────────────────────────
    id: int
    medidor_id: int
    medidor_nombre: str
    periodo: str            # "YYYY-MM"
    tipo_tarifa: str        # "T1" | "T2" | "T3"
    nro_lsp: str            # LSP N° (ej: A 9904-02665225 17)
    fecha_factura: str
    fecha_vto1: str         # primer vencimiento
    fecha_vto2: str         # segundo vencimiento (con mora)
    # ── Datos técnicos ───────────────────────────────────────────────────────
    cap_convenida_kw: float     # Capacidad de Suministro Convenida (CSC)
    cap_adquirida_kw: float     # Capacidad de Suministro Adquirida/Registrada
    tangente_fi: float          # factor de potencia medido
    # ── Consumo energético ────────────────────────────────────────────────────
    kwh_punta: float            # Energía Hrs. Punta
    kwh_valle_noc: float        # Energía Hrs. Valle Nocturno
    kwh_restantes: float        # Energía Hrs. Restantes
    kvar_reactiva: float        # Energía Reactiva (kVAR)
    drp_kw: float               # Dem. Reg. En Punta — máx. 15 min en hs. punta (kW)
    drfp_kw: float              # Dem. Reg. Fuera de Punta — máx. 15 min (kW)
    # ── Cargos netos ──────────────────────────────────────────────────────────
    cargo_fijo: float
    importe_cap_convenida: float
    importe_cap_adquirida: float
    importe_kwh_punta: float
    importe_kwh_valle_noc: float
    importe_kwh_restantes: float
    recargo_reactiva: float
    # ── Impuestos sobre subtotal neto ─────────────────────────────────────────
    ley_7290: float             # 1 %
    iva_27: float               # IVA 27 %
    contrib_art34: float        # Contrib. Art. 34 Contrato Concesión 6.424 %
    contrib_provincial: float   # 0.001 %
    percep_iva: float           # Percepción IVA RG2408/08  3 %
    # ── Otros cargos y ajustes ────────────────────────────────────────────────
    cestab: float               # CESTAB Res SE N° 976-23
    tasa_mun_ap: float          # Tasa Municipal AP
    bonificaciones: float       # Bonificaciones (negativo)
    acpot: float                # ACPOT Res SE N° 976/23 (negativo)
    iva_otros: float            # IVA 21 % s/cargos adicionales
    # ── Total ────────────────────────────────────────────────────────────────
    importe: float              # Total a pagar (1° vencimiento)
    observaciones: str

    @property
    def kwh_total(self) -> float:
        return self.kwh_punta + self.kwh_valle_noc + self.kwh_restantes

    @property
    def subtotal_neto(self) -> float:
        return (self.cargo_fijo + self.importe_cap_convenida + self.importe_cap_adquirida
                + self.importe_kwh_punta + self.importe_kwh_valle_noc
                + self.importe_kwh_restantes + self.recargo_reactiva)

    @property
    def subtotal_impuestos(self) -> float:
        return (self.ley_7290 + self.iva_27 + self.contrib_art34
                + self.contrib_provincial + self.percep_iva)

    @property
    def otros_cargos_neto(self) -> float:
        return self.cestab + self.tasa_mun_ap + self.bonificaciones + self.acpot + self.iva_otros

    @property
    def cos_phi(self) -> float:
        """cos φ calculado desde tangente fi:  cos φ = 1 / √(1 + tg²φ)"""
        import math
        if self.tangente_fi <= 0:
            return 0.0
        return round(1.0 / math.sqrt(1.0 + self.tangente_fi ** 2), 4)

    @property
    def costo_por_kwh(self) -> float:
        total = self.kwh_total
        return self.importe / total if total > 0 else 0.0
