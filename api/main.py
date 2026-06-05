from __future__ import annotations

import json
import socket
import subprocess
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

PORT = 54321


def _get_local_ips() -> list[dict]:
    """Devuelve todas las IPs locales (no loopback) con etiqueta."""
    ips: list[dict] = []
    try:
        raw = subprocess.run(
            ["ip", "-j", "addr"], capture_output=True, text=True, timeout=3
        )
        for iface in json.loads(raw.stdout):
            name: str = iface.get("ifname", "")
            if name == "lo":
                continue
            for addr in iface.get("addr_info", []):
                if addr.get("family") == "inet":
                    ip: str = addr["local"]
                    if ip.startswith("192.168.") or ip.startswith("10.") or (
                        ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31
                    ):
                        label = "Red local"
                    elif ip.startswith("25."):
                        label = "VPN Hamachi"
                    else:
                        label = "Red"
                    ips.append({"ip": ip, "label": label, "iface": name})
    except Exception:
        # Fallback mínimo con socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ips.append({"ip": s.getsockname()[0], "label": "Red local", "iface": ""})
        except Exception:
            pass
    return ips


def _get_public_ip() -> str | None:
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=4).read().decode().strip()
    except Exception:
        return None

from api.auth import router as auth_router
from api.database import initialize_api_database
from api.routers.admin import router as admin_router
from api.routers.biblioteca import router as biblioteca_router
from api.routers.ordenes import router as ordenes_router

STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_api_database()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Gestion Mantenimiento API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(ordenes_router)
    app.include_router(biblioteca_router)
    app.include_router(admin_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/api/health", tags=["health"])
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get("/api/network-info", tags=["health"])
    def network_info() -> JSONResponse:
        ips = _get_local_ips()
        public = _get_public_ip()
        if public:
            ips.append({"ip": public, "label": "Internet (IP pública)", "iface": "wan"})
        return JSONResponse({
            "port": PORT,
            "ips": ips,
            "urls": [f"http://{e['ip']}:{PORT}" for e in ips],
        })

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(INDEX_FILE, headers={"Cache-Control": "no-store"})

    @app.get("/{path:path}", include_in_schema=False)
    def spa_fallback(path: str) -> FileResponse:
        return FileResponse(INDEX_FILE, headers={"Cache-Control": "no-store"})

    @app.middleware("http")
    async def no_cache_static(request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()

