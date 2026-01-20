# CODE AGENT - RUNBOOK & USER GUIDE

## What is Code Agent?

Code Agent is a **world-class AI-powered CLI development assistant** that runs locally on your machine. It uses natural language to help you with software development tasks - you tell it what you want in plain English, and it uses its 74 tools + 20 product features to accomplish the task.

```
┌─────────────────────────────────────────────────────────────┐
│  YOU: "Create a Python function to parse JSON files"        │
│                           ↓                                 │
│  CODE AGENT: Understands → Plans → Executes → Reports       │
│                           ↓                                 │
│  RESULT: Creates the file with working code                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Ollama running locally (`ollama serve`)
- Virtual environment set up

### Start Code Agent
```powershell
cd D:\code-agent
.\.venv\Scripts\Activate.ps1
python -m src.main
```

### First Command
```
> Hello, list all files in the current directory
```

---

## 74 Tools Available (12 Categories)

### 1. Terminal Tools (4 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `run_terminal_command` | Execute any shell command | "Run npm install" |
| `list_directory` | List files in folder | "Show files in src/" |
| `get_current_directory` | Get current path | "What directory am I in?" |
| `change_directory` | Navigate folders | "Change to the tests folder" |

### 2. File Operations (7 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `read_file` | Read file contents | "Read the config.py file" |
| `write_file` | Write/overwrite file | "Write 'hello' to test.txt" |
| `create_file` | Create new file | "Create a new module called utils.py" |
| `edit_file` | Find and replace | "Change 'foo' to 'bar' in main.py" |
| `delete_file` | Delete a file | "Delete the temp.txt file" |
| `move_file` | Move/rename file | "Rename old.py to new.py" |
| `copy_file` | Copy a file | "Copy config.py to config.backup.py" |

### 3. Search Tools (4 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `search_files` | Search content (grep) | "Find all files containing 'TODO'" |
| `find_files` | Find by name pattern | "Find all .py files in src/" |
| `get_file_structure` | Show directory tree | "Show project structure" |
| `get_file_info` | Get file metadata | "How big is data.csv?" |

### 4. Git Tools (10 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `git_status` | Show repo status | "Check git status" |
| `git_diff` | Show changes | "Show what I changed" |
| `git_log` | Show commit history | "Show last 5 commits" |
| `git_branch` | Manage branches | "List all branches" |
| `git_add` | Stage files | "Stage all Python files" |
| `git_commit` | Create commit | "Commit with message 'fix bug'" |
| `git_push` | Push to remote | "Push to origin" |
| `git_pull` | Pull from remote | "Pull latest changes" |
| `git_stash` | Stash changes | "Stash my current work" |
| `git_clone` | Clone repository | "Clone https://github.com/..." |

### 5. Python Sandbox (6 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `python_exec` | Execute Python code | "Run: print('hello world')" |
| `python_eval` | Evaluate expression | "Calculate 2 ** 100" |
| `python_import` | Import modules | "Import pandas and numpy" |
| `python_repl_vars` | Show variables | "What variables are defined?" |
| `python_run_file` | Run Python file | "Execute test.py" |
| `python_repl_reset` | Reset sandbox | "Clear the Python environment" |

### 6. Workflow System (7 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `create_workflow` | Create workflow | "Create a 'deploy' workflow" |
| `add_workflow_step` | Add step | "Add 'npm build' to deploy workflow" |
| `list_workflows` | List all workflows | "Show all saved workflows" |
| `show_workflow` | View workflow | "Show the deploy workflow" |
| `run_workflow` | Execute workflow | "Run the deploy workflow" |
| `delete_workflow` | Remove workflow | "Delete the test workflow" |
| `save_command_to_workflow` | Quick save | "Save this command to workflow" |

### 7. Planning Mode (8 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `create_plan` | Create task plan | "Plan: Add user authentication" |
| `add_plan_step` | Add step to plan | "Add step: Create user model" |
| `show_plan` | View current plan | "Show the plan" |
| `approve_plan` | Approve for execution | "Approve this plan" |
| `execute_plan` | Run the plan | "Execute the plan" |
| `complete_plan_step` | Mark step done | "Mark step 1 as complete" |
| `list_plans` | List all plans | "Show all plans" |
| `delete_plan` | Remove plan | "Delete current plan" |

### 8. Context Attachments (6 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `attach_file` | Add file to context | "Attach config.py to context" |
| `attach_folder` | Add folder structure | "Attach the src/ folder" |
| `attach_selection` | Add specific lines | "Attach lines 10-50 of main.py" |
| `attach_files_by_pattern` | Add multiple files | "Attach all *.py files" |
| `show_context` | View attached context | "What's in context?" |
| `clear_context` | Remove all context | "Clear context" |

### 9. Specialized Agents (7 tools + 6 agents)
| Tool/Agent | Purpose | Example Prompt |
|------------|---------|----------------|
| `list_agents` | List available agents | "Show available agents" |
| `invoke_agent` | Call specific agent | "Ask reviewer to check my code" |
| `code_review` | Review code | "Review src/utils.py" |
| `debug_help` | Debugging assistance | "Help debug: TypeError in line 45" |
| `suggest_refactoring` | Refactor suggestions | "How can I improve this function?" |
| `generate_tests` | Create tests | "Generate tests for utils.py" |
| `generate_docs` | Create documentation | "Document the API module" |

**Available Agents:**
- `reviewer` - Code review expert
- `debugger` - Debugging specialist
- `refactor` - Refactoring advisor
- `tester` - Test writer
- `docs` - Documentation writer
- `git` - Git operations expert

### 10. Error Analysis (4 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `analyze_error` | Parse and analyze errors | "Analyze: NameError: name 'x' not defined" |
| `run_and_fix` | Run with error analysis | "Run test.py and fix any errors" |
| `diagnose_file` | Check file for issues | "Check main.py for problems" |
| `suggest_fix` | Get fix suggestions | "How do I fix this import error?" |

### 11. Build & Auto-Fix (6 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `detect_project` | Detect project type (Python, Node, Rust, Go, etc.) | "What type of project is this?" |
| `build_project` | Compile/build with error analysis | "Build the project" |
| `test_project` | Run project tests | "Run the tests" |
| `build_and_fix` | Auto-build loop with fix suggestions | "Build and fix any errors" |
| `lint_project` | Run code linters | "Lint the project" |
| `install_dependencies` | Install project dependencies | "Install dependencies" |

**Supported Project Types:**
- Python (pip, pytest, flake8, mypy)
- Node.js (npm, eslint)
- Rust (cargo, clippy)
- Go (go build, go vet)
- Java (maven, gradle)
- C# (.NET, dotnet)
- C++ (make, cmake)

### 12. Agent Rules (5 tools)
| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `create_agent_rules` | Create AGENT.md | "Create coding standards file" |
| `load_agent_rules` | Load rules | "Load the project rules" |
| `show_agent_rules` | Display rules | "Show current rules" |
| `get_rule_section` | Get specific rule | "Show the style guide section" |
| `check_rules_compliance` | Verify compliance | "Does utils.py follow the rules?" |

---

## USE CASES

### Use Case 1: Build a New Project

**Scenario:** Start a new Python web API project

```
You: Create a new FastAPI project structure in D:\projects\my_api

