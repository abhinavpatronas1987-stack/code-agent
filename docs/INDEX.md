# Code Agent - Documentation Index

## Quick Links

| Document | Description | When to Use |
|----------|-------------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, components, tech stack | Understanding how the system works |
| [RUNBOOK.md](RUNBOOK.md) | Setup, configuration, operations | Installing, configuring, troubleshooting |
| [CAPABILITIES.md](CAPABILITIES.md) | All features and tools explained | Learning what the agent can do |
| [FLOWS.md](FLOWS.md) | Visual diagrams of all processes | Understanding data flow |

---

## Getting Started (5 Minutes)

```bash
# 1. Start Ollama
ollama serve

# 2. Activate environment
cd D:\code-agent
.venv\Scripts\activate

# 3. Run CLI
python main.py

# 4. Ask anything!
> List all files here
> Create a Python script that prints hello world
> Search for TODO comments
```

---

## Documentation Summary

### Architecture (ARCHITECTURE.md)
- **System Overview**: 4-layer architecture (Client → API → Agent → LLM)
- **Components**: 15 tools across 3 categories
- **Technology**: Agno + Ollama + FastAPI + SQLite
- **Security**: Local LLM, file isolation, timeout protection

### Operations (RUNBOOK.md)
- **Installation**: Step-by-step setup guide
- **Configuration**: All environment variables explained
- **Running**: CLI mode, API server mode, service mode
- **Troubleshooting**: Common issues and solutions
- **Maintenance**: Updates, backups, log rotation

### Capabilities (CAPABILITIES.md)
- **Terminal Tools**: Execute commands, navigate filesystem
- **File Tools**: Read, write, edit, copy, move, delete
- **Search Tools**: Find files, search content, analyze structure
- **Natural Language**: Various ways to phrase requests
- **Examples**: Simple and complex task demonstrations

### Flows (FLOWS.md)
- **Startup Flow**: How the system initializes
- **CLI Flow**: User interaction loop
- **Agent Processing**: How queries become responses
- **Tool Execution**: How tools are called and return results
- **Multi-Tool Sequences**: Complex task orchestration
- **API/WebSocket**: Server communication flows
- **Error Handling**: How errors are managed
- **Session Persistence**: How state is saved

---

## Feature Matrix

| Feature | CLI | API | WebSocket |
|---------|-----|-----|-----------|
| Natural Language Chat | ✅ | ✅ | ✅ |
| Streaming Responses | ✅ | ❌ | ✅ |
| Session Persistence | ✅ | ✅ | ✅ |
| File Operations | ✅ | ✅ | ✅ |
| Terminal Commands | ✅ | ✅ | ✅ |
| Code Search | ✅ | ✅ | ✅ |

---

## Tool Reference

### Terminal Tools (4)
| Tool | Purpose |
|------|---------|
| `run_terminal_command` | Execute shell commands |
| `change_directory` | Navigate filesystem |
| `get_current_directory` | Show current path |
| `list_directory` | List folder contents |

### File Tools (7)
| Tool | Purpose |
|------|---------|
| `read_file` | Read file contents |
| `write_file` | Write/overwrite files |
| `edit_file` | Find and replace in files |
| `create_file` | Create new files |
| `delete_file` | Delete files |
| `move_file` | Move/rename files |
| `copy_file` | Copy files |

### Search Tools (4)
| Tool | Purpose |
|------|---------|
| `search_files` | Search file contents (grep) |
| `find_files` | Find files by name pattern |
| `get_file_structure` | Show directory tree |
| `get_file_info` | Get file metadata |

---

## Configuration Quick Reference

```ini
# Essential settings (.env)
OLLAMA_MODEL=qwen2.5-coder:7b    # LLM model
OLLAMA_BASE_URL=http://localhost:11434
TERMINAL_TIMEOUT=120              # Command timeout
DEBUG=false                       # Debug logging
```

---

## Support & Resources

- **Test Suite**: `python scripts/test_agent.py`
- **Demo**: `python scripts/demo.py`
- **Health Check**: `curl http://localhost:8000/health`

---

## Version

- **Code Agent**: 0.1.0
- **Agno**: 2.3.x
- **Python**: 3.11+
