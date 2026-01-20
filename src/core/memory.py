"""Persistent Memory System - Feature 2.

Remember conversations, decisions, and code changes across sessions:
- Session memory (within conversation)
- Long-term memory (across sessions)
- Semantic search for past conversations
- Context recall
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field

from src.config.settings import get_settings


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    timestamp: str
    type: str  # conversation, decision, code_change, error, solution
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    file_path: Optional[str] = None
    importance: int = 1  # 1-5, higher = more important


@dataclass
class ConversationSummary:
    """Summary of a conversation session."""
    session_id: str
    started_at: str
    ended_at: Optional[str]
    message_count: int
    topics: List[str]
    files_modified: List[str]
    key_decisions: List[str]
    errors_encountered: List[str]
    solutions_found: List[str]


class MemoryManager:
    """Manage persistent memory across sessions."""

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize memory manager."""
        settings = get_settings()
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.project_id = self._get_project_id()

        # Storage directories
        self.memory_dir = settings.data_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Project-specific memory
        self.project_memory_dir = self.memory_dir / self.project_id
        self.project_memory_dir.mkdir(parents=True, exist_ok=True)

        # Memory files
        self.entries_file = self.project_memory_dir / "entries.json"
        self.sessions_file = self.project_memory_dir / "sessions.json"
        self.index_file = self.project_memory_dir / "index.json"

        # Load existing data
        self.entries: List[MemoryEntry] = self._load_entries()
        self.sessions: List[ConversationSummary] = self._load_sessions()
        self.index: Dict[str, List[str]] = self._load_index()

        # Current session
        self.current_session: Optional[ConversationSummary] = None

        # Memory limits
        self.max_entries = 10000
        self.max_entry_size = 50000  # characters

    def _get_project_id(self) -> str:
        """Get unique ID for current project."""
        path_str = str(self.project_path.resolve())
        return hashlib.md5(path_str.encode()).hexdigest()[:12]

    def _load_entries(self) -> List[MemoryEntry]:
        """Load memory entries from disk."""
        if self.entries_file.exists():
            try:
                with open(self.entries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [MemoryEntry(**e) for e in data]
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _load_sessions(self) -> List[ConversationSummary]:
        """Load session summaries."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [ConversationSummary(**s) for s in data]
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _load_index(self) -> Dict[str, List[str]]:
        """Load search index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_entries(self):
        """Save entries to disk."""
        try:
            with open(self.entries_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(e) for e in self.entries[-self.max_entries:]], f, indent=2)
        except IOError:
            pass

    def _save_sessions(self):
        """Save sessions to disk."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(s) for s in self.sessions], f, indent=2)
        except IOError:
            pass

    def _save_index(self):
        """Save index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
        except IOError:
            pass

    def _generate_id(self) -> str:
        """Generate unique entry ID."""
        return f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for indexing."""
        import re
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text.lower())
        # Filter common words
        stopwords = {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'have', 'are', 'was', 'were', 'been'}
        return list(set(w for w in words if w not in stopwords))[:50]

    def _update_index(self, entry: MemoryEntry):
        """Update search index with entry."""
        keywords = self._extract_keywords(entry.content)
        keywords.extend(entry.tags)

        for keyword in keywords:
            if keyword not in self.index:
                self.index[keyword] = []
            if entry.id not in self.index[keyword]:
                self.index[keyword].append(entry.id)

    def start_session(self, session_id: str):
        """Start a new conversation session."""
        self.current_session = ConversationSummary(
            session_id=session_id,
            started_at=datetime.now().isoformat(),
            ended_at=None,
            message_count=0,
            topics=[],
            files_modified=[],
            key_decisions=[],
            errors_encountered=[],
            solutions_found=[],
        )

    def end_session(self):
        """End current session and save summary."""
        if self.current_session:
            self.current_session.ended_at = datetime.now().isoformat()
            self.sessions.append(self.current_session)
            self._save_sessions()
            self.current_session = None

    def remember(
        self,
        content: str,
        entry_type: str = "conversation",
        tags: Optional[List[str]] = None,
        context: Optional[Dict] = None,
        file_path: Optional[str] = None,
        importance: int = 1,
    ) -> MemoryEntry:
        """
        Store something in memory.

        Args:
            content: The content to remember
            entry_type: Type of memory (conversation, decision, code_change, error, solution)
            tags: Tags for categorization
            context: Additional context
            file_path: Related file path
            importance: 1-5 importance level

        Returns:
            Created memory entry
        """
        # Truncate if too long
        if len(content) > self.max_entry_size:
            content = content[:self.max_entry_size] + "...[truncated]"

        entry = MemoryEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            type=entry_type,
            content=content,
            context=context or {},
            tags=tags or [],
            project=str(self.project_path.name),
            file_path=file_path,
            importance=importance,
        )

        self.entries.append(entry)
        self._update_index(entry)
        self._save_entries()
        self._save_index()

        # Update session if active
        if self.current_session:
            self.current_session.message_count += 1
            if entry_type == "error":
                self.current_session.errors_encountered.append(content[:100])
            elif entry_type == "solution":
                self.current_session.solutions_found.append(content[:100])
            elif entry_type == "decision":
                self.current_session.key_decisions.append(content[:100])
            if file_path and file_path not in self.current_session.files_modified:
                self.current_session.files_modified.append(file_path)

        return entry

    def recall(
        self,
        query: str,
        limit: int = 10,
        entry_type: Optional[str] = None,
        min_importance: int = 1,
    ) -> List[MemoryEntry]:
        """
        Search memory for relevant entries.

        Args:
            query: Search query
            limit: Maximum results
            entry_type: Filter by type
            min_importance: Minimum importance level

        Returns:
            List of matching entries
        """
        keywords = self._extract_keywords(query)

        # Find matching entry IDs
        matching_ids: Dict[str, int] = {}
        for keyword in keywords:
            if keyword in self.index:
                for entry_id in self.index[keyword]:
                    matching_ids[entry_id] = matching_ids.get(entry_id, 0) + 1

        # Sort by match count
        sorted_ids = sorted(matching_ids.keys(), key=lambda x: -matching_ids[x])

        # Get entries
        results = []
        id_to_entry = {e.id: e for e in self.entries}

        for entry_id in sorted_ids:
            if entry_id in id_to_entry:
                entry = id_to_entry[entry_id]

                # Apply filters
                if entry_type and entry.type != entry_type:
                    continue
                if entry.importance < min_importance:
                    continue

                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def recall_recent(self, limit: int = 20, entry_type: Optional[str] = None) -> List[MemoryEntry]:
        """Get most recent memories."""
        entries = self.entries
        if entry_type:
            entries = [e for e in entries if e.type == entry_type]
        return list(reversed(entries[-limit:]))

    def recall_by_file(self, file_path: str, limit: int = 20) -> List[MemoryEntry]:
        """Get memories related to a specific file."""
        return [e for e in reversed(self.entries) if e.file_path == file_path][:limit]

    def recall_errors(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent errors."""
        return self.recall_recent(limit, entry_type="error")

    def recall_solutions(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent solutions."""
        return self.recall_recent(limit, entry_type="solution")

    def recall_decisions(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent decisions."""
        return self.recall_recent(limit, entry_type="decision")

    def get_context_for_prompt(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context from memory for a prompt.

        Args:
            query: The user's query
            max_tokens: Approximate max tokens for context

        Returns:
            Formatted context string
        """
        # Recall relevant memories
        memories = self.recall(query, limit=10)

        if not memories:
            return ""

        # Build context
        lines = ["## Relevant Past Context"]

        char_count = 0
        max_chars = max_tokens * 4  # Approximate

        for mem in memories:
            entry_text = f"\n**[{mem.type}]** ({mem.timestamp[:10]})"
            if mem.file_path:
                entry_text += f" - {mem.file_path}"
            entry_text += f"\n{mem.content[:500]}"

            if char_count + len(entry_text) > max_chars:
                break

            lines.append(entry_text)
            char_count += len(entry_text)

        return "\n".join(lines)

    def get_session_summary(self, session_id: Optional[str] = None) -> Optional[ConversationSummary]:
        """Get session summary."""
        if session_id:
            for session in self.sessions:
                if session.session_id == session_id:
                    return session
        return self.current_session

    def get_project_summary(self) -> Dict[str, Any]:
        """Get summary of project memory."""
        type_counts = {}
        for entry in self.entries:
            type_counts[entry.type] = type_counts.get(entry.type, 0) + 1

        return {
            "project": str(self.project_path.name),
            "total_entries": len(self.entries),
            "total_sessions": len(self.sessions),
            "entry_types": type_counts,
            "index_keywords": len(self.index),
            "oldest_entry": self.entries[0].timestamp if self.entries else None,
            "newest_entry": self.entries[-1].timestamp if self.entries else None,
        }

    def forget(self, entry_id: str) -> bool:
        """Remove a specific memory entry."""
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                self.entries.pop(i)
                self._save_entries()
                return True
        return False

    def clear_all(self):
        """Clear all memory for this project."""
        self.entries = []
        self.sessions = []
        self.index = {}
        self._save_entries()
        self._save_sessions()
        self._save_index()


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(project_path: Optional[Path] = None) -> MemoryManager:
    """Get or create memory manager."""
    global _memory_manager
    if _memory_manager is None or project_path:
        _memory_manager = MemoryManager(project_path)
    return _memory_manager


# Convenience functions
def remember(content: str, entry_type: str = "conversation", **kwargs) -> MemoryEntry:
    """Store something in memory."""
    return get_memory_manager().remember(content, entry_type, **kwargs)


def recall(query: str, limit: int = 10) -> List[MemoryEntry]:
    """Search memory."""
    return get_memory_manager().recall(query, limit)


def get_context_for_prompt(query: str) -> str:
    """Get memory context for a prompt."""
    return get_memory_manager().get_context_for_prompt(query)
