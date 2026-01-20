"""Auto-fix build tools - Compile, build, and automatically fix errors."""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum

from agno.tools.decorator import tool

from src.core.visual_output import print_build_result, print_test_result, print_task_progress


class ProjectType(Enum):
    """Supported project types."""
    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    UNKNOWN = "unknown"


@dataclass
class BuildResult:
    """Result of a build attempt."""
    success: bool
    output: str
    errors: List[str]
    warnings: List[str]
    fixed_files: List[str]


def detect_project_type(path: Path) -> ProjectType:
    """Detect the project type based on files present."""
    path = Path(path)

    # Check for project files
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists() or (path / "requirements.txt").exists():
        return ProjectType.PYTHON
    if (path / "package.json").exists():
        return ProjectType.NODEJS
    if (path / "Cargo.toml").exists():
        return ProjectType.RUST
    if (path / "go.mod").exists():
        return ProjectType.GO
    if (path / "pom.xml").exists() or (path / "build.gradle").exists():
        return ProjectType.JAVA
    if list(path.glob("*.csproj")) or list(path.glob("*.sln")):
        return ProjectType.CSHARP
    if (path / "CMakeLists.txt").exists() or (path / "Makefile").exists():
        return ProjectType.CPP

    # Check by file extensions
    py_files = list(path.glob("**/*.py"))
    js_files = list(path.glob("**/*.js")) + list(path.glob("**/*.ts"))
    rs_files = list(path.glob("**/*.rs"))
    go_files = list(path.glob("**/*.go"))

    if py_files:
        return ProjectType.PYTHON
    if js_files:
        return ProjectType.NODEJS
    if rs_files:
        return ProjectType.RUST
    if go_files:
        return ProjectType.GO

    return ProjectType.UNKNOWN


def get_build_commands(project_type: ProjectType) -> Dict[str, str]:
    """Get build and test commands for a project type."""
    commands = {
        ProjectType.PYTHON: {
            "build": "python -m py_compile",
            "test": "pytest",
            "lint": "python -m flake8",
            "typecheck": "python -m mypy",
            "install": "pip install -r requirements.txt",
        },
        ProjectType.NODEJS: {
            "build": "npm run build",
            "test": "npm test",
            "lint": "npm run lint",
            "install": "npm install",
        },
        ProjectType.RUST: {
            "build": "cargo build",
            "test": "cargo test",
            "lint": "cargo clippy",
            "check": "cargo check",
        },
        ProjectType.GO: {
            "build": "go build ./...",
            "test": "go test ./...",
            "lint": "go vet ./...",
        },
        ProjectType.JAVA: {
            "build": "mvn compile",
            "test": "mvn test",
            "package": "mvn package",
        },
        ProjectType.CSHARP: {
            "build": "dotnet build",
            "test": "dotnet test",
            "run": "dotnet run",
        },
        ProjectType.CPP: {
            "build": "make",
            "clean": "make clean",
        },
    }
    return commands.get(project_type, {})


def run_command(command: str, cwd: Optional[Path] = None, timeout: int = 120) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)


def parse_python_error(error_text: str) -> Dict:
    """Parse Python error messages."""
    import re

    result = {
        "type": "unknown",
        "file": None,
        "line": None,
        "message": error_text,
        "suggestion": None,
    }

    # Match Python traceback
    file_match = re.search(r'File "([^"]+)", line (\d+)', error_text)
    if file_match:
        result["file"] = file_match.group(1)
        result["line"] = int(file_match.group(2))

    # Match error type
    error_match = re.search(r'(\w+Error): (.+)', error_text)
    if error_match:
        result["type"] = error_match.group(1)
        result["message"] = error_match.group(2)

    # Common fix suggestions
    if "NameError" in error_text:
        result["suggestion"] = "Check variable/function name spelling or add missing import"
    elif "ImportError" in error_text or "ModuleNotFoundError" in error_text:
        result["suggestion"] = "Install missing package with pip or fix import path"
    elif "SyntaxError" in error_text:
        result["suggestion"] = "Fix syntax error - check for missing colons, brackets, or quotes"
    elif "TypeError" in error_text:
        result["suggestion"] = "Check argument types and function signatures"
    elif "IndentationError" in error_text:
        result["suggestion"] = "Fix indentation - use consistent spaces or tabs"
    elif "AttributeError" in error_text:
        result["suggestion"] = "Check if object has the attribute or method"
    elif "KeyError" in error_text:
        result["suggestion"] = "Check dictionary key exists or use .get() method"
    elif "IndexError" in error_text:
        result["suggestion"] = "Check list/array bounds before accessing"
    elif "ValueError" in error_text:
        result["suggestion"] = "Check input value is valid for the operation"
    elif "FileNotFoundError" in error_text:
        result["suggestion"] = "Check file path exists and is correct"

    return result


