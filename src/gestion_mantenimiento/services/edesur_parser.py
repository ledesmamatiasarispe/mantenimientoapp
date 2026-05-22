"""
Parser de facturas PDF de EDESUR — T1, T2 y T3 MT.

Extrae los conceptos de la factura aplicando expresiones regulares
sobre el texto del PDF (no requiere IA).

Requiere: pdfplumber  (pip install pdfplumber)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ── Resultado del parseo ──────────────────────────────────────────────────────

def parse_pdf_worker(pdf_path: str, src_path: str) -> dict:
    """
    Función top-level para ProcessPoolExecutor — corre en un proceso separado,
    sin compartir el GIL con Qt. Devuelve un dict picklable.
    """
    import sys, dataclasses
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        r = parse_factura_edesur(Path(pdf_path))
        d = dataclasses.asdict(r)
        d["ok"] = True
        return d
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@dataclass
class FacturaParseResult:
    tipo_tarifa: str = "T3"
    nro_lsp: str = ""
    nro_cliente: str = ""
    nro_medidor: str = ""
    periodo: str = ""           # YYYY-MM
    fecha_factura: str = ""     # YYYY-MM-DD
    fecha_vto1: str = ""
    fecha_vto2: str = ""        # vacío si la factura no tiene 2° vencimiento explícito
    cap_convenida_kw: float = 0.0
    cap_adquirida_kw: float = 0.0
    tangente_fi: float = 0.0
    kwh_punta: float = 0.0
    kwh_valle_noc: float = 0.0
    kwh_restantes: float = 0.0
    kvar_reactiva: float = 0.0
    drp_kw: float = 0.0     # Demanda Registrada En Punta (15 min, kW)
    drfp_kw: float = 0.0    # Demanda Registrada Fuera de Punta (15 min, kW)
    cargo_fijo: float = 0.0
    importe_cap_convenida: float = 0.0
    importe_cap_adquirida: float = 0.0
    importe_kwh_punta: float = 0.0
    importe_kwh_valle_noc: float = 0.0
    importe_kwh_restantes: float = 0.0
    recargo_reactiva: float = 0.0
    ley_7290: float = 0.0
    iva_27: float = 0.0
    contrib_art34: float = 0.0
    contrib_provincial: float = 0.0
    percep_iva: float = 0.0
    cestab: float = 0.0
    tasa_mun_ap: float = 0.0
    bonificaciones: float = 0.0     # almacenado como negativo
    acpot: float = 0.0              # almacenado como negativo
    iva_otros: float = 0.0
    importe: float = 0.0
    advertencias: list[str] = field(default_factory=list)


# ── Entrada pública ───────────────────────────────────────────────────────────

def parse_factura_edesur(pdf_path: Path | str) -> FacturaParseResult:
    """
    Lee un PDF de EDESUR y devuelve los datos estructurados.

    Lanza ImportError si pdfplumber no está instalado.
    Lanza FileNotFoundError si el archivo no existe.
    """
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "pdfplumber no está instalado.\n"
            "Instalalo con:  pip install pdfplumber"
        ) from exc

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    with pdfplumber.open(path) as pdf:
        # La factura EDESUR es siempre hoja 1; la hoja 2 tiene info general.
        text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""

    return _parse_text(text)


# ── Helpers internos ──────────────────────────────────────────────────────────

def _num(s: str) -> float:
    """Convierte '15,546,363.55' → 15546363.55  (formato EDESUR: coma=miles, punto=decimal)."""
    try:
        return float(s.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def _dmy_to_iso(s: str) -> str:
    """DD/MM/YYYY → YYYY-MM-DD."""
    try:
        d, m, y = s.strip().split("/")
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    except Exception:
        return ""


def _find(pattern: str, text: str, group: int = 1, flags: int = 0) -> str:
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else ""


def _find_num(pattern: str, text: str, group: int = 1, flags: int = 0) -> float:
    return _num(_find(pattern, text, group, flags))


def _last_positive_num(line: str) -> float:
    """Último número de una línea, ignorando los que terminan en '-'."""
    # Busca todos los números; toma el último que NO sea negativo (sin '-' al final)
    nums = re.findall(r'[\d,\.]+(?!-)', line)
    for raw in reversed(nums):
        try:
            return float(raw.replace(",", ""))
        except ValueError:
            continue
    return 0.0


def _neg_num(pattern: str, text: str) -> float:
    """Extrae un número que en la factura aparece con '-' al final (bonif., acpot)."""
    m = re.search(pattern + r'.*?([\d,\.]+)-\s*$', text, re.MULTILINE)
    return -_num(m.group(1)) if m else 0.0


# ── Parser principal ──────────────────────────────────────────────────────────

def _parse_text(text: str) -> FacturaParseResult:  # noqa: PLR0912
    r = FacturaParseResult()

    # ── Identificación ────────────────────────────────────────────────────────

    # LSP N° A 9904-02665225 17
    lsp = _find(r'LSP\s+N[°o]?\s+([A-Z]\s+[\d\-]+\s+\d+)', text)
    if not lsp:
        # Alternativa en el cuerpo: "Liquidación de Servicios Públicos (LSP) A 9904-..."
        lsp = _find(r'\(LSP\)\s+([A-Z]\s+[\d\-]+\s+\d+)', text)
    r.nro_lsp = lsp

    # Número de cliente
    r.nro_cliente = _find(
        r'n[uú]mero de cliente es\s*(\d+)', text, flags=re.IGNORECASE
    )

    # Número de medidor — primera fila de la tabla que empieza con dígitos
    m_med = re.search(r'^(\d{5,12})\s+(?:Cap\.|Energ\.)', text, re.MULTILINE)
    r.nro_medidor = m_med.group(1) if m_med else ""

    # Tipo de tarifa
    tarifa_raw = _find(r'Tarifa\s+(T\d(?:\s+MT)?)', text)
    if "T3" in tarifa_raw:
        r.tipo_tarifa = "T3"
    elif "T2" in tarifa_raw:
        r.tipo_tarifa = "T2"
    elif "T1" in tarifa_raw:
        r.tipo_tarifa = "T1"

    # ── Fechas ────────────────────────────────────────────────────────────────

    fecha_raw = _find(r'(?:Capital Federal|Buenos Aires)\s+(\d{2}/\d{2}/\d{4})', text)
    r.fecha_factura = _dmy_to_iso(fecha_raw)
    if r.fecha_factura:
        r.periodo = r.fecha_factura[:7]   # YYYY-MM

    # 1° vencimiento: "Esta liquidación vence el 29/05/2026"
    vto1_raw = _find(r'vence el\s+(\d{2}/\d{2}/\d{4})', text)
    r.fecha_vto1 = _dmy_to_iso(vto1_raw)

    # 2° vencimiento: en algunos tipos de factura hay fecha explícita
    vto2_raw = _find(r'L[íi]mite de pago en Banco\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})', text)
    if vto2_raw and vto2_raw != vto1_raw:
        r.fecha_vto2 = _dmy_to_iso(vto2_raw)

    # ── Datos técnicos (T2/T3) ────────────────────────────────────────────────

    # "Convenida 616.32" / "Adquirida 536.40" (tabla de Potencias)
    r.cap_convenida_kw = _find_num(r'Convenida\s+([\d,\.]+)', text)
    r.cap_adquirida_kw = _find_num(r'Adquirida\s+([\d,\.]+)', text)

    # "Tangente fi medido 0.1300000"
    r.tangente_fi = _find_num(r'[Tt]angente\s+fi\s+medido\s+([\d\.]+)', text)

    # ── Tabla de cargos liquidados ────────────────────────────────────────────
    # Formato: "... XX,XXX.XXX KWH YY,YYY.YY"  o  "... XX,XXX.XXX KW YY,YYY.YY"

    # Energía Hrs. Punta
    m = re.search(
        r'Energ\.\s+Hrs\.\s+[Pp]unta.*?([\d,\.]+)\s+KWH\s+([\d,\.]+)',
        text, re.DOTALL,
    )
    if m:
        r.kwh_punta = _num(m.group(1))
        r.importe_kwh_punta = _num(m.group(2))

    # Energía Hrs. Valle Nocturno
    m = re.search(
        r'Energ\.\s+Hrs\.\s+Valle\s+Noc.*?([\d,\.]+)\s+KWH\s+([\d,\.]+)',
        text, re.DOTALL,
    )
    if m:
        r.kwh_valle_noc = _num(m.group(1))
        r.importe_kwh_valle_noc = _num(m.group(2))

    # Energía Hrs. Restantes
    m = re.search(
        r'Energ\.\s+Hrs\.\s+Restantes.*?([\d,\.]+)\s+KWH\s+([\d,\.]+)',
        text, re.DOTALL,
    )
    if m:
        r.kwh_restantes = _num(m.group(1))
        r.importe_kwh_restantes = _num(m.group(2))

    # Energía Reactiva: "2,952.000 Kvar 0.00"
    m = re.search(
        r'Recargo\s+Energ[íi]?a\s+Reactiva.*?([\d,\.]+)\s+Kvar\s+([\d,\.]+)',
        text, re.DOTALL,
    )
    if m:
        r.kvar_reactiva = _num(m.group(1))
        r.recargo_reactiva = _num(m.group(2))

    # Cap. Suministro Convenida: "616.320 KW 3,287,433.62"
    m = re.search(
        r'Cap\.Sum\.Conv\..*?([\d,\.]+)\s+KW\s+([\d,\.]+)', text, re.DOTALL
    )
    if m:
        r.importe_cap_convenida = _num(m.group(2))

    # Cap. Suministro Adquirida: "536.400 KW 5,316,732.43"
    m = re.search(
        r'Cap\.Sum\.Adquirida.*?([\d,\.]+)\s+KW\s+([\d,\.]+)', text, re.DOTALL
    )
    if m:
        r.importe_cap_adquirida = _num(m.group(2))

    # Cargo Fijo T3 — último número de la línea (no tiene KW/KWH)
    m = re.search(r'Cargo Fijo T\d(.+)', text)
    if m:
        r.cargo_fijo = _last_positive_num("X" + m.group(1))

    # ── Impuestos sobre subtotal neto ─────────────────────────────────────────

    r.ley_7290 = _find_num(r'Ley 7290.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE)

    # IVA 27% — buscar con "27" en la misma línea
    m = re.search(r'Valor Agregado\s+27[.,]\d+%.*?([\d,\.]+)\s*$', text, re.MULTILINE)
    r.iva_27 = _num(m.group(1)) if m else 0.0

    r.contrib_art34 = _find_num(
        r'Contrib\.Art\.34.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE
    )
    r.contrib_provincial = _find_num(
        r'Contribuci[oó]n Provincial.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE
    )
    r.percep_iva = _find_num(
        r'Percep\s+IVA\s+RG2408.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE
    )

    # ── Otros cargos ──────────────────────────────────────────────────────────

    r.cestab = _find_num(r'CESTAB.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE)
    r.tasa_mun_ap = _find_num(r'Tasa Mun\..*?([\d,\.]+)\s*$', text, flags=re.MULTILINE)

    # Bonificaciones: "Bonificación Res ENRE 579/2024 473.74-"
    r.bonificaciones = _neg_num(r'Bonificaci[oó]n\s+Res\s+ENRE', text)

    # ACPOT: "ACPOT según Res SE N° 976/23 7,136.00-"
    r.acpot = _neg_num(r'ACPOT', text)

    # IVA 21% sobre otros cargos
    m = re.search(r'Valor Agregado\s+21[.,]\d+%.*?([\d,\.]+)\s*$', text, re.MULTILINE)
    r.iva_otros = _num(m.group(1)) if m else 0.0

    # ── Total ─────────────────────────────────────────────────────────────────

    r.importe = _find_num(
        r'Total a Pagar Hasta.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE
    )
    if r.importe == 0:
        r.importe = _find_num(
            r'Subtotal Cargos del Mes.*?([\d,\.]+)\s*$', text, flags=re.MULTILINE
        )

    # ── Demanda máxima en 15 minutos (tabla histórica) ───────────────────────
    # La tabla muestra 6 meses; el último valor de cada fila = mes actual.
    # Formato:  "DRP 16 18 22 17 57 12"  →  DRP mes actual = 12
    #           "DRFP 501 487 481 511 498 536"  →  DRFP = 536
    def _last_int_in_row(label: str) -> float:
        # DRP/DRFP pueden estar en la misma línea que otro campo (ej. "Convenida 616.32 DRP 16 18 22 17 57 12")
        m = re.search(rf'{label}\s+((?:\d+\s+)*\d+)', text)
        if not m:
            return 0.0
        nums = m.group(1).split()
        return float(nums[-1]) if nums else 0.0

    r.drp_kw  = _last_int_in_row("DRP")
    r.drfp_kw = _last_int_in_row("DRFP")

    # ── Advertencias por campos clave no encontrados ──────────────────────────

    if not r.nro_lsp:
        r.advertencias.append("No se encontró el número de LSP (N° de factura)")
    if not r.nro_medidor:
        r.advertencias.append("No se encontró el número de medidor")
    if not r.fecha_factura:
        r.advertencias.append("No se pudo extraer la fecha de emisión")
    if r.importe == 0:
        r.advertencias.append("No se pudo extraer el total a pagar")
    if r.kwh_punta + r.kwh_valle_noc + r.kwh_restantes == 0 and r.tipo_tarifa != "T1":
        r.advertencias.append("No se encontraron valores de consumo energético (kWh)")

    return r
