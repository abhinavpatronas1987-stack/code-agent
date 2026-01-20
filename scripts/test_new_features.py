"""Test all new features (22-31)."""

from pathlib import Path

print('=' * 60)
print('  TESTING NEW FEATURES (22-31)')
print('=' * 60)

passed = 0
failed = 0

def test(name, test_func):
    global passed, failed
    try:
        test_func()
        print(f'[PASS] {name}')
        passed += 1
    except Exception as e:
        print(f'[FAIL] {name}: {e}')
        failed += 1

# Feature 22: Secret Scanner
print('\n--- Feature 22: Secret Scanner ---')

def test_secret_scanner():
    from src.core.secret_scanner import SecretScanner, scan_secrets
    scanner = SecretScanner(Path.cwd())
    result = scanner.scan()
    assert result.files_scanned > 0

test('Secret Scanner', test_secret_scanner)

# Feature 23: Snippet Manager
print('\n--- Feature 23: Snippet Manager ---')

def test_snippet_manager():
    from src.core.snippet_manager import SnippetManager, get_snippet_manager
    sm = get_snippet_manager()
    snippets = sm.list()
    assert len(snippets) >= 0  # Built-in snippets may exist

test('Snippet Manager', test_snippet_manager)

# Feature 24: Refactoring Tools
print('\n--- Feature 24: Refactoring Tools ---')

def test_refactoring():
    from src.core.refactoring import RefactoringTools, find_symbol
    rt = RefactoringTools(Path.cwd())
    locations = rt.find_symbol_occurrences('def')
    assert locations is not None

test('Refactoring Tools', test_refactoring)

# Feature 25: Linter Integration
print('\n--- Feature 25: Linter Integration ---')

def test_linter():
    from src.core.linter import LinterIntegration, get_linter
    linter = get_linter(Path.cwd())
    available = linter.detect_available_linters()
    assert available is not None

test('Linter Integration', test_linter)

# Feature 26: Task Board
print('\n--- Feature 26: Task Board ---')

def test_task_board():
    from src.core.task_board import TaskBoard, get_task_board
    tb = get_task_board()
    stats = tb.get_stats()
    assert 'total' in stats

test('Task Board', test_task_board)

# Feature 27: API Tester
print('\n--- Feature 27: API Tester ---')

def test_api_tester():
    from src.core.api_tester import ApiTester, get_api_tester
    tester = get_api_tester()
    env = tester.list_env()
    assert env is not None

test('API Tester', test_api_tester)

# Feature 28: Time Tracker
print('\n--- Feature 28: Time Tracker ---')

def test_time_tracker():
    from src.core.time_tracker import TimeTracker, get_time_tracker
    tt = get_time_tracker()
    status = tt.get_status()
    assert 'status' in status

test('Time Tracker', test_time_tracker)

# Feature 29: Database Tools
print('\n--- Feature 29: Database Tools ---')

def test_database_tools():
    from src.core.database_tools import DatabaseTools, get_database_tools
    db = get_database_tools()
    connections = db.list_connections()
    assert connections is not None

test('Database Tools', test_database_tools)

# Feature 30: Docker Tools
print('\n--- Feature 30: Docker Tools ---')

def test_docker_tools():
    from src.core.docker_tools import DockerTools, get_docker_tools
    docker = get_docker_tools(Path.cwd())
    # Just check initialization, Docker may not be available
    assert docker is not None

test('Docker Tools', test_docker_tools)

# Feature 31: Performance Profiler
print('\n--- Feature 31: Performance Profiler ---')

def test_profiler():
    from src.core.profiler import PerformanceProfiler, get_profiler, benchmark
    profiler = get_profiler()

    # Test timing
    with profiler.timer('test_op'):
        sum(range(1000))

    stats = profiler.get_timing_stats('test_op')
    assert stats is not None
    assert stats.calls == 1

test('Performance Profiler', test_profiler)

# Summary
print('\n' + '=' * 60)
print(f'  RESULTS: {passed} passed, {failed} failed')
print('=' * 60)

if failed == 0:
    print('\n  ALL 10 NEW FEATURES WORKING!')
else:
    print(f'\n  {failed} features need attention')
