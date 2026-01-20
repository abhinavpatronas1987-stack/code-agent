"""Code execution sandbox for running Python code safely."""

import sys
import io
import traceback
import ast
import contextlib
from typing import Optional, Any
from dataclasses import dataclass, field

from agno.tools.decorator import tool


@dataclass
class ExecutionResult:
    """Result of code execution."""
    output: str = ""
    error: str = ""
    return_value: Any = None
    variables: dict = field(default_factory=dict)
    success: bool = True


class PythonSandbox:
    """
    A sandboxed Python execution environment.

    Maintains state between executions like a REPL.
    """

    def __init__(self):
        """Initialize the sandbox with a clean namespace."""
        self._namespace: dict[str, Any] = {
            "__builtins__": __builtins__,
            "__name__": "__sandbox__",
        }
        self._history: list[str] = []

    def reset(self) -> None:
        """Reset the sandbox to initial state."""
        self._namespace = {
            "__builtins__": __builtins__,
            "__name__": "__sandbox__",
        }
        self._history = []

    def get_variables(self) -> dict[str, str]:
        """Get user-defined variables and their types."""
        return {
            k: type(v).__name__
            for k, v in self._namespace.items()
            if not k.startswith("_")
        }

    def execute(self, code: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute Python code in the sandbox.

        Args:
            code: Python code to execute
            timeout: Maximum execution time (currently not enforced in sync mode)

        Returns:
            ExecutionResult with output, errors, and variables
        """
        result = ExecutionResult()

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Parse the code first
            tree = ast.parse(code)

            # If the last statement is an expression, we want its value
            last_expr = None
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                last_expr = tree.body.pop()

            # Compile and execute main code
            if tree.body:
                compiled = compile(tree, "<sandbox>", "exec")
                with contextlib.redirect_stdout(stdout_capture), \
                        contextlib.redirect_stderr(stderr_capture):
                    exec(compiled, self._namespace)

            # Evaluate last expression if exists
            if last_expr:
                expr_compiled = compile(
                    ast.Expression(last_expr.value), "<sandbox>", "eval"
                )
                with contextlib.redirect_stdout(stdout_capture), \
                        contextlib.redirect_stderr(stderr_capture):
                    result.return_value = eval(expr_compiled, self._namespace)

            result.output = stdout_capture.getvalue()
            result.error = stderr_capture.getvalue()
            result.variables = self.get_variables()
            result.success = True

            # Store in history
            self._history.append(code)

        except SyntaxError as e:
            result.success = False
            result.error = f"SyntaxError: {e.msg} (line {e.lineno})"

        except Exception as e:
            result.success = False
            result.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

        return result


# Global sandbox instance
_sandbox: PythonSandbox | None = None


def get_sandbox() -> PythonSandbox:
    """Get or create the global sandbox instance."""
    global _sandbox
    if _sandbox is None:
        _sandbox = PythonSandbox()
    return _sandbox


@tool
def python_exec(code: str) -> str:
    """
    Execute Python code in a sandboxed REPL environment.

    The sandbox maintains state between calls, so you can define variables
    and functions that persist across multiple executions.

    Args:
        code: Python code to execute

    Returns:
        Execution result with output and any errors.

    Examples:
        python_exec(code="x = 10\\nprint(x * 2)")
        python_exec(code="import math\\nmath.sqrt(16)")
        python_exec(code="def greet(name):\\n    return f'Hello, {name}'")
        python_exec(code="greet('World')")
    """
    sandbox = get_sandbox()
    result = sandbox.execute(code)

    output_parts = []

    if result.output:
        output_parts.append(f"**Output**:\n```\n{result.output.rstrip()}\n```")

    if result.return_value is not None:
        val_repr = repr(result.return_value)
        if len(val_repr) > 500:
            val_repr = val_repr[:500] + "..."
        output_parts.append(f"**Result**: `{val_repr}`")

    if result.error:
        output_parts.append(f"**Error**:\n```\n{result.error.rstrip()}\n```")

    if not output_parts:
        output_parts.append("Code executed successfully (no output).")

    return "\n\n".join(output_parts)


@tool
def python_repl_reset() -> str:
    """
    Reset the Python REPL sandbox to initial state.

    Clears all variables, functions, and imports from the environment.

    Returns:
        Confirmation message.

    Examples:
        python_repl_reset()
    """
    sandbox = get_sandbox()
    sandbox.reset()
    return "Python REPL sandbox has been reset. All variables cleared."


@tool
def python_repl_vars() -> str:
    """
    Show all variables defined in the Python REPL sandbox.

    Returns:
        List of variables and their types.

    Examples:
        python_repl_vars()
    """
    sandbox = get_sandbox()
    variables = sandbox.get_variables()

    if not variables:
        return "No user-defined variables in the sandbox."

    output = ["## Sandbox Variables\n"]
    for name, type_name in sorted(variables.items()):
        try:
            value = sandbox._namespace[name]
            value_repr = repr(value)
            if len(value_repr) > 100:
                value_repr = value_repr[:100] + "..."
            output.append(f"- `{name}` ({type_name}): {value_repr}")
        except Exception:
            output.append(f"- `{name}` ({type_name})")

    return "\n".join(output)


@tool
def python_eval(expression: str) -> str:
    """
    Evaluate a single Python expression and return the result.

    Unlike python_exec, this only evaluates expressions (not statements).

    Args:
        expression: Python expression to evaluate

    Returns:
        The result of the expression.

    Examples:
        python_eval(expression="2 + 2")
        python_eval(expression="[x**2 for x in range(10)]")
        python_eval(expression="len('hello world')")
    """
    sandbox = get_sandbox()

    try:
        result = eval(expression, sandbox._namespace)
        return f"**Result**: `{repr(result)}`"
    except SyntaxError as e:
        return f"**SyntaxError**: {e.msg}"
    except Exception as e:
        return f"**{type(e).__name__}**: {str(e)}"


@tool
def python_import(module: str, alias: Optional[str] = None) -> str:
    """
    Import a module into the Python sandbox.

    Args:
        module: Module name to import
        alias: Optional alias (like 'import x as y')

    Returns:
        Confirmation message.

    Examples:
        python_import(module="json")
        python_import(module="numpy", alias="np")
        python_import(module="pandas", alias="pd")
    """
    sandbox = get_sandbox()

    try:
        imported = __import__(module)

        # Handle submodules (e.g., os.path)
        parts = module.split(".")
        for part in parts[1:]:
            imported = getattr(imported, part)

        name = alias or module.split(".")[0]
        sandbox._namespace[name] = imported

        return f"Successfully imported `{module}` as `{name}`"

    except ImportError as e:
        return f"**ImportError**: Could not import `{module}`: {str(e)}"
    except Exception as e:
        return f"**{type(e).__name__}**: {str(e)}"


@tool
def python_run_file(file_path: str) -> str:
    """
    Execute a Python file in the sandbox.

    Args:
        file_path: Path to the Python file

    Returns:
        Execution result.

    Examples:
        python_run_file(file_path="script.py")
        python_run_file(file_path="./tests/test_utils.py")
    """
    from pathlib import Path
    from src.tools.terminal import get_working_dir

    path = Path(file_path)
    if not path.is_absolute():
        path = get_working_dir() / path

    if not path.exists():
        return f"**Error**: File not found: {path}"

    if not path.suffix == ".py":
        return f"**Error**: Not a Python file: {path}"

    try:
        code = path.read_text(encoding="utf-8")
        result = python_exec(code)
        return f"## Executed: {path.name}\n\n{result}"
    except Exception as e:
        return f"**Error reading file**: {str(e)}"


# Export sandbox tools
SANDBOX_TOOLS = [
    python_exec,
    python_eval,
    python_import,
    python_repl_vars,
    python_repl_reset,
    python_run_file,
]
