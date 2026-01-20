"""Tools for invoking specialized agents."""

from typing import Optional

from agno.tools.decorator import tool

from src.agents.specialized import (
    get_specialized_agent,
    list_specialized_agents,
    SPECIALIZED_AGENTS,
)


@tool
def invoke_agent(
    agent_type: str,
    task: str,
) -> str:
    """
    Invoke a specialized agent for a specific task.

    Available agents:
    - reviewer: Code review for quality, bugs, security
    - debugger: Help finding and fixing bugs
    - refactor: Improve code structure
    - tester: Write comprehensive tests
    - docs: Create documentation
    - git: Handle Git operations

    Args:
        agent_type: Type of specialized agent to use
        task: The task or question for the agent

    Returns:
        The agent's response.

    Examples:
        invoke_agent(agent_type="reviewer", task="Review the authentication module")
        invoke_agent(agent_type="debugger", task="The login function returns None unexpectedly")
        invoke_agent(agent_type="tester", task="Write tests for the User class in models.py")
    """
    agent = get_specialized_agent(agent_type)

    if not agent:
        available = ", ".join(SPECIALIZED_AGENTS.keys())
        return f"Error: Unknown agent type '{agent_type}'. Available agents: {available}"

    try:
        response = agent.run(task, stream=False)

        # Extract content from response
        if hasattr(response, "content"):
            return response.content
        return str(response)

    except Exception as e:
        return f"Error running {agent_type} agent: {str(e)}"


@tool
def list_agents() -> str:
    """
    List all available specialized agents.

    Returns:
        List of agents with their descriptions.

    Examples:
        list_agents()
    """
    agents = list_specialized_agents()

    output = ["## Available Specialized Agents\n"]

    for agent in agents:
        output.append(f"### `{agent['type']}` - {agent['name']}")
        output.append(f"{agent['description']}")
        output.append("")

    output.append("\nUse `invoke_agent(agent_type, task)` to use an agent.")

    return "\n".join(output)


@tool
def code_review(file_path: str, focus: Optional[str] = None) -> str:
    """
    Run a code review on a specific file.

    Args:
        file_path: Path to the file to review
        focus: Optional focus area (security, performance, quality, bugs)

    Returns:
        Code review results.

    Examples:
        code_review(file_path="src/auth.py")
        code_review(file_path="api/routes.py", focus="security")
    """
    focus_text = f" Focus on {focus} issues." if focus else ""
    task = f"Review the file at {file_path}.{focus_text} Provide detailed feedback."

    return invoke_agent(agent_type="reviewer", task=task)


@tool
def debug_help(
    description: str,
    file_path: Optional[str] = None,
    error_message: Optional[str] = None,
) -> str:
    """
    Get help debugging an issue.

    Args:
        description: Description of the bug or issue
        file_path: Optional file where the bug occurs
        error_message: Optional error message

    Returns:
        Debugging suggestions and potential fixes.

    Examples:
        debug_help(description="Function returns wrong value")
        debug_help(description="API returns 500", file_path="routes.py", error_message="KeyError: 'user_id'")
    """
    task = f"Debug this issue: {description}"

    if file_path:
        task += f"\nFile: {file_path}"

    if error_message:
        task += f"\nError: {error_message}"

    return invoke_agent(agent_type="debugger", task=task)


@tool
def suggest_refactoring(file_path: str, target: Optional[str] = None) -> str:
    """
    Get refactoring suggestions for a file.

    Args:
        file_path: Path to the file to refactor
        target: Optional specific function or class to focus on

    Returns:
        Refactoring suggestions.

    Examples:
        suggest_refactoring(file_path="utils.py")
        suggest_refactoring(file_path="models.py", target="UserManager class")
    """
    task = f"Analyze {file_path} and suggest refactoring improvements."

    if target:
        task += f" Focus on the {target}."

    return invoke_agent(agent_type="refactor", task=task)


@tool
def generate_tests(file_path: str, function_name: Optional[str] = None) -> str:
    """
    Generate tests for a file or specific function.

    Args:
        file_path: Path to the file to test
        function_name: Optional specific function to test

    Returns:
        Generated test code.

    Examples:
        generate_tests(file_path="calculator.py")
        generate_tests(file_path="auth.py", function_name="validate_token")
    """
    if function_name:
        task = f"Write comprehensive tests for the {function_name} function in {file_path}."
    else:
        task = f"Write comprehensive tests for all functions in {file_path}."

    return invoke_agent(agent_type="tester", task=task)


@tool
def generate_docs(file_path: str, doc_type: str = "docstring") -> str:
    """
    Generate documentation for a file.

    Args:
        file_path: Path to the file to document
        doc_type: Type of docs (docstring, readme, api)

    Returns:
        Generated documentation.

    Examples:
        generate_docs(file_path="utils.py")
        generate_docs(file_path="api/", doc_type="readme")
    """
    type_descriptions = {
        "docstring": "Add docstrings to all functions and classes",
        "readme": "Create a README file",
        "api": "Generate API documentation",
    }

    desc = type_descriptions.get(doc_type, doc_type)
    task = f"{desc} for {file_path}."

    return invoke_agent(agent_type="docs", task=task)


# Export agent tools
AGENT_TOOLS = [
    invoke_agent,
    list_agents,
    code_review,
    debug_help,
    suggest_refactoring,
    generate_tests,
    generate_docs,
]
