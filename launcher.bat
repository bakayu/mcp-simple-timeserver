@echo off
setlocal enabledelayedexpansion

rem Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

rem Check if already configured
if exist "server\venv\.configured" (
    "server\venv\Scripts\python.exe" -m mcp_simple_timeserver
    exit /b !errorlevel!
)

echo Configuring MCP Simple Time Server for first run... >&2

rem Find Python - get only the first result
set PYTHON_EXE=
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PYTHON_EXE set PYTHON_EXE=%%i
)

if not defined PYTHON_EXE (
    echo Error: Python not found in PATH >&2
    echo Please install Python 3.11 or later and ensure it's in your PATH >&2
    exit /b 1
)

rem Extract the directory from the full path
for %%i in ("%PYTHON_EXE%") do set PYTHON_HOME=%%~dpi
rem Remove trailing backslash
set PYTHON_HOME=!PYTHON_HOME:~0,-1!

echo Found Python at: !PYTHON_HOME! >&2

rem Check Python version
for /f "tokens=2" %%i in ('"%PYTHON_EXE%" --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: !PYTHON_VERSION! >&2

rem Update pyvenv.cfg
set TEMP_FILE=server\venv\pyvenv.cfg.tmp
set CONFIG_FILE=server\venv\pyvenv.cfg

if not exist "!CONFIG_FILE!" (
    echo Error: venv configuration file not found at !CONFIG_FILE! >&2
    exit /b 1
)

rem Read the file line by line and update the home line
(for /f "usebackq delims=" %%a in ("!CONFIG_FILE!") do (
    set "line=%%a"
    echo !line! | findstr /b "home = " >nul
    if !errorlevel! equ 0 (
        echo home = !PYTHON_HOME!
    ) else (
        echo !line!
    )
)) > "!TEMP_FILE!"

rem Replace the original file
move /y "!TEMP_FILE!" "!CONFIG_FILE!" >nul

rem Create marker file
echo Configured on %date% %time% > "server\venv\.configured"

echo Configuration complete. Starting server... >&2

rem Run the server
"server\venv\Scripts\python.exe" -m mcp_simple_timeserver
exit /b !errorlevel! 