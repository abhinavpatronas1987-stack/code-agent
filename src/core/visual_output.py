"""Visual output utilities for displaying agent progress and task status."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.tree import Tree
from rich.text import Text
from rich.box import ROUNDED, HEAVY
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

console = Console()


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


# Status icons and colors
STATUS_ICONS = {
    TaskStatus.PENDING: ("○", "dim"),
    TaskStatus.RUNNING: ("◐", "yellow"),
    TaskStatus.SUCCESS: ("✓", "green"),
    TaskStatus.FAILED: ("✗", "red"),
    TaskStatus.SKIPPED: ("⊘", "dim"),
    TaskStatus.WARNING: ("⚠", "yellow"),
}

PLAN_STATUS_ICONS = {
    "draft": ("📝", "dim"),
    "approved": ("✅", "green"),
    "in_progress": ("🔄", "yellow"),
    "completed": ("✓", "green"),
    "failed": ("❌", "red"),
    "cancelled": ("⊘", "dim"),
}


@dataclass
class TaskItem:
    """A task item for display."""
    name: str
    status: TaskStatus
    message: str = ""
    details: List[str] = None


def print_header(title: str, subtitle: str = "") -> None:
    """Print a styled header."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, box=ROUNDED, border_style="cyan"))


def print_step(step_num: int, total: int, title: str, status: TaskStatus = TaskStatus.RUNNING) -> None:
    """Print a step indicator."""
    icon, color = STATUS_ICONS[status]
    console.print(f"[{color}]{icon}[/{color}] [{color}]Step {step_num}/{total}:[/{color}] {title}")


def print_status(message: str, status: TaskStatus) -> None:
    """Print a status message with icon."""
    icon, color = STATUS_ICONS[status]
    console.print(f"[{color}]{icon} {message}[/{color}]")


def print_success(message: str) -> None:
    """Print a success message."""
    print_status(message, TaskStatus.SUCCESS)


