"""Planning mode for generating step-by-step task plans."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir
from src.core.visual_output import print_plan_progress


class PlanStatus(str, Enum):
    """Status of a plan or step."""
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: int
    title: str
    description: str
    commands: list[str] = field(default_factory=list)
    files_affected: list[str] = field(default_factory=list)
    status: str = PlanStatus.DRAFT.value
    output: str = ""
    error: str = ""


@dataclass
class Plan:
    """A complete task plan."""
    id: str
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    status: str = PlanStatus.DRAFT.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    workspace: str = ""
    context: str = ""
    estimated_impact: str = ""

    def to_dict(self) -> dict:
        """Convert plan to dictionary."""
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [asdict(step) for step in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "workspace": self.workspace,
            "context": self.context,
            "estimated_impact": self.estimated_impact,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        """Create plan from dictionary."""
        steps = [PlanStep(**step) for step in data.get("steps", [])]
        return cls(
            id=data["id"],
            goal=data["goal"],
            steps=steps,
            status=data.get("status", PlanStatus.DRAFT.value),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            workspace=data.get("workspace", ""),
            context=data.get("context", ""),
            estimated_impact=data.get("estimated_impact", ""),
        )


class PlanManager:
    """Manages creating, storing, and executing plans."""

    def __init__(self, storage_dir: Path | None = None):
        """Initialize plan manager."""
        self.storage_dir = storage_dir or (get_working_dir() / ".plans")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_plan: Plan | None = None

    def _get_plan_path(self, plan_id: str) -> Path:
        """Get path to plan file."""
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in plan_id)
        return self.storage_dir / f"{safe_id}.json"

    def save_plan(self, plan: Plan) -> str:
        """Save a plan to disk."""
        plan.updated_at = datetime.now().isoformat()
        plan.workspace = str(get_working_dir())

        path = self._get_plan_path(plan.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2)

        return f"Plan '{plan.id}' saved."

    def load_plan(self, plan_id: str) -> Plan | None:
        """Load a plan from disk."""
        path = self._get_plan_path(plan_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Plan.from_dict(data)

    def list_plans(self) -> list[dict]:
        """List all saved plans."""
        plans = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                plans.append({
                    "id": data["id"],
                    "goal": data["goal"][:50] + "..." if len(data["goal"]) > 50 else data["goal"],
                    "steps": len(data.get("steps", [])),
                    "status": data.get("status", "draft"),
                    "updated_at": data.get("updated_at", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return plans

    def delete_plan(self, plan_id: str) -> str:
        """Delete a plan."""
        path = self._get_plan_path(plan_id)
        if path.exists():
            path.unlink()
            return f"Plan '{plan_id}' deleted."
        return f"Plan '{plan_id}' not found."

    def set_current_plan(self, plan: Plan) -> None:
        """Set the current active plan."""
        self._current_plan = plan

    def get_current_plan(self) -> Plan | None:
        """Get the current active plan."""
        return self._current_plan


# Global plan manager instance
_plan_manager: PlanManager | None = None


def get_plan_manager() -> PlanManager:
    """Get or create the global plan manager."""
    global _plan_manager
    if _plan_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _plan_manager = PlanManager(settings.data_dir / "plans")
    return _plan_manager


def generate_plan_id() -> str:
    """Generate a unique plan ID."""
    return datetime.now().strftime("plan_%Y%m%d_%H%M%S")


@tool
def create_plan(
    goal: str,
    context: str = "",
) -> str:
    """
    Create a new plan for a complex task. Use this before executing multi-step tasks.

    Args:
        goal: The main goal or objective to accomplish
        context: Additional context about the task

    Returns:
        The new plan with a unique ID.

    Examples:
        create_plan(goal="Set up a new React project with TypeScript")
        create_plan(goal="Refactor authentication module", context="Current auth uses sessions, migrate to JWT")
    """
    manager = get_plan_manager()

    plan = Plan(
        id=generate_plan_id(),
        goal=goal,
        context=context,
    )

    manager.save_plan(plan)
    manager.set_current_plan(plan)

    return f"""## New Plan Created

**ID**: {plan.id}
**Goal**: {goal}
**Context**: {context or "(none)"}
**Status**: Draft

Use `add_plan_step` to add steps to this plan.
When ready, use `approve_plan` to mark it for execution.
"""


@tool
def add_plan_step(
    title: str,
    description: str,
    commands: Optional[str] = None,
    files_affected: Optional[str] = None,
    plan_id: Optional[str] = None,
) -> str:
    """
    Add a step to a plan.

    Args:
        title: Short title for the step
        description: Detailed description of what this step does
        commands: Comma-separated list of commands to run
        files_affected: Comma-separated list of files that will be modified
        plan_id: Optional plan ID (uses current plan if not specified)

    Returns:
        Confirmation with step details.

    Examples:
        add_plan_step(title="Install dependencies", description="Install React and TypeScript packages", commands="npm install react typescript")
        add_plan_step(title="Create components", description="Create Button and Input components", files_affected="src/components/Button.tsx,src/components/Input.tsx")
    """
    manager = get_plan_manager()

    plan = None
    if plan_id:
        plan = manager.load_plan(plan_id)
    else:
        plan = manager.get_current_plan()

    if not plan:
        return "Error: No plan found. Create a plan first with create_plan()."

    cmd_list = [c.strip() for c in commands.split(",")] if commands else []
    files_list = [f.strip() for f in files_affected.split(",")] if files_affected else []

    step = PlanStep(
        id=len(plan.steps) + 1,
        title=title,
        description=description,
        commands=cmd_list,
        files_affected=files_list,
    )

    plan.steps.append(step)
    manager.save_plan(plan)
    manager.set_current_plan(plan)

    return f"""## Step {step.id} Added

