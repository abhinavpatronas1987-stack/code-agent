"""Interactive demo script to test all features one by one."""

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


def wait_for_enter():
    input("\n  Press ENTER to continue...")


def demo_terminal(agent):
    """Demo terminal tools."""
    print_header("DEMO 1: Terminal Tools")
    print("""
  Available tools:
    - run_terminal_command: Execute any shell command
    - list_directory: List files in a directory
    - get_current_directory: Show current path
    - change_directory: Navigate filesystem

  Try these prompts:
    > "List all files here"
    > "Run: python --version"
    > "What's the current directory?"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_files(agent):
    """Demo file tools."""
    print_header("DEMO 2: File Operation Tools")
    print("""
  Available tools:
    - read_file: Read file contents
    - write_file: Write/overwrite files
    - edit_file: Find and replace in files
    - create_file: Create new files
    - delete_file: Delete files
    - move_file: Move/rename files
    - copy_file: Copy files

  Try these prompts:
    > "Read the README.md file"
    > "Create a file called hello.py with a hello world function"
    > "Show me lines 1-20 of pyproject.toml"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_search(agent):
    """Demo search tools."""
    print_header("DEMO 3: Search Tools")
    print("""
  Available tools:
    - search_files: Search file contents (like grep)
    - find_files: Find files by name pattern
    - get_file_structure: Show directory tree
    - get_file_info: Get file metadata

  Try these prompts:
    > "Find all Python files in src/"
    > "Search for 'def run' in Python files"
    > "Show me the project structure"
    > "How big is the pyproject.toml file?"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_git(agent):
    """Demo git tools."""
    print_header("DEMO 4: Git Tools")
    print("""
  Available tools:
    - git_status: Show repository status
    - git_diff: Show changes
    - git_log: Show commit history
    - git_branch: Manage branches
    - git_add: Stage files
    - git_commit: Create commits
    - git_push: Push to remote
    - git_pull: Pull from remote
    - git_stash: Stash changes
    - git_clone: Clone repositories

  Try these prompts:
    > "Check git status"
    > "Show recent commits"
    > "What branches exist?"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_sandbox(agent):
    """Demo Python sandbox tools."""
    print_header("DEMO 5: Python Sandbox (REPL)")
    print("""
  Available tools:
    - python_exec: Execute Python code
    - python_eval: Evaluate expressions
    - python_import: Import modules
    - python_repl_vars: Show defined variables
    - python_run_file: Run Python files
    - python_repl_reset: Reset sandbox

  Try these prompts:
    > "Execute: x = 10; y = 20; print(x + y)"
    > "Calculate 2 ** 100"
    > "Import numpy and create a 3x3 array of zeros"
    > "What variables are defined in the sandbox?"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_workflow(agent):
    """Demo workflow tools."""
    print_header("DEMO 6: Workflow/Notebook System")
    print("""
  Available tools:
    - create_workflow: Create a new workflow
    - add_workflow_step: Add steps to workflow
    - list_workflows: List all workflows
    - show_workflow: View workflow details
    - run_workflow: Execute a workflow
    - delete_workflow: Remove workflow
    - save_command_to_workflow: Quick save

  Try these prompts:
    > "Create a workflow called 'build-project' for building a Python project"
    > "Add step 'pip install -r requirements.txt' to build-project"
    > "Show me the build-project workflow"
    > "List all saved workflows"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_planning(agent):
    """Demo planning tools."""
    print_header("DEMO 7: Planning Mode")
    print("""
  Available tools:
    - create_plan: Create a task plan
    - add_plan_step: Add steps to plan
    - show_plan: View current plan
    - approve_plan: Approve for execution
    - execute_plan: Run the plan
    - complete_plan_step: Mark step done
    - list_plans: List all plans
    - delete_plan: Remove plan

  Try these prompts:
    > "Create a plan to add a new user authentication feature"
    > "Add step: Create user model with fields for email and password"
    > "Add step: Implement login endpoint"
    > "Show the current plan"
    > "Approve the plan"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_context(agent):
    """Demo context attachment tools."""
    print_header("DEMO 8: Context Attachments")
    print("""
  Available tools:
    - attach_file: Add file to context
    - attach_folder: Add folder structure
    - attach_selection: Add specific lines
    - attach_files_by_pattern: Add multiple files
    - show_context: View attached context
    - clear_context: Remove all context

  Try these prompts:
    > "Attach the file pyproject.toml to our conversation"
    > "Attach the src folder structure"
    > "Show what's in the current context"
    > "Attach all Python files matching *.py in src/tools/"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_agents(agent):
    """Demo specialized agents."""
    print_header("DEMO 9: Specialized Agents")
    print("""
  Available agents:
    - reviewer: Code review
    - debugger: Help debugging
    - refactor: Suggest refactoring
    - tester: Write tests
    - docs: Create documentation
    - git: Git operations

  Available tools:
    - list_agents: Show all agents
    - invoke_agent: Call specific agent
    - code_review: Quick code review
    - debug_help: Get debugging help
    - suggest_refactoring: Get refactor ideas
    - generate_tests: Create tests
    - generate_docs: Create documentation

  Try these prompts:
    > "List all available specialized agents"
    > "Review the code in src/tools/terminal.py"
    > "Help me debug: TypeError: 'NoneType' has no attribute 'split'"
    > "Generate tests for the git_status function"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_error_fixer(agent):
    """Demo error analysis tools."""
    print_header("DEMO 10: Error Analysis & Auto-Fix")
    print("""
  Available tools:
    - analyze_error: Parse and analyze errors
    - run_and_fix: Run command with error analysis
    - diagnose_file: Check file for issues
    - suggest_fix: Get fix suggestions

  Try these prompts:
    > "Analyze this error: NameError: name 'foo' is not defined"
    > "Analyze: TypeError: cannot unpack non-iterable NoneType object"
    > "Run 'python -c print(undefined)' and analyze any errors"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def demo_rules(agent):
    """Demo agent rules tools."""
    print_header("DEMO 11: Agent Rules (AGENT.md)")
    print("""
  Available tools:
    - create_agent_rules: Create AGENT.md
    - load_agent_rules: Load rules from file
    - show_agent_rules: Display current rules
    - get_rule_section: Get specific section
    - check_rules_compliance: Verify file follows rules

  Try these prompts:
    > "Create an AGENT.md file with coding standards for this project"
    > "The style guide should require type hints and docstrings"
    > "Show the current agent rules"
    """)

    while True:
        prompt = input("\n  Your prompt (or 'next' to continue): ").strip()
        if prompt.lower() == 'next':
            break
        if prompt:
            print("\n  Agent response:")
            agent.print_response(prompt)


def main():
    """Run interactive demo."""
    print("\n" + "=" * 70)
    print("  CODE AGENT - INTERACTIVE FEATURE DEMO")
    print("  Test all 68 tools with live Ollama LLM")
    print("=" * 70)

    # Check Ollama
    print("\n  Checking Ollama connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("  [ERROR] Ollama is not responding.")
            print("  Please start Ollama: ollama serve")
            return 1
        print("  [OK] Ollama is running")
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Ollama: {e}")
        return 1

    # Initialize agent
    print("\n  Initializing CodingAgent...")
    try:
        from src.agents.coding_agent import CodingAgent
        agent = CodingAgent(session_id="demo")
        print("  [OK] Agent ready with 68 tools!")
    except Exception as e:
        print(f"  [ERROR] Failed to initialize: {e}")
        return 1

    # Menu
    demos = [
        ("Terminal Tools", demo_terminal),
        ("File Operations", demo_files),
        ("Search Tools", demo_search),
        ("Git Tools", demo_git),
        ("Python Sandbox", demo_sandbox),
        ("Workflows", demo_workflow),
        ("Planning Mode", demo_planning),
        ("Context Attachments", demo_context),
        ("Specialized Agents", demo_agents),
        ("Error Analysis", demo_error_fixer),
        ("Agent Rules", demo_rules),
    ]

    while True:
        print_header("DEMO MENU")
        print("\n  Choose a feature to demo:\n")
        for i, (name, _) in enumerate(demos, 1):
            print(f"    {i}. {name}")
        print(f"    {len(demos) + 1}. Run ALL demos")
        print("    0. Exit")

        try:
            choice = input("\n  Enter choice: ").strip()
            if choice == '0':
                print("\n  Goodbye!")
                break
            elif choice == str(len(demos) + 1):
                for name, func in demos:
                    func(agent)
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(demos):
                    demos[idx][1](agent)
                else:
                    print("  Invalid choice")
        except ValueError:
            print("  Please enter a number")
        except KeyboardInterrupt:
            print("\n\n  Interrupted. Goodbye!")
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
