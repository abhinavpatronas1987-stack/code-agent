#!/usr/bin/env python
"""Quick test script to verify the agent works."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

console = Console()


def test_imports():
    """Test that all imports work."""
    console.print("[yellow]Testing imports...[/yellow]")

    try:
        from src.config.settings import get_settings
        from src.core.llm import get_ollama_model
        from src.tools.terminal import run_terminal_command, TERMINAL_TOOLS
        from src.tools.file_ops import read_file, FILE_TOOLS
        from src.tools.code_search import search_files, SEARCH_TOOLS
        from src.agents.coding_agent import CodingAgent

        console.print("[green]All imports successful![/green]")

        # Print tool count
        total_tools = len(TERMINAL_TOOLS) + len(FILE_TOOLS) + len(SEARCH_TOOLS)
        console.print(f"  - Terminal tools: {len(TERMINAL_TOOLS)}")
        console.print(f"  - File tools: {len(FILE_TOOLS)}")
        console.print(f"  - Search tools: {len(SEARCH_TOOLS)}")
        console.print(f"  - Total tools: {total_tools}")

        return True
    except Exception as e:
        console.print(f"[red]Import error: {e}[/red]")
        return False


def test_settings():
    """Test settings loading."""
    console.print("\n[yellow]Testing settings...[/yellow]")

    try:
        from src.config.settings import get_settings
        settings = get_settings()

        console.print(f"  - App: {settings.app_name}")
        console.print(f"  - Model: {settings.ollama_model}")
        console.print(f"  - Ollama URL: {settings.ollama_base_url}")
        console.print("[green]Settings loaded![/green]")
        return True
    except Exception as e:
        console.print(f"[red]Settings error: {e}[/red]")
        return False


def test_terminal_tool():
    """Test terminal tool."""
    console.print("\n[yellow]Testing terminal tool...[/yellow]")

    try:
        from src.tools.terminal import run_terminal_command

        # The tool is now a Function object, call via entrypoint
        result = run_terminal_command.entrypoint(command="echo Hello from Code Agent")
        if "Hello from Code Agent" in result:
            console.print("[green]Terminal tool works![/green]")
            return True
        else:
            console.print(f"[red]Unexpected output: {result}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]Terminal error: {e}[/red]")
        return False


def test_file_tools():
    """Test file tools."""
    console.print("\n[yellow]Testing file tools...[/yellow]")

    try:
        import tempfile
        from src.tools.file_ops import write_file, read_file, edit_file

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = f"{tmpdir}/test.txt"

            # Write - using entrypoint
            write_result = write_file.entrypoint(file_path=test_file, content="Hello, World!")
            if "Successfully" not in write_result:
                console.print(f"[red]Write failed: {write_result}[/red]")
                return False

            # Read
            read_result = read_file.entrypoint(file_path=test_file)
            if "Hello, World!" not in read_result:
                console.print(f"[red]Read failed: {read_result}[/red]")
                return False

            # Edit
            edit_result = edit_file.entrypoint(file_path=test_file, old_content="World", new_content="Agent")
            if "Successfully" not in edit_result:
                console.print(f"[red]Edit failed: {edit_result}[/red]")
                return False

            console.print("[green]File tools work![/green]")
            return True

    except Exception as e:
        console.print(f"[red]File tools error: {e}[/red]")
        return False


def test_ollama_connection():
    """Test Ollama connection."""
    console.print("\n[yellow]Testing Ollama connection...[/yellow]")

    try:
        import httpx
        from src.config.settings import get_settings

        settings = get_settings()
        url = f"{settings.ollama_base_url}/api/tags"

        response = httpx.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            console.print(f"[green]Ollama connected![/green]")
            console.print(f"  - Available models: {len(models)}")

            if models:
                for m in models[:5]:
                    console.print(f"    - {m}")
                if len(models) > 5:
                    console.print(f"    - ... and {len(models) - 5} more")

            # Check if our model is available
            if settings.ollama_model in models or any(settings.ollama_model.split(":")[0] in m for m in models):
                console.print(f"[green]Model '{settings.ollama_model}' is available![/green]")
            else:
                console.print(f"[yellow]Model '{settings.ollama_model}' not found.[/yellow]")
                console.print(f"[yellow]Run: ollama pull {settings.ollama_model}[/yellow]")

            return True
        else:
            console.print(f"[red]Ollama returned status {response.status_code}[/red]")
            return False

    except httpx.ConnectError:
        console.print("[red]Could not connect to Ollama![/red]")
        console.print("[yellow]Make sure Ollama is running: ollama serve[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]Ollama error: {e}[/red]")
        return False


def test_agent_creation():
    """Test agent creation (without running inference)."""
    console.print("\n[yellow]Testing agent creation...[/yellow]")

    try:
        from src.agents.coding_agent import CodingAgent

        agent = CodingAgent(session_id="test")
        console.print(f"[green]Agent created: {agent.agent.name}[/green]")
        console.print(f"  - Tools: {len(agent.agent.tools)}")
        return True
    except Exception as e:
        console.print(f"[red]Agent creation error: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold]Code Agent - Test Suite[/bold]",
        border_style="blue"
    ))

    tests = [
        ("Imports", test_imports),
        ("Settings", test_settings),
        ("Terminal Tool", test_terminal_tool),
        ("File Tools", test_file_tools),
        ("Ollama Connection", test_ollama_connection),
        ("Agent Creation", test_agent_creation),
    ]

    results = []
    for name, test_fn in tests:
        try:
            results.append((name, test_fn()))
        except Exception as e:
            console.print(f"[red]Test '{name}' crashed: {e}[/red]")
            results.append((name, False))

    # Summary
    console.print("\n" + "=" * 40)
    console.print("[bold]Test Summary[/bold]")
    console.print("=" * 40)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[green]PASS[/green]" if result else "[red]FAIL[/red]"
        console.print(f"  {status} {name}")

    console.print("=" * 40)
    color = "green" if passed == total else "yellow" if passed > 0 else "red"
    console.print(f"[{color}]{passed}/{total} tests passed[/{color}]")

    if passed == total:
        console.print("\n[green bold]All tests passed! Ready to use.[/green bold]")
        console.print("\nTo start the CLI:")
        console.print("  python main.py")
        console.print("\nTo start the API server:")
        console.print("  python main.py serve")
    else:
        console.print("\n[yellow]Some tests failed. Check the output above.[/yellow]")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
