@echo off
echo Starting Stockreport Reader Services...
echo ======================================

echo.
echo Starting Upload API on port 9000...
start "Upload API" cmd /k "cd backend && conda activate py311-base && uvicorn upload_api:app --host 0.0.0.0 --port 9000 --reload"

echo.
echo Starting Supervisor API on port 8000...
start "Supervisor API" cmd /k "cd backend && conda activate py311-base && uvicorn agents.supervisor.api:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Starting Frontend on port 5173...
start "Frontend" cmd /k "cd frontend && pnpm dev"

echo.
echo ======================================
echo All services are starting!
echo.
echo Services will be available at:
echo - Frontend: http://localhost:5173
echo - Upload API: http://localhost:9000/docs
echo - Supervisor API: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause > nul 