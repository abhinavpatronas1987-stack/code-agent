"""Agent rules system for loading project-specific instructions from AGENT.md."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir


@dataclass
class AgentRules:
    """Parsed agent rules from AGENT.md."""
    content: str
    file_path: Path
    sections: dict[str, str]


class RulesManager:
    """Manages loading and parsing of agent rules."""

    RULES_FILES = [
        "AGENT.md",
        ".agent.md",
        "agent.md",
        ".github/AGENT.md",
        "docs/AGENT.md",
    ]

    def __init__(self, workspace: Path | None = None):
        """Initialize rules manager."""
        self.workspace = workspace or get_working_dir()
        self._rules: AgentRules | None = None

    def find_rules_file(self) -> Path | None:
        """Find the agent rules file in the workspace."""
        for filename in self.RULES_FILES:
            path = self.workspace / filename
            if path.exists() and path.is_file():
                return path
        return None

    def load_rules(self) -> AgentRules | None:
        """Load and parse agent rules."""
        rules_path = self.find_rules_file()

        if not rules_path:
            return None

        try:
            content = rules_path.read_text(encoding="utf-8")
            sections = self._parse_sections(content)

            self._rules = AgentRules(
                content=content,
                file_path=rules_path,
                sections=sections,
            )

            return self._rules

        except Exception:
            return None

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse markdown sections from content."""
        sections = {}
        current_section = "main"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("# "):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[2:].strip().lower()
                current_content = []
            elif line.startswith("## "):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip().lower()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def get_rules(self) -> AgentRules | None:
        """Get cached rules or load them."""
        if self._rules is None:
            self.load_rules()
        return self._rules

    def get_section(self, name: str) -> str | None:
        """Get a specific section from the rules."""
        rules = self.get_rules()
        if rules:
            return rules.sections.get(name.lower())
        return None

    def reload(self) -> AgentRules | None:
        """Force reload rules from file."""
        self._rules = None
        return self.load_rules()


# Global rules manager
_rules_manager: RulesManager | None = None


def get_rules_manager(workspace: Path | None = None) -> RulesManager:
    """Get or create the global rules manager."""
    global _rules_manager
    if _rules_manager is None or workspace:
        _rules_manager = RulesManager(workspace)
    return _rules_manager


def get_project_rules() -> str:
    """Get project rules as formatted text for the agent."""
    manager = get_rules_manager()
    rules = manager.get_rules()

    if not rules:
        return ""

    return f"""
## Project-Specific Rules (from {rules.file_path.name})

{rules.content}
"""


@tool
def load_agent_rules() -> str:
    """
    Load and display agent rules from AGENT.md in the current project.

    The agent will follow these project-specific rules when working in this codebase.

    Returns:
        The content of AGENT.md or a message if not found.

    Examples:
        load_agent_rules()
    """
    manager = get_rules_manager()
    rules = manager.reload()

    if not rules:
        locations = ", ".join(RulesManager.RULES_FILES)
        return f"No AGENT.md found. Create one at: {locations}"

    return f"""## Agent Rules Loaded

**Source**: `{rules.file_path}`

{rules.content}
"""


@tool
def show_agent_rules() -> str:
    """
    Show the currently loaded agent rules.

    Returns:
        Current rules or a message if none loaded.

    Examples:
        show_agent_rules()
    """
    manager = get_rules_manager()
    rules = manager.get_rules()

    if not rules:
        return "No agent rules loaded. Use load_agent_rules() to load from AGENT.md."

    return f"""## Current Agent Rules

**Source**: `{rules.file_path}`

{rules.content}
"""