**Title**: {title}
**Description**: {description}
**Commands**: {', '.join(cmd_list) if cmd_list else '(none)'}
**Files**: {', '.join(files_list) if files_list else '(none)'}

Plan now has {len(plan.steps)} steps.
"""


@tool
def show_plan(plan_id: Optional[str] = None) -> str:
    """
    Display the current plan or a specific plan with visual progress.

    Args:
        plan_id: Optional plan ID (uses current plan if not specified)

    Returns:
        Formatted plan with all steps and visual progress.

    Examples:
        show_plan()
        show_plan(plan_id="plan_20240101_120000")
    """
    manager = get_plan_manager()

    plan = None
    if plan_id:
        plan = manager.load_plan(plan_id)
    else:
        plan = manager.get_current_plan()

    if not plan:
        return "No plan found. Create a plan first with create_plan()."

    # Find current step (first in_progress or first draft)
    current_step = 0
    for i, step in enumerate(plan.steps, 1):
        if step.status == PlanStatus.IN_PROGRESS.value:
            current_step = i
            break
        elif step.status == PlanStatus.DRAFT.value and current_step == 0:
            current_step = i

    # Convert steps for visual display
    steps_data = [
        {"title": s.title, "status": s.status}
        for s in plan.steps
    ]

    # Visual progress display
    visual = print_plan_progress(
        plan_id=plan.id,
        goal=plan.goal,
        steps=steps_data,
        current_step=current_step,
    )

    status_icons = {
        PlanStatus.DRAFT.value: "📝",
        PlanStatus.APPROVED.value: "✅",
        PlanStatus.IN_PROGRESS.value: "🔄",
        PlanStatus.COMPLETED.value: "✓",
        PlanStatus.FAILED.value: "❌",
        PlanStatus.CANCELLED.value: "⊘",
    }

    output = [visual, ""]

    # Detailed step information
    output.append("### Step Details:\n")

    for step in plan.steps:
        step_icon = status_icons.get(step.status, "○")
        status_label = step.status.upper()

        output.append(f"**{step_icon} Step {step.id}: {step.title}** `[{status_label}]`")
        output.append(f"> {step.description}")

        if step.commands:
            output.append(f"\n  Commands:")
            for cmd in step.commands:
                output.append(f"  - `{cmd}`")

        if step.files_affected:
            output.append(f"\n  Files:")
            for f in step.files_affected:
                output.append(f"  - {f}")

        if step.output:
            output.append(f"\n  Output: {step.output[:100]}...")

        if step.error:
            output.append(f"\n  ❌ Error: {step.error}")

        output.append("")

    if not plan.steps:
        output.append("(no steps yet - use add_plan_step to add steps)")

    return "\n".join(output)


@tool
def approve_plan(plan_id: Optional[str] = None) -> str:
    """
    Approve a plan for execution.

    Args:
        plan_id: Optional plan ID (uses current plan if not specified)

    Returns:
        Confirmation that plan is approved.

    Examples:
        approve_plan()
    """
    manager = get_plan_manager()

    plan = None
    if plan_id:
        plan = manager.load_plan(plan_id)
    else:
        plan = manager.get_current_plan()

    if not plan:
        return "Error: No plan found."

    if not plan.steps:
        return "Error: Cannot approve an empty plan. Add steps first."

    plan.status = PlanStatus.APPROVED.value
    manager.save_plan(plan)
    manager.set_current_plan(plan)

    return f"""## Plan Approved ✅

**ID**: {plan.id}
**Goal**: {plan.goal}
**Steps**: {len(plan.steps)}

