"""Test script for AgentStatusDisplay and AgentActivitySummary."""

import time
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

# Test 1: Import test
print("=" * 50)
print("TEST 1: Imports")
print("=" * 50)
try:
    from src.core.visual_output import (
        AgentStatusDisplay,
        AgentActivitySummary,
        TOOL_DISPLAY_NAMES,
        console
    )
    print("[OK] All imports successful")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)


# Test 2: AgentStatusDisplay spinner
print("\n" + "=" * 50)
print("TEST 2: AgentStatusDisplay Spinner")
print("=" * 50)
print("Watch for animated spinner for 3 seconds...")
time.sleep(1)

try:
    with AgentStatusDisplay(show_tools=True) as status:
        # Simulate processing
        time.sleep(1)
        status.update_status("Reading files...")
        time.sleep(1)
        status.update_status("Running command: `npm install`")
        time.sleep(1)
    print("[OK] Spinner test completed")
except Exception as e:
    print(f"[FAIL] Spinner test failed: {e}")
    import traceback
    traceback.print_exc()


# Test 3: AgentActivitySummary with mock tool calls
print("\n" + "=" * 50)
print("TEST 3: AgentActivitySummary")
print("=" * 50)

try:
    # Create a mock chunk class to simulate tool calls
    class MockChunk:
        def __init__(self, tool_calls=None, content=None):
            self.tool_calls = tool_calls
            self.content = content

    activity = AgentActivitySummary()
    activity.start()

    # Simulate various tool calls
    mock_chunks = [
        MockChunk(tool_calls=[{"name": "read_file", "arguments": {"file_path": "/src/core/visual_output.py"}}]),
        MockChunk(tool_calls=[{"name": "read_file", "arguments": {"file_path": "/src/cli.py"}}]),
        MockChunk(tool_calls=[{"name": "edit_file", "arguments": {"file_path": "/src/config/settings.py"}}]),
        MockChunk(tool_calls=[{"name": "run_terminal_command", "arguments": {"command": "npm install express"}}]),
        MockChunk(tool_calls=[{"name": "git_status", "arguments": {}}]),
        MockChunk(tool_calls=[{"name": "git_commit", "arguments": {"message": "Add new feature"}}]),
        MockChunk(tool_calls=[{"name": "search_files", "arguments": {"pattern": "def.*test"}}]),
        MockChunk(tool_calls=[{"name": "write_file", "arguments": {"file_path": "/src/new_file.py"}}]),
    ]

    for chunk in mock_chunks:
        activity.track_from_chunk(chunk)

    time.sleep(0.5)  # Simulate some work
    activity.stop()

    print("Tracked activities:")
    print(f"  - Files read: {activity.files_read}")
    print(f"  - Files written: {activity.files_written}")
    print(f"  - Files edited: {activity.files_edited}")
    print(f"  - Commands run: {activity.commands_run}")
    print(f"  - Git operations: {activity.git_operations}")
    print(f"  - Searches: {activity.searches}")
    print(f"  - Tools used: {len(activity.tools_used)}")

    print("\nSummary Panel:")
    activity.print_summary()

    print("[OK] Activity summary test completed")
except Exception as e:
    print(f"[FAIL] Activity summary test failed: {e}")
    import traceback
    traceback.print_exc()


# Test 4: Combined spinner + activity tracking
print("\n" + "=" * 50)
print("TEST 4: Combined Spinner + Activity Tracking")
print("=" * 50)

try:
    activity = AgentActivitySummary()
    activity.start()

    with AgentStatusDisplay(show_tools=True) as status:
        # Simulate agent workflow
        chunks = [
            MockChunk(tool_calls=[{"name": "read_file", "arguments": {"file_path": "package.json"}}]),
            MockChunk(tool_calls=[{"name": "run_terminal_command", "arguments": {"command": "npm test"}}]),
            MockChunk(tool_calls=[{"name": "edit_file", "arguments": {"file_path": "src/index.js"}}]),
        ]

        for chunk in chunks:
            status.update_from_chunk(chunk)
            activity.track_from_chunk(chunk)
            time.sleep(0.8)

        # Simulate content starting
        status.stop()

    activity.stop()

    print("\nAgent response would appear here...")
    activity.print_summary()

    print("[OK] Combined test completed")
except Exception as e:
    print(f"[FAIL] Combined test failed: {e}")
    import traceback
    traceback.print_exc()


# Test 5: Tool display names
print("\n" + "=" * 50)
print("TEST 5: Tool Display Names")
print("=" * 50)

print(f"Registered tool names: {len(TOOL_DISPLAY_NAMES)}")
for tool, display in list(TOOL_DISPLAY_NAMES.items())[:5]:
    print(f"  {tool} -> {display}")
print("  ...")
print("[OK] Tool display names test completed")


print("\n" + "=" * 50)
print("ALL TESTS COMPLETED")
print("=" * 50)