def parse_nodejs_error(error_text: str) -> Dict:
    """Parse Node.js/npm error messages."""
    import re

    result = {
        "type": "unknown",
        "file": None,
        "line": None,
        "message": error_text,
        "suggestion": None,
    }

    # Match file:line:column format
    file_match = re.search(r'([^\s:]+):(\d+):(\d+)', error_text)
    if file_match:
        result["file"] = file_match.group(1)
        result["line"] = int(file_match.group(2))

    # Common suggestions
    if "Cannot find module" in error_text:
        result["type"] = "ModuleNotFound"
        result["suggestion"] = "Run 'npm install' or install the specific package"
    elif "SyntaxError" in error_text:
        result["type"] = "SyntaxError"
        result["suggestion"] = "Fix JavaScript/TypeScript syntax error"
    elif "TypeError" in error_text:
        result["type"] = "TypeError"
        result["suggestion"] = "Check types and null/undefined values"
    elif "ENOENT" in error_text:
        result["type"] = "FileNotFound"
        result["suggestion"] = "Check file or directory path exists"

    return result


def parse_rust_error(error_text: str) -> Dict:
    """Parse Rust/Cargo error messages."""
    import re

    result = {
        "type": "unknown",
        "file": None,
        "line": None,
        "message": error_text,
        "suggestion": None,
    }

    # Match Rust error format: --> src/main.rs:10:5
    file_match = re.search(r'--> ([^:]+):(\d+):(\d+)', error_text)
    if file_match:
        result["file"] = file_match.group(1)
        result["line"] = int(file_match.group(2))

    # Match error code: error[E0425]
    error_match = re.search(r'error\[E(\d+)\]', error_text)
    if error_match:
        result["type"] = f"E{error_match.group(1)}"

    # Rust compiler often provides suggestions
    help_match = re.search(r'help: (.+)', error_text)
    if help_match:
        result["suggestion"] = help_match.group(1)

    return result


def parse_error(error_text: str, project_type: ProjectType) -> Dict:
    """Parse error based on project type."""
    if project_type == ProjectType.PYTHON:
        return parse_python_error(error_text)
    elif project_type == ProjectType.NODEJS:
        return parse_nodejs_error(error_text)
    elif project_type == ProjectType.RUST:
        return parse_rust_error(error_text)
    else:
        return {
            "type": "unknown",
            "file": None,
            "line": None,
            "message": error_text,
            "suggestion": "Check the error message for details",
        }


@tool(name="detect_project")
def detect_project(path: str = ".") -> str:
    """
    Detect the project type in a directory.

    Analyzes the directory to determine if it's a Python, Node.js, Rust,
    Go, Java, C#, or C++ project based on configuration files and source files.

    Args:
        path: Directory to analyze (default: current directory)

    Returns:
        Project type and available build commands.

    Examples:
        detect_project(".")
        detect_project("D:/projects/my_app")
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)
    commands = get_build_commands(project_type)

    output = [
        f"Project Path: {project_path}",
        f"Project Type: {project_type.value}",
        "",
        "Available Commands:",
    ]

    if commands:
        for name, cmd in commands.items():
            output.append(f"  - {name}: {cmd}")
    else:
        output.append("  No predefined commands for this project type")

    return "\n".join(output)


@tool(name="build_project")
def build_project(
    path: str = ".",
    command: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """
    Build a project and return the results.

    Automatically detects project type and runs the appropriate build command.
    You can also specify a custom build command.

    Args:
        path: Project directory (default: current directory)
        command: Custom build command (optional, auto-detected if not provided)
        timeout: Command timeout in seconds (default: 120)

    Returns:
        Build output including any errors or warnings.

    Examples:
        build_project(".")
        build_project("D:/projects/my_app")
        build_project(".", command="npm run build")
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)

    # Determine build command
    if command:
        build_cmd = command
    else:
        commands = get_build_commands(project_type)
        build_cmd = commands.get("build")

        if not build_cmd:
            return f"Error: No build command defined for project type: {project_type.value}\nPlease specify a custom command."

    output = [
        f"Project: {project_path}",
        f"Type: {project_type.value}",
        f"Command: {build_cmd}",
        "",
        "=== BUILD OUTPUT ===",
    ]

    exit_code, stdout, stderr = run_command(build_cmd, cwd=project_path, timeout=timeout)

    if stdout:
        output.append(stdout)
    if stderr:
        output.append(stderr)

    output.append("")
    if exit_code == 0:
        output.append("=== BUILD SUCCESSFUL ===")
    else:
        output.append(f"=== BUILD FAILED (exit code: {exit_code}) ===")

        # Parse and explain errors
        error_info = parse_error(stderr or stdout, project_type)
        if error_info["suggestion"]:
            output.append("")
            output.append("=== ERROR ANALYSIS ===")
            output.append(f"Error Type: {error_info['type']}")
            if error_info["file"]:
                output.append(f"File: {error_info['file']}")
            if error_info["line"]:
                output.append(f"Line: {error_info['line']}")
            output.append(f"Suggestion: {error_info['suggestion']}")

    return "\n".join(output)