The plan is now ready for execution. Use `execute_plan` to run it.
"""


@tool
def execute_plan(
    plan_id: Optional[str] = None,
    step_number: Optional[int] = None,
) -> str:
    """
    Execute a plan or a specific step.

    Args:
        plan_id: Optional plan ID (uses current plan if not specified)
        step_number: Optional specific step to execute

    Returns:
        Instructions for executing the plan.

    Examples:
        execute_plan()
        execute_plan(step_number=1)
    """
    manager = get_plan_manager()

    plan = None
    if plan_id:
        plan = manager.load_plan(plan_id)
    else:
        plan = manager.get_current_plan()

    if not plan:
        return "Error: No plan found."

    if plan.status == PlanStatus.DRAFT.value:
        return "Error: Plan must be approved before execution. Use approve_plan() first."

    plan.status = PlanStatus.IN_PROGRESS.value

    if step_number:
        # Execute specific step
        if step_number < 1 or step_number > len(plan.steps):
            return f"Error: Invalid step number. Plan has {len(plan.steps)} steps."

        step = plan.steps[step_number - 1]
        step.status = PlanStatus.IN_PROGRESS.value
        manager.save_plan(plan)

        output = [
            f"## Executing Step {step_number}: {step.title}",
            f"\n{step.description}",
            "\n**Execute the following**:",
        ]

        if step.commands:
            for cmd in step.commands:
                output.append(f"\n```bash\n{cmd}\n```")

        if step.files_affected:
            output.append(f"\n**Files to modify**: {', '.join(step.files_affected)}")

        output.append("\n\nUse `complete_plan_step` when done.")
        return "\n".join(output)

    # Execute all steps
    output = [
        f"## Executing Plan: {plan.id}",
        f"\n**Goal**: {plan.goal}",
        f"\n**Total Steps**: {len(plan.steps)}",
        "\n---\n",
    ]

    for step in plan.steps:
        if step.status in [PlanStatus.COMPLETED.value, PlanStatus.FAILED.value]:
            continue

        output.append(f"### Step {step.id}: {step.title}")
        output.append(step.description)

        if step.commands:
            output.append("\n**Commands**:")
            for cmd in step.commands:
                output.append(f"```bash\n{cmd}\n```")

        if step.files_affected:
            output.append(f"\n**Files**: {', '.join(step.files_affected)}")

        output.append("\n---\n")

    output.append("Execute each step using the appropriate tools.")
    output.append("Use `complete_plan_step(step_number=N)` after each step.")

    manager.save_plan(plan)
    return "\n".join(output)


@tool
def complete_plan_step(
    step_number: int,
    success: bool = True,
    output: str = "",
    plan_id: Optional[str] = None,
) -> str:
    """
    Mark a plan step as completed.

    Args:
        step_number: The step number to mark complete
        success: Whether the step succeeded
        output: Optional output or notes from the step
        plan_id: Optional plan ID (uses current plan if not specified)

    Returns:
        Confirmation and next step info.

    Examples:
        complete_plan_step(step_number=1)
        complete_plan_step(step_number=2, success=False, output="Build failed")
    """
    manager = get_plan_manager()

    plan = None
    if plan_id:
        plan = manager.load_plan(plan_id)
    else:
        plan = manager.get_current_plan()

    if not plan:
        return "Error: No plan found."

    if step_number < 1 or step_number > len(plan.steps):
        return f"Error: Invalid step number. Plan has {len(plan.steps)} steps."

    step = plan.steps[step_number - 1]
    step.status = PlanStatus.COMPLETED.value if success else PlanStatus.FAILED.value
    step.output = output

    # Check if all steps are done
    completed = sum(1 for s in plan.steps if s.status == PlanStatus.COMPLETED.value)
    failed = sum(1 for s in plan.steps if s.status == PlanStatus.FAILED.value)

    if completed + failed == len(plan.steps):
        plan.status = PlanStatus.COMPLETED.value if failed == 0 else PlanStatus.FAILED.value
        manager.save_plan(plan)
        return f"""## Plan {'Completed ✅' if failed == 0 else 'Finished with Errors ❌'}

**Steps Completed**: {completed}/{len(plan.steps)}
**Failed Steps**: {failed}
"""

    manager.save_plan(plan)

    # Find next step
    next_step = None
    for s in plan.steps:
        if s.status == PlanStatus.DRAFT.value:
            next_step = s
            break

    result = f"## Step {step_number} {'Completed ✅' if success else 'Failed ❌'}\n"
    result += f"Progress: {completed}/{len(plan.steps)} steps done\n"

    if next_step:
        result += f"\n**Next Step**: Step {next_step.id} - {next_step.title}"

    return result


@tool
def list_plans() -> str:
    """
    List all saved plans.

    Returns:
        List of plans with their status.

    Examples:
        list_plans()
    """
    manager = get_plan_manager()
    plans = manager.list_plans()

    if not plans:
        return "No plans found. Create one with create_plan()."

    status_icons = {
        "draft": "📝",
        "approved": "✅",
        "in_progress": "🔄",
        "completed": "✓",
        "failed": "❌",
        "cancelled": "⊘",
    }

    output = ["## Saved Plans\n"]

    for p in plans:
        icon = status_icons.get(p["status"], "○")
        output.append(f"### {icon} {p['id']}")
        output.append(f"  {p['goal']}")
        output.append(f"  Steps: {p['steps']} | Status: {p['status']} | Updated: {p['updated_at'][:10]}")
        output.append("")

    return "\n".join(output)


@tool
def delete_plan(plan_id: str) -> str:
    """
    Delete a plan.

    Args:
        plan_id: ID of the plan to delete

    Returns:
        Confirmation message.

    Examples:
        delete_plan(plan_id="plan_20240101_120000")
    """
    manager = get_plan_manager()
    return manager.delete_plan(plan_id)


# Export planning tools
PLANNING_TOOLS = [
    create_plan,
    add_plan_step,
    show_plan,
    approve_plan,
    execute_plan,
    complete_plan_step,
    list_plans,
    delete_plan,
]
