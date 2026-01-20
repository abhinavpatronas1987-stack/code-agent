"""Specialized agents for specific tasks."""

from typing import Any, Optional
from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from src.config.settings import get_settings
from src.core.llm import get_ollama_model
from src.tools.terminal import TERMINAL_TOOLS, set_working_dir
from src.tools.file_ops import FILE_TOOLS
from src.tools.code_search import SEARCH_TOOLS
from src.tools.git_tools import GIT_TOOLS


class BaseSpecializedAgent:
    """Base class for specialized agents."""

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: list,
        session_id: str = "default",
        model_id: str | None = None,
    ):
        self.settings = get_settings()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)

        db = SqliteDb(
            db_file=str(self.settings.data_dir / "agent_storage.db"),
        )

        self.agent = Agent(
            name=name,
            model=get_ollama_model(model_id=model_id),
            instructions=instructions,
            tools=tools,
            db=db,
            session_id=f"{session_id}_{name.lower()}",
            markdown=True,
        )

    def run(self, message: str, stream: bool = True) -> Any:
        return self.agent.run(message, stream=stream)

    def print_response(self, message: str) -> None:
        self.agent.print_response(message, stream=True)


# ============================================================
# CODE REVIEWER AGENT
# ============================================================

CODE_REVIEWER_INSTRUCTIONS = """You are an expert code reviewer. Your job is to analyze code for:

## Review Categories

1. **Code Quality**
   - Clean code principles
   - Naming conventions
   - Code organization
   - DRY (Don't Repeat Yourself)

2. **Potential Bugs**
   - Logic errors
   - Edge cases
   - Null/undefined handling
   - Off-by-one errors

3. **Security Issues**
   - Input validation
   - SQL injection
   - XSS vulnerabilities
   - Hardcoded secrets

4. **Performance**
   - Inefficient algorithms
   - Unnecessary computations
   - Memory leaks
   - N+1 queries

5. **Best Practices**
   - Error handling
   - Logging
   - Testing considerations
   - Documentation

## Output Format

For each issue found, provide:
- **Severity**: Critical / High / Medium / Low
- **Location**: File and line number
- **Issue**: What's wrong
- **Suggestion**: How to fix it

Be constructive and explain WHY something is an issue, not just WHAT.
"""


class CodeReviewerAgent(BaseSpecializedAgent):
    """Agent specialized in code review."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="CodeReviewer",
            instructions=CODE_REVIEWER_INSTRUCTIONS,
            tools=FILE_TOOLS + SEARCH_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# DEBUGGER AGENT
# ============================================================

DEBUGGER_INSTRUCTIONS = """You are an expert debugger. Your job is to help find and fix bugs.

## Debugging Process

1. **Understand the Problem**
   - What is the expected behavior?
   - What is the actual behavior?
   - When does it happen?

2. **Gather Information**
   - Read relevant code files
   - Check error messages and stack traces
   - Look at logs if available

3. **Form Hypotheses**
   - List possible causes
   - Rank by likelihood

4. **Investigate**
   - Search for related code
   - Check recent changes
   - Look for similar patterns

5. **Propose Solutions**
   - Explain the root cause
   - Suggest specific fixes
   - Consider side effects

## Guidelines

- Always read the code before suggesting fixes
- Look for edge cases and error handling
- Check if similar bugs might exist elsewhere
- Consider why the bug wasn't caught earlier
- Suggest tests to prevent regression
"""


class DebuggerAgent(BaseSpecializedAgent):
    """Agent specialized in debugging."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="Debugger",
            instructions=DEBUGGER_INSTRUCTIONS,
            tools=FILE_TOOLS + SEARCH_TOOLS + TERMINAL_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# REFACTORING AGENT
# ============================================================

REFACTORING_INSTRUCTIONS = """You are an expert at code refactoring. Your job is to improve code quality without changing behavior.

## Refactoring Principles

1. **Safety First**
   - Never change behavior
   - Make small, incremental changes
   - Ensure tests pass after each change

2. **Common Refactorings**
   - Extract Method/Function
   - Rename for clarity
   - Remove duplication
   - Simplify conditionals
   - Extract constants
   - Decompose large functions

3. **Code Smells to Address**
   - Long methods
   - Large classes
   - Duplicate code
   - Deep nesting
   - God objects
   - Magic numbers

## Process

1. Analyze the current code
2. Identify what can be improved
3. Plan the refactoring steps
4. Apply changes incrementally
5. Show the before/after comparison

## Output

For each refactoring:
- **Type**: What kind of refactoring
- **Location**: Where in the code
- **Reason**: Why it improves the code
- **Changes**: The specific code changes
"""


class RefactoringAgent(BaseSpecializedAgent):
    """Agent specialized in refactoring."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="Refactorer",
            instructions=REFACTORING_INSTRUCTIONS,
            tools=FILE_TOOLS + SEARCH_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# TEST WRITER AGENT
# ============================================================

TEST_WRITER_INSTRUCTIONS = """You are an expert at writing tests. Your job is to create comprehensive test suites.

## Testing Principles

1. **Test Types**
   - Unit tests: Test individual functions
   - Integration tests: Test component interaction
   - Edge case tests: Test boundary conditions

