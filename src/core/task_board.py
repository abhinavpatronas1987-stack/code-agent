"""Task Board - Feature 26.

Kanban-style task tracking:
- Create tasks with priorities
- Organize in columns (Todo, In Progress, Done)
- Track progress
- Link tasks to code
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Task status/column."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """Task priority."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """A task item."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    linked_files: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    due_date: str = ""
    assignee: str = ""
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        if isinstance(self.priority, str):
            self.priority = TaskPriority(self.priority)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(**data)


class TaskBoard:
    """Kanban-style task board."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize task board."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "tasks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.storage_dir / "tasks.json"
        self.tasks: Dict[str, Task] = {}
        self._load()

    def _load(self):
        """Load tasks from storage."""
        if self.tasks_file.exists():
            try:
                data = json.loads(self.tasks_file.read_text(encoding="utf-8"))
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task
            except Exception:
                pass

    def _save(self):
        """Save tasks to storage."""
        data = {
            "version": "1.0",
            "tasks": [t.to_dict() for t in self.tasks.values()],
        }
        self.tasks_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    def _generate_id(self, title: str) -> str:
        """Generate unique ID for task."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{title}:{timestamp}"
        return "task_" + hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: Optional[List[str]] = None,
        due_date: str = "",
    ) -> Task:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            priority: Priority level
            tags: Task tags
            due_date: Due date (ISO format)

        Returns:
            Created Task
        """
        task = Task(
            id=self._generate_id(title),
            title=title,
            description=description,
            priority=TaskPriority(priority),
            tags=tags or [],
            due_date=due_date,
        )

        self.tasks[task.id] = task
        self._save()

        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Task]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        if title:
            task.title = title
        if description:
            task.description = description
        if status:
            task.status = TaskStatus(status)
        if priority:
            task.priority = TaskPriority(priority)
        if tags is not None:
            task.tags = tags
        if due_date is not None:
            task.due_date = due_date
        if notes is not None:
            task.notes = notes

        task.updated_at = datetime.now().isoformat()
        self._save()

        return task

    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()
            return True
        return False

    def move(self, task_id: str, new_status: str) -> Optional[Task]:
        """Move task to a new status."""
        return self.update(task_id, status=new_status)

    def add_subtask(
        self,
        task_id: str,
        subtask_title: str,
        done: bool = False,
    ) -> Optional[Task]:
        """Add a subtask to a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        subtask = {
            "title": subtask_title,
            "done": done,
            "created_at": datetime.now().isoformat(),
        }
        task.subtasks.append(subtask)
        task.updated_at = datetime.now().isoformat()
        self._save()

        return task

    def toggle_subtask(self, task_id: str, subtask_index: int) -> Optional[Task]:
        """Toggle a subtask's done status."""
        task = self.tasks.get(task_id)
        if not task or subtask_index >= len(task.subtasks):
            return None

        task.subtasks[subtask_index]["done"] = not task.subtasks[subtask_index]["done"]
        task.updated_at = datetime.now().isoformat()
        self._save()

        return task

    def link_file(self, task_id: str, file_path: str) -> Optional[Task]:
        """Link a file to a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        if file_path not in task.linked_files:
            task.linked_files.append(file_path)
            task.updated_at = datetime.now().isoformat()
            self._save()

        return task

    def list_by_status(self, status: Optional[str] = None) -> Dict[str, List[Task]]:
        """
        List tasks grouped by status.

        Args:
            status: Filter by specific status

        Returns:
            Dict mapping status to tasks
        """
        result: Dict[str, List[Task]] = {
            TaskStatus.TODO.value: [],
            TaskStatus.IN_PROGRESS.value: [],
            TaskStatus.REVIEW.value: [],
            TaskStatus.DONE.value: [],
            TaskStatus.BLOCKED.value: [],
        }

        for task in self.tasks.values():
            if status is None or task.status.value == status:
                result[task.status.value].append(task)

        # Sort by priority within each status
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        for status_tasks in result.values():
            status_tasks.sort(key=lambda t: priority_order[t.priority])

        return result

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[str] = None,
    ) -> List[Task]:
        """Search tasks."""
        results = list(self.tasks.values())

        if query:
            query_lower = query.lower()
            results = [
                t for t in results
                if query_lower in t.title.lower()
                or query_lower in t.description.lower()
            ]

        if tags:
            tags_lower = [t.lower() for t in tags]
            results = [
                t for t in results
                if any(tag.lower() in tags_lower for tag in t.tags)
            ]

        if priority:
            results = [t for t in results if t.priority.value == priority]

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get task board statistics."""
        by_status = self.list_by_status()

        return {
            "total": len(self.tasks),
            "todo": len(by_status[TaskStatus.TODO.value]),
            "in_progress": len(by_status[TaskStatus.IN_PROGRESS.value]),
            "review": len(by_status[TaskStatus.REVIEW.value]),
            "done": len(by_status[TaskStatus.DONE.value]),
            "blocked": len(by_status[TaskStatus.BLOCKED.value]),
            "by_priority": {
                "critical": len([t for t in self.tasks.values() if t.priority == TaskPriority.CRITICAL]),
                "high": len([t for t in self.tasks.values() if t.priority == TaskPriority.HIGH]),
                "medium": len([t for t in self.tasks.values() if t.priority == TaskPriority.MEDIUM]),
                "low": len([t for t in self.tasks.values() if t.priority == TaskPriority.LOW]),
            }
        }

    def get_board_view(self) -> str:
        """Get kanban board view as text."""
        by_status = self.list_by_status()
        lines = []

        lines.append("=" * 80)
        lines.append("  TASK BOARD")
        lines.append("=" * 80)
        lines.append("")

        # Column headers
        columns = [
            ("TODO", TaskStatus.TODO.value),
            ("IN PROGRESS", TaskStatus.IN_PROGRESS.value),
            ("REVIEW", TaskStatus.REVIEW.value),
            ("DONE", TaskStatus.DONE.value),
        ]

        for col_name, status in columns:
            tasks = by_status[status]
            lines.append(f"--- {col_name} ({len(tasks)}) ---")

            if not tasks:
                lines.append("  (empty)")
            else:
                for task in tasks[:5]:
                    priority_mark = {
                        TaskPriority.CRITICAL: "[!!!]",
                        TaskPriority.HIGH: "[!!]",
                        TaskPriority.MEDIUM: "[!]",
                        TaskPriority.LOW: "[.]",
                    }[task.priority]

                    subtask_progress = ""
                    if task.subtasks:
                        done = len([s for s in task.subtasks if s.get("done")])
                        subtask_progress = f" [{done}/{len(task.subtasks)}]"

                    lines.append(f"  {priority_mark} {task.title[:40]}{subtask_progress}")
                    lines.append(f"      ID: {task.id}")

                if len(tasks) > 5:
                    lines.append(f"  ... and {len(tasks) - 5} more")

            lines.append("")

        # Stats
        stats = self.get_stats()
        lines.append("-" * 80)
        lines.append(f"Total: {stats['total']} | ")
        lines.append(f"Critical: {stats['by_priority']['critical']} | ")
        lines.append(f"Blocked: {stats['blocked']}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_markdown(self) -> str:
        """Export tasks as markdown."""
        by_status = self.list_by_status()
        lines = ["# Task Board", ""]

        for status in TaskStatus:
            tasks = by_status[status.value]
            lines.append(f"## {status.value.replace('_', ' ').title()} ({len(tasks)})")
            lines.append("")

            for task in tasks:
                checkbox = "[x]" if status == TaskStatus.DONE else "[ ]"
                priority = f"**{task.priority.value.upper()}**" if task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH] else ""
                lines.append(f"- {checkbox} {task.title} {priority}")
                if task.description:
                    lines.append(f"  - {task.description[:100]}")
                if task.subtasks:
                    for st in task.subtasks:
                        st_check = "[x]" if st.get("done") else "[ ]"
                        lines.append(f"  - {st_check} {st['title']}")
                lines.append("")

        return "\n".join(lines)


# Global instance
_task_board: Optional[TaskBoard] = None


def get_task_board() -> TaskBoard:
    """Get or create task board."""
    global _task_board
    if _task_board is None:
        _task_board = TaskBoard()
    return _task_board


# Convenience functions
def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: Optional[List[str]] = None,
) -> Task:
    """Create a new task."""
    return get_task_board().create(title, description, priority, tags)


def list_tasks(status: Optional[str] = None) -> Dict[str, List[Task]]:
    """List tasks by status."""
    return get_task_board().list_by_status(status)


def move_task(task_id: str, new_status: str) -> Optional[Task]:
    """Move task to new status."""
    return get_task_board().move(task_id, new_status)


def show_board() -> str:
    """Show task board."""
    return get_task_board().get_board_view()
