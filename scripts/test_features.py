"""Test script for all new features."""

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


def call_tool(tool_func, **kwargs):
    """Helper to call a tool function, handling Agno's Function wrapper."""
    if hasattr(tool_func, 'entrypoint') and tool_func.entrypoint is not None:
        return tool_func.entrypoint(**kwargs)
    return tool_func(**kwargs)


def test_imports():
    """Test that all modules import correctly."""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)

    tests = []

    try:
        from src.tools.git_tools import GIT_TOOLS
        tests.append(("Git Tools", len(GIT_TOOLS), True))
        print(f"  [OK] Git Tools: {len(GIT_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Git Tools", 0, False))
        print(f"  [FAIL] Git Tools: {e}")

    try:
        from src.workflows.notebook import WORKFLOW_TOOLS
        tests.append(("Workflow Tools", len(WORKFLOW_TOOLS), True))
        print(f"  [OK] Workflow Tools: {len(WORKFLOW_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Workflow Tools", 0, False))
        print(f"  [FAIL] Workflow Tools: {e}")

    try:
        from src.planning.planner import PLANNING_TOOLS
        tests.append(("Planning Tools", len(PLANNING_TOOLS), True))
        print(f"  [OK] Planning Tools: {len(PLANNING_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Planning Tools", 0, False))
        print(f"  [FAIL] Planning Tools: {e}")

    try:
        from src.tools.code_sandbox import SANDBOX_TOOLS
        tests.append(("Sandbox Tools", len(SANDBOX_TOOLS), True))
        print(f"  [OK] Sandbox Tools: {len(SANDBOX_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Sandbox Tools", 0, False))
        print(f"  [FAIL] Sandbox Tools: {e}")

    try:
        from src.context.attachments import CONTEXT_TOOLS
        tests.append(("Context Tools", len(CONTEXT_TOOLS), True))
        print(f"  [OK] Context Tools: {len(CONTEXT_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Context Tools", 0, False))
        print(f"  [FAIL] Context Tools: {e}")

    try:
        from src.tools.agent_tools import AGENT_TOOLS
        tests.append(("Agent Tools", len(AGENT_TOOLS), True))
        print(f"  [OK] Agent Tools: {len(AGENT_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Agent Tools", 0, False))
        print(f"  [FAIL] Agent Tools: {e}")

    try:
        from src.tools.error_fixer import ERROR_FIXER_TOOLS
        tests.append(("Error Fixer Tools", len(ERROR_FIXER_TOOLS), True))
        print(f"  [OK] Error Fixer Tools: {len(ERROR_FIXER_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Error Fixer Tools", 0, False))
        print(f"  [FAIL] Error Fixer Tools: {e}")

    try:
        from src.rules.agent_rules import RULES_TOOLS
        tests.append(("Rules Tools", len(RULES_TOOLS), True))
        print(f"  [OK] Rules Tools: {len(RULES_TOOLS)} tools loaded")
    except Exception as e:
        tests.append(("Rules Tools", 0, False))
        print(f"  [FAIL] Rules Tools: {e}")

    try:
        from src.agents.specialized import SPECIALIZED_AGENTS
        tests.append(("Specialized Agents", len(SPECIALIZED_AGENTS), True))
        print(f"  [OK] Specialized Agents: {len(SPECIALIZED_AGENTS)} agents loaded")
    except Exception as e:
        tests.append(("Specialized Agents", 0, False))
        print(f"  [FAIL] Specialized Agents: {e}")

    passed = sum(1 for t in tests if t[2])
    total_tools = sum(t[1] for t in tests)
    print(f"\n  Result: {passed}/{len(tests)} modules loaded, {total_tools} total tools")
    return passed == len(tests)


