@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found at .venv\Scripts\python.exe
    echo Create it first:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    pause
    exit /b 1
)

echo Closing any server already using port 8000...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000 "') do taskkill /F /PID %%p >nul 2>&1

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    if not defined LANIP set LANIP=%%a
)
set LANIP=%LANIP: =%

echo.
echo Starting Minitools Hub on your LAN - accessible from your phone too.
echo On this PC:   http://127.0.0.1:8000/
if defined LANIP (
    echo On the phone: http://%LANIP%:8000/
) else (
    echo Could not detect a LAN IPv4 address - check "ipconfig" manually.
)
echo.

set DJANGO_SETTINGS_MODULE=config.settings.dev
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause
