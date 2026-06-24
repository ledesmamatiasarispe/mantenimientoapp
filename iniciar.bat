@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"
set "ROOT=%CD%"
set "PYTHONPATH=%ROOT%\src"
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"
set "PYTHON_EXE="
set "PYTHON_FLAGS="

:: Si el .venv ya existe, saltar busqueda de Python
if exist "%VENV_PY%" goto :run

:: -- Buscar Python -------------------------------------------------------------

:: 1. Python Launcher (py.exe) - disponible con Python 3.3+ en Windows
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_FLAGS=-3"
    goto :create_venv
)

:: 2. python en PATH (verificar que sea Python 3)
python --version >nul 2>&1
if not errorlevel 1 (
    python --version 2>&1 | findstr /C:"Python 3" >nul
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        goto :create_venv
    )
)

:: 3. python3 en PATH
python3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python3"
    goto :create_venv
)

:: 4. Buscar en rutas de instalacion comunes
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :create_venv
    )
)
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :create_venv
    )
)
for /d %%D in ("%ProgramFiles(x86)%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :create_venv
    )
)
for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :create_venv
    )
)

:: Python no encontrado
echo.
echo  [ERROR] No se encontro Python 3 instalado.
echo.
echo  Para instalar Python:
echo    1. Abre tu navegador y ve a: https://www.python.org/downloads/
echo    2. Descarga la version mas reciente de Python 3
echo    3. Durante la instalacion, marca la opcion "Add Python to PATH"
echo    4. Reinicia este launcher
echo.
pause
exit /b 1

:: -- Crear entorno virtual -----------------------------------------------------

:create_venv
echo Creando entorno virtual...
"%PYTHON_EXE%" %PYTHON_FLAGS% -m venv "%ROOT%\.venv"
if errorlevel 1 (
    echo.
    echo  [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

echo Instalando dependencias (solo la primera vez, puede tardar unos minutos)...
"%VENV_PY%" -m pip install --upgrade pip -q
if errorlevel 1 goto :error
"%VENV_PY%" -m pip install -e "%ROOT%" -q
if errorlevel 1 goto :error

:: -- Arrancar la app ----------------------------------------------------------

:run
"%VENV_PY%" -c "import PySide6, certifi, openpyxl, reportlab" >nul 2>&1
if errorlevel 1 (
    echo Actualizando dependencias...
    "%VENV_PY%" -m pip install -e "%ROOT%" -q
    if errorlevel 1 goto :error
)

"%VENV_PY%" -m gestion_mantenimiento.main
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo  La aplicacion cerro con un error.
pause
exit /b 1