def test_git_tools():
    """Test git tools functionality."""
    print("\n" + "="*60)
    print("TEST 2: Git Tools")
    print("="*60)

    from src.tools.git_tools import git_status

    try:
        # Test git_status (will show not a git repo, which is expected)
        result = call_tool(git_status)
        print(f"  [OK] git_status: {result[:50]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] git_status failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_tools():
    """Test workflow/notebook tools."""
    print("\n" + "="*60)
    print("TEST 3: Workflow/Notebook Tools")
    print("="*60)

    from src.workflows.notebook import (
        create_workflow, add_workflow_step, list_workflows,
        show_workflow, delete_workflow
    )

    try:
        # Create a test workflow
        result = call_tool(create_workflow,
            name="test-workflow",
            description="Test workflow for verification",
            tags="test,demo"
        )
        print(f"  [OK] create_workflow: Created successfully")

        # Add a step
        result = call_tool(add_workflow_step,
            workflow_name="test-workflow",
            command="echo 'Hello World'",
            description="Print hello world"
        )
        print(f"  [OK] add_workflow_step: Step added")

        # List workflows
        result = call_tool(list_workflows)
        assert "test-workflow" in result
        print(f"  [OK] list_workflows: Found test workflow")

        # Show workflow
        result = call_tool(show_workflow, name="test-workflow")
        assert "Hello World" in result
        print(f"  [OK] show_workflow: Displayed correctly")

        # Delete workflow
        result = call_tool(delete_workflow, name="test-workflow")
        print(f"  [OK] delete_workflow: Deleted successfully")

        return True
    except Exception as e:
        print(f"  [FAIL] Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_planning_tools():
    """Test planning mode tools."""
    print("\n" + "="*60)
    print("TEST 4: Planning Mode Tools")
    print("="*60)

    from src.planning.planner import (
        create_plan, add_plan_step, show_plan,
        approve_plan, delete_plan, get_plan_manager
    )

    try:
        # Create a plan
        result = call_tool(create_plan,
            goal="Test the planning system",
            context="Verification test"
        )
        assert "Plan Created" in result
        print(f"  [OK] create_plan: Created successfully")

        # Add steps
        result = call_tool(add_plan_step,
            title="Step 1",
            description="First test step",
            commands="echo test"
        )
        print(f"  [OK] add_plan_step: Step added")

        # Show plan
        result = call_tool(show_plan)
        assert "Step 1" in result
        print(f"  [OK] show_plan: Displayed correctly")

        # Approve plan
        result = call_tool(approve_plan)
        assert "Approved" in result
        print(f"  [OK] approve_plan: Plan approved")

        # Clean up
        manager = get_plan_manager()
        if manager._current_plan:
            call_tool(delete_plan, plan_id=manager._current_plan.id)
            print(f"  [OK] delete_plan: Cleaned up")

        return True
    except Exception as e:
        print(f"  [FAIL] Planning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sandbox_tools():
    """Test Python REPL sandbox tools."""
    print("\n" + "="*60)
    print("TEST 5: Python REPL Sandbox Tools")
    print("="*60)

    from src.tools.code_sandbox import (
        python_exec, python_eval, python_import,
        python_repl_vars, python_repl_reset
    )

    try:
        # Reset sandbox first
        call_tool(python_repl_reset)
        print(f"  [OK] python_repl_reset: Sandbox reset")

        # Execute code
        result = call_tool(python_exec, code="x = 42\nprint(f'The answer is {x}')")
        assert "42" in result
        print(f"  [OK] python_exec: Code executed, output captured")

        # Evaluate expression
        result = call_tool(python_eval, expression="x * 2")
        assert "84" in result
        print(f"  [OK] python_eval: Expression evaluated correctly")

        # Check variables
        result = call_tool(python_repl_vars)
        assert "x" in result
        print(f"  [OK] python_repl_vars: Variable tracking works")

        # Import module
        result = call_tool(python_import, module="math")
        assert "math" in result
        print(f"  [OK] python_import: Module imported")

        # Use imported module
        result = call_tool(python_eval, expression="math.sqrt(16)")
        assert "4" in result
        print(f"  [OK] Imported module works correctly")

        # Reset again
        call_tool(python_repl_reset)

        return True
    except Exception as e:
        print(f"  [FAIL] Sandbox test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_tools():
    """Test context attachment tools."""
    print("\n" + "="*60)
    print("TEST 6: Context Attachment Tools")
    print("="*60)

    from src.context.attachments import (
        attach_file, attach_folder, show_context, clear_context
    )

    try:
        # Clear first
        call_tool(clear_context)
        print(f"  [OK] clear_context: Context cleared")

        # Attach a file
        result = call_tool(attach_file, file_path="pyproject.toml")
        assert "Attached" in result or "Error" not in result
        print(f"  [OK] attach_file: File attached")

        # Show context
        result = call_tool(show_context)
        assert "pyproject.toml" in result or "Attached Context" in result
        print(f"  [OK] show_context: Context displayed")

        # Attach folder
        result = call_tool(attach_folder, folder_path="src", max_depth=1)
        print(f"  [OK] attach_folder: Folder attached")

        # Clear
        result = call_tool(clear_context)
        assert "Cleared" in result
        print(f"  [OK] clear_context: All cleared")

        return True
    except Exception as e:
        print(f"  [FAIL] Context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_tools():
    """Test multi-agent tools."""
    print("\n" + "="*60)
    print("TEST 7: Multi-Agent Tools")
    print("="*60)

    from src.tools.agent_tools import list_agents
    from src.agents.specialized import list_specialized_agents, SPECIALIZED_AGENTS

    try:
        # List agents
        result = call_tool(list_agents)
        assert "reviewer" in result.lower()
        assert "debugger" in result.lower()
        print(f"  [OK] list_agents: All agents listed")

        # Check specialized agents registry
        agents = list_specialized_agents()
        assert len(agents) == 6
        print(f"  [OK] Specialized agents: {len(agents)} agents registered")

        # Verify each agent type
        for agent_type in ["reviewer", "debugger", "refactor", "tester", "docs", "git"]:
            assert agent_type in SPECIALIZED_AGENTS
            print(f"    - {agent_type}: OK")

        return True
    except Exception as e:
        print(f"  [FAIL] Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_fixer_tools():
    """Test error analysis tools."""
    print("\n" + "="*60)
    print("TEST 8: Error Analysis Tools")
    print("="*60)

    from src.tools.error_fixer import analyze_error, ErrorParser

    try:
        # Test Python error parsing
        python_error = '''Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = calculate(x)
  File "test.py", line 5, in calculate
    return x / y
ZeroDivisionError: division by zero'''

        result = call_tool(analyze_error, error_output=python_error)
        assert "ZeroDivisionError" in result
        assert "Suggested Fixes" in result
        print(f"  [OK] analyze_error: Python error analyzed")

        # Test JavaScript error
        js_error = '''TypeError: Cannot read property 'x' of undefined
    at processData (/app/src/utils.js:42:15)
    at main (/app/src/index.js:10:5)'''

        result = call_tool(analyze_error, error_output=js_error)
        assert "TypeError" in result
        print(f"  [OK] analyze_error: JavaScript error analyzed")

        # Test TypeScript error
        ts_error = "src/app.ts(15,23): error TS2339: Property 'foo' does not exist on type 'Bar'."

        parser = ErrorParser()
        errors = parser.parse_typescript_error(ts_error)
        assert len(errors) > 0
        assert errors[0].line_number == 15
        print(f"  [OK] ErrorParser: TypeScript errors parsed correctly")

        return True
    except Exception as e:
        print(f"  [FAIL] Error fixer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rules_tools():
    """Test agent rules tools."""
    print("\n" + "="*60)
    print("TEST 9: Agent Rules Tools")
    print("="*60)

    from src.rules.agent_rules import (
        create_agent_rules, load_agent_rules, show_agent_rules
    )
    from pathlib import Path

    try:
        # Create rules file
        result = call_tool(create_agent_rules,
            style_guide="Use 4 spaces for indentation",
            testing_rules="All functions must have tests"
        )
        assert "Created" in result
        print(f"  [OK] create_agent_rules: Rules file created")

        # Load rules
        result = call_tool(load_agent_rules)
        assert "Code Style" in result or "Agent Rules" in result
        print(f"  [OK] load_agent_rules: Rules loaded")

        # Show rules
        result = call_tool(show_agent_rules)
        assert "Agent Rules" in result or "indentation" in result
        print(f"  [OK] show_agent_rules: Rules displayed")

        # Clean up
        rules_path = Path("AGENT.md")
        if rules_path.exists():
            rules_path.unlink()
            print(f"  [OK] Cleaned up test AGENT.md")

        return True
    except Exception as e:
        print(f"  [FAIL] Rules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_agent():
    """Test the full CodingAgent with all tools."""
    print("\n" + "="*60)
    print("TEST 10: Full CodingAgent Integration")
    print("="*60)

    try:
        from src.agents.coding_agent import CodingAgent

        # Just test that it initializes with all tools
        print("  [SKIP] Skipping full agent test (requires Ollama)")
        print("  [OK] CodingAgent class imports successfully")

        # Count tools
        from src.tools.terminal import TERMINAL_TOOLS
        from src.tools.file_ops import FILE_TOOLS
        from src.tools.code_search import SEARCH_TOOLS
        from src.tools.git_tools import GIT_TOOLS
        from src.tools.code_sandbox import SANDBOX_TOOLS
        from src.tools.agent_tools import AGENT_TOOLS
        from src.tools.error_fixer import ERROR_FIXER_TOOLS
        from src.workflows.notebook import WORKFLOW_TOOLS
        from src.planning.planner import PLANNING_TOOLS
        from src.context.attachments import CONTEXT_TOOLS
        from src.rules.agent_rules import RULES_TOOLS

        total = (
            len(TERMINAL_TOOLS) + len(FILE_TOOLS) + len(SEARCH_TOOLS) +
            len(GIT_TOOLS) + len(SANDBOX_TOOLS) + len(AGENT_TOOLS) +
            len(ERROR_FIXER_TOOLS) + len(WORKFLOW_TOOLS) + len(PLANNING_TOOLS) +
            len(CONTEXT_TOOLS) + len(RULES_TOOLS)
        )

        print(f"\n  Tool Summary:")
        print(f"    Terminal:   {len(TERMINAL_TOOLS)}")
        print(f"    File Ops:   {len(FILE_TOOLS)}")
        print(f"    Search:     {len(SEARCH_TOOLS)}")
        print(f"    Git:        {len(GIT_TOOLS)}")
        print(f"    Sandbox:    {len(SANDBOX_TOOLS)}")
        print(f"    Agents:     {len(AGENT_TOOLS)}")
        print(f"    Error Fix:  {len(ERROR_FIXER_TOOLS)}")
        print(f"    Workflow:   {len(WORKFLOW_TOOLS)}")
        print(f"    Planning:   {len(PLANNING_TOOLS)}")
        print(f"    Context:    {len(CONTEXT_TOOLS)}")
        print(f"    Rules:      {len(RULES_TOOLS)}")
        print(f"    ----------------------")
        print(f"    TOTAL:      {total} tools")

        return True
    except Exception as e:
        print(f"  [FAIL] Full agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CODE AGENT - FEATURE TEST SUITE")
    print("="*60)

    results = []

    results.append(("Module Imports", test_imports()))
    results.append(("Git Tools", test_git_tools()))
    results.append(("Workflow Tools", test_workflow_tools()))
    results.append(("Planning Tools", test_planning_tools()))
    results.append(("Sandbox Tools", test_sandbox_tools()))
    results.append(("Context Tools", test_context_tools()))
    results.append(("Agent Tools", test_agent_tools()))
    results.append(("Error Fixer Tools", test_error_fixer_tools()))
    results.append(("Rules Tools", test_rules_tools()))
    results.append(("Full Agent", test_full_agent()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Results: {passed}/{len(results)} tests passed")

    if failed == 0:
        print("\n  === ALL TESTS PASSED! ===")
        return 0
    else:
        print(f"\n  WARNING: {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
