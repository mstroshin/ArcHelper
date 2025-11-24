@echo off
REM ============================================
REM ArcHelperPy - Automatic Build Script
REM ============================================

echo.
echo ========================================
echo    ArcHelperPy Build Script
echo ========================================
echo.

REM Check if Python is installed
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.13 or higher
    pause
    exit /b 1
)

echo [INFO] Python version:
py --version
echo.

REM Check if PyInstaller is installed
py -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyInstaller is not installed
    echo [INFO] Installing PyInstaller...
    py -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
    echo [SUCCESS] PyInstaller installed successfully
    echo.
)

echo [INFO] PyInstaller version:
py -m pip show pyinstaller | findstr "Version"
echo.

REM Ask user which version to build
echo Select build type:
echo 1. Release (no console, GUI only)
echo 2. Debug (with console for troubleshooting)
echo 3. Both
echo.
set /p BUILD_TYPE="Enter your choice (1/2/3): "

if "%BUILD_TYPE%"=="1" goto BUILD_RELEASE
if "%BUILD_TYPE%"=="2" goto BUILD_DEBUG
if "%BUILD_TYPE%"=="3" goto BUILD_BOTH
echo [ERROR] Invalid choice
pause
exit /b 1

:BUILD_RELEASE
echo.
echo ========================================
echo    Building Release Version
echo ========================================
echo.
py -m PyInstaller ArcHelper.spec --clean
if errorlevel 1 (
    echo [ERROR] Release build failed
    pause
    exit /b 1
)
echo.
echo [SUCCESS] Release build completed!
goto END

:BUILD_DEBUG
echo.
echo ========================================
echo    Building Debug Version
echo ========================================
echo.
py -m PyInstaller ArcHelperDebug.spec --clean
if errorlevel 1 (
    echo [ERROR] Debug build failed
    pause
    exit /b 1
)
echo.
echo [SUCCESS] Debug build completed!
goto END

:BUILD_BOTH
echo.
echo ========================================
echo    Building Release Version
echo ========================================
echo.
py -m PyInstaller ArcHelper.spec --clean
if errorlevel 1 (
    echo [ERROR] Release build failed
    pause
    exit /b 1
)
echo [SUCCESS] Release build completed!
echo.
echo ========================================
echo    Building Debug Version
echo ========================================
echo.
py -m PyInstaller ArcHelperDebug.spec --clean
if errorlevel 1 (
    echo [ERROR] Debug build failed
    pause
    exit /b 1
)
echo [SUCCESS] Debug build completed!
goto END

:END
echo.
echo ========================================
echo    Build Summary
echo ========================================
echo.
echo Build output location: dist\
echo.
if exist "dist\ArcHelper.exe" (
    echo [FOUND] ArcHelper.exe - Release version
    for %%A in ("dist\ArcHelper.exe") do echo         Size: %%~zA bytes
)
if exist "dist\ArcHelperDebug.exe" (
    echo [FOUND] ArcHelperDebug.exe - Debug version
    for %%A in ("dist\ArcHelperDebug.exe") do echo         Size: %%~zA bytes
)
echo.
echo Build artifacts: build\
echo Build logs: build\ArcHelper\warn-ArcHelper.txt
echo.
echo ========================================
echo    Build Complete!
echo ========================================
echo.
pause
