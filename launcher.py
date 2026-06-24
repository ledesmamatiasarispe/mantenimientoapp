import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request
from pathlib import Path

ROOT      = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
VENV_PY   = ROOT / ".venv" / "Scripts" / "python.exe"
SHA_FILE  = ROOT / "_version.txt"

GITHUB_REPO   = "ledesmamatiasarispe/mantenimientoapp"
GITHUB_BRANCH = "master"

# Archivos y carpetas que nunca se tocan al actualizar
SKIP_UPDATE = {
    ".venv", "iniciar.exe", "_version.txt",
    "cronograma_dump.json", "fichas_raw_dump.json",
}


# ── Busqueda de Python del sistema ────────────────────────────────────────────

def find_python():
    py = shutil.which("py")
    if py:
        r = subprocess.run([py, "-3", "--version"], capture_output=True)
        if r.returncode == 0:
            return [py, "-3"]

    python = shutil.which("python")
    if python:
        r = subprocess.run([python, "--version"], capture_output=True, text=True)
        if r.returncode == 0 and "Python 3" in (r.stdout + r.stderr):
            return [python]

    python3 = shutil.which("python3")
    if python3:
        return [python3]

    bases = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python",
        Path(os.environ.get("ProgramFiles", "")),
        Path(os.environ.get("ProgramFiles(x86)", "")),
        Path("C:/"),
    ]
    for base in bases:
        if base.exists():
            for d in sorted(base.glob("Python3*"), reverse=True):
                exe = d / "python.exe"
                if exe.exists():
                    return [str(exe)]

    return None


def abort(msg):
    print(f"\n [ERROR] {msg}\n")
    input(" Presiona Enter para cerrar...")
    sys.exit(1)


# ── Auto-actualizacion desde GitHub (sin Git) ─────────────────────────────────

def _remote_sha():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{GITHUB_BRANCH}"
    req = urllib.request.Request(url, headers={"User-Agent": "mantenimientoapp-launcher"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())["sha"]
    except Exception:
        return None


def _local_sha():
    return SHA_FILE.read_text().strip() if SHA_FILE.exists() else None


def _download_update(sha):
    url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
    print(f"  Descargando actualizacion desde GitHub...")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "update.zip"
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)
            # El ZIP contiene una carpeta raiz ej. "mantenimientoapp-master/"
            src_root = next(p for p in Path(tmp).iterdir() if p.is_dir())
            for item in src_root.iterdir():
                if item.name in SKIP_UPDATE:
                    continue
                dest = ROOT / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        SHA_FILE.write_text(sha)
        return True
    except Exception as e:
        print(f"  Advertencia: no se pudo aplicar la actualizacion ({e})")
        return False


def auto_update():
    print("Verificando actualizaciones...")
    remote = _remote_sha()
    if remote is None:
        print("  Sin conexion, usando version local.")
        return False

    local = _local_sha()
    if local == remote:
        print("  Version al dia.")
        return False

    if local is None:
        print("  Primera verificacion de version...")
    else:
        print(f"  Nueva version disponible ({local[:8]} -> {remote[:8]})")

    updated = _download_update(remote)
    if updated:
        print("  Actualizacion aplicada. Reinstalando dependencias...")
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "-e", str(ROOT), "-q"])
    return updated


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.environ["PYTHONPATH"] = str(ROOT / "src")

    if not VENV_PY.exists():
        print("Buscando Python...")
        python_cmd = find_python()
        if not python_cmd:
            abort(
                "No se encontro Python 3 instalado.\n\n"
                " Para instalar Python:\n"
                "   1. Ve a: https://www.python.org/downloads/\n"
                "   2. Descarga Python 3.11 o superior\n"
                "   3. Durante la instalacion, marca 'Add Python to PATH'\n"
                "   4. Reinicia este launcher"
            )

        print("Creando entorno virtual...")
        r = subprocess.run(python_cmd + ["-m", "venv", str(ROOT / ".venv")])
        if r.returncode != 0:
            abort("No se pudo crear el entorno virtual.")

        # Actualizar al ultimo codigo antes de instalar deps
        remote = _remote_sha()
        if remote and remote != _local_sha():
            _download_update(remote)

        print("Instalando dependencias (puede tardar unos minutos la primera vez)...")
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip", "-q"])
        r = subprocess.run([str(VENV_PY), "-m", "pip", "install", "-e", str(ROOT), "-q"])
        if r.returncode != 0:
            abort("No se pudieron instalar las dependencias.")

        print("Descargando navegador para integracion EDESUR (~200 MB, solo una vez)...")
        subprocess.run([str(VENV_PY), "-m", "playwright", "install", "chromium"])

    else:
        auto_update()

    # Verificacion rapida de dependencias
    check = subprocess.run(
        [str(VENV_PY), "-c",
         "import PySide6, certifi, openpyxl, reportlab, pdfplumber, playwright"],
        capture_output=True,
    )
    if check.returncode != 0:
        print("Actualizando dependencias...")
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "-e", str(ROOT), "-q"])
        subprocess.run([str(VENV_PY), "-m", "playwright", "install", "chromium"])

    print("Iniciando Gestion Mantenimiento...")
    r = subprocess.run([str(VENV_PY), "-m", "gestion_mantenimiento.main"])
    if r.returncode != 0:
        print("\n La aplicacion cerro con un error.")
        input(" Presiona Enter para cerrar...")


if __name__ == "__main__":
    main()
