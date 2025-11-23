@echo off
REM ArcHelperPy launcher with unbuffered output
REM This ensures console output appears immediately

SET PYTHONUNBUFFERED=1
python main.py
pause
