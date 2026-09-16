@echo off
setlocal
title Paga-Ya Simulador - Arranque automatico
cd /d "%~dp0"

echo ============================================================
echo   PAGA-YA SIMULADOR EDUCATIVO (legal, sin reja)
echo   Arranque automatico: instala, migra, puebla demo y levanta
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python. Instala Python 3.12+ desde https://www.python.org/downloads/
  echo         OJO: marca la casilla "Add python.exe to PATH" al instalar.
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Node.js. Instalo Node 20+ LTS desde https://nodejs.org
  pause
  exit /b 1
)

echo [1/5] Verificando venv del backend (aislado, no toca tu Python global)...
if not exist "backend\venv" (
  echo       Creando backend\venv...
  python -m venv backend\venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el venv.
    pause
    exit /b 1
  )
)
call backend\venv\Scripts\activate.bat

echo [2/5] Instalando librerias del backend...
python -m pip install --upgrade pip >nul
pip install -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] Fallo pip install. Revisa tu internet.
  pause
  exit /b 1
)

echo [3/5] Generando migraciones y migrando base de datos SQLite...
python backend\manage.py makemigrations
python backend\manage.py migrate
if errorlevel 1 (
  echo [ERROR] Fallo migrate.
  pause
  exit /b 1
)

echo [4/5] Poblando datos de demostracion (solo la primera vez)...
python backend\manage.py seed_demo

echo [5/5] Levantando servidores...
start "Paga Ya - Backend :8000" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python manage.py runserver"
start "Paga Ya - Frontend :5173" cmd /k "cd /d "%~dp0frontend" && if not exist node_modules call npm install && call npm run dev"

echo.
echo Esperando a que levanten los servidores...
timeout /t 9 >nul
start http://localhost:5173
echo.
echo ============================================================
echo   LISTO:
echo     Frontend: http://localhost:5173
echo     Backend:  http://localhost:8000/api/
echo     Demo: admin/admin123 ^| don_chepe/chepe123 ^| carlos/cliente123
echo   No cierres las dos ventanas negras mientras lo uses.
echo ============================================================
pause
