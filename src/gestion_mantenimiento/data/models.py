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
    dni: str
    telefono: str
    especialidad: str
    activo: bool

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
class AppAlert:
    key: str
    source: str
    title: str
    message: str
    entity_id: int
    due_date: str
