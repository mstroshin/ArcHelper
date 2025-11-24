@echo off
REM ============================================
REM ArcHelperPy - Quick Debug Build
REM ============================================

echo Building ArcHelper (Debug)...
py -m PyInstaller ArcHelperDebug.spec --clean

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build completed!
echo Output: dist\ArcHelperDebug.exe
echo.
pause