@tool
def get_rule_section(section: str) -> str:
    """
    Get a specific section from the agent rules.

    Args:
        section: Name of the section (e.g., "style", "testing", "security")

    Returns:
        The section content or a message if not found.

    Examples:
        get_rule_section(section="code style")
        get_rule_section(section="testing")
    """
    manager = get_rules_manager()
    content = manager.get_section(section)

    if not content:
        rules = manager.get_rules()
        if rules:
            available = ", ".join(rules.sections.keys())
            return f"Section '{section}' not found. Available sections: {available}"
        return "No rules loaded. Use load_agent_rules() first."

    return f"## {section.title()}\n\n{content}"


@tool
def create_agent_rules(
    style_guide: str = "",
    testing_rules: str = "",
    security_rules: str = "",
    custom_rules: str = "",
) -> str:
    """
    Create a new AGENT.md file with project-specific rules.

    Args:
        style_guide: Code style guidelines
        testing_rules: Testing requirements
        security_rules: Security considerations
        custom_rules: Any additional custom rules

    Returns:
        Confirmation message.

    Examples:
        create_agent_rules(style_guide="Use 4 spaces for indentation", testing_rules="All functions must have tests")
    """
    workspace = get_working_dir()
    rules_path = workspace / "AGENT.md"

    content = ["# Agent Rules", ""]
    content.append("This file contains project-specific rules for the AI coding agent.")
    content.append("")

    if style_guide:
        content.append("## Code Style")
        content.append("")
        content.append(style_guide)
        content.append("")

    if testing_rules:
        content.append("## Testing")
        content.append("")
        content.append(testing_rules)
        content.append("")

    if security_rules:
        content.append("## Security")
        content.append("")
        content.append(security_rules)
        content.append("")

    if custom_rules:
        content.append("## Custom Rules")
        content.append("")
        content.append(custom_rules)
        content.append("")

    if not any([style_guide, testing_rules, security_rules, custom_rules]):
        # Create a template
        content.extend([
            "## Code Style",
            "",
            "- Follow the existing code style in this project",
            "- Use meaningful variable and function names",
            "- Keep functions small and focused",
            "",
            "## Testing",
            "",
            "- Write tests for new functionality",
            "- Ensure all tests pass before committing",
            "",
            "## Security",
            "",
            "- Never hardcode secrets or credentials",
            "- Validate all user input",
            "- Use parameterized queries for database access",
            "",
            "## Documentation",
            "",
            "- Add docstrings to public functions",
            "- Update README when adding features",
            "",
        ])

    rules_path.write_text("\n".join(content), encoding="utf-8")

    # Reload rules
    manager = get_rules_manager()
    manager.reload()

    return f"Created {rules_path}. Agent will follow these rules when working in this project."


@tool
def check_rules_compliance(file_path: str) -> str:
    """
    Check if a file follows the project's agent rules.

    Args:
        file_path: Path to the file to check

    Returns:
        Compliance report.

    Examples:
        check_rules_compliance(file_path="src/main.py")
    """
    manager = get_rules_manager()
    rules = manager.get_rules()

    if not rules:
        return "No agent rules loaded. Create an AGENT.md file to define project rules."

    path = Path(file_path)
    if not path.is_absolute():
        path = get_working_dir() / path

    if not path.exists():
        return f"File not found: {path}"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

    output = [f"## Rules Compliance Check: {path.name}\n"]

    # Check against each section
    for section, section_content in rules.sections.items():
        if section == "main":
            continue

        output.append(f"### {section.title()}")

        # Extract rules from section (lines starting with -)
        rule_lines = [
            line.strip()[2:].strip()
            for line in section_content.split("\n")
            if line.strip().startswith("-")
        ]

        if not rule_lines:
            output.append("(no specific rules defined)")
            continue

        for rule in rule_lines:
            output.append(f"- [ ] {rule}")

        output.append("")

    output.append("\n**Note**: This is a checklist for manual review. ")
    output.append("The agent cannot automatically verify all rules.")

    return "\n".join(output)


# Export rules tools
RULES_TOOLS = [
    load_agent_rules,
    show_agent_rules,
    get_rule_section,
    create_agent_rules,
    check_rules_compliance,
]
