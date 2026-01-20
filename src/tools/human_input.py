"""Human-in-the-loop tools for agent interaction with users."""

from typing import Optional, List
from agno.tools.decorator import tool
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

console = Console()


@tool(name="ask_user")
def ask_user(
    question: str,
    options: Optional[List[str]] = None,
    default: Optional[str] = None,
) -> str:
    """
    Ask the user a question and wait for their response.

    Use this tool when you need clarification, input, or a decision from the user.
    This pauses execution until the user responds.

    Args:
        question: The question to ask the user
        options: Optional list of choices to present (user can still type custom answer)
        default: Optional default value if user presses Enter

    Returns:
        The user's response as a string

    Examples:
        ask_user("What should I name this function?")
        ask_user("Which database do you prefer?", options=["PostgreSQL", "MySQL", "SQLite"])
        ask_user("Enter the API endpoint", default="http://localhost:3000")
    """
    console.print()
    console.print(Panel(
        f"[bold cyan]Agent Question:[/bold cyan]\n\n{question}",
        border_style="cyan",
        padding=(1, 2),
    ))

    if options:
        console.print("\n[dim]Options:[/dim]")
        for i, opt in enumerate(options, 1):
            console.print(f"  [yellow]{i}.[/yellow] {opt}")
        console.print(f"  [dim](or type your own answer)[/dim]")
        console.print()

    prompt_text = "[bold green]Your answer[/bold green]"
    if default:
        prompt_text += f" [dim](default: {default})[/dim]"

    response = Prompt.ask(prompt_text, default=default or "")

    # If user entered a number and we have options, map to option
    if options and response.isdigit():
        idx = int(response) - 1
        if 0 <= idx < len(options):
            response = options[idx]

    console.print(f"[dim]You answered: {response}[/dim]\n")
    return response


@tool(name="confirm_action")
def confirm_action(
    action: str,
    details: Optional[str] = None,
    default: bool = False,
) -> bool:
    """
    Ask user for confirmation before performing an action.

    Use this tool before executing potentially destructive or important operations.
    Returns True if user confirms, False if they decline.

    Args:
        action: Short description of what will be done (e.g., "Delete 5 files")
        details: Optional longer explanation or list of affected items
        default: Default choice if user presses Enter (False = safer default)

    Returns:
        True if user confirms, False if they decline

    Examples:
        confirm_action("Delete all .tmp files", details="This will remove 15 files")
        confirm_action("Push changes to main branch")
        confirm_action("Overwrite config.json", details="Current file will be replaced")
    """
    console.print()

    # Build the confirmation panel
    content = f"[bold yellow]Action:[/bold yellow] {action}"
    if details:
        content += f"\n\n[dim]{details}[/dim]"

    console.print(Panel(
        content,
        title="[bold]Confirmation Required[/bold]",
        border_style="yellow",
        padding=(1, 2),
    ))

    result = Confirm.ask(
        "[bold]Proceed with this action?[/bold]",
        default=default,
    )

    if result:
        console.print("[green]✓ Confirmed[/green]\n")
    else:
        console.print("[red]✗ Cancelled[/red]\n")

    return result


@tool(name="show_options")
def show_options(
    title: str,
    options: List[str],
    descriptions: Optional[List[str]] = None,
    allow_multiple: bool = False,
) -> str:
    """
    Present a list of options for the user to choose from.

    Use this when you need the user to select from predefined choices.

    Args:
        title: Title/question for the selection
        options: List of option labels
        descriptions: Optional descriptions for each option
        allow_multiple: If True, user can select multiple (comma-separated)

    Returns:
        Selected option(s) as string (comma-separated if multiple)

    Examples:
        show_options("Select a framework", ["React", "Vue", "Angular"])
        show_options("Choose features", ["Auth", "API", "Database"], allow_multiple=True)
    """
    console.print()
    console.print(Panel(
        f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
    ))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Num", style="yellow", width=4)
    table.add_column("Option", style="white")
    if descriptions:
        table.add_column("Description", style="dim")

    for i, opt in enumerate(options, 1):
        if descriptions and i <= len(descriptions):
            table.add_row(f"{i}.", opt, descriptions[i-1])
        else:
            table.add_row(f"{i}.", opt)

    console.print(table)

    if allow_multiple:
        console.print("\n[dim]Enter numbers separated by commas (e.g., 1,3,4)[/dim]")

    response = Prompt.ask("\n[bold green]Your choice[/bold green]")

    # Parse response
    if allow_multiple:
        indices = [int(x.strip()) - 1 for x in response.split(",") if x.strip().isdigit()]
        selected = [options[i] for i in indices if 0 <= i < len(options)]
        result = ", ".join(selected) if selected else response
    else:
        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(options):
                result = options[idx]
            else:
                result = response
        else:
            result = response

    console.print(f"[dim]Selected: {result}[/dim]\n")
    return result


@tool(name="request_file_content")
def request_file_content(
    purpose: str,
    file_type: Optional[str] = None,
) -> str:
    """
    Request the user to provide file content or paste text.

    Use this when you need the user to provide content that isn't in a file,
    like API keys, configuration snippets, or code they want to modify.

    Args:
        purpose: Explain what the content will be used for
        file_type: Optional hint about expected content type (e.g., "JSON", "Python")

    Returns:
        The content provided by the user

    Examples:
        request_file_content("Please paste your API configuration")
        request_file_content("Paste the error message you're seeing")
        request_file_content("Enter your database schema", file_type="SQL")
    """
    console.print()

    content = f"[bold cyan]Input Requested:[/bold cyan]\n\n{purpose}"
    if file_type:
        content += f"\n\n[dim]Expected format: {file_type}[/dim]"
    content += "\n\n[dim]Enter/paste your content below. Type 'END' on a new line when done:[/dim]"

    console.print(Panel(content, border_style="cyan", padding=(1, 2)))

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break

    result = "\n".join(lines)
    console.print(f"\n[dim]Received {len(lines)} lines of input[/dim]\n")
    return result


@tool(name="notify_user")
def notify_user(
    message: str,
    level: str = "info",
) -> str:
    """
    Send a notification or status update to the user.

    Use this to inform the user about progress, warnings, or important information
    without requiring a response.

    Args:
        message: The message to display
        level: One of "info", "success", "warning", "error"

    Returns:
        Confirmation that message was displayed

    Examples:
        notify_user("Starting database migration...", level="info")
        notify_user("All tests passed!", level="success")
        notify_user("API rate limit approaching", level="warning")
    """
    styles = {
        "info": ("blue", "[i]"),
        "success": ("green", "[OK]"),
        "warning": ("yellow", "[!]"),
        "error": ("red", "[X]"),
    }

    color, icon = styles.get(level, ("blue", "[i]"))

    console.print(f"\n[{color}]{icon} {message}[/{color}]\n")

    return f"Notified user: {message}"


# Export all human input tools
HUMAN_INPUT_TOOLS = [
    ask_user,
    confirm_action,
    show_options,
    request_file_content,
    notify_user,
]