@tool(name="test_project")
def test_project(
    path: str = ".",
    command: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Run tests for a project.

    Automatically detects project type and runs the appropriate test command.

    Args:
        path: Project directory (default: current directory)
        command: Custom test command (optional, auto-detected if not provided)
        timeout: Command timeout in seconds (default: 300)

    Returns:
        Test output including pass/fail status.

    Examples:
        test_project(".")
        test_project("D:/projects/my_app", command="pytest -v")
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)

    # Determine test command
    if command:
        test_cmd = command
    else:
        commands = get_build_commands(project_type)
        test_cmd = commands.get("test")

        if not test_cmd:
            return f"Error: No test command defined for project type: {project_type.value}\nPlease specify a custom command."

    output = [
        f"Project: {project_path}",
        f"Type: {project_type.value}",
        f"Command: {test_cmd}",
        "",
        "=== TEST OUTPUT ===",
    ]

    exit_code, stdout, stderr = run_command(test_cmd, cwd=project_path, timeout=timeout)

    if stdout:
        output.append(stdout)
    if stderr:
        output.append(stderr)

    output.append("")
    if exit_code == 0:
        output.append("=== ALL TESTS PASSED ===")
    else:
        output.append(f"=== TESTS FAILED (exit code: {exit_code}) ===")

    return "\n".join(output)