You: Create a main.py with a basic FastAPI app with health endpoint

You: Add a users router with GET and POST endpoints

You: Create a requirements.txt with fastapi and uvicorn

You: Run the server and test it
```

**What Code Agent Does:**
1. Creates folder structure (src/, tests/, etc.)
2. Writes boilerplate code
3. Creates configuration files
4. Executes and tests the code

---

### Use Case 2: ETL Data Pipeline

**Scenario:** Build a data processing pipeline

```
You: Create an ETL project with extract, transform, load modules

You: In extract.py, add a CSVExtractor class that reads CSV files

You: In transform.py, add functions to clean nulls and normalize text

You: In load.py, add methods to save to CSV and JSON

You: Create sample data and test the full pipeline
```

**What Code Agent Does:**
1. Creates modular code structure
2. Writes data processing functions
3. Generates test data
4. Runs and validates the pipeline

---

### Use Case 3: Debug Production Issues

**Scenario:** Fix a bug reported in production

```
You: Search for files containing 'calculate_total' function

You: Read the orders.py file, lines 100-150

You: Analyze this error: TypeError: unsupported operand type '+' for int and str

You: Fix the bug by adding type conversion

You: Run the tests to verify the fix
```

**What Code Agent Does:**
1. Locates the problematic code
2. Analyzes the error
3. Suggests and applies fix
4. Verifies with tests

---

### Use Case 4: Code Review & Refactoring

**Scenario:** Improve code quality

```
You: Review the code in src/utils.py

You: Suggest refactoring for the process_data function

You: Apply the suggested refactoring

You: Generate unit tests for the refactored code

