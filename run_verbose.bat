@echo off
REM ArcHelperPy launcher with unbuffered output (verbose mode)
REM This ensures console output appears immediately

echo.
echo ===============================================
echo Starting ArcHelperPy...
echo ===============================================
echo.
echo Setting PYTHONUNBUFFERED=1 to disable output buffering...
SET PYTHONUNBUFFERED=1

echo Running Python with unbuffered mode...
echo.

python main.py

echo.
echo ===============================================
echo ArcHelperPy has been closed
echo ===============================================
echo.
pause
