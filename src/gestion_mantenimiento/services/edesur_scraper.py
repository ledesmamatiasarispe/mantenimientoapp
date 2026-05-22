"""
Scraper para la Oficina Virtual de EDESUR (ov.edesur.com.ar).

Estrategia:
  1. Login con Playwright → obtiene Bearer token JWT
  2. Llama a la API REST de EDESUR (ed.edesur.com.ar) con el token
  3. Devuelve un FacturaParseResult con los datos disponibles en la API

Datos disponibles vía API (sin PDF):
  - Número de factura (LSP N°), fechas, total
  - kWh punta / valle nocturno / restantes
  - N° de cliente, N° de medidor, tipo de tarifa

Datos que SOLO están en el PDF (requieren importar PDF manualmente):
  - Cargo fijo, importes por capacidad y energía, impuestos detallados
  - DRP, DRFP (demanda en 15 min), CESTAB, Tasa Mun, etc.

Requiere: pip install playwright  →  playwright install chromium
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# Importamos el dataclass del parser PDF para reutilizar como contenedor de resultado
from gestion_mantenimiento.services.edesur_parser import FacturaParseResult


# ── Credenciales ──────────────────────────────────────────────────────────────

def config_path() -> Path:
    from gestion_mantenimiento.data.paths import get_database_path
    return get_database_path().parent / "edesur_credenciales.json"


def cargar_credenciales() -> dict[str, str]:
    import json
    p = config_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def guardar_credenciales(usuario: str, clave: str) -> None:
    import json
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"usuario": usuario, "clave": clave}), encoding="utf-8")


# ── Resultado enriquecido con metadata de la API ──────────────────────────────

@dataclass
class ResultadoAPI:
    resultado: FacturaParseResult
    nro_cliente: str = ""
    nro_medidor_api: str = ""
    tipo_tarifa_api: str = ""
    url_pdf: str = ""              # URL de docuprint (requiere CAPTCHA para bajar)
    todas_facturas: list[dict] = field(default_factory=list)   # lista completa del historial


# ── Función principal ─────────────────────────────────────────────────────────

def obtener_datos_factura(
    usuario: str,
    clave: str,
    on_status: Callable[[str], None] | None = None,
    indice: int = 0,    # 0 = última factura, 1 = la anterior, etc.
) -> ResultadoAPI:
    """
    Hace login en EDESUR y obtiene los datos de la factura (índice 0 = última).
    NO descarga el PDF. Los campos de desglose de cargos quedan en 0.

    Lanza ImportError si playwright no está instalado.
    Lanza RuntimeError si el login falla o la API no responde.
    """
    try:
        import requests as req
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "playwright o requests no están instalados.\n"
            "Ejecutá:\n"
            "  pip install playwright requests\n"
            "  playwright install chromium"
        ) from exc

    def st(msg: str) -> None:
        if on_status:
            on_status(msg)

    # ── 1. Login y captura de token ───────────────────────────────────────────
    st("Conectando al portal EDESUR...")
    token = _login_get_token(usuario, clave, on_status)

    h = {
        "Authorization": token,
        "Accept": "application/json",
        "Referer": "https://ov.edesur.com.ar/",
    }

    # ── 2. Info del cliente (tarifa, medidor, N° cliente) ────────────────────
    st("Obteniendo datos del cliente...")

    # supply-retrieve usa el email y devuelve la lista de suministros
    supply_resp = req.get(
        f"https://ed.edesur.com.ar/api/Cliente/supply-retrieve/{usuario}",
        headers=h, timeout=20,
    )
    supply_data = supply_resp.json()

    # El campo puede ser 'supplies' (lista) o un objeto directo
    if isinstance(supply_data, list):
        supply = supply_data[0] if supply_data else {}
    elif isinstance(supply_data, dict) and "supplies" in supply_data:
        supply = supply_data["supplies"][0] if supply_data["supplies"] else {}
    else:
        supply = supply_data

    nro_cliente = str(supply.get("contractAccount", "") or supply.get("clientNumber", "")).strip()
    if not nro_cliente:
        raise RuntimeError(
            "No se pudo obtener el número de cliente. "
            "Verificá que el usuario tenga suministros asociados."
        )

    # get-client para tarifa y medidor
    cliente = req.get(
        f"https://ed.edesur.com.ar/api/Cliente/get-client/{nro_cliente}",
        headers=h, timeout=20,
    ).json()
    nro_medidor_api = str(cliente.get("meterNumber", "") or "").lstrip("0")
    tipo_tarifa_api = str(cliente.get("groupClient", "T3"))

    # ── 3. Historial de facturas ───────────────────────────────────────────────
    st("Obteniendo historial de facturas...")
    facturas_resp = req.get(
        f"https://ed.edesur.com.ar/api/Cliente/get-historical-invoices/{nro_cliente}",
        headers=h, timeout=20
    ).json()
    facturas = facturas_resp.get("invoices", [])
    if not facturas or indice >= len(facturas):
        raise RuntimeError("No hay facturas disponibles en el historial.")

    factura = facturas[indice]
    nro_lsp       = factura.get("number", "")
    issue_date    = factura.get("issueDate", "")       # "DD/MM/YYYY"
    total         = float(factura.get("totalAmount", 0))
    vto1_raw      = factura.get("firstDueDate", "")
    url_pdf       = factura.get("invoiceAccess", "")

    fecha_factura = _dmy_to_iso(issue_date)
    fecha_vto1    = _dmy_to_iso(vto1_raw) if vto1_raw and vto1_raw != "-" else ""
    periodo       = fecha_factura[:7] if fecha_factura else ""  # YYYY-MM

    # ── 4. Lecturas históricas (kWh por período) ──────────────────────────────
    st("Obteniendo consumo energético...")
    lecturas_resp = req.get(
        f"https://ed.edesur.com.ar/api/Cliente/get-historical-readings/{nro_cliente}",
        headers=h, timeout=20
    ).json()
    lecturas = lecturas_resp.get("readings", [])

    # Buscar la lectura correspondiente al período de la factura
    kwh_punta = kwh_valle = kwh_rest = 0.0
    if lecturas and periodo:
        anio_f, mes_f = periodo.split("-")
        for lec in lecturas:
            rd = lec.get("readingDate", "")[:7]   # "YYYY-MM"
            if rd.startswith(anio_f) and rd[5:7] == mes_f:
                kwh_punta = float(lec.get("activeConsumptionHP", 0) or 0)
                kwh_valle = float(lec.get("activeConsumptionNight", 0) or 0)
                kwh_rest  = float(lec.get("remainingConsumption", 0) or 0)
                break
        else:
            # fallback: primera lectura disponible
            lec = lecturas[0]
            kwh_punta = float(lec.get("activeConsumptionHP", 0) or 0)
            kwh_valle = float(lec.get("activeConsumptionNight", 0) or 0)
            kwh_rest  = float(lec.get("remainingConsumption", 0) or 0)

    # ── 5. Construir resultado ────────────────────────────────────────────────
    advs: list[str] = []
    if not kwh_punta and not kwh_valle and not kwh_rest:
        advs.append("No se encontraron datos de consumo en la API")
    advs.append(
        "Cargos detallados (IVA, contribuciones, cargo fijo, etc.) "
        "requieren importar el PDF manualmente."
    )
    if url_pdf:
        advs.append(f"PDF disponible (requiere CAPTCHA en el navegador): {url_pdf}")

    r = FacturaParseResult(
        tipo_tarifa   = _normalizar_tarifa(tipo_tarifa_api),
        nro_lsp       = nro_lsp,
        nro_cliente   = nro_cliente,
        nro_medidor   = nro_medidor_api,
        periodo       = periodo,
        fecha_factura = fecha_factura,
        fecha_vto1    = fecha_vto1,
        kwh_punta     = kwh_punta,
        kwh_valle_noc = kwh_valle,
        kwh_restantes = kwh_rest,
        importe       = total,
        advertencias  = advs,
    )

    st(f"Datos obtenidos: {nro_lsp} — ${total:,.2f}")

    r.advertencias = [
        "Desglose de cargos (IVA, contribuciones, cargo fijo, etc.) "
        "no está disponible por API. Descargá el PDF y usá 'Importar PDF'."
    ]

    return ResultadoAPI(
        resultado       = r,
        nro_cliente     = nro_cliente,
        nro_medidor_api = nro_medidor_api,
        tipo_tarifa_api = tipo_tarifa_api,
        url_pdf         = url_pdf,
        todas_facturas  = facturas,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def descargar_pdf_visible(
    url: str,
    destino: Path,
    on_status: Callable[[str], None] | None = None,
) -> Path:
    """
    Abre un navegador VISIBLE (no headless) en la URL de docuprint.
    Cloudflare Turnstile se auto-resuelve en modo headed para browsers legítimos.
    Espera hasta 90 s a que el botón se habilite, descarga el PDF y cierra.
    """
    from playwright.sync_api import sync_playwright

    def st(msg: str) -> None:
        if on_status:
            on_status(msg)

    destino.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=900,600",
            ],
        )
        ctx = browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 900, "height": 600},
        )
        page = ctx.new_page()

        st("Abriendo página de descarga (ventana temporal)...")
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        st("Esperando verificación Turnstile (se resuelve automáticamente)...")
        try:
            page.wait_for_selector("#downloadBtn:not([disabled])", timeout=90_000)
        except Exception:
            page.screenshot(path=str(destino / "_debug_turnstile.png"))
            ctx.close()
            browser.close()
            raise RuntimeError(
                "El botón de descarga no se habilitó en 90 segundos.\n"
                "Descargá el PDF manualmente desde el portal EDESUR."
            )

        st("Turnstile resuelto. Descargando PDF...")
        with page.expect_download(timeout=30_000) as dl:
            page.click("#downloadBtn")

        download = dl.value
        nombre = download.suggested_filename or "factura_edesur.pdf"
        pdf_path = destino / nombre
        download.save_as(str(pdf_path))

        ctx.close()
        browser.close()
        st(f"PDF descargado: {nombre}")
        return pdf_path


def _merge_api_pdf(api: "FacturaParseResult", pdf: "FacturaParseResult") -> "FacturaParseResult":
    """Combina datos de la API (identificación/consumo) con datos del PDF (desglose)."""
    from dataclasses import fields, replace
    # Campos que toman el valor del PDF si es > 0 o no vacío
    pdf_fields = {
        "cap_convenida_kw", "cap_adquirida_kw", "tangente_fi",
        "kvar_reactiva", "drp_kw", "drfp_kw",
        "cargo_fijo", "importe_cap_convenida", "importe_cap_adquirida",
        "importe_kwh_punta", "importe_kwh_valle_noc", "importe_kwh_restantes",
        "recargo_reactiva", "ley_7290", "iva_27", "contrib_art34",
        "contrib_provincial", "percep_iva", "cestab", "tasa_mun_ap",
        "bonificaciones", "acpot", "iva_otros",
    }
    updates: dict = {}
    for f in fields(api):
        if f.name in pdf_fields:
            val_pdf = getattr(pdf, f.name)
            if isinstance(val_pdf, float) and val_pdf != 0.0:
                updates[f.name] = val_pdf
            elif isinstance(val_pdf, str) and val_pdf:
                updates[f.name] = val_pdf

    # Mantener advertencias de la API (sin las de PDF que no aplican)
    advs = [a for a in api.advertencias if "PDF" not in a]
    updates["advertencias"] = advs

    return replace(api, **updates)


def _login_get_token(usuario: str, clave: str, on_status: Callable | None) -> str:
    from playwright.sync_api import sync_playwright

    def st(msg: str) -> None:
        if on_status: on_status(msg)

    token_cap: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = ctx.new_page()

        def on_req(r: object) -> None:
            import playwright.sync_api as _pw
            if not isinstance(r, _pw.Request):
                return
            if "ed.edesur.com.ar" in r.url and "authorization" in r.headers and not token_cap:
                token_cap.append(r.headers["authorization"])

        page.on("request", on_req)

        st("Abriendo portal EDESUR...")
        page.goto("https://ov.edesur.com.ar", timeout=40_000)
        page.wait_for_load_state("networkidle", timeout=40_000)

        st("Ingresando credenciales...")
        page.fill('input[type="email"]', usuario)
        page.fill('input[type="password"]', clave)

        st("Iniciando sesión...")
        page.click('button:has-text("Ingresar")')

        try:
            page.wait_for_function(
                "() => !document.querySelector('input[type=\"password\"]')",
                timeout=25_000,
            )
        except Exception:
            texto = page.evaluate("() => document.body.innerText").lower()
            if any(w in texto for w in ["contraseña", "incorrecta", "inválid"]):
                raise RuntimeError("Credenciales incorrectas. Verificá en Acceso EDESUR.")
            raise RuntimeError("El login no se completó. Puede que el portal esté caído.")

        # Navegar a pagos-y-facturas para que el frontend llame a la API y genere el token
        st("Obteniendo token de acceso...")
        page.goto("https://ov.edesur.com.ar/pagos-y-facturas", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)

        ctx.close()
        browser.close()

    if not token_cap:
        raise RuntimeError(
            "No se pudo obtener el token de autenticación de la API EDESUR.\n"
            "Verificá las credenciales e intentá de nuevo."
        )
    return token_cap[0]


def _extraer_cliente_de_token(token: str) -> str:
    """Decodifica el JWT para obtener datos, o extrae el N° de cliente del payload."""
    import base64, json
    try:
        parts = token.replace("Bearer ", "").split(".")
        payload_b64 = parts[1] + "=="   # padding
        payload = json.loads(base64.b64decode(payload_b64))
        # Buscar campo con número de cliente
        for k, v in payload.items():
            if isinstance(v, str) and re.match(r"^\d{8,}$", v):
                return v
    except Exception:
        pass
    return ""


def _dmy_to_iso(s: str) -> str:
    try:
        d, m, y = s.strip().split("/")
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    except Exception:
        return ""


def _normalizar_tarifa(t: str) -> str:
    t = t.upper()
    if "T3" in t: return "T3"
    if "T2" in t: return "T2"
    return "T1"
