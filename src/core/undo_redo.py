"""Undo/Redo Stack - Feature 13.

Track all file changes with ability to undo/redo:
- File create/delete/modify
- Multi-file operations
- Named action groups
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

from src.config.settings import get_settings


class ActionType(Enum):
    """Types of undoable actions."""
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    MODIFY_FILE = "modify_file"
    RENAME_FILE = "rename_file"
    CREATE_DIR = "create_dir"
    DELETE_DIR = "delete_dir"


@dataclass
class FileAction:
    """A single file action."""
    action_type: str
    file_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_path: Optional[str] = None  # For rename
    is_binary: bool = False


@dataclass
class ActionGroup:
    """A group of actions (one logical operation)."""
    id: str
    name: str
    description: str
    timestamp: str
    actions: List[Dict] = field(default_factory=list)


class UndoRedoManager:
    """Manage undo/redo stack for file operations."""

    def __init__(self, max_history: int = 100):
        """Initialize manager."""
        settings = get_settings()
        self.storage_dir = settings.data_dir / "undo_history"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.max_history = max_history
        self.undo_stack: List[ActionGroup] = []
        self.redo_stack: List[ActionGroup] = []
        self.current_group: Optional[ActionGroup] = None

        # Load history
        self._load_history()

    def _load_history(self):
        """Load history from disk."""
        history_file = self.storage_dir / "history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.undo_stack = [ActionGroup(**g) for g in data.get("undo", [])]
                    self.redo_stack = [ActionGroup(**g) for g in data.get("redo", [])]
            except (json.JSONDecodeError, IOError):
                pass

    def _save_history(self):
        """Save history to disk."""
        history_file = self.storage_dir / "history.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "undo": [asdict(g) for g in self.undo_stack[-self.max_history:]],
                    "redo": [asdict(g) for g in self.redo_stack[-self.max_history:]],
                }, f, indent=2)
        except IOError:
            pass

    def begin_group(self, name: str, description: str = ""):
        """Begin a new action group."""
        self.current_group = ActionGroup(
            id=f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            name=name,
            description=description,
            timestamp=datetime.now().isoformat(),
            actions=[],
        )

    def end_group(self):
        """End current action group and add to undo stack."""
        if self.current_group and self.current_group.actions:
            self.undo_stack.append(self.current_group)
            self.redo_stack.clear()  # Clear redo when new action is performed
            self._save_history()
        self.current_group = None

    def record_create(self, file_path: str, content: str):
        """Record file creation."""
        action = FileAction(
            action_type=ActionType.CREATE_FILE.value,
            file_path=str(file_path),
            new_content=content,
        )

        if self.current_group:
            self.current_group.actions.append(asdict(action))
        else:
            # Auto-create group for single action
            self.begin_group(f"Create {Path(file_path).name}")
            self.current_group.actions.append(asdict(action))
            self.end_group()

    def record_delete(self, file_path: str, old_content: str):
        """Record file deletion."""
        action = FileAction(
            action_type=ActionType.DELETE_FILE.value,
            file_path=str(file_path),
            old_content=old_content,
        )

        if self.current_group:
            self.current_group.actions.append(asdict(action))
        else:
            self.begin_group(f"Delete {Path(file_path).name}")
            self.current_group.actions.append(asdict(action))
            self.end_group()

    def record_modify(self, file_path: str, old_content: str, new_content: str):
        """Record file modification."""
        action = FileAction(
            action_type=ActionType.MODIFY_FILE.value,
            file_path=str(file_path),
            old_content=old_content,
            new_content=new_content,
        )

        if self.current_group:
            self.current_group.actions.append(asdict(action))
        else:
            self.begin_group(f"Modify {Path(file_path).name}")
            self.current_group.actions.append(asdict(action))
            self.end_group()

    def record_rename(self, old_path: str, new_path: str):
        """Record file rename/move."""
        action = FileAction(
            action_type=ActionType.RENAME_FILE.value,
            file_path=str(new_path),
            old_path=str(old_path),
        )

        if self.current_group:
            self.current_group.actions.append(asdict(action))
        else:
            self.begin_group(f"Rename {Path(old_path).name}")
            self.current_group.actions.append(asdict(action))
            self.end_group()

    def undo(self) -> Dict[str, Any]:
        """
        Undo the last action group.

        Returns:
            Result dict with details
        """
        if not self.undo_stack:
            return {"success": False, "error": "Nothing to undo"}

        group = self.undo_stack.pop()
        errors = []
        undone = []

        # Process actions in reverse order
        for action_data in reversed(group.actions):
            action = FileAction(**action_data)
            result = self._undo_action(action)

            if result.get("success"):
                undone.append(result)
            else:
                errors.append(result)

        # Add to redo stack
        self.redo_stack.append(group)
        self._save_history()

        return {
            "success": len(errors) == 0,
            "group": group.name,
            "undone": undone,
            "errors": errors,
        }

    def redo(self) -> Dict[str, Any]:
        """
        Redo the last undone action group.

        Returns:
            Result dict with details
        """
        if not self.redo_stack:
            return {"success": False, "error": "Nothing to redo"}

        group = self.redo_stack.pop()
        errors = []
        redone = []

        # Process actions in original order
        for action_data in group.actions:
            action = FileAction(**action_data)
            result = self._redo_action(action)

            if result.get("success"):
                redone.append(result)
            else:
                errors.append(result)

        # Add back to undo stack
        self.undo_stack.append(group)
        self._save_history()

        return {
            "success": len(errors) == 0,
            "group": group.name,
            "redone": redone,
            "errors": errors,
        }

    def _undo_action(self, action: FileAction) -> Dict[str, Any]:
        """Undo a single action."""
        try:
            file_path = Path(action.file_path)

            if action.action_type == ActionType.CREATE_FILE.value:
                # Undo create = delete
                if file_path.exists():
                    file_path.unlink()
                return {"success": True, "action": "deleted", "path": str(file_path)}

            elif action.action_type == ActionType.DELETE_FILE.value:
                # Undo delete = restore
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(action.old_content or "", encoding='utf-8')
                return {"success": True, "action": "restored", "path": str(file_path)}

            elif action.action_type == ActionType.MODIFY_FILE.value:
                # Undo modify = restore old content
                file_path.write_text(action.old_content or "", encoding='utf-8')
                return {"success": True, "action": "reverted", "path": str(file_path)}

            elif action.action_type == ActionType.RENAME_FILE.value:
                # Undo rename = move back
                old_path = Path(action.old_path)
                if file_path.exists():
                    old_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(old_path))
                return {"success": True, "action": "renamed_back", "path": str(old_path)}

            return {"success": False, "error": f"Unknown action type: {action.action_type}"}

        except Exception as e:
            return {"success": False, "error": str(e), "path": action.file_path}

    def _redo_action(self, action: FileAction) -> Dict[str, Any]:
        """Redo a single action."""
        try:
            file_path = Path(action.file_path)

            if action.action_type == ActionType.CREATE_FILE.value:
                # Redo create
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(action.new_content or "", encoding='utf-8')
                return {"success": True, "action": "created", "path": str(file_path)}

            elif action.action_type == ActionType.DELETE_FILE.value:
                # Redo delete
                if file_path.exists():
                    file_path.unlink()
                return {"success": True, "action": "deleted", "path": str(file_path)}

            elif action.action_type == ActionType.MODIFY_FILE.value:
                # Redo modify
                file_path.write_text(action.new_content or "", encoding='utf-8')
                return {"success": True, "action": "modified", "path": str(file_path)}

            elif action.action_type == ActionType.RENAME_FILE.value:
                # Redo rename
                old_path = Path(action.old_path)
                if old_path.exists():
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_path), str(file_path))
                return {"success": True, "action": "renamed", "path": str(file_path)}

            return {"success": False, "error": f"Unknown action type: {action.action_type}"}

        except Exception as e:
            return {"success": False, "error": str(e), "path": action.file_path}

    def get_undo_history(self, limit: int = 20) -> List[Dict]:
        """Get undo history."""
        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "timestamp": g.timestamp,
                "action_count": len(g.actions),
            }
            for g in reversed(self.undo_stack[-limit:])
        ]

    def get_redo_history(self, limit: int = 20) -> List[Dict]:
        """Get redo history."""
        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "timestamp": g.timestamp,
                "action_count": len(g.actions),
            }
            for g in reversed(self.redo_stack[-limit:])
        ]

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def clear_history(self):
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._save_history()


# Global instance
_undo_manager: Optional[UndoRedoManager] = None


def get_undo_manager() -> UndoRedoManager:
    """Get or create undo manager."""
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoRedoManager()
    return _undo_manager


# Convenience functions
def undo() -> Dict[str, Any]:
    """Undo last action."""
    return get_undo_manager().undo()


def redo() -> Dict[str, Any]:
    """Redo last undone action."""
    return get_undo_manager().redo()


def record_file_create(file_path: str, content: str):
    """Record file creation."""
    get_undo_manager().record_create(file_path, content)


def record_file_delete(file_path: str, old_content: str):
    """Record file deletion."""
    get_undo_manager().record_delete(file_path, old_content)


def record_file_modify(file_path: str, old_content: str, new_content: str):
    """Record file modification."""
    get_undo_manager().record_modify(file_path, old_content, new_content)


def begin_action_group(name: str, description: str = ""):
    """Begin action group."""
    get_undo_manager().begin_group(name, description)


def end_action_group():
    """End action group."""
    get_undo_manager().end_group()
