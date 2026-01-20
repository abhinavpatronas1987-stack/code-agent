"""Context attachment system for @file, @folder mentions."""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir
from src.tools.file_ops import read_file
from src.tools.code_search import get_file_structure


@dataclass
class Attachment:
    """Represents an attached context item."""
    type: str  # "file", "folder", "url", "selection"
    path: str
    content: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class ContextManager:
    """Manages context attachments for the conversation."""

    def __init__(self):
        """Initialize context manager."""
        self._attachments: list[Attachment] = []

    def clear(self) -> None:
        """Clear all attachments."""
        self._attachments = []

    def add_file(
        self,
        file_path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
    ) -> str:
        """Add a file to the context."""
        path = Path(file_path)
        if not path.is_absolute():
            path = get_working_dir() / path

        if not path.exists():
            return f"Error: File not found: {path}"

        if not path.is_file():
            return f"Error: Not a file: {path}"

        try:
            content = path.read_text(encoding="utf-8")

            # Handle line ranges
            if line_start is not None or line_end is not None:
                lines = content.split("\n")
                start = (line_start or 1) - 1
                end = line_end or len(lines)
                content = "\n".join(lines[start:end])

            attachment = Attachment(
                type="file",
                path=str(path),
                content=content,
                line_start=line_start,
                line_end=line_end,
            )
            self._attachments.append(attachment)

            line_info = ""
            if line_start or line_end:
                line_info = f" (lines {line_start or 1}-{line_end or 'end'})"

            return f"Attached: {path.name}{line_info}"

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def add_folder(self, folder_path: str, max_depth: int = 3) -> str:
        """Add folder structure to the context."""
        path = Path(folder_path)
        if not path.is_absolute():
            path = get_working_dir() / path

        if not path.exists():
            return f"Error: Folder not found: {path}"

        if not path.is_dir():
            return f"Error: Not a folder: {path}"

        # Get folder structure
        structure = self._get_folder_structure(path, max_depth)

        attachment = Attachment(
            type="folder",
            path=str(path),
            content=structure,
        )
        self._attachments.append(attachment)

        return f"Attached folder: {path.name}/"

    def _get_folder_structure(self, path: Path, max_depth: int, prefix: str = "") -> str:
        """Get folder structure as text."""
        lines = []

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            dirs = [i for i in items if i.is_dir() and not i.name.startswith(".")]
            files = [i for i in items if i.is_file() and not i.name.startswith(".")]

            for d in dirs:
                lines.append(f"{prefix}{d.name}/")
                if max_depth > 1:
                    lines.append(self._get_folder_structure(d, max_depth - 1, prefix + "  "))

            for f in files:
                size = f.stat().st_size
                size_str = self._format_size(size)
                lines.append(f"{prefix}{f.name} ({size_str})")

        except PermissionError:
            lines.append(f"{prefix}(permission denied)")

        return "\n".join(lines)

    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def get_context(self) -> str:
        """Get all attached context as formatted text."""
        if not self._attachments:
            return ""

        parts = ["## Attached Context\n"]

        for att in self._attachments:
            if att.type == "file":
                line_info = ""
                if att.line_start or att.line_end:
                    line_info = f" (lines {att.line_start or 1}-{att.line_end or 'end'})"
                parts.append(f"### File: {Path(att.path).name}{line_info}")
                parts.append(f"```\n{att.content}\n```\n")

            elif att.type == "folder":
                parts.append(f"### Folder: {Path(att.path).name}/")
                parts.append(f"```\n{att.content}\n```\n")

        return "\n".join(parts)

    def get_attachments(self) -> list[Attachment]:
        """Get all attachments."""
        return self._attachments.copy()


# Global context manager
_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Get or create the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def parse_mentions(text: str) -> list[dict]:
    """
    Parse @file and @folder mentions from text.

    Patterns:
        @file:path/to/file.py
        @file:path/to/file.py:10-20  (line range)
        @folder:path/to/folder
        @folder:src/
    """
    mentions = []

    # Match @file:path or @file:path:line-line
    file_pattern = r"@file:([^\s:]+)(?::(\d+)-(\d+))?"
    for match in re.finditer(file_pattern, text):
        mentions.append({
            "type": "file",
            "path": match.group(1),
            "line_start": int(match.group(2)) if match.group(2) else None,
            "line_end": int(match.group(3)) if match.group(3) else None,
        })

    # Match @folder:path
    folder_pattern = r"@folder:([^\s]+)"
    for match in re.finditer(folder_pattern, text):
        mentions.append({
            "type": "folder",
            "path": match.group(1),
        })

    return mentions


