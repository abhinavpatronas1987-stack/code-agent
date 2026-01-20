"""Interactive TUI (Terminal User Interface) - Feature 18.

Rich terminal UI with:
- Split panels (files, chat, context)
- Syntax highlighting
- Keyboard shortcuts
- Real-time updates
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from rich.console import Console, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.prompt import Prompt
from rich.markdown import Markdown

from src.config.settings import get_settings


@dataclass
class TUIState:
    """State for the TUI."""
    current_file: Optional[str] = None
    context_files: List[str] = None
    messages: List[Dict] = None
    status: str = "Ready"
    model: str = ""
    working_dir: str = ""
    show_files: bool = True
    show_context: bool = True

    def __post_init__(self):
        if self.context_files is None:
            self.context_files = []
        if self.messages is None:
            self.messages = []


class TerminalUI:
    """Rich Terminal User Interface."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize TUI."""
        self.console = Console()
        settings = get_settings()

        self.state = TUIState(
            model=settings.ollama_model,
            working_dir=str(working_dir or Path.cwd()),
        )

        # Layout configuration
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        """Setup the panel layout."""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )

        self.layout["main"].split_row(
            Layout(name="sidebar", size=30, visible=self.state.show_files),
            Layout(name="content", ratio=2),
            Layout(name="context", size=35, visible=self.state.show_context),
        )

    def _render_header(self) -> Panel:
        """Render the header panel."""
        header_text = Text()
        header_text.append("🚀 CODE AGENT ", style="bold blue")
        header_text.append(f"│ Model: ", style="dim")
        header_text.append(f"{self.state.model} ", style="green")
        header_text.append(f"│ ", style="dim")
        header_text.append(f"{self.state.working_dir}", style="cyan")

        return Panel(header_text, style="blue", height=3)

    def _render_file_tree(self) -> Panel:
        """Render the file tree panel."""
        tree = Tree(f"📁 {Path(self.state.working_dir).name}")

        try:
            root_path = Path(self.state.working_dir)
            self._add_directory_to_tree(tree, root_path, depth=0, max_depth=3)
        except Exception:
            tree.add("[red]Error loading files[/red]")

        return Panel(tree, title="Files", border_style="blue")

    def _add_directory_to_tree(self, tree: Tree, path: Path, depth: int, max_depth: int):
        """Recursively add directory contents to tree."""
        if depth >= max_depth:
            return

        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        ignore_files = {'.DS_Store', 'Thumbs.db'}

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

            for item in items[:20]:  # Limit items
                if item.name in ignore_dirs or item.name in ignore_files:
                    continue

                if item.is_dir():
                    branch = tree.add(f"📁 {item.name}")
                    self._add_directory_to_tree(branch, item, depth + 1, max_depth)
                else:
                    icon = self._get_file_icon(item.suffix)
                    style = "green" if str(item) == self.state.current_file else ""
                    tree.add(f"{icon} {item.name}", style=style)

        except PermissionError:
            tree.add("[dim]Permission denied[/dim]")

    def _get_file_icon(self, suffix: str) -> str:
        """Get icon for file type."""
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.yaml': '⚙️',
            '.yml': '⚙️',
            '.toml': '⚙️',
            '.sh': '🔧',
            '.ps1': '🔧',
            '.bat': '🔧',
            '.css': '🎨',
            '.html': '🌐',
            '.rs': '🦀',
            '.go': '🐹',
        }
        return icons.get(suffix.lower(), '📄')

    def _render_chat(self) -> Panel:
        """Render the chat panel."""
        chat_content = []

        for msg in self.state.messages[-10:]:  # Show last 10 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')[:500]

            if role == 'user':
                chat_content.append(Text(f"You: {content}\n", style="cyan"))
            else:
                chat_content.append(Text(f"Agent: {content}\n", style="green"))

        if not chat_content:
            chat_content.append(Text("Type your request below...", style="dim"))

        return Panel(
            Group(*chat_content),
            title="💬 Chat",
            border_style="green",
        )

    def _render_context(self) -> Panel:
        """Render the context panel."""
        if not self.state.context_files:
            content = Text("No files in context\n\nUse /attach <file> to add", style="dim")
        else:
            content = Text()
            content.append("Attached Files:\n\n", style="bold")
            for f in self.state.context_files[:10]:
                content.append(f"📎 {f}\n", style="cyan")

        return Panel(content, title="📎 Context", border_style="yellow")

    def _render_footer(self) -> Panel:
        """Render the footer/status panel."""
        footer_text = Text()
        footer_text.append(f"Status: {self.state.status} ", style="green")
        footer_text.append("│ ", style="dim")
        footer_text.append("[F1] Help ", style="dim")
        footer_text.append("[F2] Files ", style="dim")
        footer_text.append("[F3] Context ", style="dim")
        footer_text.append("[Ctrl+C] Exit", style="dim")

        return Panel(footer_text, style="dim", height=3)

    def render(self) -> Layout:
        """Render the full TUI."""
        self.layout["header"].update(self._render_header())
        self.layout["main"]["sidebar"].update(self._render_file_tree())
        self.layout["main"]["content"].update(self._render_chat())
        self.layout["main"]["context"].update(self._render_context())
        self.layout["footer"].update(self._render_footer())

        return self.layout

    def add_message(self, role: str, content: str):
        """Add a message to chat."""
        self.state.messages.append({
            'role': role,
            'content': content,
        })

    def set_status(self, status: str):
        """Set status message."""
        self.state.status = status

    def add_context_file(self, file_path: str):
        """Add file to context."""
        if file_path not in self.state.context_files:
            self.state.context_files.append(file_path)

    def remove_context_file(self, file_path: str):
        """Remove file from context."""
        if file_path in self.state.context_files:
            self.state.context_files.remove(file_path)

    def clear_context(self):
        """Clear all context files."""
        self.state.context_files = []

    def toggle_files(self):
        """Toggle file panel visibility."""
        self.state.show_files = not self.state.show_files
        self._setup_layout()

    def toggle_context(self):
        """Toggle context panel visibility."""
        self.state.show_context = not self.state.show_context
        self._setup_layout()

    def show_help(self):
        """Show help dialog."""
        help_text = """
## Keyboard Shortcuts
- F1: Show this help
- F2: Toggle file panel
- F3: Toggle context panel
- Ctrl+C: Exit

## Commands
- /help: Show all commands
- /attach <file>: Add file to context
- /clear: Clear chat history
- /exit: Exit TUI

## Tips
- Type naturally to interact with the agent
- Use Tab for auto-complete
- Arrow keys to scroll history
"""
        self.console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))

    def display_static(self):
        """Display static TUI (one-time render)."""
        self.console.print(self.render())

    def run_simple(self):
        """Run simplified TUI mode."""
        self.console.clear()

        # Header
        self.console.print(self._render_header())
        self.console.print()

        # Two-column layout simulation
        cols = self.console.size.width

        if cols > 100:
            # Wide terminal - show side panels
            table = Table(show_header=False, box=None, padding=0)
            table.add_column(width=25)
            table.add_column(ratio=1)
            table.add_column(width=30)

            # This is simplified - real implementation would need rich Layout
            self.console.print(self._render_file_tree())

        # Chat area
        self.console.print(self._render_chat())

        # Footer
        self.console.print(self._render_footer())


