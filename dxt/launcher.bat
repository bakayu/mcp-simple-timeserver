@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem If the venv is already configured, just run the server.
if exist "server\venv\.configured" (
    goto :run_server
)

rem --- First-Time Setup Logic ---
echo Configuring MCP Simple Time Server for first run... >&2

rem Find Python
set PYTHON_EXE=
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PYTHON_EXE set PYTHON_EXE=%%i
)
if not defined PYTHON_EXE (
    echo Error: Python not found in PATH. >&2
    exit /b 1
)
echo Found Python at: %PYTHON_EXE% >&2

rem Update pyvenv.cfg
for %%i in ("%PYTHON_EXE%") do set PYTHON_HOME=%%~dpi
set PYTHON_HOME=!PYTHON_HOME:~0,-1!
set CONFIG_FILE=server\venv\pyvenv.cfg
set TEMP_FILE=server\venv\pyvenv.cfg.tmp
(for /f "usebackq delims=" %%a in ("!CONFIG_FILE!") do (
    set "line=%%a"
    echo !line! | findstr /b "home = " >nul
    if !errorlevel! equ 0 (
        echo home = !PYTHON_HOME!
    ) else (
        echo !line!
    )
)) > "!TEMP_FILE!"
move /y "!TEMP_FILE!" "!CONFIG_FILE!" >nul

rem Create marker file to skip this setup next time
echo Configured on %date% %time% > "server\venv\.configured"
echo Configuration complete. Restarting process... >&2

rem Re-execute this script. The parent cmd.exe holds the stdio pipes
rem and will correctly pass them to the new process.
call "%~f0"
exit /b %errorlevel%


:run_server
rem This label is reached on subsequent runs or after the 'call' above.
"server\venv\Scripts\python.exe" -m mcp_simple_timeserver
exit /b %errorlevel! 