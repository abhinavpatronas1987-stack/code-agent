# Code Agent - Architecture Document

## 1. Executive Summary

Code Agent is an **Agentic Development Environment (ADE)** - an AI-powered terminal platform that enables developers to interact with their codebase using natural language. Built with the Agno framework and local LLMs (Ollama), it provides a privacy-first, enterprise-ready coding assistant.

### Key Features
- Natural language command execution
- File operations (read, write, edit, search)
- Terminal command execution
- Code analysis and search
- Session persistence and memory
- REST API and WebSocket support

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   CLI Client    │  │   Web Client    │  │  API Consumer   │              │
│  │   (cli.py)      │  │   (Future)      │  │  (REST/WS)      │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                          API LAYER                                           │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                    ┌────────────┴────────────┐                              │
│                    │     FastAPI Server      │                              │
│                    │     (server.py)         │                              │
│                    ├─────────────────────────┤                              │
│                    │  • REST Endpoints       │                              │
│                    │  • WebSocket Handler    │                              │
│                    │  • Session Management   │                              │
│                    └────────────┬────────────┘                              │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                         AGENT LAYER                                          │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                    ┌────────────┴────────────┐                              │
│                    │     Coding Agent        │                              │
│                    │   (coding_agent.py)     │                              │
│                    ├─────────────────────────┤                              │
│                    │  • Agno Agent Core      │                              │
│                    │  • Tool Orchestration   │                              │
│                    │  • Response Generation  │                              │
│                    └────────────┬────────────┘                              │
│                                 │                                           │
│         ┌───────────────────────┼───────────────────────┐                   │
│         │                       │                       │                   │
│  ┌──────┴──────┐    ┌───────────┴───────────┐    ┌──────┴──────┐           │
│  │  Terminal   │    │      File Ops         │    │   Search    │           │
│  │   Tools     │    │       Tools           │    │   Tools     │           │
│  │  (4 tools)  │    │      (7 tools)        │    │  (4 tools)  │           │
│  └─────────────┘    └───────────────────────┘    └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                          LLM LAYER                                           │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                    ┌────────────┴────────────┐                              │
│                    │    Ollama (Local LLM)   │                              │
│                    │       (llm.py)          │                              │
│                    ├─────────────────────────┤                              │
│                    │  • Model: gpt-oss:20b   │                              │
│                    │  • Context: 32K tokens  │                              │
│                    │  • Local execution      │                              │
│                    └─────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                        DATA LAYER                                            │
├─────────────────────────────────┼───────────────────────────────────────────┤
│    ┌────────────────┐    ┌──────┴───────┐    ┌────────────────┐             │
│    │   SQLite DB    │    │  File System │    │  Working Dir   │             │
│    │  (Sessions)    │    │   (Code)     │    │   (Context)    │             │
│    └────────────────┘    └──────────────┘    └────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

```
src/
├── __init__.py                 # Package initialization
├── cli.py                      # Interactive CLI interface
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Pydantic settings management
│
├── core/
│   ├── __init__.py
│   ├── llm.py                  # Ollama LLM integration
│   └── base_agent.py           # Base agent class
│
├── agents/
│   ├── __init__.py
│   └── coding_agent.py         # Main coding agent
│
├── tools/
│   ├── __init__.py
│   ├── terminal.py             # Terminal execution tools
│   ├── file_ops.py             # File operation tools
│   └── code_search.py          # Code search tools
│
├── api/
│   ├── __init__.py
│   └── server.py               # FastAPI server
│
├── memory/
│   ├── __init__.py
│   └── session.py              # Session management
│
└── workflows/
    ├── __init__.py
    └── task_manager.py         # Task tracking
```

---

## 3. Component Details

### 3.1 Agent Layer (Agno Framework)

The core of Code Agent is built on the **Agno** framework, which provides:

```python
# Agent Configuration
Agent(
    name="CodeAgent",
    model=Ollama(...),           # Local LLM
    instructions=INSTRUCTIONS,    # System prompt
    tools=[...],                  # 15 available tools
    db=SqliteDb(...),            # Persistence
    session_id="...",            # Session tracking
    markdown=True,               # Markdown responses
)
```

**Key Capabilities:**
- Tool calling and orchestration
- Conversation memory
- Session persistence
- Streaming responses

### 3.2 Tool System

Tools are Python functions decorated with `@tool` that the agent can call:

