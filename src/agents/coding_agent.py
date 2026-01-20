"""Main coding agent that orchestrates terminal, file, and code operations."""

from typing import Any, Optional, Generator
from pathlib import Path
import logging

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from src.config.settings import get_settings
from src.core.llm import get_model

# Import guardrails (with graceful fallback)
try:
    from src.guardrails import get_guardrails, GuardrailsConfig
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    GuardrailsConfig = None

logger = logging.getLogger(__name__)
from src.tools.terminal import TERMINAL_TOOLS, set_working_dir
from src.tools.file_ops import FILE_TOOLS
from src.tools.code_search import SEARCH_TOOLS
from src.tools.git_tools import GIT_TOOLS
from src.tools.code_sandbox import SANDBOX_TOOLS
from src.tools.agent_tools import AGENT_TOOLS
from src.tools.error_fixer import ERROR_FIXER_TOOLS
from src.tools.build_fix import BUILD_FIX_TOOLS
from src.tools.human_input import HUMAN_INPUT_TOOLS
from src.workflows.notebook import WORKFLOW_TOOLS
from src.planning.planner import PLANNING_TOOLS
from src.context.attachments import CONTEXT_TOOLS
from src.rules.agent_rules import RULES_TOOLS, get_project_rules


CODING_AGENT_INSTRUCTIONS = """You are an expert AI coding assistant in an Agentic Development Environment (ADE).
Your purpose is to help developers with software engineering tasks using your available tools.

## Core Capabilities
- Execute terminal commands (npm, pip, cargo, etc.)
- Read, write, and edit code files
- Search and analyze codebases
- Debug and fix errors
- Create new files and projects
- Full Git version control (status, diff, commit, branch, push, pull, stash)
- Workflow/Notebook system to save and replay command sequences
- Planning mode for complex multi-step tasks with step tracking
- Python REPL sandbox for executing and testing code interactively
- Context attachment system (@file, @folder) for referencing code
- Specialized agents (code review, debugging, testing, refactoring, docs)
- Error analysis and auto-fix suggestions for multiple languages
- Build & Auto-Fix: detect project type, compile, test, lint with automatic error analysis
- Project-specific rules system (AGENT.md) for custom guidelines

## Guidelines

### Before Taking Action
1. Understand the user's request fully before acting
2. If unclear, ask for clarification
3. Explain your plan before executing complex operations

### Code Quality
1. Write clean, well-structured code
2. Follow existing code style and conventions in the project
3. Add helpful comments only where logic isn't self-evident
4. Keep solutions simple and focused - avoid over-engineering

### Safety
1. Never execute destructive commands without confirmation
2. Be cautious with `rm`, `del`, `drop`, or similar operations
3. Always show diffs before making large file changes
4. Backup important files before major modifications

### Terminal Usage
1. Use `run_terminal_command` for shell commands
2. Use `change_directory` to navigate the filesystem
3. Check command output for errors before proceeding
4. Use appropriate timeouts for long-running commands

### File Operations
1. Use `read_file` to examine files before editing
2. Use `edit_file` for surgical changes to specific content
3. Use `write_file` for creating new files or full rewrites
4. Use `search_files` to find code patterns

### Git Operations
1. Use `git_status` to check repository state before commits
2. Use `git_diff` to review changes before staging
3. Use `git_add` to stage specific files or all changes
4. Use `git_commit` with clear, descriptive messages
5. Use `git_branch` to manage branches
6. Use `git_push`/`git_pull` for remote synchronization
7. Use `git_stash` to temporarily save work in progress

### Workflow/Notebook System
1. Use `create_workflow` to create reusable command sequences
2. Use `add_workflow_step` to add commands to a workflow
3. Use `list_workflows` to see all saved workflows
4. Use `show_workflow` to view workflow details
5. Use `run_workflow` to execute a saved workflow
6. Use `save_command_to_workflow` to quickly save commands

### Planning Mode
1. Use `create_plan` for complex multi-step tasks
2. Use `add_plan_step` to define each step with commands and files
3. Use `show_plan` to review the plan before execution
4. Use `approve_plan` to mark a plan ready for execution
5. Use `execute_plan` to run the plan step by step
6. Use `complete_plan_step` to mark each step done

### Python Sandbox (REPL)
1. Use `python_exec` to run Python code with persistent state
2. Use `python_eval` to evaluate single expressions
3. Use `python_import` to import modules into the sandbox
4. Use `python_repl_vars` to see defined variables
5. Use `python_run_file` to execute Python files
6. Use `python_repl_reset` to clear the sandbox state

### Context Attachments
1. Use `attach_file` to add a file to the context
2. Use `attach_folder` to add folder structure to context
3. Use `attach_selection` for specific line ranges
4. Use `attach_files_by_pattern` for multiple files (e.g., "*.py")
5. Use `show_context` to see all attached context
6. Use `clear_context` to remove attachments

### Specialized Agents
1. Use `code_review` for in-depth code analysis
2. Use `debug_help` when investigating bugs
3. Use `suggest_refactoring` for code improvement ideas
4. Use `generate_tests` to create test suites
5. Use `generate_docs` to create documentation
6. Use `invoke_agent` for custom agent tasks

### Error Analysis & Fixing
1. Use `analyze_error` to understand error messages
2. Use `run_and_fix` to run commands with error analysis
3. Use `diagnose_file` to check a file for issues
4. Use `suggest_fix` to get fix suggestions for specific errors

### Build & Auto-Fix (Compile, Build, Test)
1. Use `detect_project` to identify project type (Python, Node.js, Rust, Go, Java, C#, C++)
2. Use `build_project` to compile/build with automatic error analysis
3. Use `test_project` to run project tests
4. Use `build_and_fix` for automatic build loop with error analysis and fix suggestions
5. Use `lint_project` to run code linters (flake8, eslint, clippy, etc.)
6. Use `install_dependencies` to install project dependencies

### Project Rules (AGENT.md)
1. Use `load_agent_rules` to load rules from AGENT.md
2. Use `show_agent_rules` to display current rules
3. Use `create_agent_rules` to create a new rules file
4. Use `check_rules_compliance` to verify a file follows rules

### Human-in-the-Loop (IMPORTANT!)
Always involve the user for important decisions and confirmations:

1. **Use `ask_user`** when you need:
   - Clarification on ambiguous requirements
   - User preferences (naming, structure, style)
   - Input that only the user can provide (API keys, credentials)
   - Decisions between multiple valid approaches

2. **Use `confirm_action`** BEFORE:
   - Deleting any files or directories
   - Overwriting existing files with different content
   - Running commands that modify system state
   - Pushing to remote git repositories
   - Making breaking changes to code
   - Installing new dependencies

3. **Use `show_options`** when:
   - Multiple valid solutions exist
   - User needs to choose between frameworks/libraries
   - Selecting which files to modify

4. **Use `notify_user`** to:
   - Report progress on long-running tasks
   - Warn about potential issues
   - Confirm successful completion of steps

5. **NEVER proceed without confirmation for**:
   - `rm`, `del`, `rmdir` commands
   - `git push`, `git push --force`
   - Dropping databases or tables
   - Modifying production configurations
   - Any irreversible operation

### Problem Solving
1. Break complex tasks into smaller steps
2. Test changes incrementally when possible
3. If something fails, analyze the error and try a different approach
4. Report progress on multi-step tasks
5. Ask the user when unsure - it's better to ask than to assume

## Response Style
- Be concise and direct
- Show code blocks with syntax highlighting
- Explain what you did and why
- Suggest next steps when appropriate
"""


