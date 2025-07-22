@echo off
echo Checking Stockreport Reader Services...
echo ======================================
echo.

echo Checking Frontend (http://localhost:5173)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:5173 || echo Frontend is NOT running
echo.

echo Checking Upload API (http://localhost:9000)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:9000/health || echo Upload API is NOT running
echo.

echo Checking Supervisor API (http://localhost:8000)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8000/health || echo Supervisor API is NOT running
echo.

echo ======================================
echo.
echo If all services show "Status: 200", they are running correctly.
echo.
pause 