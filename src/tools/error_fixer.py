"""Error detection and auto-fix suggestion tools."""

import re
from typing import Optional
from dataclasses import dataclass

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir, run_terminal_command
from src.tools.file_ops import read_file
from src.tools.code_search import search_files


@dataclass
class ErrorInfo:
    """Parsed error information."""
    error_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    stack_trace: Optional[str] = None


class ErrorParser:
    """Parses error messages from different languages and tools."""

    @staticmethod
    def parse_python_error(output: str) -> list[ErrorInfo]:
        """Parse Python error output."""
        errors = []

        # Match Python traceback
        tb_pattern = r'File "([^"]+)", line (\d+)'
        error_pattern = r'(\w+Error|\w+Exception): (.+?)(?:\n|$)'

        tb_matches = list(re.finditer(tb_pattern, output))
        error_match = re.search(error_pattern, output)

        if error_match:
            file_path = None
            line_number = None

            if tb_matches:
                last_tb = tb_matches[-1]
                file_path = last_tb.group(1)
                line_number = int(last_tb.group(2))

            errors.append(ErrorInfo(
                error_type=error_match.group(1),
                message=error_match.group(2).strip(),
                file_path=file_path,
                line_number=line_number,
                stack_trace=output,
            ))

        return errors

    @staticmethod
    def parse_javascript_error(output: str) -> list[ErrorInfo]:
        """Parse JavaScript/Node.js error output."""
        errors = []

        # Match Node.js error
        pattern = r'(\w+Error): (.+?)\n\s+at .+?[(\s]([^:)]+):(\d+):(\d+)'

        for match in re.finditer(pattern, output, re.MULTILINE):
            errors.append(ErrorInfo(
                error_type=match.group(1),
                message=match.group(2).strip(),
                file_path=match.group(3),
                line_number=int(match.group(4)),
                column=int(match.group(5)),
                stack_trace=output,
            ))

        return errors

    @staticmethod
    def parse_typescript_error(output: str) -> list[ErrorInfo]:
        """Parse TypeScript compiler errors."""
        errors = []

        # Match TS error format: file(line,col): error TS####: message
        pattern = r'([^\s(]+)\((\d+),(\d+)\): error (TS\d+): (.+)'

        for match in re.finditer(pattern, output):
            errors.append(ErrorInfo(
                error_type=match.group(4),
                message=match.group(5).strip(),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                column=int(match.group(3)),
            ))

        return errors

    @staticmethod
    def parse_rust_error(output: str) -> list[ErrorInfo]:
        """Parse Rust compiler errors."""
        errors = []

        # Match Rust error format
        pattern = r'error\[([^\]]+)\]: (.+?)\n\s*--> ([^:]+):(\d+):(\d+)'

        for match in re.finditer(pattern, output, re.MULTILINE):
            errors.append(ErrorInfo(
                error_type=match.group(1),
                message=match.group(2).strip(),
                file_path=match.group(3),
                line_number=int(match.group(4)),
                column=int(match.group(5)),
            ))

        return errors

    @staticmethod
    def parse_generic(output: str) -> list[ErrorInfo]:
        """Generic error parsing for unknown formats."""
        errors = []

        # Common patterns
        patterns = [
            r'error: (.+)',
            r'Error: (.+)',
            r'ERROR: (.+)',
            r'failed: (.+)',
            r'FAILED: (.+)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, output, re.IGNORECASE):
                errors.append(ErrorInfo(
                    error_type="Error",
                    message=match.group(1).strip(),
                ))
                break

        return errors

    def parse(self, output: str) -> list[ErrorInfo]:
        """Parse error output and detect the language automatically."""
        errors = []

        # Try language-specific parsers
        if "Traceback" in output or "Error:" in output and ".py" in output:
            errors = self.parse_python_error(output)

        elif "TypeError:" in output or "ReferenceError:" in output or "SyntaxError:" in output:
            if ".js" in output or ".ts" in output:
                errors = self.parse_javascript_error(output)

        elif "error TS" in output:
            errors = self.parse_typescript_error(output)

        elif "error[E" in output:
            errors = self.parse_rust_error(output)

        if not errors:
            errors = self.parse_generic(output)

        return errors


# Common fix suggestions for known errors
FIX_SUGGESTIONS = {
    # Python errors
    "NameError": [
        "Check if the variable/function is defined before use",
        "Check for typos in variable/function names",
        "Ensure the import statement is present",
    ],
    "TypeError": [
        "Check the types of arguments being passed",
        "Ensure the correct number of arguments",
        "Verify the object supports the operation",
    ],
    "ImportError": [
        "Verify the module is installed (pip install <module>)",
        "Check the module name spelling",
        "Ensure the module is in PYTHONPATH",
    ],
    "ModuleNotFoundError": [
        "Install the missing module: pip install <module>",
        "Check if you're in the correct virtual environment",
        "Verify the module name is correct",
    ],
    "AttributeError": [
        "Check if the object has the attribute",
        "Verify the object is not None",
        "Check for typos in attribute name",
    ],
    "KeyError": [
        "Check if the key exists before accessing",
        "Use .get() method with a default value",
        "Verify the key spelling",
    ],
    "IndexError": [
        "Check the list/array length before accessing",
        "Verify the index is within bounds",
        "Handle empty collections",
    ],
    "ValueError": [
        "Validate input before processing",
        "Check data format and type",
        "Handle edge cases",
    ],
    "SyntaxError": [
        "Check for missing colons, parentheses, or brackets",
        "Verify proper indentation",
        "Look for unclosed strings",
    ],
    "IndentationError": [
        "Use consistent indentation (spaces or tabs, not both)",
        "Check for mixed indentation",
        "Verify block structure",
    ],

    # JavaScript/TypeScript errors
    "ReferenceError": [
        "Ensure the variable is declared before use",
        "Check for typos in variable names",
        "Verify the scope of the variable",
    ],
    "undefined": [
        "Check if the value is initialized",
        "Add null/undefined checks",
        "Use optional chaining (?.) operator",
    ],

    # Generic
    "Error": [
        "Read the full error message carefully",
        "Check the line number mentioned in the error",
        "Search for similar issues online",
    ],
}


def get_fix_suggestions(error_type: str) -> list[str]:
    """Get fix suggestions for an error type."""
    # Try exact match
    if error_type in FIX_SUGGESTIONS:
        return FIX_SUGGESTIONS[error_type]

    # Try partial match
    for key in FIX_SUGGESTIONS:
        if key.lower() in error_type.lower():
            return FIX_SUGGESTIONS[key]

    return FIX_SUGGESTIONS.get("Error", [])


@tool
def analyze_error(error_output: str) -> str:
    """
    Analyze an error message and provide fix suggestions.

    Args:
        error_output: The error output to analyze

    Returns:
        Analysis with error details and fix suggestions.

    Examples:
        analyze_error(error_output="NameError: name 'foo' is not defined")
        analyze_error(error_output="TypeError: cannot read property 'x' of undefined")
    """
    parser = ErrorParser()
    errors = parser.parse(error_output)

    if not errors:
        return "Could not parse error. Please provide the full error message."

    output = ["## Error Analysis\n"]

    for i, error in enumerate(errors, 1):
        if len(errors) > 1:
            output.append(f"### Error {i}")

        output.append(f"**Type**: `{error.error_type}`")
        output.append(f"**Message**: {error.message}")

        if error.file_path:
            loc = f"{error.file_path}"
            if error.line_number:
                loc += f":{error.line_number}"
            if error.column:
                loc += f":{error.column}"
            output.append(f"**Location**: `{loc}`")

        output.append("\n**Suggested Fixes**:")
        suggestions = get_fix_suggestions(error.error_type)
        for j, suggestion in enumerate(suggestions, 1):
            output.append(f"{j}. {suggestion}")

        output.append("")

    return "\n".join(output)


@tool
def run_and_fix(
    command: str,
    auto_retry: bool = False,
) -> str:
    """
    Run a command and analyze any errors, providing fix suggestions.

    Args:
        command: The command to run
        auto_retry: Whether to retry after simple fixes (not implemented yet)

    Returns:
        Command output or error analysis with fix suggestions.

    Examples:
        run_and_fix(command="python main.py")
        run_and_fix(command="npm run build")
        run_and_fix(command="cargo build")
    """
    result = run_terminal_command(command)

    # Check if there was an error
    if "Error" in result or "error" in result or "FAILED" in result or "failed" in result:
        analysis = analyze_error(result)

        output = [
            "## Command Output\n",
            "```",
            result[:2000] if len(result) > 2000 else result,
            "```\n",
            analysis,
        ]

        return "\n".join(output)

    return result


@tool
def diagnose_file(file_path: str) -> str:
    """
    Run basic diagnostics on a file and report any issues.

    Args:
        file_path: Path to the file to diagnose

    Returns:
        Diagnostic results.

    Examples:
        diagnose_file(file_path="main.py")
        diagnose_file(file_path="src/index.ts")
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.is_absolute():
        path = get_working_dir() / path

    if not path.exists():
        return f"Error: File not found: {path}"

    ext = path.suffix.lower()
    output = [f"## Diagnostics: {path.name}\n"]

    # Run appropriate linter/checker based on file type
    if ext == ".py":
        # Try python syntax check
        result = run_terminal_command(f'python -m py_compile "{path}"')
        if "Error" in result or "error" in result:
            output.append("### Syntax Errors")
            output.append("```")
            output.append(result)
            output.append("```")
            output.append(analyze_error(result))
        else:
            output.append("Syntax check passed.")

    elif ext in [".js", ".jsx"]:
        result = run_terminal_command(f'node --check "{path}"')
        if "Error" in result or "error" in result:
            output.append("### Syntax Errors")
            output.append("```")
            output.append(result)
            output.append("```")
            output.append(analyze_error(result))
        else:
            output.append("Syntax check passed.")

    elif ext in [".ts", ".tsx"]:
        result = run_terminal_command(f'npx tsc --noEmit "{path}"')
        if "error" in result.lower():
            output.append("### TypeScript Errors")
            output.append("```")
            output.append(result)
            output.append("```")
            output.append(analyze_error(result))
        else:
            output.append("TypeScript check passed.")

    elif ext == ".rs":
        # For Rust, check the whole project
        result = run_terminal_command("cargo check")
        if "error" in result.lower():
            output.append("### Rust Errors")
            output.append("```")
            output.append(result)
            output.append("```")
            output.append(analyze_error(result))
        else:
            output.append("Rust check passed.")

    else:
        output.append(f"No specific diagnostics available for {ext} files.")
        output.append("Use appropriate language-specific tools for checking.")

    return "\n".join(output)


@tool
def suggest_fix(
    file_path: str,
    line_number: int,
    error_message: str,
) -> str:
    """
    Suggest a specific fix for an error at a given location.

    Args:
        file_path: Path to the file with the error
        line_number: Line number where the error occurs
        error_message: The error message

    Returns:
        Suggested fix with context.

    Examples:
        suggest_fix(file_path="main.py", line_number=42, error_message="NameError: name 'foo' is not defined")
    """
    # Read the file and get context
    content = read_file(file_path)

    if content.startswith("Error"):
        return content

    lines = content.split("\n")

    # Get context around the error line
    start = max(0, line_number - 5)
    end = min(len(lines), line_number + 5)
    context_lines = lines[start:end]

    output = [
        f"## Fix Suggestion for `{file_path}:{line_number}`\n",
        f"**Error**: {error_message}\n",
        "### Code Context",
        "```",
    ]

    for i, line in enumerate(context_lines, start + 1):
        marker = ">>>" if i == line_number else "   "
        output.append(f"{marker} {i}: {line}")

    output.append("```\n")

    # Analyze the error
    analysis = analyze_error(error_message)
    output.append(analysis)

    output.append("\n### Recommended Action")
    output.append("Review the error line and apply one of the suggested fixes above.")
    output.append("Then run the code again to verify the fix.")

    return "\n".join(output)


# Export error fixer tools
ERROR_FIXER_TOOLS = [
    analyze_error,
    run_and_fix,
    diagnose_file,
    suggest_fix,
]
