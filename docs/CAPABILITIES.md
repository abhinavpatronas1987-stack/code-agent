# Code Agent - Capabilities & Features

## Overview

Code Agent is an AI-powered coding assistant with **15 tools** across 3 categories that can help you with software development tasks through natural language.

---

## 1. Tool Categories

### Summary Table

| Category | Tools | Description |
|----------|-------|-------------|
| Terminal | 4 | Execute shell commands, navigate filesystem |
| File Operations | 7 | Read, write, edit, manage files |
| Code Search | 4 | Search files, find patterns, analyze structure |

---

## 2. Terminal Tools (4)

### 2.1 run_terminal_command

**Purpose:** Execute any shell command

**Capabilities:**
- Run any terminal command (git, npm, pip, cargo, etc.)
- Capture stdout and stderr
- Return exit codes
- Timeout protection

**Examples:**
```
User: "Run git status"
User: "Install numpy with pip"
User: "List all running processes"
User: "Build the project with npm run build"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| command | string | The command to execute |
| working_dir | string | Optional directory to run in |
| timeout | int | Optional timeout in seconds |

---

### 2.2 change_directory

**Purpose:** Navigate the filesystem

**Capabilities:**
- Change working directory
- Support relative paths (./src, ..)
- Support absolute paths
- Expand ~ to home directory

**Examples:**
```
User: "Go to the src folder"
User: "Navigate to D:\projects\myapp"
User: "Go back to parent directory"
```

---

### 2.3 get_current_directory

**Purpose:** Show current location

**Examples:**
```
User: "Where am I?"
User: "What's the current directory?"
```

---

### 2.4 list_directory

**Purpose:** List directory contents

**Capabilities:**
- List files and folders
- Show file sizes
- Sort directories first
- Filter hidden files

**Examples:**
```
User: "What files are here?"
User: "Show me everything including hidden files"
User: "List the contents of ./src"
```

---

## 3. File Operation Tools (7)

### 3.1 read_file

**Purpose:** Read file contents

**Capabilities:**
- Read any text file
- Show line numbers
- Read specific line ranges
- Handle multiple encodings

**Examples:**
```
User: "Show me the main.py file"
User: "Read lines 50-100 of config.json"
User: "What's in the README?"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| file_path | string | Path to file |
| start_line | int | Optional start line |
| end_line | int | Optional end line |

---

### 3.2 write_file

**Purpose:** Write/overwrite file contents

**Capabilities:**
- Create new files
- Overwrite existing files
- Create parent directories automatically

**Examples:**
```
User: "Create a new file called utils.py with a helper function"
User: "Write 'Hello World' to output.txt"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| file_path | string | Path to file |
| content | string | Content to write |
| create_dirs | bool | Create parent dirs if needed |

---

### 3.3 edit_file

**Purpose:** Make surgical edits to files

**Capabilities:**
- Find and replace specific content
- Show diff of changes
- Replace single or all occurrences
- Preserve file structure

**Examples:**
```
User: "Change the function name from 'old_func' to 'new_func'"
User: "Replace 'localhost' with '0.0.0.0' in the config"
User: "Fix the typo 'teh' to 'the'"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| file_path | string | Path to file |
| old_content | string | Text to find |
| new_content | string | Replacement text |
| occurrence | int | Which occurrence (-1 for all) |

---

### 3.4 create_file

**Purpose:** Create new files

**Capabilities:**
- Create empty or pre-filled files
- Optionally overwrite existing
- Create parent directories

**Examples:**
```
User: "Create a new Python file called test.py"
User: "Make a config.json with default settings"
```

---

### 3.5 delete_file

**Purpose:** Delete files

**Capabilities:**
- Remove files
- Validation before deletion

**Examples:**
```
User: "Delete the temp.txt file"
User: "Remove old_backup.py"
```

---

### 3.6 move_file

**Purpose:** Move or rename files

**Capabilities:**
- Rename files
- Move to different directory
- Create destination directories

**Examples:**
```
User: "Rename main.py to app.py"
User: "Move config.json to the settings folder"
```

---

### 3.7 copy_file

**Purpose:** Copy files

**Capabilities:**
- Duplicate files
- Copy to different locations
- Preserve file attributes

**Examples:**
```
User: "Make a backup of database.db"
User: "Copy template.py to new_module.py"
```

---

## 4. Code Search Tools (4)

### 4.1 search_files

**Purpose:** Search file contents (like grep)

**Capabilities:**
- Regex pattern matching
- Filter by file type
- Search recursively
- Case insensitive option

