"""Code search and analysis tools."""

import os
import re
import fnmatch
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir


# Common patterns to ignore
DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    ".env",
    "*.egg-info",
    ".idea",
    ".vscode",
    "*.min.js",
    "*.min.css",
    "*.map",
    "coverage",
    ".coverage",
    "htmlcov",
]


def should_ignore(path: Path, ignore_patterns: list[str]) -> bool:
    """Check if path should be ignored."""
    name = path.name
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def is_binary_file(file_path: Path) -> bool:
    """Check if file is binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return True
    except Exception:
        return True
    return False


@tool(name="search_files")
def search_files(
    pattern: str,
    directory: Optional[str] = None,
    file_pattern: Optional[str] = None,
    max_results: int = 50,
) -> str:
    """
    Search for text pattern in files using regex.

    Similar to grep/ripgrep - searches file contents for matching text.

    Args:
        pattern: Regex pattern to search for (e.g., "def.*test", "import os")
        directory: Directory to search in (defaults to working directory)
        file_pattern: Glob pattern to filter files (e.g., "*.py", "*.ts")
        max_results: Maximum number of results to return

    Returns:
        Matching lines with file paths and line numbers.

    Examples:
        search_files("def test_")  # Find all test functions
        search_files("import.*from", file_pattern="*.py")
        search_files("TODO|FIXME")  # Find all TODOs
    """
    search_dir = Path(directory) if directory else get_working_dir()
    if not search_dir.is_absolute():
        search_dir = (get_working_dir() / search_dir).resolve()

    if not search_dir.exists():
        return f"Error: Directory does not exist: {search_dir}"

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    results = []
    files_searched = 0
    files_matched = 0

    for root, dirs, files in os.walk(search_dir):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(Path(d), DEFAULT_IGNORE_PATTERNS)]

        for filename in files:
            if should_ignore(Path(filename), DEFAULT_IGNORE_PATTERNS):
                continue

            if file_pattern and not fnmatch.fnmatch(filename, file_pattern):
                continue

            file_path = Path(root) / filename

            if is_binary_file(file_path):
                continue

            files_searched += 1

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        file_matches.append((line_num, line.strip()[:200]))

                if file_matches:
                    files_matched += 1
                    rel_path = file_path.relative_to(search_dir)
                    for line_num, line in file_matches:
                        results.append(f"{rel_path}:{line_num}: {line}")
                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break

            except Exception:
                continue

        if len(results) >= max_results:
            break

    # Format output
    output = [
        f"Search: '{pattern}' in {search_dir}",
        f"Files searched: {files_searched}, Files matched: {files_matched}",
        f"Results: {len(results)}" + (f" (limited to {max_results})" if len(results) >= max_results else ""),
        "",
    ]

    if results:
        output.extend(results)
    else:
        output.append("No matches found.")

    return "\n".join(output)


@tool(name="find_files")
def find_files(
    pattern: str,
    directory: Optional[str] = None,
    max_results: int = 100,
) -> str:
    """
    Find files by name pattern.

    Similar to the `find` command - searches for files matching a glob pattern.

    Args:
        pattern: Glob pattern for file names (e.g., "*.py", "test_*.js", "**/*.md")
        directory: Directory to search in (defaults to working directory)
        max_results: Maximum number of results

    Returns:
        List of matching file paths.

    Examples:
        find_files("*.py")  # All Python files
        find_files("test_*")  # All test files
        find_files("*.md")  # All markdown files
    """
    search_dir = Path(directory) if directory else get_working_dir()
    if not search_dir.is_absolute():
        search_dir = (get_working_dir() / search_dir).resolve()

    if not search_dir.exists():
        return f"Error: Directory does not exist: {search_dir}"

    results = []

    # Use recursive glob if ** in pattern, otherwise walk
    if "**" in pattern:
        for file_path in search_dir.glob(pattern):
            if file_path.is_file():
                if not any(should_ignore(Path(p), DEFAULT_IGNORE_PATTERNS) for p in file_path.parts):
                    results.append(file_path.relative_to(search_dir))
                    if len(results) >= max_results:
                        break
    else:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if not should_ignore(Path(d), DEFAULT_IGNORE_PATTERNS)]

            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    file_path = Path(root) / filename
                    results.append(file_path.relative_to(search_dir))
                    if len(results) >= max_results:
                        break

            if len(results) >= max_results:
                break

    # Format output
    output = [
        f"Find: '{pattern}' in {search_dir}",
        f"Found: {len(results)} files" + (f" (limited to {max_results})" if len(results) >= max_results else ""),
        "",
    ]

    if results:
        for path in sorted(results):
            output.append(str(path))
    else:
        output.append("No files found.")

    return "\n".join(output)


@tool(name="get_file_structure")
def get_file_structure(
    directory: Optional[str] = None,
    max_depth: int = 3,
    show_files: bool = True,
) -> str:
    """
    Get directory structure as a tree.

    Shows the hierarchical structure of files and directories.

    Args:
        directory: Directory to analyze (defaults to working directory)
        max_depth: Maximum depth to traverse
        show_files: Whether to include files (not just directories)

    Returns:
        Tree-like representation of the directory structure.

    Examples:
        get_file_structure()
        get_file_structure("./src", max_depth=2)
    """
    search_dir = Path(directory) if directory else get_working_dir()
    if not search_dir.is_absolute():
        search_dir = (get_working_dir() / search_dir).resolve()

    if not search_dir.exists():
        return f"Error: Directory does not exist: {search_dir}"

    def build_tree(path: Path, prefix: str = "", depth: int = 0) -> list[str]:
        if depth > max_depth:
            return []

        lines = []
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            entries = [e for e in entries if not should_ignore(e, DEFAULT_IGNORE_PATTERNS)]

            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "

                if entry.is_dir():
                    lines.append(f"{prefix}{connector}{entry.name}/")
                    lines.extend(build_tree(entry, prefix + extension, depth + 1))
                elif show_files:
                    lines.append(f"{prefix}{connector}{entry.name}")

        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")

        return lines

    tree_lines = [f"{search_dir.name}/"]
    tree_lines.extend(build_tree(search_dir))

    return "\n".join(tree_lines)


@tool(name="get_file_info")
def get_file_info(file_path: str) -> str:
    """
    Get detailed information about a file.

    Args:
        file_path: Path to the file

    Returns:
        File metadata including size, type, modification time.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = (get_working_dir() / path).resolve()

    if not path.exists():
        return f"Error: File does not exist: {path}"

    try:
        stat = path.stat()

        # Detect file type by extension
        ext = path.suffix.lower()
        file_types = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript (React)",
            ".jsx": "JavaScript (React)",
            ".java": "Java",
            ".rs": "Rust",
            ".go": "Go",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++ Header",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".md": "Markdown",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".xml": "XML",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL",
            ".sh": "Shell Script",
            ".bash": "Bash Script",
            ".ps1": "PowerShell",
        }
        file_type = file_types.get(ext, f"Unknown ({ext})" if ext else "No extension")

        # Format size
        size = stat.st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        # Count lines if text file
        line_count = "N/A"
        if not is_binary_file(path):
            try:
                line_count = sum(1 for _ in open(path, "r", encoding="utf-8", errors="ignore"))
            except Exception:
                pass

        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        info = [
            f"File: {path}",
            f"Type: {file_type}",
            f"Size: {size_str}",
            f"Lines: {line_count}",
            f"Modified: {mtime}",
        ]

        return "\n".join(info)

    except Exception as e:
        return f"Error getting file info: {str(e)}"


# Export all search tools
SEARCH_TOOLS = [
    search_files,
    find_files,
    get_file_structure,
    get_file_info,
]
