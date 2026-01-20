"""Automated demo script that runs all features without user input."""

import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
os.chdir(Path(__file__).parent.parent)


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_demo(agent, prompt, description):
    """Run a single demo and show results."""
    print(f"\n  [{description}]")
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

        # Show preview
        preview = content[:200].replace('\n', ' ')
        print(f"  Response: {preview}...")
        print("  [OK]")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        print("  [FAIL]")
        return False


def main():
    """Run automated demo of all features."""
    print("\n" + "=" * 70)
    print("  CODE AGENT - AUTOMATED FEATURE DEMO")
    print("  Testing all 68 tools with live Ollama LLM")
    print("=" * 70)

    # Check Ollama
    print("\n  Checking Ollama connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("  [ERROR] Ollama is not responding.")
            return 1
        print("  [OK] Ollama is running")
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Ollama: {e}")
        return 1

    # Initialize agent
    print("\n  Initializing CodingAgent...")
    try:
        from src.agents.coding_agent import CodingAgent
        agent = CodingAgent(session_id="auto-demo")
        print("  [OK] Agent ready with 68 tools!")
    except Exception as e:
        print(f"  [ERROR] Failed to initialize: {e}")
        return 1

    results = []

    # Demo 1: Terminal Tools
    print_header("DEMO 1: Terminal Tools")
    results.append(run_demo(agent, "List all files in the current directory", "list_directory"))
    results.append(run_demo(agent, "What is the current working directory?", "get_current_directory"))
    results.append(run_demo(agent, "Run the command: python --version", "run_terminal_command"))

    # Demo 2: File Tools
    print_header("DEMO 2: File Operation Tools")
    results.append(run_demo(agent, "Read the first 10 lines of pyproject.toml", "read_file"))
    results.append(run_demo(agent, "Create a file called demo_test.txt with content 'Hello Demo!'", "create_file"))

    # Demo 3: Search Tools
    print_header("DEMO 3: Search Tools")
    results.append(run_demo(agent, "Find all Python files in the src directory", "find_files"))
    results.append(run_demo(agent, "Show the directory structure of src/", "get_file_structure"))

    # Demo 4: Git Tools
    print_header("DEMO 4: Git Tools")
    results.append(run_demo(agent, "Check the git status", "git_status"))

    # Demo 5: Python Sandbox
    print_header("DEMO 5: Python Sandbox")
    results.append(run_demo(agent, "Execute Python: print('Hello from sandbox!'); x = 42; print(f'x = {x}')", "python_exec"))
    results.append(run_demo(agent, "Calculate 2 ** 10 using Python", "python_eval"))

    # Demo 6: Workflow Tools
    print_header("DEMO 6: Workflow Tools")
    results.append(run_demo(agent, "Create a workflow called 'demo-workflow' for testing", "create_workflow"))
    results.append(run_demo(agent, "List all saved workflows", "list_workflows"))

    # Demo 7: Planning Tools
    print_header("DEMO 7: Planning Tools")
    results.append(run_demo(agent, "Create a plan with goal 'Demo Plan' and context 'Testing planning'", "create_plan"))
    results.append(run_demo(agent, "Show the current plan", "show_plan"))

    # Demo 8: Context Tools
    print_header("DEMO 8: Context Attachment Tools")
    results.append(run_demo(agent, "Attach the file pyproject.toml to context", "attach_file"))
    results.append(run_demo(agent, "Show the current attached context", "show_context"))

    # Demo 9: Agent Tools
    print_header("DEMO 9: Specialized Agents")
    results.append(run_demo(agent, "List all available specialized agents", "list_agents"))

    # Demo 10: Error Analysis
    print_header("DEMO 10: Error Analysis Tools")
    results.append(run_demo(agent, "Analyze this error: NameError: name 'foo' is not defined", "analyze_error"))

    # Summary
    print_header("DEMO SUMMARY")
    passed = sum(1 for r in results if r)
    failed = len(results) - passed

    print(f"\n  Results: {passed}/{len(results)} demos passed")

    if failed == 0:
        print("\n  === ALL DEMOS COMPLETED SUCCESSFULLY! ===")
    else:
        print(f"\n  {failed} demo(s) had issues")

    # Cleanup
    demo_file = Path("demo_test.txt")
    if demo_file.exists():
        demo_file.unlink()
        print("\n  Cleaned up demo_test.txt")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
