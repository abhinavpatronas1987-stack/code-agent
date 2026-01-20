"""Smart Context Window - Feature 4.

Intelligent context management:
- Auto-include relevant files
- Token budget management
- Priority-based inclusion
- Context compression
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

from src.config.settings import get_settings


@dataclass
class ContextItem:
    """An item in the context window."""
    path: str
    content: str
    priority: float  # 0.0 to 1.0
    tokens: int
    source: str  # "explicit", "auto", "memory"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """The current context window."""
    items: List[ContextItem] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 8000
    query: str = ""


class SmartContextManager:
    """Manage intelligent context for the agent."""

    # Approximate tokens per character
    TOKENS_PER_CHAR = 0.25

    # File importance by extension
    FILE_PRIORITIES = {
        '.py': 0.9,
        '.ts': 0.9,
        '.tsx': 0.9,
        '.js': 0.85,
        '.jsx': 0.85,
        '.rs': 0.9,
        '.go': 0.9,
        '.java': 0.85,
        '.json': 0.7,
        '.yaml': 0.7,
        '.yml': 0.7,
        '.toml': 0.7,
        '.md': 0.6,
        '.txt': 0.5,
        '.sh': 0.6,
        '.sql': 0.8,
    }

    # Important file patterns
    IMPORTANT_FILES = {
        'package.json': 0.95,
        'pyproject.toml': 0.95,
        'Cargo.toml': 0.95,
        'go.mod': 0.95,
        'requirements.txt': 0.9,
        'setup.py': 0.9,
        '.env.example': 0.8,
        'README.md': 0.85,
        'Makefile': 0.8,
        'Dockerfile': 0.85,
        'docker-compose.yml': 0.85,
    }

    def __init__(self, working_dir: Optional[Path] = None, max_tokens: int = 8000):
        """Initialize context manager."""
        self.working_dir = working_dir or Path.cwd()
        self.max_tokens = max_tokens
        self.context = ContextWindow(max_tokens=max_tokens)
        self.explicit_files: Set[str] = set()
        self.file_cache: Dict[str, str] = {}

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return int(len(text) * self.TOKENS_PER_CHAR)

    def add_file(self, path: str, priority: Optional[float] = None) -> bool:
        """
        Add a file to context explicitly.

        Args:
            path: File path
            priority: Optional priority override

        Returns:
            True if added successfully
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.working_dir / path

        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return False

        tokens = self.estimate_tokens(content)
        if tokens > self.max_tokens // 2:
            # File too large, truncate
            max_chars = (self.max_tokens // 2) // self.TOKENS_PER_CHAR
            content = content[:int(max_chars)] + "\n... (truncated)"
            tokens = self.estimate_tokens(content)

        if priority is None:
            priority = self._get_file_priority(file_path)

        item = ContextItem(
            path=str(file_path),
            content=content,
            priority=priority,
            tokens=tokens,
            source="explicit",
        )

        self.explicit_files.add(str(file_path))
        self._add_item(item)
        return True

    def remove_file(self, path: str) -> bool:
        """Remove a file from context."""
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.working_dir / path

        path_str = str(file_path)
        self.explicit_files.discard(path_str)

        for i, item in enumerate(self.context.items):
            if item.path == path_str:
                self.context.items.pop(i)
                self._recalculate_tokens()
                return True

        return False

    def clear(self):
        """Clear all context."""
        self.context.items = []
        self.context.total_tokens = 0
        self.explicit_files.clear()

    def build_context_for_query(self, query: str) -> ContextWindow:
        """
        Build optimized context for a query.

        Args:
            query: User's query/prompt

        Returns:
            Optimized context window
        """
        self.context.query = query

        # Start with explicit files
        items = [item for item in self.context.items if item.source == "explicit"]

        # Auto-discover relevant files
        auto_files = self._find_relevant_files(query)

        for path, score in auto_files:
            if str(path) not in self.explicit_files:
                try:
                    content = path.read_text(encoding='utf-8')
                    tokens = self.estimate_tokens(content)

                    if tokens > self.max_tokens // 4:
                        # Truncate large files
                        max_chars = (self.max_tokens // 4) // self.TOKENS_PER_CHAR
                        content = content[:int(max_chars)] + "\n... (truncated)"
                        tokens = self.estimate_tokens(content)

                    items.append(ContextItem(
                        path=str(path),
                        content=content,
                        priority=score,
                        tokens=tokens,
                        source="auto",
                    ))
                except (IOError, UnicodeDecodeError):
                    continue

        # Sort by priority and fit within budget
        items.sort(key=lambda x: x.priority, reverse=True)
        final_items = []
        total_tokens = 0

        for item in items:
            if total_tokens + item.tokens <= self.max_tokens:
                final_items.append(item)
                total_tokens += item.tokens

        self.context.items = final_items
        self.context.total_tokens = total_tokens

        return self.context

    def _get_file_priority(self, path: Path) -> float:
        """Get priority for a file."""
        # Check important files
        if path.name in self.IMPORTANT_FILES:
            return self.IMPORTANT_FILES[path.name]

        # Check by extension
        return self.FILE_PRIORITIES.get(path.suffix.lower(), 0.5)

    def _find_relevant_files(self, query: str) -> List[tuple]:
        """Find files relevant to the query."""
        results = []

        # Extract potential file/function names from query
        keywords = self._extract_keywords(query)

        # Search for files
        try:
            for path in self.working_dir.rglob('*'):
                if not path.is_file():
                    continue

                # Skip ignored directories
                parts = path.parts
                if any(p.startswith('.') or p in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build')
                       for p in parts):
                    continue

                # Skip non-text files
                if path.suffix.lower() not in self.FILE_PRIORITIES:
                    continue

                # Calculate relevance score
                score = self._calculate_relevance(path, keywords)
                if score > 0.3:
                    results.append((path, score))

        except Exception:
            pass

        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)

        # Return top 10
        return results[:10]

    def _extract_keywords(self, query: str) -> Set[str]:
        """Extract keywords from query."""
        keywords = set()

        # Words that look like identifiers
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query)
        for word in words:
            if len(word) > 2:
                keywords.add(word.lower())

        # File patterns
        files = re.findall(r'[\w\-]+\.\w+', query)
        for f in files:
            keywords.add(f.lower())

        return keywords

    def _calculate_relevance(self, path: Path, keywords: Set[str]) -> float:
        """Calculate relevance score for a file."""
        score = 0.0

        # Base priority from file type
        base_priority = self._get_file_priority(path)
        score += base_priority * 0.3

        # Check filename match
        name_lower = path.name.lower()
        stem_lower = path.stem.lower()

        for keyword in keywords:
            if keyword in name_lower:
                score += 0.3
            elif keyword in stem_lower:
                score += 0.2

        # Check path match
        path_str = str(path).lower()
        for keyword in keywords:
            if keyword in path_str:
                score += 0.1

        # Content matching (cached)
        try:
            path_str = str(path)
            if path_str not in self.file_cache:
                content = path.read_text(encoding='utf-8')[:5000]  # First 5000 chars
                self.file_cache[path_str] = content.lower()

            content = self.file_cache[path_str]
            matches = sum(1 for k in keywords if k in content)
            score += min(0.3, matches * 0.05)

        except (IOError, UnicodeDecodeError):
            pass

        return min(1.0, score)

    def _add_item(self, item: ContextItem):
        """Add item to context, managing budget."""
        # Remove existing item with same path
        self.context.items = [i for i in self.context.items if i.path != item.path]

        # Add new item
        self.context.items.append(item)
        self._recalculate_tokens()

        # Trim if over budget
        self._trim_to_budget()

    def _recalculate_tokens(self):
        """Recalculate total tokens."""
        self.context.total_tokens = sum(item.tokens for item in self.context.items)

    def _trim_to_budget(self):
        """Trim context to fit within budget."""
        if self.context.total_tokens <= self.max_tokens:
            return

        # Sort: explicit first, then by priority
        self.context.items.sort(
            key=lambda x: (x.source == "explicit", x.priority),
            reverse=True
        )

        # Remove lowest priority items until within budget
        while self.context.total_tokens > self.max_tokens and self.context.items:
            # Don't remove explicit items
            for i in range(len(self.context.items) - 1, -1, -1):
                if self.context.items[i].source != "explicit":
                    self.context.items.pop(i)
                    self._recalculate_tokens()
                    break
            else:
                # Only explicit items left, truncate the largest
                if self.context.items:
                    largest = max(self.context.items, key=lambda x: x.tokens)
                    max_chars = (self.max_tokens // len(self.context.items)) // self.TOKENS_PER_CHAR
                    largest.content = largest.content[:int(max_chars)] + "\n... (truncated)"
                    largest.tokens = self.estimate_tokens(largest.content)
                    self._recalculate_tokens()
                break

    def get_context_string(self) -> str:
        """Get context as a formatted string."""
        if not self.context.items:
            return ""

        parts = ["# Context Files\n"]

        for item in self.context.items:
            rel_path = item.path
            try:
                rel_path = str(Path(item.path).relative_to(self.working_dir))
            except ValueError:
                pass

            parts.append(f"\n## {rel_path}\n")
            parts.append(f"```\n{item.content}\n```\n")

        return "\n".join(parts)

    def get_summary(self) -> Dict[str, Any]:
        """Get context summary."""
        return {
            "total_files": len(self.context.items),
            "explicit_files": len(self.explicit_files),
            "auto_files": len([i for i in self.context.items if i.source == "auto"]),
            "total_tokens": self.context.total_tokens,
            "max_tokens": self.max_tokens,
            "usage_percent": (self.context.total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            "files": [
                {
                    "path": item.path,
                    "tokens": item.tokens,
                    "priority": item.priority,
                    "source": item.source,
                }
                for item in self.context.items
            ],
        }

    def list_files(self) -> List[str]:
        """List files in context."""
        return [item.path for item in self.context.items]


# Global context manager
_context_manager: Optional[SmartContextManager] = None


def get_context_manager(working_dir: Optional[Path] = None) -> SmartContextManager:
    """Get or create context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = SmartContextManager(working_dir)
    return _context_manager


# Convenience functions
def add_to_context(path: str) -> bool:
    """Add file to context."""
    return get_context_manager().add_file(path)


def remove_from_context(path: str) -> bool:
    """Remove file from context."""
    return get_context_manager().remove_file(path)


def build_context(query: str) -> ContextWindow:
    """Build context for query."""
    return get_context_manager().build_context_for_query(query)


def get_context_summary() -> Dict[str, Any]:
    """Get context summary."""
    return get_context_manager().get_summary()


def clear_context():
    """Clear all context."""
    get_context_manager().clear()
