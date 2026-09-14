@echo off
echo Installing Portsy...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install Portsy
echo Installing Portsy via pip...
pip install psutil requests
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Copy executable to a standard location
if not exist "%USERPROFILE%\AppData\Local\Portsy" mkdir "%USERPROFILE%\AppData\Local\Portsy"
copy portsy.exe "%USERPROFILE%\AppData\Local\Portsy\"

REM Add to PATH (requires admin rights)
echo.
echo To use 'portsy' command globally, add the following to your PATH:
echo %USERPROFILE%\AppData\Local\Portsy
echo.
echo Installation complete!
echo Run: portsy --help
pause
