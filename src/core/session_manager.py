"""Session Manager - Feature 16.

Session management:
- Save/resume sessions
- Session history
- Context restoration
- Multi-project switching
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from src.config.settings import get_settings


@dataclass
class Message:
    """A conversation message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = ""
    tool_calls: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Session:
    """A code agent session."""
    id: str
    name: str
    project_path: str
    created_at: str = ""
    updated_at: str = ""
    messages: List[Message] = field(default_factory=list)
    context_files: List[str] = field(default_factory=list)
    model: str = ""
    profile: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


class SessionManager:
    """Manage code agent sessions."""

    def __init__(self):
        """Initialize session manager."""
        settings = get_settings()
        self.sessions_dir = settings.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[Session] = None
        self._index: Dict[str, Dict] = {}
        self._load_index()

    def _load_index(self):
        """Load session index."""
        index_file = self.sessions_dir / "index.json"
        if index_file.exists():
            try:
                self._index = json.loads(index_file.read_text())
            except (json.JSONDecodeError, IOError):
                self._index = {}

    def _save_index(self):
        """Save session index."""
        index_file = self.sessions_dir / "index.json"
        try:
            index_file.write_text(json.dumps(self._index, indent=2))
        except IOError:
            pass

    def _generate_id(self, name: str, project: str) -> str:
        """Generate session ID."""
        data = f"{name}:{project}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]

    def create(
        self,
        name: str,
        project_path: Optional[Path] = None,
        model: str = "",
        profile: str = "",
    ) -> Session:
        """
        Create a new session.

        Args:
            name: Session name
            project_path: Project directory
            model: Model to use
            profile: Profile to use

        Returns:
            Created session
        """
        project = str(project_path or Path.cwd())
        session_id = self._generate_id(name, project)

        session = Session(
            id=session_id,
            name=name,
            project_path=project,
            model=model,
            profile=profile,
        )

        # Save session
        self._save_session(session)

        # Update index
        self._index[session_id] = {
            "id": session_id,
            "name": name,
            "project_path": project,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": 0,
        }
        self._save_index()

        self.current_session = session
        return session

    def load(self, session_id: str) -> Optional[Session]:
        """
        Load a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            data = json.loads(session_file.read_text())
            # Convert messages
            messages = [Message(**m) for m in data.get("messages", [])]
            data["messages"] = messages
            session = Session(**data)
            self.current_session = session
            return session
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def save(self, session: Optional[Session] = None) -> bool:
        """Save current or specified session."""
        session = session or self.current_session
        if not session:
            return False

        session.updated_at = datetime.now().isoformat()
        return self._save_session(session)

    def _save_session(self, session: Session) -> bool:
        """Save session to disk."""
        session_file = self.sessions_dir / f"{session.id}.json"
        try:
            # Convert to dict
            data = asdict(session)
            # Convert messages
            data["messages"] = [asdict(m) for m in session.messages]
            session_file.write_text(json.dumps(data, indent=2))

            # Update index
            if session.id in self._index:
                self._index[session.id]["updated_at"] = session.updated_at
                self._index[session.id]["message_count"] = len(session.messages)
                self._save_index()

            return True
        except IOError:
            return False

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.sessions_dir / f"{session_id}.json"

        if session_file.exists():
            try:
                session_file.unlink()
            except IOError:
                return False

        if session_id in self._index:
            del self._index[session_id]
            self._save_index()

        if self.current_session and self.current_session.id == session_id:
            self.current_session = None

        return True

    def list(
        self,
        project_path: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        List sessions.

        Args:
            project_path: Filter by project
            limit: Max sessions to return

        Returns:
            List of session summaries
        """
        sessions = list(self._index.values())

        if project_path:
            sessions = [s for s in sessions if s.get("project_path") == str(project_path)]

        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return sessions[:limit]

    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
    ):
        """Add message to current session."""
        if not self.current_session:
            return

        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
        )
        self.current_session.messages.append(message)
        self.save()

    def add_context_file(self, file_path: str):
        """Add file to session context."""
        if not self.current_session:
            return

        if file_path not in self.current_session.context_files:
            self.current_session.context_files.append(file_path)
            self.save()

    def remove_context_file(self, file_path: str):
        """Remove file from session context."""
        if not self.current_session:
            return

        if file_path in self.current_session.context_files:
            self.current_session.context_files.remove(file_path)
            self.save()

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get recent messages from current session."""
        if not self.current_session:
            return []
        return self.current_session.messages[-count:]

    def clear_messages(self):
        """Clear messages from current session."""
        if self.current_session:
            self.current_session.messages = []
            self.save()

    def export_session(self, session_id: str, output_path: Path) -> bool:
        """Export session to file."""
        session = self.load(session_id)
        if not session:
            return False

        try:
            data = asdict(session)
            data["messages"] = [asdict(m) for m in session.messages]
            output_path.write_text(json.dumps(data, indent=2))
            return True
        except IOError:
            return False

    def import_session(self, input_path: Path) -> Optional[Session]:
        """Import session from file."""
        try:
            data = json.loads(input_path.read_text())
            messages = [Message(**m) for m in data.get("messages", [])]
            data["messages"] = messages

            # Generate new ID to avoid conflicts
            data["id"] = self._generate_id(data["name"], data["project_path"])

            session = Session(**data)
            self._save_session(session)

            self._index[session.id] = {
                "id": session.id,
                "name": session.name,
                "project_path": session.project_path,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": len(session.messages),
            }
            self._save_index()

            return session
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def get_report(self) -> str:
        """Generate sessions report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  SESSIONS")
        lines.append("=" * 50)

        sessions = self.list(limit=10)

        if not sessions:
            lines.append("\nNo sessions found.")
            lines.append("Create one with: session = session_manager.create('name')")
        else:
            lines.append(f"\nTotal sessions: {len(self._index)}")
            lines.append("\nRecent sessions:")

            for s in sessions:
                current = " *" if self.current_session and s["id"] == self.current_session.id else ""
                lines.append(f"\n  [{s['id']}]{current}")
                lines.append(f"    Name: {s['name']}")
                lines.append(f"    Project: {s['project_path']}")
                lines.append(f"    Messages: {s.get('message_count', 0)}")
                lines.append(f"    Updated: {s['updated_at'][:19]}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


# Global instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# Convenience functions
def create_session(name: str, project_path: Optional[Path] = None) -> Session:
    """Create a new session."""
    return get_session_manager().create(name, project_path)


def load_session(session_id: str) -> Optional[Session]:
    """Load a session."""
    return get_session_manager().load(session_id)


def list_sessions(project_path: Optional[str] = None) -> List[Dict]:
    """List sessions."""
    return get_session_manager().list(project_path)


def save_session() -> bool:
    """Save current session."""
    return get_session_manager().save()