@tool
def attach_file(
    file_path: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
) -> str:
    """
    Attach a file to the conversation context.

    The file contents will be available for reference in subsequent messages.

    Args:
        file_path: Path to the file to attach
        line_start: Optional start line number
        line_end: Optional end line number

    Returns:
        Confirmation message.

    Examples:
        attach_file(file_path="src/main.py")
        attach_file(file_path="config.json", line_start=1, line_end=50)
    """
    manager = get_context_manager()
    return manager.add_file(file_path, line_start, line_end)


@tool
def attach_folder(
    folder_path: str,
    max_depth: int = 3,
) -> str:
    """
    Attach a folder structure to the conversation context.

    Shows the folder tree without file contents.

    Args:
        folder_path: Path to the folder
        max_depth: How deep to show the structure (default 3)

    Returns:
        Confirmation message.

    Examples:
        attach_folder(folder_path="src")
        attach_folder(folder_path=".", max_depth=2)
    """
    manager = get_context_manager()
    return manager.add_folder(folder_path, max_depth)


@tool
def show_context() -> str:
    """
    Show all currently attached context.

    Returns:
        Formatted list of all attachments.

    Examples:
        show_context()
    """
    manager = get_context_manager()
    context = manager.get_context()

    if not context:
        return "No context attached. Use attach_file or attach_folder to add context."

    return context


@tool
def clear_context() -> str:
    """
    Clear all attached context.

    Returns:
        Confirmation message.

    Examples:
        clear_context()
    """
    manager = get_context_manager()
    count = len(manager.get_attachments())
    manager.clear()
    return f"Cleared {count} attachment(s)."


@tool
def attach_selection(
    file_path: str,
    start_line: int,
    end_line: int,
    description: str = "",
) -> str:
    """
    Attach a specific selection from a file.

    Args:
        file_path: Path to the file
        start_line: Starting line number
        end_line: Ending line number
        description: Optional description of the selection

    Returns:
        Confirmation with the selected content.

    Examples:
        attach_selection(file_path="main.py", start_line=10, end_line=25, description="The main function")
    """
    manager = get_context_manager()
    result = manager.add_file(file_path, start_line, end_line)

    if result.startswith("Error"):
        return result

    # Get the last attachment to show the content
    attachments = manager.get_attachments()
    if attachments:
        last = attachments[-1]
        preview = last.content[:200] + "..." if len(last.content) > 200 else last.content
        desc = f" ({description})" if description else ""
        return f"{result}{desc}\n\n**Preview**:\n```\n{preview}\n```"

    return result


@tool
def attach_files_by_pattern(pattern: str) -> str:
    """
    Attach multiple files matching a glob pattern.

    Args:
        pattern: Glob pattern like "*.py" or "src/**/*.ts"

    Returns:
        List of attached files.

    Examples:
        attach_files_by_pattern(pattern="*.py")
        attach_files_by_pattern(pattern="src/**/*.js")
    """
    from pathlib import Path

    working_dir = get_working_dir()
    manager = get_context_manager()

    files = list(working_dir.glob(pattern))

    if not files:
        return f"No files found matching pattern: {pattern}"

    # Limit to prevent context explosion
    max_files = 10
    if len(files) > max_files:
        files = files[:max_files]
        truncated = True
    else:
        truncated = False

    results = []
    for f in files:
        if f.is_file():
            result = manager.add_file(str(f))
            results.append(f"  - {f.name}")

    output = [f"Attached {len(results)} file(s):"]
    output.extend(results)

    if truncated:
        output.append(f"\n(Limited to {max_files} files. Use more specific patterns.)")

    return "\n".join(output)


# Export context tools
CONTEXT_TOOLS = [
    attach_file,
    attach_folder,
    attach_selection,
    attach_files_by_pattern,
    show_context,
    clear_context,
]
