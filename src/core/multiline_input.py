"""Multi-line input handler for CLI - Similar to Claude Code input experience."""

import sys
import os
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

console = Console()


class MultilineInput:
    """
    Multi-line input handler with paste support.

    Features:
    - Multi-line input (Enter for new line, double Enter or Ctrl+D to submit)
    - Paste detection and handling
    - Visual feedback showing input mode
    - Line count display
    - Cancel with Ctrl+C
    """

    def __init__(
        self,
        prompt: str = ">",
        continuation_prompt: str = "...",
        submit_on_double_enter: bool = True,
        show_line_count: bool = True,
    ):
        self.prompt = prompt
        self.continuation_prompt = continuation_prompt
        self.submit_on_double_enter = submit_on_double_enter
        self.show_line_count = show_line_count

    def get_input(self, initial_prompt: Optional[str] = None) -> Tuple[str, bool]:
        """
        Get multi-line input from user.

        Returns:
            Tuple of (input_text, was_cancelled)
        """
        lines = []
        prompt = initial_prompt or self.prompt
        last_was_empty = False

        # Show input hint
        console.print("[dim]Enter your message (press Enter twice to send, Ctrl+C to cancel)[/dim]")

        try:
            while True:
                # Show appropriate prompt
                if lines:
                    display_prompt = f"[dim]{self.continuation_prompt}[/dim] "
                else:
                    display_prompt = f"[bold cyan]{prompt}[/bold cyan] "

                # Get line
                console.print(display_prompt, end="")
                try:
                    line = input()
                except EOFError:
                    # Ctrl+D pressed - submit
                    break

                # Check for double enter to submit
                if self.submit_on_double_enter and line == "" and last_was_empty:
                    # Remove the last empty line we added
                    if lines and lines[-1] == "":
                        lines.pop()
                    break

                lines.append(line)
                last_was_empty = (line == "")

                # Show line count for multi-line input
                if self.show_line_count and len(lines) > 1:
                    # Move cursor up and show count
                    pass  # Rich handles this differently

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return "", True

        return "\n".join(lines), False


class EnhancedInput:
    """
    Enhanced input with paste detection and better UX.
    """

    def __init__(self):
        self.is_windows = sys.platform == 'win32'

    def get_input(self, prompt_prefix: str = "") -> Tuple[str, bool]:
        """
        Get input with enhanced features.

        Features:
        - Single line for simple inputs
        - Auto-detects paste (multiple lines)
        - Shows visual feedback

        Returns:
            Tuple of (input_text, was_cancelled)
        """
        console.print()
        console.print(f"[bold cyan]{prompt_prefix}[/bold cyan] [dim]>[/dim] ", end="")

        try:
            # Try to read first line
            first_line = input()

            # Check if it looks like there might be more (pasted content)
            # On Windows, pasted content usually comes all at once
            # We'll use a simple heuristic: if the line ends with certain chars, prompt for more

            if not first_line.strip():
                return "", False

            # Check if this might be a multi-line paste or user wants to continue
            if first_line.rstrip().endswith(('\\', '{', '[', '(', ':',  '"""', "'''")):
                return self._get_multiline(first_line)

            # Check if user typed special command for multi-line mode
            if first_line.strip() == '"""' or first_line.strip() == "'''":
                return self._get_multiline_block(first_line.strip())

            return first_line, False

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return "", True
        except EOFError:
            return "", True

    def _get_multiline(self, first_line: str) -> Tuple[str, bool]:
        """Continue reading multi-line input."""
        lines = [first_line]
        empty_count = 0

        console.print("[dim]  ... (Enter twice to send)[/dim]")

        try:
            while True:
                console.print("[dim]  ...[/dim] ", end="")
                line = input()

                if line == "":
                    empty_count += 1
                    if empty_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_count = 0
                    lines.append(line)

        except (KeyboardInterrupt, EOFError):
            pass

        # Remove trailing empty lines
        while lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines), False

    def _get_multiline_block(self, delimiter: str) -> Tuple[str, bool]:
        """Read a block of text until delimiter is seen again."""
        lines = []

        console.print(f"[dim]  ... (enter {delimiter} on new line to send)[/dim]")

        try:
            while True:
                console.print("[dim]  ...[/dim] ", end="")
                line = input()

                if line.strip() == delimiter:
                    break

                lines.append(line)

        except (KeyboardInterrupt, EOFError):
            pass

        return "\n".join(lines), False


