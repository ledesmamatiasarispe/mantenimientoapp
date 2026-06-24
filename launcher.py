import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"


def find_python():
    # 1. py launcher
    py = shutil.which("py")
    if py:
        r = subprocess.run([py, "-3", "--version"], capture_output=True)
        if r.returncode == 0:
            return [py, "-3"]

    # 2. python en PATH (solo Python 3)
    python = shutil.which("python")
    if python:
        r = subprocess.run([python, "--version"], capture_output=True, text=True)
        if r.returncode == 0 and "Python 3" in (r.stdout + r.stderr):
            return [python]

    # 3. python3 en PATH
    python3 = shutil.which("python3")
    if python3:
        return [python3]

    # 4. Rutas de instalacion comunes
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

        print("Instalando dependencias (puede tardar unos minutos la primera vez)...")
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip", "-q"])
        r = subprocess.run([str(VENV_PY), "-m", "pip", "install", "-e", str(ROOT), "-q"])
        if r.returncode != 0:
            abort("No se pudieron instalar las dependencias.")

    check = subprocess.run(
        [str(VENV_PY), "-c", "import PySide6, certifi, openpyxl, reportlab"],
        capture_output=True,
    )
    if check.returncode != 0:
        print("Actualizando dependencias...")
        subprocess.run([str(VENV_PY), "-m", "pip", "install", "-e", str(ROOT), "-q"])

    print("Iniciando Gestion Mantenimiento...")
    r = subprocess.run([str(VENV_PY), "-m", "gestion_mantenimiento.main"])
    if r.returncode != 0:
        print("\n La aplicacion cerro con un error.")
        input(" Presiona Enter para cerrar...")


if __name__ == "__main__":
    main()