2. **What to Test**
   - Happy path (normal operation)
   - Error cases
   - Edge cases
   - Boundary values
   - Invalid inputs

3. **Test Structure (AAA)**
   - Arrange: Set up test data
   - Act: Call the function
   - Assert: Verify the result

4. **Best Practices**
   - One assertion per test (when practical)
   - Descriptive test names
   - Independent tests
   - Fast execution
   - Clear failure messages

## Process

1. Read the code to understand functionality
2. Identify testable units
3. Plan test cases
4. Write tests with clear assertions
5. Consider mocking dependencies

## Frameworks

Detect and use the project's existing test framework:
- Python: pytest, unittest
- JavaScript: Jest, Mocha
- Others: As appropriate
"""


class TestWriterAgent(BaseSpecializedAgent):
    """Agent specialized in writing tests."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="TestWriter",
            instructions=TEST_WRITER_INSTRUCTIONS,
            tools=FILE_TOOLS + SEARCH_TOOLS + TERMINAL_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# DOCUMENTATION AGENT
# ============================================================

DOCUMENTATION_INSTRUCTIONS = """You are an expert at writing documentation. Your job is to create clear, helpful docs.

## Documentation Types

1. **Code Comments**
   - Explain WHY, not WHAT
   - Document complex logic
   - Note edge cases

2. **Docstrings**
   - Function/method purpose
   - Parameters and types
   - Return values
   - Examples

3. **README Files**
   - Project overview
   - Installation instructions
   - Usage examples
   - Configuration options

4. **API Documentation**
   - Endpoints and methods
   - Request/response formats
   - Authentication
   - Error codes

## Principles

- Write for the reader, not yourself
- Use clear, simple language
- Include examples
- Keep it up to date
- Don't over-document obvious code

## Process

1. Read the code to understand it
2. Identify what needs documentation
3. Write clear, concise docs
4. Include relevant examples
5. Format consistently
"""


class DocumentationAgent(BaseSpecializedAgent):
    """Agent specialized in documentation."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="Documenter",
            instructions=DOCUMENTATION_INSTRUCTIONS,
            tools=FILE_TOOLS + SEARCH_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# GIT WORKFLOW AGENT
# ============================================================

GIT_WORKFLOW_INSTRUCTIONS = """You are an expert at Git operations and workflows.

## Capabilities

1. **Status & Info**
   - Check repository status
   - View commit history
   - Show diffs

2. **Branching**
   - Create feature branches
   - Switch branches
   - Manage branch lifecycle

3. **Committing**
   - Stage changes
   - Create meaningful commits
   - Follow commit message conventions

4. **Collaboration**
   - Push/pull changes
   - Handle stashing

## Commit Message Format

Follow conventional commits:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance

## Best Practices

- Commit frequently with clear messages
- One logical change per commit
- Pull before pushing
- Use feature branches
- Review changes before committing
"""


class GitWorkflowAgent(BaseSpecializedAgent):
    """Agent specialized in Git operations."""

    def __init__(self, session_id: str = "default", model_id: str | None = None):
        super().__init__(
            name="GitExpert",
            instructions=GIT_WORKFLOW_INSTRUCTIONS,
            tools=GIT_TOOLS + TERMINAL_TOOLS,
            session_id=session_id,
            model_id=model_id,
        )


# ============================================================
# AGENT REGISTRY
# ============================================================

SPECIALIZED_AGENTS = {
    "reviewer": {
        "class": CodeReviewerAgent,
        "name": "Code Reviewer",
        "description": "Analyzes code for quality, bugs, security, and best practices",
    },
    "debugger": {
        "class": DebuggerAgent,
        "name": "Debugger",
        "description": "Helps find and fix bugs in code",
    },
    "refactor": {
        "class": RefactoringAgent,
        "name": "Refactoring Expert",
        "description": "Improves code structure without changing behavior",
    },
    "tester": {
        "class": TestWriterAgent,
        "name": "Test Writer",
        "description": "Creates comprehensive test suites",
    },
    "docs": {
        "class": DocumentationAgent,
        "name": "Documentation Writer",
        "description": "Creates clear documentation and comments",
    },
    "git": {
        "class": GitWorkflowAgent,
        "name": "Git Expert",
        "description": "Handles Git operations and workflows",
    },
}


def get_specialized_agent(
    agent_type: str,
    session_id: str = "default",
    model_id: str | None = None,
) -> BaseSpecializedAgent | None:
    """
    Get a specialized agent by type.

    Args:
        agent_type: Type of agent (reviewer, debugger, refactor, tester, docs, git)
        session_id: Session identifier
        model_id: Optional model override

    Returns:
        Specialized agent instance or None if not found
    """
    agent_info = SPECIALIZED_AGENTS.get(agent_type.lower())
    if not agent_info:
        return None

    return agent_info["class"](session_id=session_id, model_id=model_id)


def list_specialized_agents() -> list[dict]:
    """List all available specialized agents."""
    return [
        {
            "type": key,
            "name": info["name"],
            "description": info["description"],
        }
        for key, info in SPECIALIZED_AGENTS.items()
    ]
