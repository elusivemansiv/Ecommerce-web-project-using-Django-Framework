@echo off
TITLE Bahari Ponno Launcher
echo ==========================================
echo    STARTING BAHARI PONNO PROJECT
echo ==========================================

:: Start the Backend
echo [1/2] Launching Backend Server...
start "BP Backend" cmd /k "cd /d f:\Bahari_Ponno && venv\Scripts\activate && python manage.py runserver"

:: Give the backend a second to start
timeout /t 2 /nobreak > nul

:: Start the Frontend
echo [2/2] Launching Frontend Server...
start "BP Frontend" cmd /k "cd /d f:\UI BP && python -m http.server 3000"

echo.
echo ==========================================
echo    PROJECT IS RUNNING!
echo.
echo    Backend:  http://127.0.0.1:8000
echo    Frontend: http://localhost:3000
echo ==========================================
echo.
echo Close the individual windows to stop the servers.
pause
