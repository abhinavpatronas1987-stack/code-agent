#!/usr/bin/env python
"""End-to-end demo of the Code Agent."""

import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

console = Console(force_terminal=True)


def run_demo():
    """Run an end-to-end demo of the agent."""
    console.print(Panel.fit(
        "[bold blue]Code Agent - End-to-End Demo[/bold blue]\n"
        "[dim]Demonstrating AI-powered coding assistant[/dim]",
        border_style="blue"
    ))

    # Import after adding to path
    from src.agents.coding_agent import CodingAgent
    from src.tools.terminal import set_working_dir

    # Set workspace to project directory
    workspace = Path(__file__).parent.parent
    set_working_dir(workspace)

    console.print(f"\n[cyan]Workspace:[/cyan] {workspace}")
    console.print("[yellow]Creating agent...[/yellow]")

    # Create the agent
    agent = CodingAgent(session_id="demo", workspace=str(workspace))

    console.print(f"[green]Agent created with {len(agent.agent.tools)} tools[/green]\n")

    # Single demo query
    query = "List all Python files in the src directory"

    console.print(Panel(
        f"[bold]Query:[/bold] {query}",
        border_style="green"
    ))

    console.print("[yellow]Agent thinking...[/yellow]\n")

    try:
        # Run the agent without streaming for cleaner output
        response = agent.run(query, stream=False)

        # Print response content
        if hasattr(response, 'content') and response.content:
            # Clean up any problematic characters
            content = response.content.encode('ascii', 'replace').decode('ascii')
            print(content)
        else:
            print(str(response))

        console.print("\n[bold green]Demo successful! Agent is working.[/bold green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()

    console.print("\n" + "=" * 60)
    console.print("\nTo use interactively, run:")
    console.print("  [cyan]python main.py[/cyan]")


if __name__ == "__main__":
    run_demo()
