"""Terminal execution tool for running shell commands."""

import os
import subprocess
import shlex
from pathlib import Path
from typing import Optional

from agno.tools.decorator import tool

from src.config.settings import get_settings
from src.core.tool_logger import log_tool_call


# Global working directory state (per session in production)
_current_working_dir: Path = Path.cwd()


def get_working_dir() -> Path:
    """Get current working directory."""
    global _current_working_dir
    return _current_working_dir


def set_working_dir(path: Path) -> None:
    """Set current working directory."""
    global _current_working_dir
    _current_working_dir = path


@tool
def run_terminal_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """
    Execute a shell command in the terminal.

    Use this tool to run any terminal/shell command. The command runs
    in the current working directory unless specified otherwise.

    Args:
        command: The shell command to execute (e.g., "ls -la", "git status", "npm install")
        working_dir: Optional directory to run the command in. If not provided,
                    uses the current working directory.
        timeout: Optional timeout in seconds (default: 120)

    Returns:
        A formatted string containing:
        - The command that was executed
        - Working directory
        - stdout output
        - stderr output (if any)
        - Exit code

    Examples:
        run_terminal_command("git status")
        run_terminal_command("npm install", working_dir="/path/to/project")
        run_terminal_command("python script.py", timeout=60)
    """
    # Log the tool call
    log_tool_call("run_terminal_command", command=command)

    settings = get_settings()
    timeout = timeout or settings.terminal_timeout

    # Determine working directory
    cwd = Path(working_dir) if working_dir else get_working_dir()
    if not cwd.exists():
        return f"Error: Working directory does not exist: {cwd}"

    try:
        # Use shell=True on Windows for proper command interpretation
        is_windows = os.name == "nt"

        if is_windows:
            # Windows: run through cmd or powershell
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        else:
            # Unix: split command and run directly
            result = subprocess.run(
                shlex.split(command),
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ},
            )

        # Format output
        output_parts = [
            f"Command: {command}",
            f"Working Directory: {cwd}",
            f"Exit Code: {result.returncode}",
            "",
            "=== STDOUT ===",
            result.stdout.strip() if result.stdout else "(no output)",
        ]

        if result.stderr:
            output_parts.extend([
                "",
                "=== STDERR ===",
                result.stderr.strip(),
            ])

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds: {command}"
    except Exception as e:
        return f"Error executing command: {command}\nError: {str(e)}"


@tool
def change_directory(path: str) -> str:
    """
    Change the current working directory.

    Use this tool to navigate to a different directory before running commands.

    Args:
        path: The directory path to change to. Can be:
              - Absolute path: "C:/Users/project" or "/home/user/project"
              - Relative path: "./src" or "../parent"
              - Home directory: "~" or "~/projects"

    Returns:
        Confirmation message with the new working directory, or an error message.

    Examples:
        change_directory("C:/Users/username/projects/myapp")
        change_directory("./src")
        change_directory("..")
    """
    # Log the tool call
    log_tool_call("change_directory", path=path)

    global _current_working_dir

    try:
        # Expand user home directory
        expanded_path = Path(path).expanduser()

        # Make absolute if relative
        if not expanded_path.is_absolute():
            expanded_path = (_current_working_dir / expanded_path).resolve()
        else:
            expanded_path = expanded_path.resolve()

        # Check if directory exists
        if not expanded_path.exists():
            return f"Error: Directory does not exist: {expanded_path}"

        if not expanded_path.is_dir():
            return f"Error: Path is not a directory: {expanded_path}"

        # Update working directory
        _current_working_dir = expanded_path

        return f"Changed directory to: {_current_working_dir}"

    except Exception as e:
        return f"Error changing directory: {str(e)}"


@tool
def get_current_directory() -> str:
    """
    Get the current working directory.

    Returns:
        The absolute path of the current working directory.
    """
    return f"Current directory: {get_working_dir()}"


@tool
def list_directory(
    path: Optional[str] = None,
    show_hidden: bool = False,
    long_format: bool = True,
) -> str:
    """
    List contents of a directory.

    Args:
        path: Directory to list (defaults to current working directory)
        show_hidden: Whether to show hidden files (starting with .)
        long_format: Whether to show detailed information (size, date)

    Returns:
        Formatted directory listing.

    Examples:
        list_directory()
        list_directory("./src", show_hidden=True)
    """
    # Log the tool call
    log_tool_call("list_directory", path=path or ".")

    target_dir = Path(path) if path else get_working_dir()

    if not target_dir.is_absolute():
        target_dir = (get_working_dir() / target_dir).resolve()

    if not target_dir.exists():
        return f"Error: Directory does not exist: {target_dir}"

    if not target_dir.is_dir():
        return f"Error: Path is not a directory: {target_dir}"

    try:
        entries = list(target_dir.iterdir())

        # Filter hidden files if needed
        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        # Sort: directories first, then files
        entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

        if not entries:
            return f"Directory is empty: {target_dir}"

        output_lines = [f"Contents of: {target_dir}", ""]

        if long_format:
            for entry in entries:
                try:
                    stat = entry.stat()
                    size = stat.st_size
                    is_dir = entry.is_dir()

                    # Format size
                    if is_dir:
                        size_str = "<DIR>".rjust(10)
                    elif size < 1024:
                        size_str = f"{size}B".rjust(10)
                    elif size < 1024 * 1024:
                        size_str = f"{size // 1024}KB".rjust(10)
                    else:
                        size_str = f"{size // (1024 * 1024)}MB".rjust(10)

                    output_lines.append(f"{size_str}  {entry.name}")
                except (OSError, PermissionError):
                    output_lines.append(f"{'???'.rjust(10)}  {entry.name}")
        else:
            # Simple format
            for entry in entries:
                prefix = "[DIR] " if entry.is_dir() else "      "
                output_lines.append(f"{prefix}{entry.name}")

        return "\n".join(output_lines)

    except PermissionError:
        return f"Error: Permission denied accessing: {target_dir}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


# Export all terminal tools
TERMINAL_TOOLS = [
    run_terminal_command,
    change_directory,
    get_current_directory,
    list_directory,
]
