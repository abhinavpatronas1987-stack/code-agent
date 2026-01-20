"""Tool activity logger for real-time display of agent actions."""

from rich.console import Console
from functools import wraps
from typing import Callable, Any
import time

console = Console()

# Global flag to enable/disable logging
_logging_enabled = True


def set_tool_logging(enabled: bool) -> None:
    """Enable or disable tool logging."""
    global _logging_enabled
    _logging_enabled = enabled


def get_tool_logging() -> bool:
    """Check if tool logging is enabled."""
    return _logging_enabled


def _short_path(path: str) -> str:
    """Get shortened version of a path."""
    if not path:
        return "unknown"
    parts = path.replace("\\", "/").split("/")
    if len(parts) > 2:
        return "/".join(parts[-2:])
    return parts[-1] if parts else path


def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text if too long."""
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text


def log_tool_call(tool_name: str, **kwargs) -> None:
    """Log a tool call with its arguments."""
    if not _logging_enabled:
        return

    # Format based on tool type
    if tool_name == "read_file":
        path = kwargs.get("file_path", kwargs.get("path", "unknown"))
        console.print(f"  [cyan]>[/cyan] [dim]Reading:[/dim] {_short_path(path)}")

    elif tool_name == "write_file":
        path = kwargs.get("file_path", kwargs.get("path", "unknown"))
        console.print(f"  [green]>[/green] [dim]Writing:[/dim] {_short_path(path)}")

    elif tool_name == "create_file":
        path = kwargs.get("file_path", kwargs.get("path", "unknown"))
        console.print(f"  [green]>[/green] [dim]Creating:[/dim] {_short_path(path)}")

    elif tool_name == "edit_file":
        path = kwargs.get("file_path", kwargs.get("path", "unknown"))
        console.print(f"  [yellow]>[/yellow] [dim]Editing:[/dim] {_short_path(path)}")

    elif tool_name == "delete_file":
        path = kwargs.get("file_path", kwargs.get("path", "unknown"))
        console.print(f"  [red]>[/red] [dim]Deleting:[/dim] {_short_path(path)}")

    elif tool_name == "move_file":
        src = kwargs.get("source", "unknown")
        dst = kwargs.get("destination", "unknown")
        console.print(f"  [blue]>[/blue] [dim]Moving:[/dim] {_short_path(src)} -> {_short_path(dst)}")

    elif tool_name == "copy_file":
        src = kwargs.get("source", "unknown")
        dst = kwargs.get("destination", "unknown")
        console.print(f"  [blue]>[/blue] [dim]Copying:[/dim] {_short_path(src)} -> {_short_path(dst)}")

    elif tool_name == "run_terminal_command":
        cmd = kwargs.get("command", "unknown")
        console.print(f"  [magenta]>[/magenta] [dim]Running:[/dim] `{_truncate(cmd, 60)}`")

    elif tool_name == "change_directory":
        path = kwargs.get("path", "unknown")
        console.print(f"  [blue]>[/blue] [dim]Changing dir:[/dim] {_short_path(path)}")

    elif tool_name == "list_directory":
        path = kwargs.get("path", kwargs.get("directory", "."))
        console.print(f"  [cyan]>[/cyan] [dim]Listing:[/dim] {_short_path(path)}")

    elif tool_name.startswith("git_"):
        op = tool_name.replace("git_", "").replace("_", " ").title()
        console.print(f"  [magenta]>[/magenta] [dim]Git {op}[/dim]")

    elif tool_name in ["search_files", "find_in_files", "grep_search"]:
        pattern = kwargs.get("pattern", kwargs.get("query", ""))
        console.print(f"  [cyan]>[/cyan] [dim]Searching:[/dim] '{_truncate(pattern, 40)}'")

    elif tool_name.startswith("python_"):
        op = tool_name.replace("python_", "").replace("_", " ").title()
        console.print(f"  [yellow]>[/yellow] [dim]Python {op}[/dim]")

    else:
        # Generic log for other tools
        display_name = tool_name.replace("_", " ").title()
        console.print(f"  [dim]>[/dim] [dim]{display_name}[/dim]")


def log_tool_result(tool_name: str, success: bool, message: str = "") -> None:
    """Log a tool result."""
    if not _logging_enabled:
        return

    if success:
        console.print(f"    [green]OK[/green]")
    else:
        if message:
            console.print(f"    [red]Error:[/red] [dim]{_truncate(message, 60)}[/dim]")
        else:
            console.print(f"    [red]Failed[/red]")


def with_logging(tool_name: str):
    """Decorator to add logging to a tool function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Log the call
            log_tool_call(tool_name, **kwargs)

            # Execute the tool
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            # Check if result indicates success or failure
            result_str = str(result) if result else ""
            success = not (
                result_str.startswith("Error:") or
                result_str.startswith("error:") or
                "Error" in result_str[:50]
            )

            # Log result for slower operations
            if elapsed > 1.0:
                console.print(f"    [dim]({elapsed:.1f}s)[/dim]")

            return result
        return wrapper
    return decorator
