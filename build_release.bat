@echo off
REM ============================================
REM ArcHelperPy - Quick Release Build
REM ============================================

echo Building ArcHelper (Release)...
py -m PyInstaller ArcHelper.spec --clean

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build completed!
echo Output: dist\ArcHelper.exe
echo.
pause
