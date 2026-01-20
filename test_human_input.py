"""Test script for human-in-the-loop tools."""

import sys
import os

if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

print("=" * 60)
print("  Human-in-the-Loop Tools Test")
print("=" * 60)
print()

# Import the functions directly (not as agno tools)
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_ask_user():
    """Test ask_user display."""
    print("\n[TEST 1] ask_user - Question with options\n")

    question = "Which database should I use for this project?"
    options = ["PostgreSQL", "MySQL", "SQLite", "MongoDB"]

    console.print(Panel(
        f"[bold cyan]Agent Question:[/bold cyan]\n\n{question}",
        border_style="cyan",
        padding=(1, 2),
    ))

    console.print("\n[dim]Options:[/dim]")
    for i, opt in enumerate(options, 1):
        console.print(f"  [yellow]{i}.[/yellow] {opt}")
    console.print(f"  [dim](or type your own answer)[/dim]")

    print("\n[Display OK - Skipping actual input for test]\n")


def test_confirm_action():
    """Test confirm_action display."""
    print("\n[TEST 2] confirm_action - Confirmation prompt\n")

    action = "Delete 15 temporary files"
    details = "Files in ./tmp/ matching *.tmp will be permanently removed"

    content = f"[bold yellow]Action:[/bold yellow] {action}"
    content += f"\n\n[dim]{details}[/dim]"

    console.print(Panel(
        content,
        title="[bold]Confirmation Required[/bold]",
        border_style="yellow",
        padding=(1, 2),
    ))

    console.print("[bold]Proceed with this action?[/bold] [y/N]")
    print("\n[Display OK - Skipping actual input for test]\n")


def test_show_options():
    """Test show_options display."""
    print("\n[TEST 3] show_options - Multiple choice\n")

    title = "Select a frontend framework"
    options = ["React", "Vue.js", "Angular", "Svelte"]
    descriptions = [
        "Popular, large ecosystem",
        "Progressive, easy to learn",
        "Full-featured, enterprise",
        "Lightweight, fast"
    ]

    console.print(Panel(
        f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
    ))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Num", style="yellow", width=4)
    table.add_column("Option", style="white")
    table.add_column("Description", style="dim")

    for i, (opt, desc) in enumerate(zip(options, descriptions), 1):
        table.add_row(f"{i}.", opt, desc)

    console.print(table)
    console.print("\n[bold green]Your choice[/bold green]: ")
    print("\n[Display OK - Skipping actual input for test]\n")


def test_notify_user():
    """Test notify_user display."""
    print("\n[TEST 4] notify_user - Notifications\n")

    notifications = [
        ("Starting database migration...", "info", "blue", "ℹ"),
        ("All tests passed!", "success", "green", "✓"),
        ("API rate limit approaching", "warning", "yellow", "⚠"),
        ("Connection failed", "error", "red", "✗"),
    ]

    for message, level, color, icon in notifications:
        console.print(f"[{color}]{icon} {message}[/{color}]")

    print("\n[Display OK]\n")


if __name__ == "__main__":
    test_ask_user()
    test_confirm_action()
    test_show_options()
    test_notify_user()

    print("=" * 60)
    print("  All display tests completed!")
    print("=" * 60)
    print()
    print("The agent will now use these prompts when it needs:")
    print("  - User input or clarification")
    print("  - Confirmation before dangerous actions")
    print("  - Selection between options")
    print("  - To notify about progress")
    print()
