@echo off
echo ============================================
echo  DeepScanX AI — Local Development Startup
echo ============================================
echo.

:: Start Flask backend in a new window
echo [1/2] Starting Flask backend on http://localhost:5000 ...
start "DeepScanX Backend" cmd /k "cd /d "%~dp0backend" && python run.py"

:: Wait a moment for Flask to initialize
timeout /t 3 /nobreak > nul

:: Start React frontend in a new window
echo [2/2] Starting React frontend on http://localhost:5173 ...
start "DeepScanX Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are starting in separate windows.
echo  - Frontend: http://localhost:5173
echo  - Backend:  http://localhost:5000
echo.
echo Press any key to close this launcher window...
pause > nul
