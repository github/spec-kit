@echo off
REM Global Memory Installation Script for Windows
REM Usage: install.bat [--global-home PATH] [--skip-ollama]

setlocal enabledelayedexpansion

REM Parse arguments
set "GLOBAL_HOME=%USERPROFILE%\.claude"
set "SKIP_OLLAMA=0"

:parse_args
if "%~1"=="--global-home" (
    set "GLOBAL_HOME=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--skip-ollama" (
    set "SKIP_OLLAMA=1"
    shift
    goto parse_args
)

echo === SpecKit Global Memory Installation ===
echo.
echo Global Home: %GLOBAL_HOME%
echo.

REM Create directory structure
echo [1/5] Creating directory structure...
if not exist "%GLOBAL_HOME%" mkdir "%GLOBAL_HOME%"
if not exist "%GLOBAL_HOME%\spec-kit" mkdir "%GLOBAL_HOME%\spec-kit"
if not exist "%GLOBAL_HOME%\spec-kit\config" mkdir "%GLOBAL_HOME%\spec-kit\config"
if not exist "%GLOBAL_HOME%\spec-kit\templates" mkdir "%GLOBAL_HOME%\spec-kit\templates"
if not exist "%GLOBAL_HOME%\memory" mkdir "%GLOBAL_HOME%\memory"
if not exist "%GLOBAL_HOME%\memory\projects" mkdir "%GLOBAL_HOME%\memory\projects"
if not exist "%GLOBAL_HOME%\memory\backups" mkdir "%GLOBAL_HOME%\memory\backups"
echo Directory structure created.

REM Copy templates
echo [2/5] Copying memory templates...
if exist "templates\memory" (
    xcopy /E /I /Y "templates\memory" "%GLOBAL_HOME%\spec-kit\templates\memory\" >nul
    echo Templates copied.
) else (
    echo Warning: templates\memory not found, skipping template copy.
)

REM Create global memory files
echo [3/5] Initializing global memory...
python "%~dp0init_memory.py" --project-id ".global" --project-name "Global Memory" --global-home "%GLOBAL_HOME%"
if errorlevel 1 (
    echo Error: Failed to initialize global memory.
    exit /b 1
)

REM Check Ollama
echo [4/5] Checking Ollama availability...
if %SKIP_OLLAMA%==1 (
    echo Skipping Ollama check (--skip-ollama specified).
) else (
    python -c "import requests; r = requests.get('http://localhost:11434/api/tags', timeout=2); print('Ollama is running')" >nul 2>&1
    if errorlevel 1 (
        echo Note: Ollama not detected. Vector memory will be disabled.
        echo To install Ollama: https://ollama.ai/download
        echo To use vector memory, install Ollama and run: ollama pull mxbai-embed-large
    ) else (
        echo Ollama detected. Vector memory available.
    )
)

REM Create version file
echo [5/5] Creating version file...
echo 0.1.0 > "%GLOBAL_HOME%\spec-kit\config\.version"
echo Version 0.1.0 installed.

echo.
echo === Installation Complete ===
echo.
echo Memory location: %GLOBAL_HOME%\memory\projects\.global
echo Config location: %GLOBAL_HOME%\spec-kit\config
echo.
echo Next steps:
echo 1. Verify installation: python scripts\memory\verify_install.py
echo 2. Initialize memory for your project: python scripts\memory\init_memory.py
echo 3. See docs/INSTALL_MEMORY.md for full documentation
echo.

endlocal
exit /b 0