**Examples:**
```
User: "Find all TODO comments in the code"
User: "Search for 'import os' in Python files"
User: "Find where the 'authenticate' function is defined"
User: "Look for any API keys in the codebase"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| pattern | string | Regex pattern to search |
| directory | string | Where to search |
| file_pattern | string | File glob (*.py, *.js) |
| max_results | int | Limit results |

---

### 4.2 find_files

**Purpose:** Find files by name pattern

**Capabilities:**
- Glob pattern matching
- Recursive search
- Ignore common directories (node_modules, .git)

**Examples:**
```
User: "Find all Python files"
User: "Where are the test files?"
User: "Find all markdown files"
User: "List all config files"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| pattern | string | Glob pattern (*.py, test_*) |
| directory | string | Where to search |
| max_results | int | Limit results |

---

### 4.3 get_file_structure

**Purpose:** Show directory tree

**Capabilities:**
- Visual tree representation
- Configurable depth
- Show/hide files
- Ignore common directories

**Examples:**
```
User: "Show me the project structure"
User: "What's the folder layout?"
User: "Display the directory tree"
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| directory | string | Root directory |
| max_depth | int | How deep to traverse |
| show_files | bool | Include files or just dirs |

---

### 4.4 get_file_info

**Purpose:** Get file metadata

**Capabilities:**
- File size
- File type detection
- Line count
- Modification time

**Examples:**
```
User: "How big is the database file?"
User: "When was main.py last modified?"
User: "How many lines in utils.py?"
```

---

## 5. Natural Language Capabilities

The agent can understand various ways of asking for the same thing:

### File Reading
```
✓ "Show me the file main.py"
✓ "Read main.py"
✓ "What's in main.py?"
✓ "Display the contents of main.py"
✓ "Open main.py"
✓ "Cat main.py"
```

### File Writing
```
✓ "Create a file called test.py"
✓ "Make a new file test.py with hello world"
✓ "Write a Python script that prints hello"
✓ "Generate a config file"
```

### Searching
```
✓ "Find all Python files"
✓ "Search for TODO comments"
✓ "Where is the database connection defined?"
✓ "Look for authentication code"
✓ "Find files containing 'password'"
```

### Terminal Commands
```
✓ "Run git status"
✓ "Execute npm install"
✓ "Check git log"
✓ "Build the project"
✓ "Run the tests"
```

---

## 6. Complex Task Examples

### Example 1: Code Review Assistance
```
User: "Find all functions that don't have docstrings"
Agent: Uses search_files to find 'def ' patterns, analyzes results
```

### Example 2: Project Setup
```
User: "Create a basic Flask app structure"
Agent:
1. Creates app.py with Flask boilerplate
2. Creates requirements.txt
3. Creates templates/ directory
4. Creates static/ directory
```

### Example 3: Bug Investigation
```
User: "Find where the error 'connection refused' might come from"
Agent:
1. Searches for 'connection' in code
2. Searches for error handling patterns
3. Lists relevant files
```

### Example 4: Refactoring
```
User: "Rename the function 'getData' to 'fetch_data' everywhere"
Agent:
1. Finds all occurrences of 'getData'
2. Shows files that will be modified
3. Applies changes with edit_file
```

### Example 5: Documentation
```
User: "Show me the project structure and explain each folder"
Agent:
1. Uses get_file_structure
2. Reads key files
3. Provides explanation
```

---

## 7. Safety Features

### What the Agent Will NOT Do (without confirmation):
- Delete important files
- Overwrite without warning
- Execute destructive shell commands
- Access files outside workspace
- Run commands indefinitely

### Built-in Protections:
- Command timeouts (default 120s)
- Working directory scope
- Path validation
- Error handling on all operations

---

## 8. Limitations

### Current Limitations:
| Limitation | Workaround |
|------------|------------|
| No interactive commands | Use non-interactive alternatives |
| No GUI applications | Use CLI tools only |
| Large file handling | Use line ranges for big files |
| Binary files | Cannot read binary content |
| Network operations | Use curl/wget via terminal |

### Model-Dependent:
- Quality depends on Ollama model used
- Complex reasoning requires larger models
- Code generation quality varies by model

---

## 9. Best Practices

### For Best Results:
1. **Be specific** - "Read lines 1-50 of main.py" vs "show me main.py"
2. **One task at a time** - Break complex requests into steps
3. **Provide context** - "In the src folder, find all test files"
4. **Use the right tool** - Let the agent choose or specify

### Example Good Prompts:
```
✓ "Create a Python function that validates email addresses and save it to utils.py"
✓ "Search for all files that import 'requests' library"
✓ "Show me the project structure, then read the main entry point"
✓ "Find TODO comments and list them with file names"
```

### Example Less Effective Prompts:
```
✗ "Fix my code" (too vague)
✗ "Make it better" (needs specifics)
✗ "Do everything" (too broad)
```
