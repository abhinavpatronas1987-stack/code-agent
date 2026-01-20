"""Watch Mode - Feature 15.

Continuous file watching with auto-suggestions:
- Monitor file changes
- Auto-detect issues
- Suggest fixes in real-time
- Hot reload detection
"""

import os
import time
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Set
from dataclasses import dataclass
from enum import Enum

from src.config.settings import get_settings


class ChangeType(Enum):
    """Types of file changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChange:
    """A file change event."""
    path: str
    change_type: str
    timestamp: str
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    size: int = 0


@dataclass
class WatchIssue:
    """An issue detected during watch."""
    file_path: str
    line: Optional[int]
    issue_type: str  # syntax_error, unused_import, type_error, etc.
    message: str
    suggestion: Optional[str]
    severity: str  # error, warning, info


class FileWatcher:
    """Watch files for changes."""

    # Ignore patterns
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
        'dist', 'build', '.tox', '.pytest_cache', '.mypy_cache', 'target',
    }

    IGNORE_EXTENSIONS = {
        '.pyc', '.pyo', '.so', '.dll', '.log', '.tmp', '.swp', '.swo',
    }

    def __init__(
        self,
        project_path: Optional[Path] = None,
        on_change: Optional[Callable[[FileChange], None]] = None,
        on_issue: Optional[Callable[[WatchIssue], None]] = None,
    ):
        """Initialize file watcher."""
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.on_change = on_change
        self.on_issue = on_issue

        # File state tracking
        self.file_hashes: Dict[str, str] = {}
        self.file_mtimes: Dict[str, float] = {}

        # Watch state
        self.running = False
        self.watch_thread: Optional[threading.Thread] = None
        self.poll_interval = 1.0  # seconds

        # Change history
        self.changes: List[FileChange] = []
        self.issues: List[WatchIssue] = []

        # Initialize file state
        self._scan_files()

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        parts = path.parts

        # Check directory names
        for part in parts:
            if part in self.IGNORE_DIRS:
                return True

        # Check extension
        if path.suffix.lower() in self.IGNORE_EXTENSIONS:
            return True

        # Check if hidden
        if path.name.startswith('.'):
            return True

        return False

    def _hash_file(self, path: Path) -> Optional[str]:
        """Get hash of file content."""
        try:
            content = path.read_bytes()
            return hashlib.md5(content).hexdigest()[:16]
        except (IOError, PermissionError):
            return None

    def _scan_files(self) -> Dict[str, str]:
        """Scan all files and get their hashes."""
        hashes = {}

        for root, dirs, files in os.walk(self.project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for filename in files:
                file_path = Path(root) / filename

                if self._should_ignore(file_path):
                    continue

                rel_path = str(file_path.relative_to(self.project_path))
                file_hash = self._hash_file(file_path)

                if file_hash:
                    hashes[rel_path] = file_hash
                    try:
                        self.file_mtimes[rel_path] = file_path.stat().st_mtime
                    except OSError:
                        pass

        return hashes

    def _detect_changes(self) -> List[FileChange]:
        """Detect file changes since last scan."""
        changes = []
        new_hashes = self._scan_files()

        # Check for modified/created files
        for path, new_hash in new_hashes.items():
            old_hash = self.file_hashes.get(path)

            if old_hash is None:
                # New file
                changes.append(FileChange(
                    path=path,
                    change_type=ChangeType.CREATED.value,
                    timestamp=datetime.now().isoformat(),
                    new_hash=new_hash,
                    size=self._get_file_size(path),
                ))
            elif old_hash != new_hash:
                # Modified file
                changes.append(FileChange(
                    path=path,
                    change_type=ChangeType.MODIFIED.value,
                    timestamp=datetime.now().isoformat(),
                    old_hash=old_hash,
                    new_hash=new_hash,
                    size=self._get_file_size(path),
                ))

        # Check for deleted files
        for path in set(self.file_hashes.keys()) - set(new_hashes.keys()):
            changes.append(FileChange(
                path=path,
                change_type=ChangeType.DELETED.value,
                timestamp=datetime.now().isoformat(),
                old_hash=self.file_hashes[path],
            ))

        # Update state
        self.file_hashes = new_hashes

        return changes

    def _get_file_size(self, rel_path: str) -> int:
        """Get file size."""
        try:
            return (self.project_path / rel_path).stat().st_size
        except OSError:
            return 0

    def _analyze_file(self, file_path: str) -> List[WatchIssue]:
        """Analyze a file for issues."""
        issues = []
        full_path = self.project_path / file_path

        if not full_path.exists():
            return issues

        suffix = full_path.suffix.lower()

        try:
            content = full_path.read_text(encoding='utf-8', errors='ignore')
        except IOError:
            return issues

        # Python-specific checks
        if suffix == '.py':
            issues.extend(self._analyze_python(file_path, content))

        # JavaScript/TypeScript checks
        elif suffix in ('.js', '.jsx', '.ts', '.tsx'):
            issues.extend(self._analyze_javascript(file_path, content))

        return issues

    def _analyze_python(self, file_path: str, content: str) -> List[WatchIssue]:
        """Analyze Python file for common issues."""
        issues = []
        lines = content.splitlines()

        # Track imports
        imports = set()
        used_names = set()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Syntax check - basic patterns
            if stripped.startswith('def ') and not stripped.endswith(':'):
                if '(' in stripped and ')' in stripped and ':' not in stripped:
                    issues.append(WatchIssue(
                        file_path=file_path,
                        line=line_num,
                        issue_type="syntax_error",
                        message="Function definition missing colon",
                        suggestion="Add ':' at the end of the function definition",
                        severity="error",
                    ))

            if stripped.startswith('class ') and not stripped.endswith(':'):
                if '(' in stripped and ')' in stripped and ':' not in stripped:
                    issues.append(WatchIssue(
                        file_path=file_path,
                        line=line_num,
                        issue_type="syntax_error",
                        message="Class definition missing colon",
                        suggestion="Add ':' at the end of the class definition",
                        severity="error",
                    ))

            # Track imports
            if stripped.startswith('import '):
                parts = stripped[7:].split(',')
                for part in parts:
                    name = part.strip().split(' as ')[0].split('.')[0]
                    imports.add(name)

            if stripped.startswith('from ') and 'import' in stripped:
                import_part = stripped.split('import')[1]
                for name in import_part.split(','):
                    name = name.strip().split(' as ')[-1]
                    if name != '*':
                        imports.add(name)

            # Track used names (simplified)
            import re
            words = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', line)
            used_names.update(words)

        # Check for unused imports (simplified)
        for imp in imports:
            if imp not in used_names and imp not in ('os', 'sys', 'typing', 're', 'json'):
                issues.append(WatchIssue(
                    file_path=file_path,
                    line=None,
                    issue_type="unused_import",
                    message=f"Possibly unused import: {imp}",
                    suggestion=f"Remove unused import '{imp}' if not needed",
                    severity="warning",
                ))

        # Check for common issues
        if 'print(' in content and 'import logging' not in content:
            count = content.count('print(')
            if count > 5:
                issues.append(WatchIssue(
                    file_path=file_path,
                    line=None,
                    issue_type="code_quality",
                    message=f"Found {count} print statements",
                    suggestion="Consider using logging instead of print",
                    severity="info",
                ))

        return issues

    def _analyze_javascript(self, file_path: str, content: str) -> List[WatchIssue]:
        """Analyze JavaScript/TypeScript file for common issues."""
        issues = []

        # Check for console.log
        if 'console.log' in content:
            count = content.count('console.log')
            if count > 3:
                issues.append(WatchIssue(
                    file_path=file_path,
                    line=None,
                    issue_type="code_quality",
                    message=f"Found {count} console.log statements",
                    suggestion="Consider removing debug logs before commit",
                    severity="info",
                ))

        # Check for var usage
        if 'var ' in content:
            issues.append(WatchIssue(
                file_path=file_path,
                line=None,
                issue_type="code_quality",
                message="Using 'var' instead of 'let' or 'const'",
                suggestion="Use 'const' for constants and 'let' for variables",
                severity="warning",
            ))

        return issues

    def _watch_loop(self):
        """Main watch loop."""
        while self.running:
            try:
                changes = self._detect_changes()

                for change in changes:
                    self.changes.append(change)

                    # Callback
                    if self.on_change:
                        self.on_change(change)

                    # Analyze changed file
                    if change.change_type != ChangeType.DELETED.value:
                        issues = self._analyze_file(change.path)
                        for issue in issues:
                            self.issues.append(issue)
                            if self.on_issue:
                                self.on_issue(issue)

                time.sleep(self.poll_interval)

            except Exception as e:
                # Log error but continue watching
                print(f"Watch error: {e}")
                time.sleep(self.poll_interval)

    def start(self):
        """Start watching."""
        if self.running:
            return

        self.running = True
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def stop(self):
        """Stop watching."""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2)
            self.watch_thread = None

    def get_recent_changes(self, limit: int = 20) -> List[FileChange]:
        """Get recent changes."""
        return list(reversed(self.changes[-limit:]))

    def get_recent_issues(self, limit: int = 20) -> List[WatchIssue]:
        """Get recent issues."""
        return list(reversed(self.issues[-limit:]))

    def clear_history(self):
        """Clear change history."""
        self.changes = []
        self.issues = []


# Global watcher instance
_file_watcher: Optional[FileWatcher] = None


def get_file_watcher(project_path: Optional[Path] = None) -> FileWatcher:
    """Get or create file watcher."""
    global _file_watcher
    if _file_watcher is None:
        _file_watcher = FileWatcher(project_path)
    return _file_watcher


def start_watch(
    on_change: Optional[Callable] = None,
    on_issue: Optional[Callable] = None,
) -> FileWatcher:
    """Start file watching."""
    watcher = get_file_watcher()
    watcher.on_change = on_change
    watcher.on_issue = on_issue
    watcher.start()
    return watcher


def stop_watch():
    """Stop file watching."""
    global _file_watcher
    if _file_watcher:
        _file_watcher.stop()
