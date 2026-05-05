@echo off
setlocal
cd /d "%~dp0"
set "VENV_PY=%~dp0.venv\Scripts\python.exe"

echo Iniciando API de tecnicos...
echo.
echo Acceder desde el celular (misma red WiFi):
echo   http://mantenimiento:54321
echo.
echo Presiona Ctrl+C para detener.
echo.

"%~dp0.venv\Scripts\uvicorn.exe" api.main:app --host 0.0.0.0 --port 54321
pause