@tool(name="build_and_fix")
def build_and_fix(
    path: str = ".",
    command: Optional[str] = None,
    max_attempts: int = 3,
    timeout: int = 120,
) -> str:
    """
    Build a project and automatically attempt to fix errors.

    This tool will:
    1. Detect project type
    2. Run the build command
    3. If build fails, analyze the error
    4. Suggest fixes (you can then apply them)
    5. Repeat until success or max attempts reached

    Args:
        path: Project directory (default: current directory)
        command: Custom build command (optional)
        max_attempts: Maximum fix attempts (default: 3)
        timeout: Command timeout in seconds (default: 120)

    Returns:
        Build results with error analysis and fix suggestions.

    Examples:
        build_and_fix(".")
        build_and_fix("D:/projects/my_app", max_attempts=5)
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)
    commands = get_build_commands(project_type)

    # Determine build command
    if command:
        build_cmd = command
    else:
        build_cmd = commands.get("build")
        if not build_cmd:
            return f"Error: No build command for {project_type.value}. Specify a custom command."

    output = [
        "=== AUTO-FIX BUILD ===",
        f"Project: {project_path}",
        f"Type: {project_type.value}",
        f"Command: {build_cmd}",
        f"Max Attempts: {max_attempts}",
        "",
    ]

    for attempt in range(1, max_attempts + 1):
        output.append(f"--- Attempt {attempt}/{max_attempts} ---")

        exit_code, stdout, stderr = run_command(build_cmd, cwd=project_path, timeout=timeout)

        if exit_code == 0:
            output.append("")
            output.append("=== BUILD SUCCESSFUL! ===")
            if stdout:
                output.append("")
                output.append("Output:")
                output.append(stdout[:500] + "..." if len(stdout) > 500 else stdout)
            return "\n".join(output)

        # Build failed - analyze error
        error_text = stderr or stdout
        error_info = parse_error(error_text, project_type)

        output.append(f"Build failed with exit code: {exit_code}")
        output.append("")
        output.append("Error Analysis:")
        output.append(f"  Type: {error_info['type']}")
        if error_info["file"]:
            output.append(f"  File: {error_info['file']}")
        if error_info["line"]:
            output.append(f"  Line: {error_info['line']}")
        output.append(f"  Message: {error_info['message'][:200]}...")
        if error_info["suggestion"]:
            output.append(f"  Suggestion: {error_info['suggestion']}")
        output.append("")

        # For now, we report the error - actual fixing would require code modification
        # which should be done by the LLM using edit_file tool
        if attempt < max_attempts:
            output.append("To fix this error, use the edit_file tool to make the suggested changes.")
            output.append("Then run build_and_fix again.")
            break

    output.append("")
    output.append("=== BUILD FAILED ===")
    output.append("")
    output.append("Recommended Actions:")
    output.append("1. Read the error file with: read_file(\"<file_path>\")")
    output.append("2. Apply the fix with: edit_file(\"<file_path>\", \"<old>\", \"<new>\")")
    output.append("3. Re-run build with: build_and_fix(\"<path>\")")

    return "\n".join(output)


@tool(name="lint_project")
def lint_project(
    path: str = ".",
    command: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """
    Run linter/code checker on a project.

    Checks code for style issues, potential bugs, and best practices.

    Args:
        path: Project directory (default: current directory)
        command: Custom lint command (optional)
        timeout: Command timeout in seconds (default: 120)

    Returns:
        Lint output with issues found.

    Examples:
        lint_project(".")
        lint_project(".", command="flake8 src/")
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)
    commands = get_build_commands(project_type)

    if command:
        lint_cmd = command
    else:
        lint_cmd = commands.get("lint")
        if not lint_cmd:
            # Fallback lint commands
            if project_type == ProjectType.PYTHON:
                lint_cmd = "python -m flake8 . --max-line-length=120"
            else:
                return f"No lint command for {project_type.value}. Specify a custom command."

    output = [
        f"Project: {project_path}",
        f"Type: {project_type.value}",
        f"Command: {lint_cmd}",
        "",
        "=== LINT OUTPUT ===",
    ]

    exit_code, stdout, stderr = run_command(lint_cmd, cwd=project_path, timeout=timeout)

    if stdout:
        output.append(stdout)
    if stderr:
        output.append(stderr)

    output.append("")
    if exit_code == 0:
        output.append("=== NO ISSUES FOUND ===")
    else:
        output.append(f"=== LINT ISSUES FOUND (exit code: {exit_code}) ===")

    return "\n".join(output)


@tool(name="install_dependencies")
def install_dependencies(
    path: str = ".",
    command: Optional[str] = None,
    timeout: int = 300,
) -> str:
    """
    Install project dependencies.

    Automatically detects project type and runs the appropriate install command.

    Args:
        path: Project directory (default: current directory)
        command: Custom install command (optional)
        timeout: Command timeout in seconds (default: 300)

    Returns:
        Install output.

    Examples:
        install_dependencies(".")
        install_dependencies(".", command="pip install -e .")
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        return f"Error: Path does not exist: {project_path}"

    project_type = detect_project_type(project_path)
    commands = get_build_commands(project_type)

    if command:
        install_cmd = command
    else:
        install_cmd = commands.get("install")
        if not install_cmd:
            return f"No install command for {project_type.value}. Specify a custom command."

    output = [
        f"Project: {project_path}",
        f"Type: {project_type.value}",
        f"Command: {install_cmd}",
        "",
        "=== INSTALLING DEPENDENCIES ===",
    ]

    exit_code, stdout, stderr = run_command(install_cmd, cwd=project_path, timeout=timeout)

    if stdout:
        output.append(stdout)
    if stderr:
        output.append(stderr)

    output.append("")
    if exit_code == 0:
        output.append("=== DEPENDENCIES INSTALLED ===")
    else:
        output.append(f"=== INSTALL FAILED (exit code: {exit_code}) ===")

    return "\n".join(output)


# Export all build/fix tools
BUILD_FIX_TOOLS = [
    detect_project,
    build_project,
    test_project,
    build_and_fix,
    lint_project,
    install_dependencies,
]