You: Run the tests
```

**What Code Agent Does:**
1. Analyzes code for issues
2. Suggests improvements
3. Applies changes
4. Creates tests
5. Validates everything works

---

### Use Case 5: Git Workflow Automation

**Scenario:** Manage git operations

```
You: Check git status

You: Show me what changed in the last commit

You: Create a new feature branch called 'add-auth'

You: Stage all Python files

You: Commit with message 'Add user authentication module'

You: Push to origin
```

**What Code Agent Does:**
1. Executes git commands
2. Shows status and diffs
3. Manages branches
4. Creates commits
5. Syncs with remote

---

### Use Case 6: Documentation Generation

**Scenario:** Document your codebase

```
You: Attach all Python files in src/ to context

You: Generate documentation for the API module

You: Create a README.md with project overview

You: Add usage examples to the documentation
```

**What Code Agent Does:**
1. Reads all source files
2. Understands the code structure
3. Generates comprehensive docs
4. Creates README with examples

---

### Use Case 7: Testing Automation

**Scenario:** Create and run tests

```
You: Generate unit tests for src/calculator.py

You: Create a test file tests/test_calculator.py

You: Run pytest and show results

You: Fix any failing tests
```

**What Code Agent Does:**
1. Analyzes code to test
2. Generates test cases
3. Creates test files
4. Runs tests and fixes issues

---

### Use Case 8: Build & Auto-Fix

**Scenario:** Build project and automatically fix errors

```
You: What type of project is this?

You: Install the dependencies

You: Build and fix any errors

You: Run the tests

You: Lint the project and fix issues
```

**What Code Agent Does:**
1. Detects project type (Python, Node.js, Rust, Go, Java, etc.)
2. Runs appropriate build commands
3. Analyzes build errors
4. Suggests specific fixes with file/line info
5. Runs linters for code quality

**Example Build & Fix Workflow:**
```
You: Build and fix the project

[Agent detects Python project]
[Runs: python -m py_compile]
[Error: SyntaxError in main.py line 25]
[Agent suggests: "Missing colon at end of if statement"]
[You: Fix it]
[Agent re-builds - SUCCESS]
```

---

### Use Case 9: Workflow Automation (Notebooks)

**Scenario:** Create reusable workflows

```
You: Create a workflow called 'deploy-prod'

You: Add step: Run tests with pytest

You: Add step: Build docker image

You: Add step: Push to registry

You: Add step: Deploy to kubernetes

You: Save and show the workflow
```

**What Code Agent Does:**
1. Creates workflow definition
2. Adds sequential steps
3. Saves for reuse
4. Can execute on demand

---

### Use Case 10: Project Setup from Scratch

**Scenario:** Initialize a complete project

```
You: Create a Django project structure for an e-commerce app

You: Set up the database models for products, orders, users

You: Create REST API endpoints

You: Add authentication with JWT

You: Create admin panel configuration

You: Generate initial migrations

You: Create a docker-compose.yml for development
```

---

### Use Case 11: Learning & Exploration

**Scenario:** Understand unfamiliar codebase

```
You: Show me the project structure

You: Find the main entry point of this application

You: Search for all API endpoints

You: Read the authentication module

You: Explain how the caching system works
```

**What Code Agent Does:**
1. Maps the codebase
2. Finds key components
3. Reads and explains code
4. Helps understand architecture

---

## Best Practices

### 1. Be Specific
```
❌ Bad:  "Fix the bug"
✅ Good: "Fix the TypeError in src/utils.py line 45 where string is added to int"
```

### 2. Work Incrementally
```
❌ Bad:  "Build me a complete e-commerce website"
✅ Good: "Create the user model first, then we'll add products"
```

### 3. Use Context
```
❌ Bad:  "Update the function"
✅ Good: "Attach src/utils.py to context, then update the parse_data function"
```

### 4. Verify Results
```
✅ Good: "Run the tests after making changes"
✅ Good: "Show me the file after editing"
```

### 5. Use Planning for Complex Tasks
```
✅ Good: "Create a plan to add user authentication with these steps..."
```

---

## Troubleshooting

### Ollama Not Responding
```powershell
# Start Ollama
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### Agent Not Finding Files
```
# Use absolute paths
You: Read D:\projects\myapp\src\main.py

# Or set working directory first
You: Change directory to D:\projects\myapp
```

### Slow Responses
- Ollama processes locally - speed depends on your hardware
- Use smaller prompts for faster responses
- Consider using a smaller model in config

