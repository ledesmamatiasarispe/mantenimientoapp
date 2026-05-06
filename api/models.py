from __future__ import annotations

from pydantic import BaseModel, Field


class TecnicoPublic(BaseModel):
    id: int
    nombre: str
    apellido: str
    legajo: str
    telefono: str
    especialidad: str

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


class LoginRequest(BaseModel):
    legajo: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    tecnico: TecnicoPublic


class RepuestoOrdenItem(BaseModel):
    id: int
    repuesto_id: int | None
    descripcion: str
    cantidad: float
    costo_unitario: float


class ProgramaAdjuntoItem(BaseModel):
    id: int
    tipo: str
    nombre: str


class ProgramaResumen(BaseModel):
    id: int
    descripcion: str
    frecuencia_meses: int
    ultima_ejecucion: str
    proxima_ejecucion: str
    adjuntos: list[ProgramaAdjuntoItem]


class OrdenCard(BaseModel):
    id: int
    equipo_id: int
    equipo_nombre: str
    equipo_tipo_nombre: str
    equipo_marca: str
    equipo_modelo: str
    equipo_ubicacion: str
    tipo: str
    descripcion: str
    fecha_apertura: str
    fecha_cierre: str
    estado: str
    tecnico_id: int | None
    tecnico_nombre: str
    costo_mano_obra: float
    observaciones: str


class ColaboradorItem(BaseModel):
    id: int
    nombre: str
    apellido: str

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


class OrdenDetail(OrdenCard):
    repuestos: list[RepuestoOrdenItem]
    programas: list[ProgramaResumen]
    colaboradores: list[ColaboradorItem] = []


class AgregarRepuestoOrdenRequest(BaseModel):
    repuesto_id: int
    cantidad: float = 1.0


class RepuestoDisponible(BaseModel):
    id: int
    nombre: str
    stock_actual: float
    stock_minimo: float


class HistorialOrdenItem(BaseModel):
    id: int
    tipo: str
    descripcion: str
    fecha_apertura: str
    fecha_cierre: str
    estado: str
    observaciones: str
    tecnico_nombre: str
    colaboradores: list[str] = []


class CrearOrdenRequest(BaseModel):
    equipo_id: int
    tipo: str = "CORRECTIVO"
    descripcion: str = ""
    observaciones: str = ""


class ObservacionRequest(BaseModel):
    texto: str = ""


class CompletarOrdenRequest(BaseModel):
    observaciones: str = ""


class EquipoCard(BaseModel):
    id: int
    nombre: str
    tipo_id: int | None
    tipo_nombre: str
    numero_serie: str
    marca: str
    modelo: str
    ubicacion: str
    observaciones: str
    programas_activos_count: int


class EquipoDetail(EquipoCard):
    fecha_adquisicion: str
    programas: list[ProgramaResumen]


class ProgramaDetail(BaseModel):
    id: int
    equipo_id: int
    equipo_nombre: str
    descripcion: str
    frecuencia_meses: int
    ultima_ejecucion: str
    proxima_ejecucion: str
    adjuntos: list[ProgramaAdjuntoItem]

