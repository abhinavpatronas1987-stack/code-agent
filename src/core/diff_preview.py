"""Diff Preview System - Feature 8.

Show exact changes before applying:
- Unified diff format
- Syntax highlighting
- Interactive accept/reject
- Hunk-by-hunk review
"""

import difflib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class DiffAction(Enum):
    """Actions for diff hunks."""
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"
    SKIP = "skip"


@dataclass
class DiffHunk:
    """A single diff hunk (change block)."""
    start_old: int
    count_old: int
    start_new: int
    count_new: int
    lines: List[str]
    context_before: List[str]
    context_after: List[str]


@dataclass
class FileDiff:
    """Diff for a single file."""
    file_path: str
    old_content: str
    new_content: str
    hunks: List[DiffHunk]
    is_new_file: bool = False
    is_deleted: bool = False


class DiffPreview:
    """Generate and manage diff previews."""

    def __init__(self, context_lines: int = 3):
        """Initialize diff preview."""
        self.context_lines = context_lines
        self.pending_changes: List[FileDiff] = []

    def create_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
    ) -> FileDiff:
        """
        Create a diff between old and new content.

        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content

        Returns:
            FileDiff object with hunks
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate unified diff
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=self.context_lines,
        ))

        # Parse into hunks
        hunks = self._parse_hunks(diff)

        return FileDiff(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            hunks=hunks,
            is_new_file=len(old_content) == 0,
            is_deleted=len(new_content) == 0,
        )

    def _parse_hunks(self, diff_lines: List[str]) -> List[DiffHunk]:
        """Parse diff output into hunks."""
        hunks = []
        current_hunk = None
        current_lines = []

        for line in diff_lines:
            if line.startswith("@@"):
                # Save previous hunk
                if current_hunk:
                    current_hunk.lines = current_lines
                    hunks.append(current_hunk)

                # Parse hunk header: @@ -start,count +start,count @@
                parts = line.split()
                old_range = parts[1][1:].split(",")
                new_range = parts[2][1:].split(",")

                current_hunk = DiffHunk(
                    start_old=int(old_range[0]),
                    count_old=int(old_range[1]) if len(old_range) > 1 else 1,
                    start_new=int(new_range[0]),
                    count_new=int(new_range[1]) if len(new_range) > 1 else 1,
                    lines=[],
                    context_before=[],
                    context_after=[],
                )
                current_lines = []

            elif current_hunk and not line.startswith(("---", "+++")):
                current_lines.append(line)

        # Save last hunk
        if current_hunk:
            current_hunk.lines = current_lines
            hunks.append(current_hunk)

        return hunks

    def format_diff(self, file_diff: FileDiff, color: bool = True) -> str:
        """
        Format diff for display.

        Args:
            file_diff: FileDiff to format
            color: Whether to include ANSI colors

        Returns:
            Formatted diff string
        """
        lines = []

        # Header
        if file_diff.is_new_file:
            lines.append(f"{'[NEW FILE]' if not color else '[green][NEW FILE][/green]'} {file_diff.file_path}")
        elif file_diff.is_deleted:
            lines.append(f"{'[DELETED]' if not color else '[red][DELETED][/red]'} {file_diff.file_path}")
        else:
            lines.append(f"{'[MODIFIED]' if not color else '[yellow][MODIFIED][/yellow]'} {file_diff.file_path}")

        lines.append("")

        # Hunks
        for i, hunk in enumerate(file_diff.hunks, 1):
            lines.append(f"--- Hunk {i}/{len(file_diff.hunks)} ---")
            lines.append(f"@@ -{hunk.start_old},{hunk.count_old} +{hunk.start_new},{hunk.count_new} @@")

            for line in hunk.lines:
                if line.startswith("+"):
                    if color:
                        lines.append(f"[green]{line.rstrip()}[/green]")
                    else:
                        lines.append(line.rstrip())
                elif line.startswith("-"):
                    if color:
                        lines.append(f"[red]{line.rstrip()}[/red]")
                    else:
                        lines.append(line.rstrip())
                else:
                    lines.append(f"  {line.rstrip()}" if line.strip() else "")

            lines.append("")

        return "\n".join(lines)

    def format_inline_diff(self, old_content: str, new_content: str) -> str:
        """Format an inline word-by-word diff."""
        old_words = old_content.split()
        new_words = new_content.split()

        matcher = difflib.SequenceMatcher(None, old_words, new_words)
        result = []

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                result.extend(old_words[i1:i2])
            elif op == "delete":
                result.append(f"[red][-{' '.join(old_words[i1:i2])}-][/red]")
            elif op == "insert":
                result.append(f"[green][+{' '.join(new_words[j1:j2])}+][/green]")
            elif op == "replace":
                result.append(f"[red][-{' '.join(old_words[i1:i2])}-][/red]")
                result.append(f"[green][+{' '.join(new_words[j1:j2])}+][/green]")

        return " ".join(result)

    def add_pending_change(self, file_diff: FileDiff):
        """Add a change to pending list."""
        # Remove existing diff for same file
        self.pending_changes = [d for d in self.pending_changes if d.file_path != file_diff.file_path]
        self.pending_changes.append(file_diff)

    def get_pending_changes(self) -> List[FileDiff]:
        """Get all pending changes."""
        return self.pending_changes

    def clear_pending(self):
        """Clear all pending changes."""
        self.pending_changes = []

    def apply_change(self, file_diff: FileDiff) -> Dict[str, Any]:
        """
        Apply a file change.

        Args:
            file_diff: The diff to apply

        Returns:
            Result dict
        """
        try:
            file_path = Path(file_diff.file_path)

            if file_diff.is_deleted:
                if file_path.exists():
                    file_path.unlink()
                return {"success": True, "action": "deleted", "path": str(file_path)}

            # Create parent dirs if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write new content
            file_path.write_text(file_diff.new_content, encoding='utf-8')

            return {"success": True, "action": "written", "path": str(file_path)}

        except Exception as e:
            return {"success": False, "error": str(e), "path": file_diff.file_path}

    def apply_all_pending(self) -> List[Dict[str, Any]]:
        """Apply all pending changes."""
        results = []
        for diff in self.pending_changes:
            results.append(self.apply_change(diff))
        self.clear_pending()
        return results


# Global instance
_diff_preview: Optional[DiffPreview] = None


def get_diff_preview() -> DiffPreview:
    """Get or create diff preview instance."""
    global _diff_preview
    if _diff_preview is None:
        _diff_preview = DiffPreview()
    return _diff_preview


def preview_file_change(
    file_path: str,
    new_content: str,
    old_content: Optional[str] = None,
) -> str:
    """
    Generate preview for a file change.

    Args:
        file_path: Path to file
        new_content: New content to write
        old_content: Original content (read from file if not provided)

    Returns:
        Formatted diff string
    """
    path = Path(file_path)

    if old_content is None:
        if path.exists():
            try:
                old_content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                old_content = "[Binary file]"
        else:
            old_content = ""

    diff_preview = get_diff_preview()
    file_diff = diff_preview.create_diff(file_path, old_content, new_content)
    diff_preview.add_pending_change(file_diff)

    return diff_preview.format_diff(file_diff)


def apply_pending_changes() -> List[Dict[str, Any]]:
    """Apply all pending changes."""
    return get_diff_preview().apply_all_pending()


def clear_pending_changes():
    """Clear pending changes."""
    get_diff_preview().clear_pending()


def get_change_summary() -> Dict[str, int]:
    """Get summary of pending changes."""
    changes = get_diff_preview().get_pending_changes()
    return {
        "total": len(changes),
        "new_files": sum(1 for c in changes if c.is_new_file),
        "modified": sum(1 for c in changes if not c.is_new_file and not c.is_deleted),
        "deleted": sum(1 for c in changes if c.is_deleted),
        "total_hunks": sum(len(c.hunks) for c in changes),
    }
