@echo off
title PLA-Based Rule Engine Designer
echo ========================================================
echo   Starting PLA-Based Rule Engine Designer Web Server
echo ========================================================
echo.

set PYTHON="C:\Users\ASUS TUF\AppData\Local\Programs\Python\Python312\python.exe"

if not exist %PYTHON% (
    set PYTHON=python
)

echo Using Python: %PYTHON%
%PYTHON% -m pip install -r backend\requirements.txt --quiet

echo.
echo Starting Flask server at http://127.0.0.1:5000 ...
echo Press Ctrl+C to stop.
echo.

start http://127.0.0.1:5000
%PYTHON% backend\app.py

pause