class RichMultilineInput:
    """
    Rich multi-line input with visual panel display.
    """

    def __init__(self, working_dir: str = ""):
        self.working_dir = working_dir
        self.is_windows = sys.platform == 'win32'

    def get_input(self) -> Tuple[str, bool]:
        """
        Get input with rich display.

        Modes:
        - Single line: Just type and press Enter
        - Multi-line: Start with ``` or press Shift+Enter (shown as typing on new line)
        - Paste: Automatically detected

        Returns:
            Tuple of (input_text, was_cancelled)
        """
        lines = []
        is_multiline = False
        delimiter = None

        # Show prompt
        dir_display = self.working_dir.split('\\')[-1] if '\\' in self.working_dir else self.working_dir.split('/')[-1]
        if not dir_display:
            dir_display = "~"

        try:
            # First line
            console.print(f"\n[bold cyan]{dir_display}[/bold cyan] [green]>[/green] ", end="")
            first_line = input()

            if not first_line:
                return "", False

            # Check for multi-line mode triggers
            if first_line.strip() in ('```', '"""', "'''"):
                delimiter = first_line.strip()
                is_multiline = True
                console.print(f"[dim]  Multi-line mode (enter {delimiter} to send)[/dim]")
            elif first_line.rstrip().endswith('\\'):
                is_multiline = True
                lines.append(first_line.rstrip()[:-1])  # Remove trailing backslash
                console.print("[dim]  Continuing... (empty line to send)[/dim]")
            else:
                # Check for incomplete structures
                open_brackets = first_line.count('{') - first_line.count('}')
                open_brackets += first_line.count('[') - first_line.count(']')
                open_brackets += first_line.count('(') - first_line.count(')')

                if open_brackets > 0 or first_line.rstrip().endswith(':'):
                    is_multiline = True
                    lines.append(first_line)
                    console.print("[dim]  Continuing... (Enter twice to send)[/dim]")
                else:
                    return first_line, False

            if not lines and is_multiline and delimiter:
                # Block mode - read until delimiter
                while True:
                    console.print("[dim]  |[/dim] ", end="")
                    line = input()
                    if line.strip() == delimiter:
                        break
                    lines.append(line)
            else:
                # Continue reading lines
                empty_count = 0
                while True:
                    console.print("[dim]  |[/dim] ", end="")
                    line = input()

                    if line == "":
                        empty_count += 1
                        if empty_count >= 2:
                            break
                        lines.append(line)
                    else:
                        empty_count = 0
                        if line.rstrip().endswith('\\'):
                            lines.append(line.rstrip()[:-1])
                        else:
                            lines.append(line)

            # Clean up trailing empty lines
            while lines and lines[-1] == "":
                lines.pop()

            result = "\n".join(lines)

            # Show what was captured for multi-line
            if len(lines) > 1:
                console.print(f"[dim]  ({len(lines)} lines)[/dim]")

            return result, False

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return "", True
        except EOFError:
            return "\n".join(lines) if lines else "", False


def get_multiline_input(working_dir: str = "") -> Tuple[str, bool]:
    """
    Convenience function for getting multi-line input.

    Usage:
        text, cancelled = get_multiline_input("/path/to/project")
        if not cancelled and text:
            process(text)

    Returns:
        Tuple of (input_text, was_cancelled)
    """
    handler = RichMultilineInput(working_dir)
    return handler.get_input()


# Simple paste-aware input for basic usage
def get_input_simple(prompt: str = ">") -> Tuple[str, bool]:
    """
    Simple input with basic multi-line support.

    - Type message and press Enter to send
    - Use ``` to start multi-line mode
    - Paste is automatically handled

    Returns:
        Tuple of (input_text, was_cancelled)
    """
    try:
        console.print(f"[bold cyan]{prompt}[/bold cyan] ", end="")
        line = input()

        if not line:
            return "", False

        # Multi-line mode
        if line.strip() in ('```', '"""', "'''", '<<<'):
            lines = []
            end_marker = line.strip()
            if end_marker == '<<<':
                end_marker = '>>>'

            console.print(f"[dim]Enter text, then {end_marker} to send:[/dim]")
            while True:
                console.print("[dim]|[/dim] ", end="")
                next_line = input()
                if next_line.strip() == end_marker:
                    break
                lines.append(next_line)

            return "\n".join(lines), False

        return line, False

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        return "", True
    except EOFError:
        return "", True