def print_error(message: str, details: str = "") -> None:
    """Print an error message."""
    print_status(message, TaskStatus.FAILED)
    if details:
        console.print(f"  [dim]{details}[/dim]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print_status(message, TaskStatus.WARNING)


def print_task_list(tasks: List[TaskItem], title: str = "Tasks") -> None:
    """Print a formatted task list."""
    table = Table(title=title, box=ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Status", width=3, justify="center")
    table.add_column("Task", style="white")
    table.add_column("Details", style="dim")

    for task in tasks:
        icon, color = STATUS_ICONS[task.status]
        table.add_row(
            f"[{color}]{icon}[/{color}]",
            task.name,
            task.message
        )

    console.print(table)


def print_plan_progress(
    plan_id: str,
    goal: str,
    steps: List[Dict[str, Any]],
    current_step: int = 0,
) -> str:
    """
    Generate a formatted plan progress display.

    Returns a string for the agent to output.
    """
    output = []

    # Header
    output.append("```")
    output.append("╔════════════════════════════════════════════════════════════╗")
    output.append(f"║  PLAN: {plan_id[:50]:<50} ║")
    output.append("╠════════════════════════════════════════════════════════════╣")
    output.append(f"║  Goal: {goal[:52]:<52} ║")
    output.append("╠════════════════════════════════════════════════════════════╣")

    # Steps
    for i, step in enumerate(steps, 1):
        status = step.get("status", "draft")
        title = step.get("title", "Untitled")[:45]

        # Choose icon based on status
        if status == "completed":
            icon = "[✓]"
            status_text = "DONE"
        elif status == "in_progress":
            icon = "[►]"
            status_text = "RUNNING"
        elif status == "failed":
            icon = "[✗]"
            status_text = "FAILED"
        else:
            icon = "[ ]"
            status_text = "PENDING"

        # Highlight current step
        if i == current_step:
            output.append(f"║  {icon} Step {i}: {title:<45} {status_text:>8} ◄ ║")
        else:
            output.append(f"║  {icon} Step {i}: {title:<45} {status_text:>8}   ║")

    # Progress bar
    completed = sum(1 for s in steps if s.get("status") == "completed")
    total = len(steps)
    progress_pct = (completed / total * 100) if total > 0 else 0
    bar_width = 40
    filled = int(bar_width * completed / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    output.append("╠════════════════════════════════════════════════════════════╣")
    output.append(f"║  Progress: [{bar}] {progress_pct:5.1f}% ║")
    output.append(f"║  Completed: {completed}/{total} steps{' ' * 43}║")
    output.append("╚════════════════════════════════════════════════════════════╝")
    output.append("```")

    return "\n".join(output)


def print_build_result(
    project: str,
    project_type: str,
    command: str,
    success: bool,
    output: str,
    errors: List[Dict[str, Any]] = None,
    warnings: List[str] = None,
) -> str:
    """
    Generate a formatted build result display.

    Returns a string for the agent to output.
    """
    result = []

    # Header
    status_icon = "✓ SUCCESS" if success else "✗ FAILED"
    status_line = "═" * 60

    result.append("```")
    result.append(f"╔{status_line}╗")
    result.append(f"║  BUILD RESULT: {status_icon:<44} ║")
    result.append(f"╠{status_line}╣")
    result.append(f"║  Project: {project[:48]:<48} ║")
    result.append(f"║  Type:    {project_type[:48]:<48} ║")
    result.append(f"║  Command: {command[:48]:<48} ║")
    result.append(f"╠{status_line}╣")

    if success:
        result.append(f"║  [✓] Build completed successfully{' ' * 25}║")
    else:
        result.append(f"║  [✗] Build failed with errors{' ' * 29}║")

    result.append(f"╚{status_line}╝")
    result.append("```")

    # Errors section
    if errors and not success:
        result.append("\n### Errors Found:")
        result.append("```")
        for i, err in enumerate(errors[:5], 1):  # Limit to 5 errors
            err_type = err.get("type", "Error")
            err_file = err.get("file", "unknown")
            err_line = err.get("line", "?")
            err_msg = err.get("message", "Unknown error")[:60]
            result.append(f"  {i}. [{err_type}] {err_file}:{err_line}")
            result.append(f"     {err_msg}")
        if len(errors) > 5:
            result.append(f"  ... and {len(errors) - 5} more errors")
        result.append("```")

    # Warnings section
    if warnings:
        result.append("\n### Warnings:")
        result.append("```")
        for warn in warnings[:3]:
            result.append(f"  ⚠ {warn[:70]}")
        if len(warnings) > 3:
            result.append(f"  ... and {len(warnings) - 3} more warnings")
        result.append("```")

    # Suggestions for failures
    if not success and errors:
        result.append("\n### Suggested Actions:")
        for i, err in enumerate(errors[:3], 1):
            suggestion = err.get("suggestion", "Review the error and fix the issue")
            result.append(f"{i}. {suggestion}")

    return "\n".join(result)


def print_test_result(
    project: str,
    passed: int,
    failed: int,
    skipped: int,
    duration: float = 0,
    failed_tests: List[Dict[str, str]] = None,
) -> str:
    """
    Generate a formatted test result display.

    Returns a string for the agent to output.
    """
    total = passed + failed + skipped
    success = failed == 0

    result = []

    # Header
    status_icon = "✓ ALL PASSED" if success else f"✗ {failed} FAILED"

    result.append("```")
    result.append("╔════════════════════════════════════════════════════════════╗")
    result.append(f"║  TEST RESULTS: {status_icon:<44} ║")
    result.append("╠════════════════════════════════════════════════════════════╣")
    result.append(f"║  Project: {project[:48]:<48} ║")
    result.append("╠════════════════════════════════════════════════════════════╣")

    # Stats
    result.append(f"║  ✓ Passed:  {passed:<5}  ✗ Failed: {failed:<5}  ⊘ Skipped: {skipped:<5}  ║")
    result.append(f"║  Total: {total:<5} tests    Duration: {duration:.2f}s{' ' * 21}║")

    # Progress bar
    if total > 0:
        bar_width = 40
        passed_width = int(bar_width * passed / total)
        failed_width = int(bar_width * failed / total)
        skipped_width = bar_width - passed_width - failed_width

        bar = "█" * passed_width + "▓" * failed_width + "░" * skipped_width
        result.append(f"║  [{bar}] ║")

    result.append("╚════════════════════════════════════════════════════════════╝")
    result.append("```")

    # Failed tests details
    if failed_tests and not success:
        result.append("\n### Failed Tests:")
        result.append("```")
        for test in failed_tests[:5]:
            name = test.get("name", "unknown")[:50]
            error = test.get("error", "")[:40]
            result.append(f"  ✗ {name}")
            if error:
                result.append(f"    Error: {error}")
        if len(failed_tests) > 5:
            result.append(f"  ... and {len(failed_tests) - 5} more failed tests")
        result.append("```")

    return "\n".join(result)


def print_task_progress(
    task_name: str,
    current: int,
    total: int,
    status: str = "running",
    details: str = "",
) -> str:
    """
    Generate a task progress indicator.

    Returns a string for the agent to output.
    """
    percentage = (current / total * 100) if total > 0 else 0
    bar_width = 30
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    status_icons = {
        "running": "◐",
        "success": "✓",
        "failed": "✗",
        "pending": "○",
    }
    icon = status_icons.get(status, "○")

    result = f"{icon} {task_name}: [{bar}] {current}/{total} ({percentage:.0f}%)"
    if details:
        result += f" - {details}"

    return result


def format_error_summary(errors: List[Dict[str, Any]]) -> str:
    """Format a summary of errors for display."""
    if not errors:
        return "No errors found."

    result = ["### Error Summary:", ""]

    # Group by type
    by_type = {}
    for err in errors:
        err_type = err.get("type", "Error")
        if err_type not in by_type:
            by_type[err_type] = []
        by_type[err_type].append(err)

    result.append("| Type | Count | First Occurrence |")
    result.append("|------|-------|-----------------|")

    for err_type, errs in by_type.items():
        first = errs[0]
        loc = f"{first.get('file', '?')}:{first.get('line', '?')}"
        result.append(f"| {err_type} | {len(errs)} | {loc} |")

    result.append("")
    result.append(f"**Total: {len(errors)} errors**")

    return "\n".join(result)


# Tool display names for better readability
TOOL_DISPLAY_NAMES = {
    "run_terminal_command": "Running command",
    "change_directory": "Changing directory",
    "read_file": "Reading file",
    "write_file": "Writing file",
    "edit_file": "Editing file",
    "list_directory": "Listing directory",
    "search_files": "Searching files",
    "find_in_files": "Finding in files",
    "grep_search": "Searching with grep",
    "git_status": "Checking git status",
    "git_diff": "Getting git diff",
    "git_add": "Staging files",
    "git_commit": "Committing changes",
    "git_push": "Pushing to remote",
    "git_pull": "Pulling from remote",
    "git_branch": "Managing branches",
    "git_stash": "Stashing changes",
    "python_exec": "Executing Python",
    "python_eval": "Evaluating expression",
    "python_import": "Importing module",
    "code_review": "Reviewing code",
    "debug_help": "Debugging",
    "suggest_refactoring": "Suggesting refactors",
    "generate_tests": "Generating tests",
    "generate_docs": "Generating docs",
    "analyze_error": "Analyzing error",
    "build_project": "Building project",
    "test_project": "Running tests",
    "lint_project": "Linting code",
    "create_plan": "Creating plan",
    "execute_plan": "Executing plan",
    "attach_file": "Attaching file",
    "attach_folder": "Attaching folder",
}


class AgentStatusDisplay:
    """
    Display agent activity status with animated spinner and tool information.
    Uses Rich's Live display for continuous animation.

    Usage:
        with AgentStatusDisplay() as status:
            for chunk in agent.run(message, stream=True):
                status.update_from_chunk(chunk)
                if chunk.content:
                    status.stop()  # Stop spinner before printing
                    print(chunk.content)
    """

    def __init__(self, show_tools: bool = True):
        """
        Initialize the status display.

        Args:
            show_tools: Whether to display tool call information
        """
        self.show_tools = show_tools
        self.current_tool: Optional[str] = None
        self.current_args: Optional[Dict[str, Any]] = None
        self.current_status: str = "Processing..."
        self.tool_history: List[str] = []
        self.is_active = False
        self._live: Optional[Live] = None
        self._progress: Optional[Progress] = None
        self._task_id = None
        self._started_response = False
        self._stopped = False

    def __enter__(self):
        """Start the status display with animated spinner."""
        self.is_active = True
        self._stopped = False
        self._started_response = False

        # Create progress with spinner
        self._progress = Progress(
            SpinnerColumn(spinner_name="dots", style="yellow"),
            TextColumn("[dim]{task.description}[/dim]"),
            console=console,
            transient=True,  # Remove when done
        )
        self._live = Live(
            self._progress,
            console=console,
            refresh_per_second=10,
            transient=True,
        )
        self._live.start()
        self._task_id = self._progress.add_task(self.current_status, total=None)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the status display."""
        self.stop()
        return False

    def stop(self) -> None:
        """Stop the spinner and clear the display."""
        if self._stopped:
            return
        self._stopped = True
        self.is_active = False

        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
        self._progress = None
        self._task_id = None

    def _get_tool_display(self, tool_name: str, args: Optional[Dict] = None) -> str:
        """Get a user-friendly display name for a tool."""
        display_name = TOOL_DISPLAY_NAMES.get(tool_name, tool_name.replace("_", " ").title())

        # Add context from args if available
        if args:
            if "command" in args:
                cmd = args["command"]
                # Truncate long commands
                if len(cmd) > 40:
                    cmd = cmd[:37] + "..."
                return f"{display_name}: `{cmd}`"
            elif "file_path" in args or "path" in args:
                path = args.get("file_path") or args.get("path", "")
                # Show just filename for brevity
                if "/" in path or "\\" in path:
                    path = path.replace("\\", "/").split("/")[-1]
                return f"{display_name}: {path}"
            elif "pattern" in args:
                pattern = args["pattern"]
                if len(pattern) > 30:
                    pattern = pattern[:27] + "..."
                return f"{display_name}: '{pattern}'"
            elif "message" in args:
                msg = args["message"]
                if len(msg) > 30:
                    msg = msg[:27] + "..."
                return f"{display_name}: {msg}"

        return display_name

    def update_status(self, status: str) -> None:
        """Update the status message displayed next to the spinner."""
        self.current_status = status
        if self._progress and self._task_id is not None and not self._stopped:
            self._progress.update(self._task_id, description=status)

    def update_from_chunk(self, chunk: Any) -> Optional[str]:
        """
        Update the display based on a response chunk.

        Args:
            chunk: A response chunk from agent.run()

        Returns:
            Tool status message if a new tool was called, None otherwise
        """
        if self._stopped:
            return None

        tool_message = None

        # Check for tool calls
        if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("arguments", {})

                self.current_tool = tool_name
                self.current_args = tool_args
                self.tool_history.append(tool_name)

                if self.show_tools and self.is_active:
                    display = self._get_tool_display(tool_name, tool_args)
                    tool_message = display
                    self.update_status(display)

        # Stop spinner when content starts streaming
        if hasattr(chunk, 'content') and chunk.content:
            if not self._started_response:
                self._started_response = True
                self.stop()

        return tool_message

    def show_thinking(self, message: str = "Thinking...") -> None:
        """Show a thinking/processing indicator."""
        if self.is_active and not self._stopped:
            self.update_status(message)

    def show_tool_start(self, tool_name: str, args: Optional[Dict] = None) -> None:
        """Manually show that a tool is starting."""
        self.current_tool = tool_name
        self.current_args = args
        if self.is_active and self.show_tools and not self._stopped:
            display = self._get_tool_display(tool_name, args)
            self.update_status(display)

    def show_tool_complete(self, tool_name: str, success: bool = True) -> None:
        """Show that a tool completed (prints a line, doesn't affect spinner)."""
        icon = "[green]✓[/green]" if success else "[red]✗[/red]"
        display = TOOL_DISPLAY_NAMES.get(tool_name, tool_name)
        # Temporarily stop live to print
        if self._live and not self._stopped:
            self._live.stop()
            console.print(f"  {icon} [dim]{display}[/dim]")
            self._live.start()
        else:
            console.print(f"  {icon} [dim]{display}[/dim]")

    def get_tool_summary(self) -> str:
        """Get a summary of tools that were called."""
        if not self.tool_history:
            return "No tools were called"

        # Count tool usage
        tool_counts = {}
        for tool in self.tool_history:
            display = TOOL_DISPLAY_NAMES.get(tool, tool)
            tool_counts[display] = tool_counts.get(display, 0) + 1

        parts = [f"{name} ({count}x)" if count > 1 else name
                 for name, count in tool_counts.items()]
        return ", ".join(parts)


@contextmanager
def agent_status(show_tools: bool = True):
    """
    Context manager for displaying agent activity status with animated spinner.

    Usage:
        with agent_status() as status:
            for chunk in agent.run(message, stream=True):
                status.update_from_chunk(chunk)
                # handle content...
    """
    display = AgentStatusDisplay(show_tools=show_tools)
    try:
        with display:
            yield display
    finally:
        display.stop()


class AgentActivitySummary:
    """
    Track and display a summary of agent activities.

    Tracks:
    - Files read/written/edited
    - Commands executed
    - Git operations
    - Tools used
    - Errors encountered
    """

    def __init__(self):
        self.files_read: List[str] = []
        self.files_written: List[str] = []
        self.files_edited: List[str] = []
        self.commands_run: List[Dict[str, Any]] = []
        self.git_operations: List[str] = []
        self.searches: List[str] = []
        self.tools_used: List[str] = []
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start tracking time."""
        import time
        self.start_time = time.time()

    def stop(self) -> None:
        """Stop tracking time."""
        import time
        self.end_time = time.time()

    def track_from_chunk(self, chunk: Any) -> None:
        """Extract activity information from a response chunk."""
        if not hasattr(chunk, 'tool_calls') or not chunk.tool_calls:
            return

        for tool_call in chunk.tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("arguments", {})

            self.tools_used.append(tool_name)
            self._categorize_tool_call(tool_name, tool_args)

    def _categorize_tool_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        """Categorize a tool call into the appropriate list."""
        # File operations
        if tool_name == "read_file":
            path = args.get("file_path") or args.get("path", "unknown")
            self.files_read.append(self._short_path(path))

        elif tool_name == "write_file":
            path = args.get("file_path") or args.get("path", "unknown")
            self.files_written.append(self._short_path(path))

        elif tool_name == "edit_file":
            path = args.get("file_path") or args.get("path", "unknown")
            self.files_edited.append(self._short_path(path))

        # Terminal commands
        elif tool_name == "run_terminal_command":
            cmd = args.get("command", "unknown")
            self.commands_run.append({
                "command": cmd[:60] + "..." if len(cmd) > 60 else cmd,
            })

        # Git operations
        elif tool_name.startswith("git_"):
            op = tool_name.replace("git_", "").replace("_", " ").title()
            detail = ""
            if "message" in args:
                detail = f": {args['message'][:30]}..."
            elif "branch" in args:
                detail = f": {args['branch']}"
            self.git_operations.append(f"{op}{detail}")

        # Search operations
        elif tool_name in ["search_files", "find_in_files", "grep_search"]:
            pattern = args.get("pattern", args.get("query", ""))
            if pattern:
                self.searches.append(pattern[:40])

    def _short_path(self, path: str) -> str:
        """Get shortened version of a path."""
        if not path:
            return "unknown"
        # Get just filename or last 2 parts
        parts = path.replace("\\", "/").split("/")
        if len(parts) > 2:
            return "/".join(parts[-2:])
        return parts[-1] if parts else path

    def _get_duration(self) -> str:
        """Get formatted duration."""
        if not self.start_time or not self.end_time:
            return ""
        duration = self.end_time - self.start_time
        if duration < 1:
            return f"{duration*1000:.0f}ms"
        elif duration < 60:
            return f"{duration:.1f}s"
        else:
            mins = int(duration // 60)
            secs = duration % 60
            return f"{mins}m {secs:.0f}s"

    def has_activity(self) -> bool:
        """Check if any activity was tracked."""
        return bool(
            self.files_read or self.files_written or self.files_edited or
            self.commands_run or self.git_operations or self.searches
        )

    def print_summary(self, show_if_empty: bool = False) -> None:
        """Print a formatted summary of agent activities."""
        if not self.has_activity() and not show_if_empty:
            return

        console.print()

        # Create summary panel
        summary_parts = []

        # Duration
        duration = self._get_duration()
        if duration:
            summary_parts.append(f"[dim]Completed in {duration}[/dim]")

        # Files
        if self.files_read:
            unique_files = list(dict.fromkeys(self.files_read))  # Remove duplicates, preserve order
            if len(unique_files) <= 3:
                files_str = ", ".join(unique_files)
            else:
                files_str = f"{', '.join(unique_files[:3])} +{len(unique_files)-3} more"
            summary_parts.append(f"[cyan]◈ Read:[/cyan] {files_str}")

        if self.files_written:
            unique_files = list(dict.fromkeys(self.files_written))
            if len(unique_files) <= 3:
                files_str = ", ".join(unique_files)
            else:
                files_str = f"{', '.join(unique_files[:3])} +{len(unique_files)-3} more"
            summary_parts.append(f"[green]◈ Created:[/green] {files_str}")

        if self.files_edited:
            unique_files = list(dict.fromkeys(self.files_edited))
            if len(unique_files) <= 3:
                files_str = ", ".join(unique_files)
            else:
                files_str = f"{', '.join(unique_files[:3])} +{len(unique_files)-3} more"
            summary_parts.append(f"[yellow]◈ Edited:[/yellow] {files_str}")

        # Commands
        if self.commands_run:
            if len(self.commands_run) == 1:
                summary_parts.append(f"[blue]◈ Ran:[/blue] `{self.commands_run[0]['command']}`")
            else:
                summary_parts.append(f"[blue]◈ Ran:[/blue] {len(self.commands_run)} commands")

        # Git
        if self.git_operations:
            unique_ops = list(dict.fromkeys(self.git_operations))
            if len(unique_ops) <= 2:
                ops_str = ", ".join(unique_ops)
            else:
                ops_str = f"{', '.join(unique_ops[:2])} +{len(unique_ops)-2} more"
            summary_parts.append(f"[magenta]◈ Git:[/magenta] {ops_str}")

        # Searches
        if self.searches:
            unique_searches = list(dict.fromkeys(self.searches))
            summary_parts.append(f"[dim]◈ Searched:[/dim] {len(unique_searches)} patterns")

        if summary_parts:
            # Print as a compact summary box
            console.print(Panel(
                "\n".join(summary_parts),
                title="[bold]Summary[/bold]",
                title_align="left",
                border_style="dim",
                padding=(0, 1),
            ))

    def get_summary_text(self) -> str:
        """Get summary as plain text."""
        if not self.has_activity():
            return "No file or command operations performed."

        parts = []

        if self.files_read:
            parts.append(f"Read {len(set(self.files_read))} file(s)")
        if self.files_written:
            parts.append(f"Created {len(set(self.files_written))} file(s)")
        if self.files_edited:
            parts.append(f"Edited {len(set(self.files_edited))} file(s)")
        if self.commands_run:
            parts.append(f"Ran {len(self.commands_run)} command(s)")
        if self.git_operations:
            parts.append(f"{len(self.git_operations)} git operation(s)")

        return " • ".join(parts)
