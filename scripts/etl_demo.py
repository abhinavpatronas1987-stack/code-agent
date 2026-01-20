"""Demo: Using Code Agent to build an ETL project."""

import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, description):
    print(f"\n  STEP {step_num}: {description}")
    print("-" * 50)


def run_agent_task(agent, prompt):
    """Run a task and show the response."""
    print(f"\n  > Prompt: {prompt[:70]}..." if len(prompt) > 70 else f"\n  > Prompt: {prompt}")
    print("  > Processing...")

    try:
        response = agent.run(prompt, stream=False)

        # Extract content
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'messages') and response.messages:
            last_msg = response.messages[-1]
            content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        else:
            content = str(response)

        # Show response (truncated)
        lines = content.split('\n')
        preview = '\n'.join(lines[:10])
        print(f"\n  Response:\n{preview}")
        if len(lines) > 10:
            print(f"  ... ({len(lines) - 10} more lines)")
        print("\n  [OK]")
        return True

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return False


def main():
    print_header("CODE AGENT - ETL PROJECT DEMO")
    print("""
  This demo shows how to use Code Agent to build a real ETL project.

  Code Agent will use its 68 tools to:
  - Create project structure
  - Write Python code for Extract, Transform, Load
  - Test the code
  - Run the pipeline
    """)

    # Check Ollama
    print("  Checking Ollama connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("  [ERROR] Ollama not responding. Run: ollama serve")
            return 1
        print("  [OK] Ollama is running")
    except Exception as e:
        print(f"  [ERROR] Cannot connect to Ollama: {e}")
        return 1

    # Initialize agent
    print("\n  Initializing Code Agent...")
    try:
        from src.agents.coding_agent import CodingAgent
        agent = CodingAgent(
            session_id="etl-builder",
            workspace=Path("D:/projects/my_etl_project")
        )
        print("  [OK] Agent ready!")
    except Exception as e:
        print(f"  [ERROR] Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # =========================================
    # STEP 1: Create Project Structure
    # =========================================
    print_step(1, "Creating ETL Project Structure")

    run_agent_task(agent, """
    Create the folder structure for an ETL project at D:/projects/my_etl_project:
    - src/ folder for source code
    - data/input/ for input files
    - data/output/ for output files
    - logs/ for log files
    - tests/ for test files
    Also create an empty __init__.py in src/
    """)

    # =========================================
    # STEP 2: Create Extract Module
    # =========================================
    print_step(2, "Creating Extract Module")

    run_agent_task(agent, """
    Create a file D:/projects/my_etl_project/src/extract.py with a CSVExtractor class that:
    - Takes a file path as input
    - Has an extract() method that reads CSV and returns list of dictionaries
    - Handles file not found errors
    - Logs the number of records extracted
    Include proper docstrings and type hints.
    """)

    # =========================================
    # STEP 3: Create Transform Module
    # =========================================
    print_step(3, "Creating Transform Module")

    run_agent_task(agent, """
    Create a file D:/projects/my_etl_project/src/transform.py with a DataTransformer class that:
    - Takes a list of dictionaries as input
    - Has methods: clean_nulls(), normalize_text(), filter_records()
    - Has a transform() method that applies all transformations
    - Returns the transformed data
    Include proper docstrings and type hints.
    """)

    # =========================================
    # STEP 4: Create Load Module
    # =========================================
    print_step(4, "Creating Load Module")

    run_agent_task(agent, """
    Create a file D:/projects/my_etl_project/src/load.py with a DataLoader class that:
    - Takes data and output path as input
    - Has methods: to_csv(), to_json()
    - Logs the number of records saved
    - Returns success/failure status
    Include proper docstrings and type hints.
    """)

    # =========================================
    # STEP 5: Create Pipeline Orchestrator
    # =========================================
    print_step(5, "Creating Pipeline Orchestrator")

    run_agent_task(agent, """
    Create a file D:/projects/my_etl_project/src/pipeline.py with an ETLPipeline class that:
    - Combines Extract, Transform, Load steps
    - Has a run() method that executes the full pipeline
    - Tracks metrics: records extracted, transformed, loaded
    - Handles errors gracefully
    - Logs progress at each step
    Also create a main() function that can be run from command line.
    """)

    # =========================================
    # STEP 6: Create Sample Data
    # =========================================
    print_step(6, "Creating Sample Data")

    run_agent_task(agent, """
    Create a sample CSV file at D:/projects/my_etl_project/data/input/sample_data.csv with:
    - Columns: id, name, email, age, city
    - 10 sample records with some realistic data
    - Include some null values and inconsistent casing for testing
    """)

    # =========================================
    # STEP 7: Test the Pipeline
    # =========================================
    print_step(7, "Testing the Pipeline")

    run_agent_task(agent, """
    Run the ETL pipeline by executing:
    python D:/projects/my_etl_project/src/pipeline.py

    Show me the output and any errors.
    """)

    # =========================================
    # STEP 8: Show Results
    # =========================================
    print_step(8, "Showing Results")

    run_agent_task(agent, """
    Show me the contents of the output file that was created.
    List all files in D:/projects/my_etl_project/data/output/
    """)

    # Summary
    print_header("DEMO COMPLETE")
    print("""
  Code Agent has built an ETL pipeline for you!

  Project Location: D:/projects/my_etl_project/

  Files Created:
    - src/extract.py   - Data extraction from CSV
    - src/transform.py - Data transformation/cleaning
    - src/load.py      - Data loading to CSV/JSON
    - src/pipeline.py  - Pipeline orchestrator
    - data/input/sample_data.csv - Test data

  To run the pipeline yourself:
    cd D:/projects/my_etl_project
    python src/pipeline.py

  This demonstrates how Code Agent can help you build
  real projects by using natural language commands!
    """)

    return 0


if __name__ == "__main__":
    sys.exit(main())