def create_tui(working_dir: Optional[Path] = None) -> TerminalUI:
    """Create a TUI instance."""
    return TerminalUI(working_dir)


def show_dashboard(working_dir: Optional[Path] = None):
    """Show a quick dashboard view."""
    from src.core.project_detector import detect_project
    from src.core.codebase_index import get_code_indexer

    console = Console()
    settings = get_settings()

    # Header
    console.print(Panel.fit(
        f"[bold blue]CODE AGENT DASHBOARD[/bold blue]\n"
        f"[dim]Model: {settings.ollama_model}[/dim]",
        border_style="blue",
    ))

    # Project info
    try:
        project = detect_project(working_dir)

        project_table = Table(title="Project Overview", show_header=False)
        project_table.add_column("Property", style="cyan")
        project_table.add_column("Value", style="green")

        project_table.add_row("Name", project.name)
        project_table.add_row("Language", project.primary_language)
        project_table.add_row("Files", str(project.file_count))
        project_table.add_row("Lines", f"{project.total_lines:,}")
        project_table.add_row("Frameworks", ", ".join(project.frameworks) or "None")
        project_table.add_row("Tests", "✓" if project.has_tests else "✗")
        project_table.add_row("Docs", "✓" if project.has_docs else "✗")

        console.print(project_table)
    except Exception as e:
        console.print(f"[red]Could not analyze project: {e}[/red]")

    # Index stats
    try:
        indexer = get_code_indexer(working_dir)
        if indexer.index:
            stats_table = Table(title="Codebase Index", show_header=False)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")

            stats_table.add_row("Symbols", str(indexer.index.total_symbols))
            stats_table.add_row("TODOs", str(len(indexer.get_all_todos())))

            for lang, count in indexer.index.languages.items():
                stats_table.add_row(f"{lang} files", str(count))

            console.print(stats_table)
    except Exception:
        pass

    console.print()
