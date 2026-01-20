"""Task and workflow management for tracking agent progress."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A single task in a workflow."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    parent_id: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)

    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: str = "") -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "subtasks": self.subtasks,
        }


@dataclass
class Workflow:
    """A workflow containing multiple tasks."""
    id: str
    name: str
    description: str = ""
    tasks: dict[str, Task] = field(default_factory=dict)
    task_order: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING

    def add_task(
        self,
        title: str,
        description: str = "",
        parent_id: Optional[str] = None,
    ) -> Task:
        """Add a task to the workflow."""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            title=title,
            description=description,
            parent_id=parent_id,
        )

        self.tasks[task_id] = task
        self.task_order.append(task_id)

        if parent_id and parent_id in self.tasks:
            self.tasks[parent_id].subtasks.append(task_id)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> list[Task]:
        """Get all pending tasks in order."""
        return [
            self.tasks[tid] for tid in self.task_order
            if self.tasks[tid].status == TaskStatus.PENDING
        ]

    def get_current_task(self) -> Optional[Task]:
        """Get the current in-progress task."""
        for tid in self.task_order:
            if self.tasks[tid].status == TaskStatus.IN_PROGRESS:
                return self.tasks[tid]
        return None

    def get_next_task(self) -> Optional[Task]:
        """Get the next pending task."""
        for tid in self.task_order:
            if self.tasks[tid].status == TaskStatus.PENDING:
                return self.tasks[tid]
        return None

    def update_status(self) -> None:
        """Update workflow status based on task states."""
        statuses = [t.status for t in self.tasks.values()]

        if all(s == TaskStatus.COMPLETED for s in statuses):
            self.status = TaskStatus.COMPLETED
        elif any(s == TaskStatus.IN_PROGRESS for s in statuses):
            self.status = TaskStatus.IN_PROGRESS
        elif any(s == TaskStatus.FAILED for s in statuses):
            self.status = TaskStatus.FAILED
        else:
            self.status = TaskStatus.PENDING

    def to_dict(self) -> dict:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "tasks": [self.tasks[tid].to_dict() for tid in self.task_order],
        }

    def get_progress_display(self) -> str:
        """Get a text display of workflow progress."""
        lines = [f"## {self.name}", ""]

        for tid in self.task_order:
            task = self.tasks[tid]
            status_icons = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.IN_PROGRESS: "[>]",
                TaskStatus.COMPLETED: "[x]",
                TaskStatus.FAILED: "[!]",
                TaskStatus.CANCELLED: "[-]",
            }
            icon = status_icons[task.status]
            lines.append(f"{icon} {task.title}")

            if task.description:
                lines.append(f"    {task.description}")

        # Summary
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        total = len(self.tasks)
        lines.append("")
        lines.append(f"Progress: {completed}/{total} tasks completed")

        return "\n".join(lines)


class TaskManager:
    """Manages workflows and tasks across sessions."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self.session_workflows: dict[str, list[str]] = {}  # session_id -> workflow_ids

    def create_workflow(
        self,
        name: str,
        description: str = "",
        session_id: Optional[str] = None,
    ) -> Workflow:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())[:8]
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
        )

        self.workflows[workflow_id] = workflow

        if session_id:
            if session_id not in self.session_workflows:
                self.session_workflows[session_id] = []
            self.session_workflows[session_id].append(workflow_id)

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_session_workflows(self, session_id: str) -> list[Workflow]:
        """Get all workflows for a session."""
        workflow_ids = self.session_workflows.get(session_id, [])
        return [self.workflows[wid] for wid in workflow_ids if wid in self.workflows]

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            # Clean up session references
            for session_id in self.session_workflows:
                if workflow_id in self.session_workflows[session_id]:
                    self.session_workflows[session_id].remove(workflow_id)
            return True
        return False


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
