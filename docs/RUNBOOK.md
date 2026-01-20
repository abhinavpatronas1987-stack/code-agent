# Code Agent - Operations Runbook

## Table of Contents
1. [Quick Start](#1-quick-start)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Running the Application](#4-running-the-application)
5. [Operations Guide](#5-operations-guide)
6. [Troubleshooting](#6-troubleshooting)
7. [Monitoring](#7-monitoring)
8. [Maintenance](#8-maintenance)

---

## 1. Quick Start

### 30-Second Setup
```bash
# 1. Ensure Ollama is running
ollama serve

# 2. Pull a coding model (if not already)
ollama pull qwen2.5-coder:7b

# 3. Navigate to project
cd D:\code-agent

# 4. Activate environment
.venv\Scripts\activate

# 5. Run CLI
python main.py
```

### Verify Everything Works
```bash
python scripts/test_agent.py
```

Expected output: `6/6 tests passed`

---

## 2. Installation

### 2.1 Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.11+ | `python --version` |
| Ollama | Latest | `ollama --version` |
| Git | Any | `git --version` |

### 2.2 Step-by-Step Installation

#### Step 1: Install Ollama
```bash
# Windows: Download from https://ollama.ai
# Or use winget:
winget install Ollama.Ollama
```

#### Step 2: Pull an LLM Model
```bash
# Recommended for coding tasks:
ollama pull qwen2.5-coder:7b

# Alternative models:
ollama pull llama3.1:8b
ollama pull codellama:13b
ollama pull deepseek-coder:6.7b
```

#### Step 3: Clone/Setup Project
```bash
cd D:\code-agent

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

#### Step 4: Configure Environment
```bash
# Copy example config
copy .env.example .env

# Edit .env with your settings
notepad .env
```

#### Step 5: Verify Installation
```bash
python scripts/test_agent.py
```

---

## 3. Configuration

### 3.1 Environment Variables (.env)

```ini
# ===========================================
# CODE AGENT CONFIGURATION
# ===========================================

# Application Settings
DEBUG=false                    # Enable debug logging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR

# Server Settings (for API mode)
HOST=0.0.0.0                   # Bind address
PORT=8000                      # Port number

# ===========================================
# OLLAMA / LLM CONFIGURATION
# ===========================================

OLLAMA_BASE_URL=http://localhost:11434    # Ollama server URL
OLLAMA_MODEL=qwen2.5-coder:7b             # Model to use
OLLAMA_EMBEDDING_MODEL=nomic-embed-text   # Embedding model (future)

# ===========================================
# AGENT CONFIGURATION
# ===========================================

AGENT_MAX_ITERATIONS=50        # Max tool calls per request
AGENT_TIMEOUT=300              # Request timeout (seconds)
AGENT_MEMORY_ENABLED=true      # Enable conversation memory

# ===========================================
# DATABASE
# ===========================================

DATABASE_URL=sqlite+aiosqlite:///./data/code_agent.db

# ===========================================
# TERMINAL
# ===========================================

TERMINAL_SHELL=powershell.exe  # Windows
# TERMINAL_SHELL=bash          # Linux/Mac
TERMINAL_TIMEOUT=120           # Command timeout (seconds)

# ===========================================
# SECURITY
# ===========================================

SECRET_KEY=change-this-in-production
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### 3.2 Model Selection Guide

| Model | Size | Best For | VRAM Required |
|-------|------|----------|---------------|
| qwen2.5-coder:7b | 4.7GB | Coding tasks | 8GB |
| llama3.1:8b | 4.7GB | General purpose | 8GB |
| codellama:13b | 7.4GB | Code generation | 16GB |
| deepseek-coder:6.7b | 3.8GB | Code completion | 8GB |
| gpt-oss:20b | 13GB | Complex reasoning | 24GB |

### 3.3 Changing Models

```bash
# Update .env
OLLAMA_MODEL=llama3.1:8b

# Or specify at runtime
python -c "
from src.agents.coding_agent import CodingAgent
agent = CodingAgent(model_id='codellama:13b')
"
```

---

## 4. Running the Application

### 4.1 CLI Mode (Interactive)

```bash
# Start in current directory
python main.py

# Start in specific workspace
python main.py cli D:\projects\myapp

# With custom model
python -c "
from src.cli import run_cli
from src.tools.terminal import set_working_dir
from pathlib import Path
set_working_dir(Path('D:/projects/myapp'))
run_cli()
"
```

**CLI Commands:**
| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/cd <path>` | Change directory |
| `/pwd` | Print working directory |
| `/clear` | Clear chat history |
| `/exit` | Exit CLI |

### 4.2 API Server Mode

```bash
# Start server
python main.py serve

# Server runs at http://localhost:8000
```

**API Endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/sessions

# Send message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List files", "session_id": "your-session-id"}'
```

### 4.3 WebSocket Usage

```python
import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:8000/ws/my-session"
    async with websockets.connect(uri) as ws:
        # Send message
        await ws.send(json.dumps({
            "type": "message",
            "content": "What files are here?"
        }))

        # Receive streaming response
        while True:
            response = await ws.recv()
            data = json.loads(response)
            if data["type"] == "done":
                break
            print(data.get("content", ""), end="")

asyncio.run(chat())
```

### 4.4 Running as a Service (Windows)

```powershell
# Create a scheduled task or use NSSM
# Download NSSM from https://nssm.cc

nssm install CodeAgent "D:\code-agent\.venv\Scripts\python.exe"
nssm set CodeAgent AppDirectory "D:\code-agent"
nssm set CodeAgent AppParameters "main.py serve"
nssm start CodeAgent
```

---

## 5. Operations Guide

### 5.1 Daily Operations

#### Check System Status
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check API server (if running)
curl http://localhost:8000/health

# Run test suite
python scripts/test_agent.py
```

#### View Logs
```bash
# Console output shows all interactions
# For file logging, add to settings.py:
# LOG_FILE=logs/code_agent.log
```

### 5.2 Session Management

```bash
# Sessions are stored in: data/agent_storage.db

# View sessions (SQLite)
sqlite3 data/agent_storage.db "SELECT * FROM sessions LIMIT 10;"

# Clear all sessions
rm data/agent_storage.db
# Or
python -c "
from pathlib import Path
Path('data/agent_storage.db').unlink(missing_ok=True)
print('Sessions cleared')
"
```

### 5.3 Working Directory Management

```bash
# The agent operates in a "working directory"
# Default: Current directory when started

# In CLI:
/cd D:\projects\myapp

# Programmatically:
from src.tools.terminal import set_working_dir
from pathlib import Path
set_working_dir(Path('D:/projects/myapp'))
```

---

## 6. Troubleshooting

### 6.1 Common Issues

#### Issue: "Ollama not running"
```bash
# Solution 1: Start Ollama
ollama serve

# Solution 2: Check port
netstat -an | findstr 11434

# Solution 3: Restart Ollama
taskkill /f /im ollama.exe
ollama serve
```

#### Issue: "Model not found"
```bash
# List available models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:7b

# Update .env to match
OLLAMA_MODEL=qwen2.5-coder:7b
```

#### Issue: "Out of memory"
```bash
# Use smaller model
OLLAMA_MODEL=qwen2.5-coder:3b

# Or reduce context window in llm.py
options={
    "num_ctx": 8192,  # Reduce from 32768
}
```

#### Issue: "Command timeout"
```bash
# Increase timeout in .env
TERMINAL_TIMEOUT=300

# Or in specific call
run_terminal_command("long command", timeout=600)
```

#### Issue: "Unicode errors on Windows"
```bash
# Run with UTF-8
chcp 65001
python main.py

# Or set environment
set PYTHONIOENCODING=utf-8
```

### 6.2 Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG

# Run with verbose output
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.cli import run_cli
run_cli()
"
```

### 6.3 Reset Everything

```bash
# Nuclear option - full reset
cd D:\code-agent

# Remove data
rmdir /s /q data

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# Recreate data directory
mkdir data

# Run tests
python scripts/test_agent.py
```

---

## 7. Monitoring

### 7.1 Health Checks

```bash
# Ollama health
curl http://localhost:11434/api/tags

# API server health
curl http://localhost:8000/health

# Full system test
python scripts/test_agent.py
```

### 7.2 Performance Metrics

```python
# Add timing to requests
import time

start = time.time()
response = agent.run("Your query", stream=False)
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
```

### 7.3 Resource Monitoring

```bash
# Windows - Check Ollama memory
tasklist | findstr ollama

# GPU usage (if using CUDA)
nvidia-smi

# Python memory
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

---

## 8. Maintenance

### 8.1 Regular Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Clear old sessions | Weekly | `rm data/agent_storage.db` |
| Update dependencies | Monthly | `pip install -e ".[dev]" -U` |
| Update Ollama | Monthly | `ollama pull model:latest` |
| Backup data | Weekly | `copy data\* backup\` |

### 8.2 Updating the Application

```bash
# Update code (if using git)
git pull

# Update dependencies
pip install -e ".[dev]" -U

# Verify
python scripts/test_agent.py
```

### 8.3 Updating Ollama Models

```bash
# List current models
ollama list

# Update specific model
ollama pull qwen2.5-coder:7b

# Remove old models
ollama rm old-model:tag
```

### 8.4 Database Maintenance

```bash
# Compact SQLite database
sqlite3 data/agent_storage.db "VACUUM;"

# Backup database
copy data\agent_storage.db data\agent_storage_backup.db

# Check database integrity
sqlite3 data/agent_storage.db "PRAGMA integrity_check;"
```

### 8.5 Log Rotation

```python
# Add to settings.py for log rotation
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/code_agent.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## Appendix A: Quick Reference

### CLI Commands
```
/help   - Show help
/cd     - Change directory
/pwd    - Print working directory
/clear  - Clear history
/exit   - Exit
```

### API Endpoints
```
GET  /           - Server info
GET  /health     - Health check
POST /chat       - Send message
POST /sessions   - Create session
GET  /sessions/{id} - Get session
DELETE /sessions/{id} - Delete session
WS   /ws/{id}    - WebSocket streaming
```

### File Locations
```
data/agent_storage.db  - Session database
.env                   - Configuration
logs/                  - Log files (if enabled)
```

### Environment Variables
```
OLLAMA_MODEL          - LLM model name
OLLAMA_BASE_URL       - Ollama server URL
DEBUG                 - Enable debug mode
LOG_LEVEL             - Logging level
TERMINAL_TIMEOUT      - Command timeout
```
