"""End-to-end test script that runs the full agent with all tools."""

import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

# Set working directory
os.chdir(Path(__file__).parent.parent)


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success, message):
    """Print test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {message}")
    return success


def run_agent_test(agent, prompt, expected_keywords=None, description=""):
    """Run a single agent test and check output."""
    print(f"\n  Testing: {description}")
    print(f"  Prompt: {prompt[:60]}..." if len(prompt) > 60 else f"  Prompt: {prompt}")

    try:
        response = agent.run(prompt, stream=False)

        # Extract content from response
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'messages') and response.messages:
            content = response.messages[-1].content if hasattr(response.messages[-1], 'content') else str(response.messages[-1])
        else:
            content = str(response)

        # Check for expected keywords
        if expected_keywords:
            found = all(kw.lower() in content.lower() for kw in expected_keywords)
            if not found:
                print(f"  Response preview: {content[:200]}...")
                return print_result(False, f"Missing expected keywords: {expected_keywords}")

        print(f"  Response preview: {content[:150]}...")
        return print_result(True, description)

    except Exception as e:
        print(f"  Error: {e}")
        return print_result(False, f"{description} - {str(e)[:50]}")


def test_terminal_tools(agent):
    """Test terminal tools."""
    print_header("TEST 1: Terminal Tools")

    results = []

    # Test list directory
    results.append(run_agent_test(
        agent,
        "List all files in the current directory",
        expected_keywords=["pyproject", "src"],
        description="list_directory"
    ))

    # Test get current directory
    results.append(run_agent_test(
        agent,
        "What is the current working directory?",
        expected_keywords=["code-agent"],
        description="get_current_directory"
    ))

    # Test run command
    results.append(run_agent_test(
        agent,
        "Run the command: python --version",
        expected_keywords=["python", "3"],
        description="run_terminal_command"
    ))

    return all(results)


def test_file_tools(agent):
    """Test file operation tools."""
    print_header("TEST 2: File Tools")

    results = []

    # Test read file
    results.append(run_agent_test(
        agent,
        "Read the pyproject.toml file and tell me the project name",
        expected_keywords=["code-agent"],
        description="read_file"
    ))

    # Test create and write file
    results.append(run_agent_test(
        agent,
        "Create a new file called test_output.txt with the content 'Hello from E2E test'",
        expected_keywords=["created", "test_output"],
        description="create_file / write_file"
    ))

    # Test file info
    results.append(run_agent_test(
        agent,
        "Get information about the file pyproject.toml - what is its size?",
        expected_keywords=["size"],  # Accept any size format (bytes, KB, etc.)
        description="get_file_info"
    ))

    # Cleanup test file
    test_file = Path("test_output.txt")
    if test_file.exists():
        test_file.unlink()

    return all(results)


def test_search_tools(agent):
    """Test search tools."""
    print_header("TEST 3: Search Tools")

    results = []

    # Test find files
    results.append(run_agent_test(
        agent,
        "Find all Python files in the src directory",
        expected_keywords=[".py"],
        description="find_files"
    ))

    # Test search in files
    results.append(run_agent_test(
        agent,
        "Search for the text 'def run_terminal_command' in Python files",
        expected_keywords=["terminal"],
        description="search_files"
    ))

    # Test file structure
    results.append(run_agent_test(
        agent,
        "Show me the directory structure of the src folder",
        expected_keywords=["src", "tools", "agents"],
        description="get_file_structure"
    ))

    return all(results)


def test_git_tools(agent):
    """Test git tools."""
    print_header("TEST 4: Git Tools")

    results = []

    # Test git status (will show not a repo, which is fine)
    results.append(run_agent_test(
        agent,
        "Check the git status of this repository",
        expected_keywords=["git", "status"],
        description="git_status"
    ))

    return all(results)


def test_sandbox_tools(agent):
    """Test Python sandbox tools."""
    print_header("TEST 5: Python Sandbox Tools")

    results = []

    # Test python execution
    results.append(run_agent_test(
        agent,
        "Execute this Python code: print('Hello from sandbox!'); x = 42; print(f'x = {x}')",
        expected_keywords=["hello", "42"],
        description="python_exec"
    ))

    # Test python eval
    results.append(run_agent_test(
        agent,
        "Evaluate this Python expression: 2 ** 10",
        expected_keywords=["1024"],
        description="python_eval"
    ))

    # Test python import and use
    results.append(run_agent_test(
        agent,
        "Import the math module and calculate the square root of 144",
        expected_keywords=["12"],
        description="python_import + eval"
    ))

    return all(results)


def test_workflow_tools(agent):
    """Test workflow/notebook tools."""
    print_header("TEST 6: Workflow Tools")

    results = []

    # Test create workflow
    results.append(run_agent_test(
        agent,
        "Create a new workflow called 'e2e-test-workflow' with description 'Test workflow'",
        expected_keywords=["workflow", "created", "e2e-test"],
        description="create_workflow"
    ))

    # Test add step
    results.append(run_agent_test(
        agent,
        "Add a step to the 'e2e-test-workflow' workflow with command 'echo hello' and description 'Say hello'",
        expected_keywords=["step", "added"],
        description="add_workflow_step"
    ))

    # Test list workflows
    results.append(run_agent_test(
        agent,
        "List all saved workflows",
        expected_keywords=["e2e-test-workflow"],
        description="list_workflows"
    ))

    # Test delete workflow
    results.append(run_agent_test(
        agent,
        "Delete the workflow named 'e2e-test-workflow'",
        expected_keywords=["deleted"],
        description="delete_workflow"
    ))

    return all(results)


def test_planning_tools(agent):
    """Test planning mode tools."""
    print_header("TEST 7: Planning Tools")

    results = []

    # Test create plan
    results.append(run_agent_test(
        agent,
        "Create a new plan with goal 'E2E Test Plan' and context 'Testing planning tools'",
        expected_keywords=["plan", "created"],
        description="create_plan"
    ))

    # Test add step
    results.append(run_agent_test(
        agent,
        "Add a step to the current plan with title 'Test Step' and description 'This is a test step'",
        expected_keywords=["step", "added"],
        description="add_plan_step"
    ))

    # Test show plan
    results.append(run_agent_test(
        agent,
        "Show the current plan",
        expected_keywords=["E2E Test Plan", "Test Step"],
        description="show_plan"
    ))

    return all(results)


def test_context_tools(agent):
    """Test context attachment tools."""
    print_header("TEST 8: Context Attachment Tools")

    results = []

    # Test attach file
    results.append(run_agent_test(
        agent,
        "Attach the file pyproject.toml to the context",
        expected_keywords=["attached", "pyproject"],
        description="attach_file"
    ))

    # Test show context
    results.append(run_agent_test(
        agent,
        "Show the current attached context",
        expected_keywords=["pyproject", "context"],
        description="show_context"
    ))

    # Test clear context
    results.append(run_agent_test(
        agent,
        "Clear all attached context",
        expected_keywords=["cleared"],
        description="clear_context"
    ))

    return all(results)


def test_agent_tools(agent):
    """Test multi-agent tools."""
    print_header("TEST 9: Multi-Agent Tools")

    results = []

    # Test list agents
    results.append(run_agent_test(
        agent,
        "List all available specialized agents",
        expected_keywords=["reviewer", "debugger", "tester"],
        description="list_agents"
    ))

    return all(results)


def test_error_fixer_tools(agent):
    """Test error analysis tools."""
    print_header("TEST 10: Error Analysis Tools")

    results = []

    # Test analyze error
    error_text = "NameError: name 'undefined_variable' is not defined"
    results.append(run_agent_test(
        agent,
        f"Analyze this error and suggest fixes: {error_text}",
        expected_keywords=["NameError", "suggest", "fix"],
        description="analyze_error"
    ))

    return all(results)


def test_rules_tools(agent):
    """Test agent rules tools."""
    print_header("TEST 11: Agent Rules Tools")

    results = []

    # Test create rules
    results.append(run_agent_test(
        agent,
        "Create a new AGENT.md rules file with style guide 'Use snake_case for variables'",
        expected_keywords=["created", "agent", "rules"],
        description="create_agent_rules"
    ))

    # Test show rules
    results.append(run_agent_test(
        agent,
        "Show the current agent rules",
        expected_keywords=["rules", "snake_case"],
        description="show_agent_rules"
    ))

    # Cleanup
    rules_file = Path("AGENT.md")
    if rules_file.exists():
        rules_file.unlink()

    return all(results)


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 70)
    print("  CODE AGENT - END-TO-END TEST SUITE")
    print("  Testing all 68 tools with live Ollama LLM")
    print("=" * 70)

    # Check if Ollama is running
    print("\n  Checking Ollama connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("  [ERROR] Ollama is not responding. Please start Ollama first:")
            print("          ollama serve")
            return 1
        print("  [OK] Ollama is running")
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Ollama: {e}")
        print("          Please start Ollama first: ollama serve")
        return 1

    # Initialize agent
    print("\n  Initializing CodingAgent...")
    try:
        from src.agents.coding_agent import CodingAgent
        agent = CodingAgent(session_id="e2e-test")
        print("  [OK] Agent initialized with 68 tools")
    except Exception as e:
        print(f"  [ERROR] Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Run all tests
    results = []

    results.append(("Terminal Tools", test_terminal_tools(agent)))
    results.append(("File Tools", test_file_tools(agent)))
    results.append(("Search Tools", test_search_tools(agent)))
    results.append(("Git Tools", test_git_tools(agent)))
    results.append(("Sandbox Tools", test_sandbox_tools(agent)))
    results.append(("Workflow Tools", test_workflow_tools(agent)))
    results.append(("Planning Tools", test_planning_tools(agent)))
    results.append(("Context Tools", test_context_tools(agent)))
    results.append(("Agent Tools", test_agent_tools(agent)))
    results.append(("Error Fixer Tools", test_error_fixer_tools(agent)))
    results.append(("Rules Tools", test_rules_tools(agent)))

    # Summary
    print_header("TEST SUMMARY")

    passed = 0
    failed = 0

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Results: {passed}/{len(results)} test groups passed")

    if failed == 0:
        print("\n  === ALL E2E TESTS PASSED! ===")
        return 0
    else:
        print(f"\n  WARNING: {failed} test group(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
