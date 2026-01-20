"""Time Tracking - Feature 28.

Track time spent on tasks:
- Start/stop timer
- Log time entries
- Reports by project/task
- Productivity insights
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum


class TimerStatus(Enum):
    """Timer status."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class TimeEntry:
    """A time tracking entry."""
    id: str
    task: str
    project: str
    start_time: str
    end_time: str
    duration: int  # seconds
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeEntry":
        return cls(**data)


@dataclass
class ActiveTimer:
    """Currently active timer."""
    task: str
    project: str
    start_time: str
    paused_time: int = 0  # Accumulated pause time in seconds
    pause_start: str = ""
    tags: List[str] = field(default_factory=list)
    status: TimerStatus = TimerStatus.RUNNING

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveTimer":
        data["status"] = TimerStatus(data["status"])
        return cls(**data)


class TimeTracker:
    """Time tracking utilities."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize time tracker."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "time"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.storage_dir / "entries.json"
        self.timer_file = self.storage_dir / "timer.json"
        self.entries: List[TimeEntry] = []
        self.active_timer: Optional[ActiveTimer] = None
        self._load()

    def _load(self):
        """Load entries and active timer."""
        if self.entries_file.exists():
            try:
                data = json.loads(self.entries_file.read_text(encoding="utf-8"))
                self.entries = [TimeEntry.from_dict(e) for e in data.get("entries", [])]
            except Exception:
                pass

        if self.timer_file.exists():
            try:
                data = json.loads(self.timer_file.read_text(encoding="utf-8"))
                if data:
                    self.active_timer = ActiveTimer.from_dict(data)
            except Exception:
                pass

    def _save(self):
        """Save entries and timer."""
        data = {
            "version": "1.0",
            "entries": [e.to_dict() for e in self.entries],
        }
        self.entries_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        if self.active_timer:
            self.timer_file.write_text(
                json.dumps(self.active_timer.to_dict(), indent=2),
                encoding="utf-8"
            )
        elif self.timer_file.exists():
            self.timer_file.unlink()

    def _generate_id(self) -> str:
        """Generate unique ID."""
        import hashlib
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12]

    def start(
        self,
        task: str,
        project: str = "default",
        tags: Optional[List[str]] = None,
    ) -> ActiveTimer:
        """
        Start time tracking.

        Args:
            task: Task name
            project: Project name
            tags: Task tags

        Returns:
            Active timer
        """
        # Stop any existing timer
        if self.active_timer:
            self.stop()

        self.active_timer = ActiveTimer(
            task=task,
            project=project,
            start_time=datetime.now().isoformat(),
            tags=tags or [],
            status=TimerStatus.RUNNING,
        )
        self._save()

        return self.active_timer

    def stop(self) -> Optional[TimeEntry]:
        """Stop current timer and create entry."""
        if not self.active_timer:
            return None

        # Calculate duration
        start = datetime.fromisoformat(self.active_timer.start_time)
        end = datetime.now()
        total_seconds = int((end - start).total_seconds())

        # Subtract paused time
        if self.active_timer.status == TimerStatus.PAUSED and self.active_timer.pause_start:
            pause_start = datetime.fromisoformat(self.active_timer.pause_start)
            self.active_timer.paused_time += int((end - pause_start).total_seconds())

        duration = total_seconds - self.active_timer.paused_time

        # Create entry
        entry = TimeEntry(
            id=self._generate_id(),
            task=self.active_timer.task,
            project=self.active_timer.project,
            start_time=self.active_timer.start_time,
            end_time=end.isoformat(),
            duration=duration,
            tags=self.active_timer.tags,
        )

        self.entries.append(entry)
        self.active_timer = None
        self._save()

        return entry

    def pause(self) -> Optional[ActiveTimer]:
        """Pause current timer."""
        if not self.active_timer or self.active_timer.status != TimerStatus.RUNNING:
            return None

        self.active_timer.status = TimerStatus.PAUSED
        self.active_timer.pause_start = datetime.now().isoformat()
        self._save()

        return self.active_timer

    def resume(self) -> Optional[ActiveTimer]:
        """Resume paused timer."""
        if not self.active_timer or self.active_timer.status != TimerStatus.PAUSED:
            return None

        # Calculate paused duration
        if self.active_timer.pause_start:
            pause_start = datetime.fromisoformat(self.active_timer.pause_start)
            self.active_timer.paused_time += int((datetime.now() - pause_start).total_seconds())

        self.active_timer.status = TimerStatus.RUNNING
        self.active_timer.pause_start = ""
        self._save()

        return self.active_timer

    def cancel(self) -> bool:
        """Cancel current timer without saving entry."""
        if self.active_timer:
            self.active_timer = None
            self._save()
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current timer status."""
        if not self.active_timer:
            return {"status": "stopped"}

        start = datetime.fromisoformat(self.active_timer.start_time)
        elapsed = int((datetime.now() - start).total_seconds())

        # Adjust for pauses
        if self.active_timer.status == TimerStatus.PAUSED and self.active_timer.pause_start:
            pause_start = datetime.fromisoformat(self.active_timer.pause_start)
            current_pause = int((datetime.now() - pause_start).total_seconds())
            elapsed -= (self.active_timer.paused_time + current_pause)
        else:
            elapsed -= self.active_timer.paused_time

        return {
            "status": self.active_timer.status.value,
            "task": self.active_timer.task,
            "project": self.active_timer.project,
            "elapsed": elapsed,
            "elapsed_formatted": self._format_duration(elapsed),
            "started_at": self.active_timer.start_time,
        }

    def log_entry(
        self,
        task: str,
        duration: int,
        project: str = "default",
        date: Optional[str] = None,
        notes: str = "",
    ) -> TimeEntry:
        """
        Manually log a time entry.

        Args:
            task: Task name
            duration: Duration in minutes
            project: Project name
            date: Date (ISO format, default: today)
            notes: Additional notes

        Returns:
            Created TimeEntry
        """
        if date:
            entry_date = datetime.fromisoformat(date)
        else:
            entry_date = datetime.now()

        entry = TimeEntry(
            id=self._generate_id(),
            task=task,
            project=project,
            start_time=entry_date.isoformat(),
            end_time=(entry_date + timedelta(minutes=duration)).isoformat(),
            duration=duration * 60,  # Convert to seconds
            notes=notes,
        )

        self.entries.append(entry)
        self._save()

        return entry

    def get_entries(
        self,
        project: Optional[str] = None,
        task: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
    ) -> List[TimeEntry]:
        """Get time entries with filters."""
        results = self.entries.copy()

        if project:
            results = [e for e in results if e.project.lower() == project.lower()]

        if task:
            task_lower = task.lower()
            results = [e for e in results if task_lower in e.task.lower()]

        if date_from:
            from_date = datetime.fromisoformat(date_from)
            results = [e for e in results if datetime.fromisoformat(e.start_time) >= from_date]

        if date_to:
            to_date = datetime.fromisoformat(date_to)
            results = [e for e in results if datetime.fromisoformat(e.start_time) <= to_date]

        # Sort by start time descending
        results.sort(key=lambda x: x.start_time, reverse=True)

        return results[:limit]

    def get_summary(
        self,
        period: str = "today",
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get time tracking summary.

        Args:
            period: "today", "week", "month", "all"
            project: Filter by project

        Returns:
            Summary statistics
        """
        now = datetime.now()

        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = datetime.min

        entries = [
            e for e in self.entries
            if datetime.fromisoformat(e.start_time) >= start_date
        ]

        if project:
            entries = [e for e in entries if e.project.lower() == project.lower()]

        total_seconds = sum(e.duration for e in entries)

        # Group by project
        by_project: Dict[str, int] = {}
        for entry in entries:
            by_project[entry.project] = by_project.get(entry.project, 0) + entry.duration

        # Group by task
        by_task: Dict[str, int] = {}
        for entry in entries:
            by_task[entry.task] = by_task.get(entry.task, 0) + entry.duration

        # Top tasks
        top_tasks = sorted(by_task.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "period": period,
            "total_seconds": total_seconds,
            "total_formatted": self._format_duration(total_seconds),
            "entry_count": len(entries),
            "by_project": {k: self._format_duration(v) for k, v in by_project.items()},
            "top_tasks": [(t, self._format_duration(d)) for t, d in top_tasks],
            "average_per_day": self._format_duration(total_seconds // max(1, (now - start_date).days or 1)),
        }

    def _format_duration(self, seconds: int) -> str:
        """Format duration as human readable."""
        if seconds < 0:
            seconds = 0

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_report(self, period: str = "week") -> str:
        """Generate time tracking report."""
        summary = self.get_summary(period)
        lines = []

        lines.append("=" * 60)
        lines.append("  TIME TRACKING REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Current status
        status = self.get_status()
        if status["status"] != "stopped":
            lines.append(f"[ACTIVE] {status['task']} - {status['elapsed_formatted']}")
            lines.append("")

        # Period summary
        lines.append(f"Period: {summary['period'].upper()}")
        lines.append(f"Total Time: {summary['total_formatted']}")
        lines.append(f"Entries: {summary['entry_count']}")
        lines.append(f"Avg/Day: {summary['average_per_day']}")
        lines.append("")

        # By project
        if summary['by_project']:
            lines.append("By Project:")
            for proj, time in summary['by_project'].items():
                lines.append(f"  {proj}: {time}")
            lines.append("")

        # Top tasks
        if summary['top_tasks']:
            lines.append("Top Tasks:")
            for task, time in summary['top_tasks']:
                lines.append(f"  {task}: {time}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_time_tracker: Optional[TimeTracker] = None


def get_time_tracker() -> TimeTracker:
    """Get or create time tracker."""
    global _time_tracker
    if _time_tracker is None:
        _time_tracker = TimeTracker()
    return _time_tracker


# Convenience functions
def start_timer(task: str, project: str = "default") -> ActiveTimer:
    """Start time tracking."""
    return get_time_tracker().start(task, project)


def stop_timer() -> Optional[TimeEntry]:
    """Stop time tracking."""
    return get_time_tracker().stop()


def get_timer_status() -> Dict[str, Any]:
    """Get timer status."""
    return get_time_tracker().get_status()


def get_time_summary(period: str = "today") -> Dict[str, Any]:
    """Get time summary."""
    return get_time_tracker().get_summary(period)
