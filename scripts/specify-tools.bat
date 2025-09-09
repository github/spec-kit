@echo off
REM Windows batch wrapper for spec-kit scripts
REM Provides Command Prompt integration for common spec-kit operations

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: specify-tools.bat ^<command^> [arguments...]
    echo.
    echo Available commands:
    echo   create-feature      Create a new feature branch and structure
    echo   setup-plan          Setup implementation plan structure
    echo   check-prerequisites Check task prerequisites
    echo   update-context      Update agent context files
    echo   get-paths           Get feature paths
    echo.
    echo Use --help with any command for more information
    exit /b 1
)

REM Get repository root
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set REPO_ROOT=%%i
if "%REPO_ROOT%"=="" (
    echo Error: Not in a git repository
    exit /b 1
)

REM Map commands to script names
set COMMAND=%~1
if "%COMMAND%"=="create-feature" set SCRIPT_NAME=create_new_feature
if "%COMMAND%"=="setup-plan" set SCRIPT_NAME=setup_plan
if "%COMMAND%"=="check-prerequisites" set SCRIPT_NAME=check_task_prerequisites
if "%COMMAND%"=="update-context" set SCRIPT_NAME=update_agent_context
if "%COMMAND%"=="get-paths" set SCRIPT_NAME=get_feature_paths

if "%SCRIPT_NAME%"=="" (
    echo Error: Unknown command: %COMMAND%
    exit /b 1
)

REM Shift arguments
shift

REM Try Python script first, then bash as fallback
set PYTHON_SCRIPT=%REPO_ROOT%\scripts\py\%SCRIPT_NAME%.py
set BASH_SCRIPT=%REPO_ROOT%\scripts\%SCRIPT_NAME:_=-%%.sh

if exist "%PYTHON_SCRIPT%" (
    python "%PYTHON_SCRIPT%" %*
) else if exist "%BASH_SCRIPT%" (
    bash "%BASH_SCRIPT%" %*
) else (
    echo Error: Script not found: %SCRIPT_NAME%
    exit /b 1
)

exit /b %errorlevel%