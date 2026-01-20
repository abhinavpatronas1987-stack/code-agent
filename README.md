# Code Agent

An Agentic Development Environment (ADE) - AI-powered terminal platform built with Agno and local LLMs.

## Features

- **Natural Language Commands**: Describe what you want to do in plain English
- **Terminal Execution**: Run shell commands, navigate directories
- **File Operations**: Read, write, edit, and search files
- **Code Analysis**: Search codebases, find patterns, analyze structure
- **Local LLM**: Uses Ollama for privacy-first AI (no data leaves your machine)
- **Session Memory**: Remembers context across conversations
- **WebSocket API**: Real-time streaming responses

## Prerequisites

1. **Python 3.11+**
2. **Ollama** - Local LLM runtime
   ```bash
   # Install Ollama: https://ollama.ai
   # Then pull a coding model:
   ollama pull qwen2.5-coder:7b
   ```

## Installation

```bash
# Clone the repository
cd code-agent

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Quick Start

### 1. Start Ollama
Make sure Ollama is running with your model:
```bash
ollama serve
# In another terminal:
ollama run qwen2.5-coder:7b
```

### 2. Run the CLI
```bash
python main.py
```

### 3. Or run the API server
```bash
python main.py serve
```

## Usage

### CLI Mode
```bash
# Start in current directory
python main.py

# Start in specific workspace
python main.py cli /path/to/project
```

CLI Commands:
- `/help` - Show help
- `/cd <path>` - Change directory
- `/pwd` - Show current directory
- `/clear` - Clear history
- `/exit` - Exit

Example prompts:
- "Show me the files in this directory"
- "Read the contents of main.py"
- "Create a new file called utils.py with a function to parse JSON"
- "Find all TODO comments in the codebase"
- "Run the tests"

### API Mode
```bash
python main.py serve
```

The server runs on `http://localhost:8000`:
- `POST /chat` - Send a message (non-streaming)
- `WS /ws/{session_id}` - WebSocket for streaming
- `GET /sessions` - List sessions
- `GET /health` - Health check

## Configuration

Create a `.env` file (see `.env.example`):
```env
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_BASE_URL=http://localhost:11434
DEBUG=false
```

## Project Structure

```
code-agent/
├── src/
│   ├── agents/         # Agent implementations
│   │   └── coding_agent.py
│   ├── api/            # FastAPI server
│   │   └── server.py
│   ├── config/         # Configuration
│   │   └── settings.py
│   ├── core/           # Core components
│   │   ├── llm.py      # Ollama integration
│   │   └── base_agent.py
│   ├── memory/         # Session management
│   │   └── session.py
│   ├── tools/          # Agent tools
│   │   ├── terminal.py    # Terminal commands
│   │   ├── file_ops.py    # File operations
│   │   └── code_search.py # Code search
│   ├── workflows/      # Task management
│   │   └── task_manager.py
│   └── cli.py          # CLI interface
├── tests/              # Test suite
├── scripts/            # Utility scripts
├── main.py             # Entry point
└── pyproject.toml      # Project config
```

## Available Tools

### Terminal Tools
- `run_terminal_command` - Execute shell commands
- `change_directory` - Navigate filesystem
- `get_current_directory` - Show current path
- `list_directory` - List directory contents

### File Tools
- `read_file` - Read file contents
- `write_file` - Write/overwrite files
- `edit_file` - Surgical edits with find/replace
- `create_file` - Create new files
- `delete_file` - Delete files
- `move_file` - Move/rename files
- `copy_file` - Copy files

### Search Tools
- `search_files` - Search file contents (grep-like)
- `find_files` - Find files by name pattern
- `get_file_structure` - Show directory tree
- `get_file_info` - Get file metadata

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run test script
python scripts/test_agent.py

# Format code
ruff format .

# Lint
ruff check .
```

## Roadmap

- [ ] Multi-agent workflows
- [ ] Git integration tools
- [ ] Code execution sandbox
- [ ] Web UI (React + xterm.js)
- [ ] MCP server support
- [ ] Workflow templates

## License

MIT
