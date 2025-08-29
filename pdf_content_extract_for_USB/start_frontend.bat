@echo off
echo Starting USB PD Parser Frontend Server...
echo.
echo This will start a web server on port 5000.
echo You can access the application at http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python server.py --port 5000

pause
