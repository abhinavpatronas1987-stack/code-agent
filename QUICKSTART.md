# Code Agent - Quick Start Guide

## Prerequisites

- Python 3.12+
- Ollama running locally (for local LLM)
- Virtual environment set up

## Installation

```powershell
# Clone or navigate to project
cd D:\code-agent

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Running the App

### Basic Start
```powershell
python -m src.cli
```

### With Options
```powershell
# Use specific model
python -m src.cli -m ollama/llama3:8b

# Enable diff preview (see changes before applying)
python -m src.cli --diff

# Dry run mode (show changes without applying)
python -m src.cli --dry-run

# Work in specific directory
python -m src.cli D:\my-project

# Batch mode (run prompts from file)
python -m src.cli -b prompts.txt
```

### Using Start Script
```powershell
.\start.ps1
```

## Verifying Installation

### Run Feature Demo
```powershell
python scripts\run_demo.py
```

### Run All Tests
```powershell
python scripts\test_all_features.py
```

## Available Commands (Inside CLI)

### General
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/quit` or `/exit` | Exit the CLI |
| `/clear` | Clear screen |
| `/status` | Show current status |

### Project Creation (Cross-Platform)
| Command | Description |
|---------|-------------|
| `/new <name> <path> [type]` | Create project in any directory |
| `/new types` | List available project types |

**Project Types:** python, python-api, python-cli, node, node-api, react, vue, go, rust, generic

**Examples:**
```
/new myapp D:\projects python-api
/new myapi ~/projects node-api
/new webapp C:\Users\dev\code react
```

### Models & Configuration
| Command | Description |
|---------|-------------|
| `/model` | List/switch AI models |
| `/model <name>` | Switch to specific model |
| `/profile` | List configuration profiles |
| `/profile <name>` | Switch profile (default, debug, creative, etc.) |

### Code Analysis
| Command | Description |
|---------|-------------|
| `/metrics` | Show code metrics dashboard |
| `/deps` | Analyze dependencies |
| `/explain <file>` | Explain code in plain English |

### File Operations
| Command | Description |
|---------|-------------|
| `/diff` | Toggle diff preview mode |
| `/undo` | Undo last change |
| `/redo` | Redo undone change |
| `/checkpoint` | Create checkpoint |
| `/restore` | Restore from checkpoint |

### Development
| Command | Description |
|---------|-------------|
| `/test` | Run tests |
| `/test --coverage` | Run tests with coverage |
| `/git` | Show git status |
| `/git log` | Show commit history |
| `/git branches` | List branches |

### Documentation
| Command | Description |
|---------|-------------|
| `/docs <file>` | Generate docstrings |
| `/readme` | Generate README |

### Templates & Scaffolding
| Command | Description |
|---------|-------------|
| `/templates` | List code templates |
| `/scaffold <template>` | Create from template |

### Sessions
| Command | Description |
|---------|-------------|
| `/session save` | Save current session |
| `/session load <id>` | Load saved session |
| `/sessions` | List all sessions |

### Advanced
| Command | Description |
|---------|-------------|
| `/dashboard` | Open interactive TUI |
| `/watch` | Toggle file watch mode |
| `/index` | Reindex codebase |
| `/plugins` | List installed plugins |

## Available Models (19 Total)

### Local (Ollama)
- `ollama/gpt-oss:20b` - GPT-OSS 20B
- `ollama/llama3:8b` - Llama 3 8B
- `ollama/llama3:70b` - Llama 3 70B
- `ollama/codellama:13b` - Code Llama 13B
- `ollama/mistral:7b` - Mistral 7B
- `ollama/mixtral:8x7b` - Mixtral 8x7B

### Cloud (Requires API Keys)
- OpenAI: `openai/gpt-4`, `openai/gpt-4-turbo`, `openai/gpt-3.5-turbo`
- Anthropic: `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`
- Google: `google/gemini-pro`, `google/gemini-pro-vision`
- Groq: `groq/llama3-70b`, `groq/mixtral-8x7b`
- OpenRouter: `openrouter/auto`

## Configuration Profiles

| Profile | Description |
|---------|-------------|
| `default` | Balanced settings |
| `debug` | Verbose output, detailed errors |
| `creative` | Higher temperature for creative tasks |
| `precise` | Lower temperature for accuracy |
| `fast` | Optimized for speed |
| `thorough` | Detailed analysis |
| `minimal` | Reduced output |
| `backend` | Backend development focus |

Switch profile:
```
/profile creative
```

## Environment Variables

```powershell
# For cloud models (optional)
$env:OPENAI_API_KEY = "your-key"
$env:ANTHROPIC_API_KEY = "your-key"
$env:GOOGLE_API_KEY = "your-key"
$env:GROQ_API_KEY = "your-key"
```

## Project Structure

```
code-agent/
├── src/
│   ├── cli.py              # Main CLI entry point
│   ├── agents/             # AI agents
│   ├── core/               # 20 feature modules
│   ├── tools/              # 68 tools
│   └── config/             # Settings
├── scripts/
│   ├── run_demo.py         # Feature demo
│   └── test_all_features.py # Test suite
├── data/                   # Runtime data
└── QUICKSTART.md           # This file
```

## Troubleshooting

### Ollama not running
```powershell
# Start Ollama
ollama serve

# Pull a model
ollama pull llama3:8b
```

### Module not found
```powershell
# Ensure venv is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission errors
```powershell
# Run as administrator or check file permissions
```

## Examples

### Analyze a file
```
> Analyze the main.py file and suggest improvements
```

### Create a new feature
```
> Create a REST API endpoint for user authentication
```

### Fix a bug
```
> Fix the TypeError in src/utils/parser.py line 45
```

### Run tests
```
/test --coverage
```

### Generate documentation
```
/docs src/core/metrics_dashboard.py
```

## Support

- 68 tools available
- 20 CLI features
- 19 AI models supported
- 8 configuration profiles
- 10 code templates

All features tested and working!
