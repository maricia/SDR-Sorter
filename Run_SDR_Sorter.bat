@echo off
cd /d "%~dp0"

echo Starting SDR Zip Sorter...
echo.

python SDRSorterGUIV4.py

if errorlevel 1 (
    echo.
    echo ERROR: Python failed to run the application.
    echo Make sure Python is installed and available.
)

pause
