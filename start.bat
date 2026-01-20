@echo off
setlocal EnableDelayedExpansion
title Code Agent - AI Development Environment
color 0A

echo.
echo ======================================================
echo        CODE AGENT - AI Development Environment
echo        31 Features + 68 Tools - Build Anything!
echo ======================================================
echo.

cd /d D:\code-agent

echo [1/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/4] Configuring LLM Provider...
echo.

REM Check LLM_PROVIDER from .env or default to anthropic
set LLM_PROVIDER=anthropic
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="LLM_PROVIDER" set LLM_PROVIDER=%%b
)

if /i "%LLM_PROVIDER%"=="anthropic" (
    echo Using Anthropic Claude model
    echo.
    set /p ANTHROPIC_API_KEY="Enter your Anthropic API Key: "
    if "!ANTHROPIC_API_KEY!"=="" (
        echo.
        echo [ERROR] API key is required for Anthropic provider!
        echo Either enter a key or change LLM_PROVIDER=ollama in .env
        pause
        exit /b 1
    )
    echo [OK] API key configured
) else (
    echo Using Ollama local model
    echo [3/4] Checking Ollama connection...
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [WARNING] Ollama is not running!
        echo Some features may not work without Ollama.
        echo To start: ollama serve
        echo.
    )
    if %errorlevel% equ 0 (
        echo [OK] Ollama is running
    )
)

echo.
echo [4/4] Starting Code Agent CLI...
echo.
echo ======================================================
echo   COMMANDS:
echo     /help      - Show all commands
echo     /new       - Create new project anywhere
echo     /tasks     - Task board
echo     /secrets   - Scan for secrets
echo     /timer     - Time tracking
echo     /docker    - Docker management
echo     /exit      - Exit
echo.
echo   CHAT: Just type naturally!
echo     "Create a Python API project in D:\projects"
echo     "Analyze my code for security issues"
echo     "Help me fix the error in main.py"
echo ======================================================
echo.

python -m src.cli %*

pause