class CodingAgent:
    """
    Main coding agent that combines all tools for software development tasks.

    This agent can:
    - Execute terminal commands
    - Read, write, and edit files
    - Search and analyze code
    - Help with debugging and development
    """

    def __init__(
        self,
        session_id: str = "default",
        workspace: str | Path | None = None,
        model_id: str | None = None,
        enable_guardrails: bool = True,
        guardrails_config: Optional[Any] = None,
    ):
        """
        Initialize the coding agent.

        Args:
            session_id: Unique session identifier for memory persistence
            workspace: Working directory for the agent
            model_id: Optional override for the LLM model
            enable_guardrails: Whether to enable guardrails protection
            guardrails_config: Optional custom guardrails configuration
        """
        self.settings = get_settings()
        self.session_id = session_id

        # Initialize guardrails
        self.guardrails = None
        self._guardrails_enabled = enable_guardrails and GUARDRAILS_AVAILABLE
        if self._guardrails_enabled:
            try:
                self.guardrails = get_guardrails(guardrails_config)
                logger.info("Guardrails protection enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize guardrails: {e}")
                self._guardrails_enabled = False

        # Ensure data directory exists
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)

        # Set workspace
        if workspace:
            workspace_path = Path(workspace).resolve()
            if workspace_path.exists():
                set_working_dir(workspace_path)

        # Combine all tools
        all_tools = (
            TERMINAL_TOOLS
            + FILE_TOOLS
            + SEARCH_TOOLS
            + GIT_TOOLS
            + SANDBOX_TOOLS
            + AGENT_TOOLS
            + ERROR_FIXER_TOOLS
            + BUILD_FIX_TOOLS
            + HUMAN_INPUT_TOOLS
            + WORKFLOW_TOOLS
            + PLANNING_TOOLS
            + CONTEXT_TOOLS
            + RULES_TOOLS
        )

        # Load project-specific rules if available
        project_rules = get_project_rules()
        full_instructions = CODING_AGENT_INSTRUCTIONS
        if project_rules:
            full_instructions += "\n" + project_rules

        # Set up database for persistence
        db = SqliteDb(
            db_file=str(self.settings.data_dir / "agent_storage.db"),
        )

        # Create the agent
        self.agent = Agent(
            name="CodeAgent",
            model=get_model(model_id=model_id),
            description="Expert AI coding assistant for software development",
            instructions=full_instructions,
            tools=all_tools,
            db=db,
            session_id=session_id,
            markdown=True,
            add_datetime_to_context=True,
        )

    def run(self, message: str, stream: bool = True) -> Any:
        """
        Run the agent with a user message.

        Args:
            message: User's input
            stream: Whether to stream the response

        Returns:
            Agent response
        """
        # Check input through guardrails
        if self.guardrails and self._guardrails_enabled:
            is_safe, error_msg = self.guardrails.check_input_sync(message)
            if not is_safe:
                logger.warning(f"Input blocked by guardrails: {error_msg}")
                return self._create_blocked_response(error_msg)

        # Run the agent
        response = self.agent.run(message, stream=stream)

        # Process output through guardrails (for non-streaming)
        if not stream and self.guardrails and self._guardrails_enabled:
            if hasattr(response, 'content') and response.content:
                response.content = self.guardrails.process_output_sync(response.content)

        return response

    def _create_blocked_response(self, error_msg: str) -> Any:
        """
        Create a response object for blocked requests.

        Args:
            error_msg: The error message to display

        Returns:
            Response-like object with the error message
        """
        class BlockedResponse:
            def __init__(self, message: str):
                self.content = f"Request blocked: {message}"
                self.blocked = True
                self.messages = []

            def __iter__(self):
                # Allow iteration for streaming compatibility
                yield self

        return BlockedResponse(error_msg)

    async def arun(self, message: str, stream: bool = True) -> Any:
        """
        Run the agent asynchronously.

        Args:
            message: User's input
            stream: Whether to stream the response

        Returns:
            Agent response
        """
        # Check input through guardrails
        if self.guardrails and self._guardrails_enabled:
            is_safe, error_msg = await self.guardrails.check_input(message)
            if not is_safe:
                logger.warning(f"Input blocked by guardrails: {error_msg}")
                return self._create_blocked_response(error_msg)

        # Run the agent
        response = await self.agent.arun(message, stream=stream)

        # Process output through guardrails (for non-streaming)
        if not stream and self.guardrails and self._guardrails_enabled:
            if hasattr(response, 'content') and response.content:
                response.content = await self.guardrails.process_output(response.content)

        return response

    def print_response(self, message: str) -> None:
        """Run and print the response (for CLI usage)."""
        self.agent.print_response(message, stream=True)

    def get_history(self) -> list[dict]:
        """Get conversation history."""
        return self.agent.get_history()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.agent.clear_history()

    def get_guardrails_status(self) -> dict:
        """
        Get the current guardrails status.

        Returns:
            Dict with guardrails status information
        """
        if self.guardrails and self._guardrails_enabled:
            return {
                "enabled": True,
                **self.guardrails.get_status()
            }
        return {
            "enabled": False,
            "reason": "not_available" if not GUARDRAILS_AVAILABLE else "disabled"
        }


def create_coding_agent(
    session_id: str = "default",
    workspace: str | None = None,
) -> CodingAgent:
    """
    Factory function to create a coding agent.

    Args:
        session_id: Session identifier
        workspace: Working directory path

    Returns:
        Configured CodingAgent instance
    """
    return CodingAgent(session_id=session_id, workspace=workspace)
