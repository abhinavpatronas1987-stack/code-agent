"""Checkpoint System - Feature 12.

Save and restore project state:
- Full file snapshots
- Incremental changes
- Named checkpoints
- Auto-checkpoints before risky operations
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from src.config.settings import get_settings


@dataclass
class FileSnapshot:
    """Snapshot of a single file."""
    path: str
    content_hash: str
    size: int
    modified_time: float
    content: Optional[str] = None  # Stored separately for large files


@dataclass
class Checkpoint:
    """A project checkpoint."""
    id: str
    name: str
    description: str
    created_at: str
    project_path: str
    files: List[Dict]
    file_count: int
    total_size: int
    auto_created: bool = False


class CheckpointManager:
    """Manages project checkpoints."""

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize checkpoint manager."""
        settings = get_settings()
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.checkpoint_dir = settings.data_dir / "checkpoints" / self._get_project_id()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = 50
        self.max_file_size = 10 * 1024 * 1024  # 10MB max per file

        # Patterns to ignore
        self.ignore_patterns = [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "env", ".env", "*.pyc", "*.pyo", "*.so", "*.dll",
            ".DS_Store", "Thumbs.db", "*.log", "dist", "build",
            ".agent", "*.egg-info", ".pytest_cache", ".mypy_cache",
            ".coverage", "htmlcov", "*.sqlite", "*.db"
        ]

    def _get_project_id(self) -> str:
        """Get unique ID for current project."""
        path_str = str(self.project_path.resolve())
        return hashlib.md5(path_str.encode()).hexdigest()[:12]

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(path)
        name = path.name

        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in path_str or name == pattern:
                return True
        return False

    def _hash_content(self, content: bytes) -> str:
        """Get hash of content."""
        return hashlib.sha256(content).hexdigest()[:16]

    def _collect_files(self) -> List[FileSnapshot]:
        """Collect all files in project."""
        files = []

        for root, dirs, filenames in os.walk(self.project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            for filename in filenames:
                file_path = Path(root) / filename

                if self._should_ignore(file_path):
                    continue

                try:
                    stat = file_path.stat()

                    # Skip large files
                    if stat.st_size > self.max_file_size:
                        continue

                    # Read content
                    try:
                        content = file_path.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        # Binary file - read as bytes
                        content = file_path.read_bytes().hex()

                    relative_path = file_path.relative_to(self.project_path)

                    files.append(FileSnapshot(
                        path=str(relative_path),
                        content_hash=self._hash_content(content.encode() if isinstance(content, str) else bytes.fromhex(content)),
                        size=stat.st_size,
                        modified_time=stat.st_mtime,
                        content=content,
                    ))
                except (PermissionError, OSError):
                    continue

        return files

    def create(self, name: str, description: str = "", auto: bool = False) -> Checkpoint:
        """
        Create a new checkpoint.

        Args:
            name: Checkpoint name
            description: Optional description
            auto: Whether auto-created (before risky operation)

        Returns:
            Created checkpoint
        """
        checkpoint_id = f"chk_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Collect files
        files = self._collect_files()

        # Create checkpoint
        checkpoint = Checkpoint(
            id=checkpoint_id,
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            project_path=str(self.project_path),
            files=[asdict(f) for f in files],
            file_count=len(files),
            total_size=sum(f.size for f in files),
            auto_created=auto,
        )

        # Save checkpoint
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(checkpoint), f, indent=2)

        # Cleanup old checkpoints
        self._cleanup_old_checkpoints()

        return checkpoint

    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints if over limit."""
        checkpoints = sorted(self.checkpoint_dir.glob("chk_*.json"))
        while len(checkpoints) > self.max_checkpoints:
            oldest = checkpoints.pop(0)
            oldest.unlink()

    def list(self) -> List[Dict]:
        """List all checkpoints."""
        checkpoints = []

        for path in sorted(self.checkpoint_dir.glob("chk_*.json"), reverse=True):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    checkpoints.append({
                        "id": data["id"],
                        "name": data["name"],
                        "description": data.get("description", ""),
                        "created_at": data["created_at"],
                        "file_count": data["file_count"],
                        "total_size": data["total_size"],
                        "auto_created": data.get("auto_created", False),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        return checkpoints

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            return None

        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Checkpoint(**data)

    def restore(self, checkpoint_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Restore project to checkpoint state.

        Args:
            checkpoint_id: ID of checkpoint to restore
            dry_run: If True, only show what would change

        Returns:
            Dict with restore results
        """
        checkpoint = self.get(checkpoint_id)
        if not checkpoint:
            return {"success": False, "error": f"Checkpoint not found: {checkpoint_id}"}

        # Compare current state with checkpoint
        current_files = {f.path: f for f in self._collect_files()}
        checkpoint_files = {f["path"]: f for f in checkpoint.files}

        changes = {
            "files_to_restore": [],
            "files_to_delete": [],
            "files_unchanged": [],
        }

        # Check files in checkpoint
        for path, snap in checkpoint_files.items():
            current = current_files.get(path)
            if not current:
                changes["files_to_restore"].append({"path": path, "action": "create"})
            elif current.content_hash != snap["content_hash"]:
                changes["files_to_restore"].append({"path": path, "action": "restore"})
            else:
                changes["files_unchanged"].append(path)

        # Check for files to delete (exist now but not in checkpoint)
        for path in current_files:
            if path not in checkpoint_files:
                changes["files_to_delete"].append(path)

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "checkpoint": checkpoint_id,
                "changes": changes,
            }

        # Actually restore
        restored = []
        errors = []

        for file_info in changes["files_to_restore"]:
            path = file_info["path"]
            snap = checkpoint_files[path]

            try:
                file_path = self.project_path / path
                file_path.parent.mkdir(parents=True, exist_ok=True)

                content = snap.get("content", "")
                if content.startswith("0x") or all(c in "0123456789abcdef" for c in content[:100]):
                    # Binary content stored as hex
                    file_path.write_bytes(bytes.fromhex(content))
                else:
                    file_path.write_text(content, encoding='utf-8')

                restored.append(path)
            except Exception as e:
                errors.append({"path": path, "error": str(e)})

        # Delete files not in checkpoint
        deleted = []
        for path in changes["files_to_delete"]:
            try:
                file_path = self.project_path / path
                if file_path.exists():
                    file_path.unlink()
                    deleted.append(path)
            except Exception as e:
                errors.append({"path": path, "error": str(e)})

        return {
            "success": len(errors) == 0,
            "checkpoint": checkpoint_id,
            "restored": restored,
            "deleted": deleted,
            "errors": errors,
        }

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            return True
        return False

    def diff(self, checkpoint_id: str) -> Dict[str, Any]:
        """Show diff between current state and checkpoint."""
        checkpoint = self.get(checkpoint_id)
        if not checkpoint:
            return {"error": f"Checkpoint not found: {checkpoint_id}"}

        current_files = {f.path: f for f in self._collect_files()}
        checkpoint_files = {f["path"]: f for f in checkpoint.files}

        diffs = {
            "modified": [],
            "added": [],
            "deleted": [],
            "unchanged": 0,
        }

        for path, snap in checkpoint_files.items():
            current = current_files.get(path)
            if not current:
                diffs["deleted"].append(path)
            elif current.content_hash != snap["content_hash"]:
                diffs["modified"].append(path)
            else:
                diffs["unchanged"] += 1

        for path in current_files:
            if path not in checkpoint_files:
                diffs["added"].append(path)

        return diffs


# Global instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager(project_path: Optional[Path] = None) -> CheckpointManager:
    """Get or create checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None or project_path:
        _checkpoint_manager = CheckpointManager(project_path)
    return _checkpoint_manager


# Convenience functions
def create_checkpoint(name: str, description: str = "", auto: bool = False) -> Checkpoint:
    """Create a checkpoint."""
    return get_checkpoint_manager().create(name, description, auto)


def list_checkpoints() -> List[Dict]:
    """List all checkpoints."""
    return get_checkpoint_manager().list()


def restore_checkpoint(checkpoint_id: str, dry_run: bool = False) -> Dict:
    """Restore to a checkpoint."""
    return get_checkpoint_manager().restore(checkpoint_id, dry_run)


def auto_checkpoint(operation: str) -> Checkpoint:
    """Create auto-checkpoint before risky operation."""
    return get_checkpoint_manager().create(
        name=f"auto: before {operation}",
        description=f"Auto-created before: {operation}",
        auto=True
    )
