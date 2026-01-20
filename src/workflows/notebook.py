"""Workflow/Notebook system for saving and replaying command sequences."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    command: str
    description: str = ""
    expected_output: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Workflow:
    """A saved workflow/notebook containing multiple steps."""
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    workspace: str = ""

    def to_dict(self) -> dict:
        """Convert workflow to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [asdict(step) for step in self.steps],
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "workspace": self.workspace,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Create workflow from dictionary."""
        steps = [WorkflowStep(**step) for step in data.get("steps", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            workspace=data.get("workspace", ""),
        )


class WorkflowManager:
    """Manages saving, loading, and executing workflows."""

    def __init__(self, storage_dir: Path | None = None):
        """Initialize workflow manager."""
        self.storage_dir = storage_dir or (get_working_dir() / ".workflows")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_workflow_path(self, name: str) -> Path:
        """Get path to workflow file."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return self.storage_dir / f"{safe_name}.json"

    def save_workflow(self, workflow: Workflow) -> str:
        """Save a workflow to disk."""
        workflow.updated_at = datetime.now().isoformat()
        workflow.workspace = str(get_working_dir())

        path = self._get_workflow_path(workflow.name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(workflow.to_dict(), f, indent=2)

        return f"Workflow '{workflow.name}' saved to {path}"

    def load_workflow(self, name: str) -> Workflow | None:
        """Load a workflow from disk."""
        path = self._get_workflow_path(name)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Workflow.from_dict(data)

    def list_workflows(self) -> list[dict]:
        """List all saved workflows."""
        workflows = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                workflows.append({
                    "name": data["name"],
                    "description": data.get("description", ""),
                    "steps": len(data.get("steps", [])),
                    "tags": data.get("tags", []),
                    "updated_at": data.get("updated_at", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return workflows

    def delete_workflow(self, name: str) -> str:
        """Delete a workflow."""
        path = self._get_workflow_path(name)
        if path.exists():
            path.unlink()
            return f"Workflow '{name}' deleted."
        return f"Workflow '{name}' not found."


# Global workflow manager instance
_workflow_manager: WorkflowManager | None = None


def get_workflow_manager() -> WorkflowManager:
    """Get or create the global workflow manager."""
    global _workflow_manager
    if _workflow_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()
        _workflow_manager = WorkflowManager(settings.data_dir / "workflows")
    return _workflow_manager


@tool
def create_workflow(
    name: str,
    description: str = "",
    tags: Optional[str] = None,
) -> str:
    """
    Create a new empty workflow/notebook.

    Args:
        name: Name of the workflow
        description: Description of what the workflow does
        tags: Comma-separated tags for categorization

    Returns:
        Confirmation message.

    Examples:
        create_workflow(name="setup-project", description="Initialize a new Python project")
        create_workflow(name="deploy", description="Deploy to production", tags="deploy,prod")
    """
    manager = get_workflow_manager()

    # Check if exists
    if manager.load_workflow(name):
        return f"Error: Workflow '{name}' already exists. Use a different name or delete it first."

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    workflow = Workflow(
        name=name,
        description=description,
        tags=tag_list,
    )

    return manager.save_workflow(workflow)


@tool
def add_workflow_step(
    workflow_name: str,
    command: str,
    description: str = "",
) -> str:
    """
    Add a step to an existing workflow.

    Args:
        workflow_name: Name of the workflow to add to
        command: The command or instruction to add
        description: Description of what this step does

    Returns:
        Confirmation message.

    Examples:
        add_workflow_step(workflow_name="setup-project", command="python -m venv .venv")
        add_workflow_step(workflow_name="deploy", command="git push origin main", description="Push to remote")
    """
    manager = get_workflow_manager()

    workflow = manager.load_workflow(workflow_name)
    if not workflow:
        return f"Error: Workflow '{workflow_name}' not found."

    step = WorkflowStep(command=command, description=description)
    workflow.steps.append(step)

    return manager.save_workflow(workflow) + f"\nStep {len(workflow.steps)} added."


@tool
def list_workflows(tag: Optional[str] = None) -> str:
    """
    List all saved workflows.

    Args:
        tag: Optional tag to filter by

    Returns:
        List of workflows with their details.

    Examples:
        list_workflows()
        list_workflows(tag="deploy")
    """
    manager = get_workflow_manager()
    workflows = manager.list_workflows()

    if not workflows:
        return "No workflows found. Create one with create_workflow()."

    if tag:
        workflows = [w for w in workflows if tag in w.get("tags", [])]
        if not workflows:
            return f"No workflows found with tag '{tag}'."

    output = ["## Saved Workflows\n"]
    for w in workflows:
        tags_str = f" [{', '.join(w['tags'])}]" if w['tags'] else ""
        output.append(f"### {w['name']}{tags_str}")
        output.append(f"  {w['description']}" if w['description'] else "  (no description)")
        output.append(f"  Steps: {w['steps']} | Updated: {w['updated_at'][:10]}")
        output.append("")

    return "\n".join(output)


@tool
def show_workflow(name: str) -> str:
    """
    Show details of a specific workflow.

    Args:
        name: Name of the workflow

    Returns:
        Workflow details including all steps.

    Examples:
        show_workflow(name="setup-project")
    """
    manager = get_workflow_manager()
    workflow = manager.load_workflow(name)

    if not workflow:
        return f"Workflow '{name}' not found."

    output = [
        f"# Workflow: {workflow.name}",
        f"Description: {workflow.description}" if workflow.description else "",
        f"Tags: {', '.join(workflow.tags)}" if workflow.tags else "",
        f"Workspace: {workflow.workspace}" if workflow.workspace else "",
        f"Created: {workflow.created_at[:10]} | Updated: {workflow.updated_at[:10]}",
        "",
        "## Steps",
        "",
    ]

    for i, step in enumerate(workflow.steps, 1):
        output.append(f"### Step {i}")
        if step.description:
            output.append(f"*{step.description}*")
        output.append(f"```")
        output.append(step.command)
        output.append(f"```")
        output.append("")

    if not workflow.steps:
        output.append("(no steps yet)")

    return "\n".join(output)


@tool
def delete_workflow(name: str) -> str:
    """
    Delete a workflow.

    Args:
        name: Name of the workflow to delete

    Returns:
        Confirmation message.

    Examples:
        delete_workflow(name="old-workflow")
    """
    manager = get_workflow_manager()
    return manager.delete_workflow(name)


@tool
def run_workflow(
    name: str,
    dry_run: bool = False,
) -> str:
    """
    Execute all steps in a workflow.

    Args:
        name: Name of the workflow to run
        dry_run: If True, show commands without executing

    Returns:
        Results of each step execution.

    Examples:
        run_workflow(name="setup-project")
        run_workflow(name="deploy", dry_run=True)
    """
    manager = get_workflow_manager()
    workflow = manager.load_workflow(name)

    if not workflow:
        return f"Workflow '{name}' not found."

    if not workflow.steps:
        return f"Workflow '{name}' has no steps to run."

    if dry_run:
        output = [f"## Dry Run: {workflow.name}\n"]
        for i, step in enumerate(workflow.steps, 1):
            output.append(f"**Step {i}**: {step.description or 'No description'}")
            output.append(f"```")
            output.append(step.command)
            output.append(f"```")
            output.append("")
        return "\n".join(output)

    # For actual execution, we return the steps for the agent to execute
    output = [f"## Executing Workflow: {workflow.name}\n"]
    output.append("The following commands will be executed:\n")

    for i, step in enumerate(workflow.steps, 1):
        output.append(f"**Step {i}**: {step.description or step.command}")
        output.append(f"Command: `{step.command}`")
        output.append("")

    output.append("\n**Note**: Execute each command using run_terminal_command or the appropriate tool.")

    return "\n".join(output)


@tool
def save_command_to_workflow(
    workflow_name: str,
    command: str,
    description: str = "",
    create_if_missing: bool = True,
) -> str:
    """
    Quick save a command to a workflow, creating the workflow if it doesn't exist.

    Args:
        workflow_name: Name of the workflow
        command: Command to save
        description: Description of the command
        create_if_missing: Create workflow if it doesn't exist

    Returns:
        Confirmation message.

    Examples:
        save_command_to_workflow(workflow_name="my-commands", command="npm run build")
    """
    manager = get_workflow_manager()

    workflow = manager.load_workflow(workflow_name)

    if not workflow:
        if create_if_missing:
            workflow = Workflow(name=workflow_name)
        else:
            return f"Workflow '{workflow_name}' not found."

    step = WorkflowStep(command=command, description=description)
    workflow.steps.append(step)

    result = manager.save_workflow(workflow)
    return f"Command saved to workflow '{workflow_name}' (Step {len(workflow.steps)})"


# Export workflow tools
WORKFLOW_TOOLS = [
    create_workflow,
    add_workflow_step,
    list_workflows,
    show_workflow,
    delete_workflow,
    run_workflow,
    save_command_to_workflow,
]