```
┌─────────────────────────────────────────────────────────────────┐
│                        TOOL REGISTRY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TERMINAL TOOLS (4)          FILE TOOLS (7)                     │
│  ├─ run_terminal_command     ├─ read_file                       │
│  ├─ change_directory         ├─ write_file                      │
│  ├─ get_current_directory    ├─ edit_file                       │
│  └─ list_directory           ├─ create_file                     │
│                              ├─ delete_file                     │
│  SEARCH TOOLS (4)            ├─ move_file                       │
│  ├─ search_files             └─ copy_file                       │
│  ├─ find_files                                                  │
│  ├─ get_file_structure                                          │
│  └─ get_file_info                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 LLM Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                     OLLAMA INTEGRATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Configuration:                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Model:        gpt-oss:20b (or any Ollama model)        │    │
│  │  Host:         http://localhost:11434                    │    │
│  │  Context:      32,768 tokens                             │    │
│  │  Max Output:   4,096 tokens                              │    │
│  │  Temperature:  0.1 (deterministic)                       │    │
│  │  Timeout:      300 seconds                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Supported Models:                                               │
│  • qwen2.5-coder:7b     (recommended for coding)                │
│  • llama3.1:8b          (general purpose)                       │
│  • codellama:13b        (code specialized)                      │
│  • deepseek-coder:6.7b  (coding focused)                        │
│  • Any Ollama-compatible model                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 API Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REST Endpoints:                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  GET  /              → Server info                       │    │
│  │  GET  /health        → Health check                      │    │
│  │  POST /chat          → Send message (non-streaming)      │    │
│  │  POST /sessions      → Create new session                │    │
│  │  GET  /sessions/{id} → Get session info                  │    │
│  │  DELETE /sessions/{id} → Delete session                  │    │
│  │  GET  /sessions/{id}/history → Get chat history          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  WebSocket:                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  WS /ws/{session_id}  → Real-time streaming chat         │    │
│  │                                                          │    │
│  │  Protocol:                                               │    │
│  │  → Client: {"type": "message", "content": "..."}         │    │
│  │  ← Server: {"type": "chunk", "content": "..."}           │    │
│  │  ← Server: {"type": "tool_call", "name": "...", ...}     │    │
│  │  ← Server: {"type": "done"}                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 Request Processing Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │   CLI/   │     │  Coding  │     │  Ollama  │
│  Input   │────▶│   API    │────▶│  Agent   │────▶│   LLM    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                        │               │
                                        │               │
                                        ▼               │
                                  ┌──────────┐          │
                                  │  Tools   │          │
                                  │ Executed │          │
                                  └────┬─────┘          │
                                       │                │
                                       ▼                │
                                  ┌──────────┐          │
                                  │  Tool    │          │
                                  │ Results  │──────────┘
                                  └────┬─────┘
                                       │
                                       ▼
                                  ┌──────────┐
                                  │ Response │
                                  │ to User  │
                                  └──────────┘
```

### 4.2 Tool Execution Flow

```
User: "Create a file called test.py with hello world"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. AGENT RECEIVES MESSAGE                                        │
│    • Parses user intent                                          │
│    • Identifies required action: file creation                   │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. LLM DECIDES TOOL CALL                                         │
│    • Tool: create_file                                           │
│    • Args: {file_path: "test.py", content: "print('Hello')"}    │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. TOOL EXECUTION                                                │
│    • create_file.entrypoint() called                            │
│    • File written to filesystem                                  │
│    • Result: "Successfully created file: test.py"               │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. RESPONSE GENERATION                                           │
│    • LLM receives tool result                                    │
│    • Generates human-readable response                           │
│    • "I've created test.py with a hello world program"          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Session Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Session Creation                                             │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • Generate session_id (UUID)                        │     │
│     │  • Initialize SQLite database                        │     │
│     │  • Set working directory                             │     │
│     │  • Create agent instance                             │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  2. Message Processing                                           │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • Receive user message                              │     │
│     │  • Load conversation history                         │     │
│     │  • Execute agent.run()                               │     │
│     │  • Store message + response                          │     │
│     └─────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  3. Session Persistence                                          │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • SQLite: data/agent_storage.db                     │     │
│     │  • Tables: sessions, messages, tool_calls            │     │
│     │  • Auto-save on each interaction                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. LOCAL LLM (Privacy First)                                    │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • All AI processing on local machine               │     │
│     │  • No data sent to external servers                 │     │
│     │  • Code never leaves your environment               │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
│  2. File System Isolation                                        │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • Working directory scoped operations              │     │
│     │  • Path validation before file ops                  │     │
│     │  • No access outside workspace by default           │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
│  3. Command Execution Safety                                     │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • Timeout limits on all commands                   │     │
│     │  • Destructive command warnings in prompts          │     │
│     │  • Subprocess isolation                             │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
│  4. API Security (Production)                                    │
│     ┌─────────────────────────────────────────────────────┐     │
│     │  • CORS configuration                               │     │
│     │  • Session-based access                             │     │
│     │  • Rate limiting (configurable)                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Scalability Considerations

### Current (Single Instance)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│  Code Agent │────▶│   Ollama    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Future (Multi-Instance)
```
                    ┌─────────────┐
                    │   Load      │
                    │  Balancer   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Agent 1   │  │  Agent 2   │  │  Agent 3   │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                    ┌─────┴─────┐
                    │  Shared   │
                    │  Ollama   │
                    │  Cluster  │
                    └───────────┘
```

---

## 7. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Agent Framework | Agno 2.3.x | Agent orchestration, tool calling |
| LLM Runtime | Ollama | Local model inference |
| API Server | FastAPI | REST API, WebSocket |
| Database | SQLite | Session persistence |
| CLI | Rich | Terminal UI |
| Language | Python 3.11+ | Core runtime |

---

## 8. File Locations

| File | Purpose |
|------|---------|
| `data/agent_storage.db` | SQLite database for sessions |
| `.env` | Environment configuration |
| `src/config/settings.py` | Application settings |
| `src/agents/coding_agent.py` | Main agent logic |
| `src/tools/*.py` | Tool implementations |

---

## 9. Extension Points

### Adding New Tools
```python
# src/tools/my_tool.py
from agno.tools.decorator import tool

@tool
def my_custom_tool(param: str) -> str:
    """Tool description for the LLM."""
    # Implementation
    return result

# Add to TOOLS list and import in coding_agent.py
```

### Adding New Models
```python
# .env
OLLAMA_MODEL=your-model-name:tag

# Or programmatically
agent = CodingAgent(model_id="different-model")
```

### Custom Instructions
```python
# Modify CODING_AGENT_INSTRUCTIONS in coding_agent.py
CODING_AGENT_INSTRUCTIONS = """
Your custom system prompt...
"""
```