### Tool Errors
```
# If a tool fails, ask for details
You: Show me the error details

# Try alternative approach
You: Use a different method to accomplish this
```

---

## Configuration

### Change LLM Model
Edit `src/config.py`:
```python
MODEL_ID = "llama3:8b"  # or other Ollama models
```

### Set Default Workspace
```python
DEFAULT_WORKSPACE = Path("D:/projects")
```

### Adjust Timeouts
```python
LLM_TIMEOUT = 120  # seconds
```

---

## File Locations

```
D:\code-agent\
├── src\
│   ├── agents\         # Agent implementations
│   ├── tools\          # All 68 tools
│   ├── config.py       # Configuration
│   └── main.py         # Entry point
├── scripts\
│   ├── demo_features.py    # Interactive demo
│   ├── demo_auto.py        # Automated demo
│   └── test_e2e.py         # End-to-end tests
├── data\
│   └── workflows\      # Saved workflows
└── RUNBOOK.md          # This file
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| List files | "List files in current directory" |
| Read file | "Read src/main.py" |
| Create file | "Create hello.py with print('hi')" |
| Edit file | "Change 'old' to 'new' in config.py" |
| Search | "Find files containing 'TODO'" |
| Git status | "Check git status" |
| Run Python | "Execute: print(2+2)" |
| Run command | "Run: npm install" |
| Review code | "Review src/utils.py" |
| Debug | "Analyze error: NameError..." |
| Create tests | "Generate tests for calc.py" |
| Plan task | "Create plan to add feature X" |

---

## 20 World-Class CLI Product Features

### Phase 1: Core Features
| Feature | Command | Description |
|---------|---------|-------------|
| Multi-Model Support | `/models` | 19 models from Ollama, OpenAI, Anthropic, Google, Groq |
| Checkpoint System | `/checkpoint` | Save/restore project snapshots |
| Diff Preview Mode | `/diff` | Preview changes before applying |
| Project Auto-Detection | `/init` | Auto-detect language, frameworks, structure |
| Undo/Redo Stack | `/undo`, `/redo` | Full history of file changes |

### Phase 2: Intelligence Features
| Feature | Command | Description |
|---------|---------|-------------|
| Persistent Memory | `/memory`, `/recall` | Remember context across sessions |
| Codebase Indexing | `/index`, `/symbols` | Semantic code search with 2000+ symbols |
| Watch Mode | `/watch` | Real-time file monitoring with auto-fix |
| Code Explanation | `/explain` | Deep code analysis with ASCII flow diagrams |
| Smart Context | `/context`, `/attach` | Intelligent context management |

### Phase 3: Analysis Features
| Feature | Command | Description |
|---------|---------|-------------|
| Dependency Analyzer | `/deps` | Import graph and circular dependency detection |
| Code Metrics | `/metrics` | Complexity, coverage, technical debt |
| Git Integration | `/git` | Enhanced git with smart commit messages |
| Test Runner | `/test`, `/coverage` | Multi-framework test support (pytest, jest, go test) |
| Doc Generator | `/docs`, `/readme` | Auto-generate docstrings and README |

### Phase 4: Productivity Features
| Feature | Command | Description |
|---------|---------|-------------|
| Code Templates | `/templates` | Scaffolding for Python, TypeScript, Go |
| Session Manager | `/session` | Save/resume sessions with full context |
| Shell Integration | Run commands | Smart command suggestions and error fixes |
| Interactive TUI | `/tui`, `/dashboard` | Rich terminal UI with split panels |
| Plugin System | `/plugins` | Extensible with custom tools and commands |
| Profiles & Presets | `/profiles`, `/preset` | 8 built-in presets (fast, creative, debug, etc.) |

### Quick Start with Features

```bash
# Start with project analysis
/init                          # Auto-detect project
/index                         # Index codebase
/dashboard                     # Show project overview

# Use smart context
/attach src/main.py           # Add files to context
/explain src/utils.py         # Deep code explanation

# Enable safety features
/checkpoint before-refactor    # Save state
/diff on                       # Preview mode

# Run and test
/test                          # Run tests
/coverage                      # With coverage

# Git workflow
/git                           # Status report
/git log                       # Recent commits
```

---

## Support

- **Issues:** Check error messages and try alternative approaches
- **Logs:** Check `logs/` folder for detailed logs
- **Reset:** Restart the agent if stuck

---

*Code Agent - Your AI-Powered Development Assistant*
*74 Tools • 20 Product Features • 12 Categories • Unlimited Possibilities*
