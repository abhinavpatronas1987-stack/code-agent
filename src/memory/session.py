"""Session and conversation management."""

import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

from src.config.settings import get_settings


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None


@dataclass
class Conversation:
    """A conversation containing multiple messages."""
    id: str
    title: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    workspace: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs) -> Message:
        """Add a message to the conversation."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def get_context(self, max_messages: int = 20) -> list[dict]:
        """Get conversation context for the agent."""
        recent = self.messages[-max_messages:]
        return [
            {"role": m.role, "content": m.content}
            for m in recent
        ]


@dataclass
class Session:
    """A session containing workspace state and conversations."""
    id: str
    workspace: Path
    conversations: dict[str, Conversation] = field(default_factory=dict)
    active_conversation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        """Create a new conversation in this session."""
        conv_id = str(uuid.uuid4())[:8]
        conv = Conversation(
            id=conv_id,
            title=title,
            workspace=str(self.workspace),
        )
        self.conversations[conv_id] = conv
        self.active_conversation_id = conv_id
        return conv

    def get_active_conversation(self) -> Optional[Conversation]:
        """Get the currently active conversation."""
        if self.active_conversation_id:
            return self.conversations.get(self.active_conversation_id)
        return None


class SessionManager:
    """Manages sessions and conversations."""

    def __init__(self):
        self.settings = get_settings()
        self.sessions: dict[str, Session] = {}

    def create_session(
        self,
        workspace: str | Path | None = None,
        session_id: str | None = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            workspace: Working directory for the session
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            New Session instance
        """
        session_id = session_id or str(uuid.uuid4())

        if workspace:
            workspace_path = Path(workspace).resolve()
        else:
            workspace_path = self.settings.workspace_root

        session = Session(
            id=session_id,
            workspace=workspace_path,
        )

        # Create initial conversation
        session.create_conversation("Session Start")

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: str,
        workspace: str | Path | None = None,
    ) -> Session:
        """Get existing session or create a new one."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        return self.create_session(workspace=workspace, session_id=session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[dict]:
        """List all sessions with basic info."""
        return [
            {
                "id": s.id,
                "workspace": str(s.workspace),
                "conversations": len(s.conversations),
                "created_at": s.created_at.isoformat(),
            }
            for s in self.sessions.values()
        ]


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
