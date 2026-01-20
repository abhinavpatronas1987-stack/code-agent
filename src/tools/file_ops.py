"""File operations tools for reading, writing, and editing files."""

import os
import difflib
from pathlib import Path
from typing import Optional

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir
from src.core.tool_logger import log_tool_call


def resolve_path(path: str) -> Path:
    """Resolve a path relative to working directory."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (get_working_dir() / p).resolve()
    return p


@tool(name="read_file")
def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
) -> str:
    """
    Read the contents of a file.

    Use this tool to view file contents. For large files, you can specify
    line ranges to read specific portions.

    Args:
        file_path: Path to the file to read (absolute or relative to working dir)
        start_line: Optional starting line number (1-indexed). Alias: line_start
        end_line: Optional ending line number (inclusive). Alias: line_end
        line_start: Alias for start_line (for compatibility)
        line_end: Alias for end_line (for compatibility)

    Returns:
        File contents with line numbers, or an error message.

    Examples:
        read_file("src/main.py")
        read_file("config.json", start_line=1, end_line=50)
    """
    # Log the tool call
    log_tool_call("read_file", file_path=file_path)

    # Handle parameter aliases - prefer start_line/end_line, fall back to line_start/line_end
    if start_line is None and line_start is not None:
        start_line = line_start
    if end_line is None and line_end is not None:
        end_line = line_end
    path = resolve_path(file_path)

    if not path.exists():
        return f"Error: File does not exist: {path}"

    if not path.is_file():
        return f"Error: Path is not a file: {path}"

    try:
        # Try to detect encoding
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None

        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return f"Error: Could not decode file with supported encodings: {path}"

        lines = content.splitlines()
        total_lines = len(lines)

        # Apply line range if specified
        if start_line is not None or end_line is not None:
            start = (start_line or 1) - 1  # Convert to 0-indexed
            end = end_line or total_lines

            # Validate range
            start = max(0, min(start, total_lines))
            end = max(start, min(end, total_lines))

            lines = lines[start:end]
            line_offset = start + 1
        else:
            line_offset = 1

        # Format with line numbers
        output_lines = [f"File: {path}", f"Lines: {total_lines} total", ""]

        # Limit output for very large files
        max_display_lines = 500
        if len(lines) > max_display_lines:
            lines = lines[:max_display_lines]
            output_lines.append(f"(Showing first {max_display_lines} lines)")
            output_lines.append("")

        # Add line numbers
        line_num_width = len(str(line_offset + len(lines)))
        for i, line in enumerate(lines):
            line_num = str(line_offset + i).rjust(line_num_width)
            output_lines.append(f"{line_num} | {line}")

        return "\n".join(output_lines)

    except PermissionError:
        return f"Error: Permission denied reading file: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool(name="write_file")
def write_file(
    file_path: str,
    content: str,
    create_dirs: bool = True,
) -> str:
    """
    Write content to a file, creating it if it doesn't exist.

    WARNING: This will overwrite existing file contents!

    Args:
        file_path: Path to the file to write
        content: The content to write to the file
        create_dirs: Whether to create parent directories if they don't exist

    Returns:
        Success message or error.

    Examples:
        write_file("output.txt", "Hello, World!")
        write_file("src/new_module.py", "def hello():\\n    print('Hi')")
    """
    # Log the tool call
    log_tool_call("write_file", file_path=file_path)

    path = resolve_path(file_path)

    try:
        # Create parent directories if needed
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists for reporting
        existed = path.exists()

        # Write the file
        path.write_text(content, encoding="utf-8")

        if existed:
            return f"Successfully overwrote file: {path}"
        else:
            return f"Successfully created file: {path}"

    except PermissionError:
        return f"Error: Permission denied writing to: {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool(name="edit_file")
def edit_file(
    file_path: str,
    old_content: str,
    new_content: str,
    occurrence: int = 1,
) -> str:
    """
    Edit a file by replacing specific content.

    This tool finds the exact `old_content` string in the file and replaces
    it with `new_content`. Use this for precise, surgical edits.

    Args:
        file_path: Path to the file to edit
        old_content: The exact text to find and replace
        new_content: The text to replace it with
        occurrence: Which occurrence to replace (1 = first, -1 = all)

    Returns:
        Success message with diff preview, or error.

    Examples:
        edit_file("main.py", "def old_func():", "def new_func():")
        edit_file("config.json", '"debug": false', '"debug": true')
    """
    # Log the tool call
    log_tool_call("edit_file", file_path=file_path)

    path = resolve_path(file_path)

    if not path.exists():
        return f"Error: File does not exist: {path}"

    try:
        original = path.read_text(encoding="utf-8")

        # Count occurrences
        count = original.count(old_content)

        if count == 0:
            return f"Error: Could not find the specified content in {path}\n\nSearched for:\n{old_content}"

        # Perform replacement
        if occurrence == -1:
            # Replace all occurrences
            modified = original.replace(old_content, new_content)
            replaced_count = count
        else:
            # Replace specific occurrence
            if occurrence > count:
                return f"Error: Only {count} occurrence(s) found, cannot replace occurrence {occurrence}"

            # Find the nth occurrence
            pos = -1
            for _ in range(occurrence):
                pos = original.find(old_content, pos + 1)

            # Replace at that position
            modified = (
                original[:pos] +
                new_content +
                original[pos + len(old_content):]
            )
            replaced_count = 1

        # Generate diff
        diff = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
            lineterm="",
        ))

        # Write the modified content
        path.write_text(modified, encoding="utf-8")

        # Format output
        output = [
            f"Successfully edited {path}",
            f"Replaced {replaced_count} occurrence(s)",
            "",
            "=== DIFF ===",
        ]
        output.extend(diff[:50])  # Limit diff output

        if len(diff) > 50:
            output.append(f"... ({len(diff) - 50} more lines)")

        return "\n".join(output)

    except PermissionError:
        return f"Error: Permission denied editing: {path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


@tool(name="create_file")
def create_file(
    file_path: str,
    content: str = "",
    overwrite: bool = False,
) -> str:
    """
    Create a new file.

    Args:
        file_path: Path for the new file
        content: Initial content for the file (optional)
        overwrite: Whether to overwrite if file exists (default: False)

    Returns:
        Success message or error.

    Examples:
        create_file("src/new_module.py")
        create_file("README.md", "# My Project\\n\\nDescription here.")
    """
    # Log the tool call
    log_tool_call("create_file", file_path=file_path)

    path = resolve_path(file_path)

    if path.exists() and not overwrite:
        return f"Error: File already exists: {path}\nUse overwrite=True to replace it."

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully created file: {path}"

    except PermissionError:
        return f"Error: Permission denied creating: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


@tool(name="delete_file")
def delete_file(file_path: str) -> str:
    """
    Delete a file.

    WARNING: This permanently deletes the file!

    Args:
        file_path: Path to the file to delete

    Returns:
        Success message or error.
    """
    # Log the tool call
    log_tool_call("delete_file", file_path=file_path)

    path = resolve_path(file_path)

    if not path.exists():
        return f"Error: File does not exist: {path}"

    if not path.is_file():
        return f"Error: Path is not a file: {path}"

    try:
        path.unlink()
        return f"Successfully deleted file: {path}"

    except PermissionError:
        return f"Error: Permission denied deleting: {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


@tool(name="move_file")
def move_file(source: str, destination: str) -> str:
    """
    Move or rename a file.

    Args:
        source: Path to the file to move
        destination: New path for the file

    Returns:
        Success message or error.

    Examples:
        move_file("old_name.py", "new_name.py")
        move_file("temp/file.txt", "final/file.txt")
    """
    # Log the tool call
    log_tool_call("move_file", source=source, destination=destination)

    src_path = resolve_path(source)
    dst_path = resolve_path(destination)

    if not src_path.exists():
        return f"Error: Source file does not exist: {src_path}"

    if dst_path.exists():
        return f"Error: Destination already exists: {dst_path}"

    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)
        return f"Successfully moved {src_path} to {dst_path}"

    except PermissionError:
        return f"Error: Permission denied"
    except Exception as e:
        return f"Error moving file: {str(e)}"


@tool(name="copy_file")
def copy_file(source: str, destination: str) -> str:
    """
    Copy a file.

    Args:
        source: Path to the file to copy
        destination: Path for the copy

    Returns:
        Success message or error.
    """
    # Log the tool call
    log_tool_call("copy_file", source=source, destination=destination)

    import shutil

    src_path = resolve_path(source)
    dst_path = resolve_path(destination)

    if not src_path.exists():
        return f"Error: Source file does not exist: {src_path}"

    try:
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        return f"Successfully copied {src_path} to {dst_path}"

    except PermissionError:
        return f"Error: Permission denied"
    except Exception as e:
        return f"Error copying file: {str(e)}"


# Export all file tools
FILE_TOOLS = [
    read_file,
    write_file,
    edit_file,
    create_file,
    delete_file,
    move_file,
    copy_file,
]
