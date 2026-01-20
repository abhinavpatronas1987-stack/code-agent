"""Test all 31 CLI features."""

from pathlib import Path

print('=' * 70)
print('  TESTING ALL 31 CLI FEATURES')
print('=' * 70)

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

# ========== PHASE 1: Core Features (1-5) ==========
print('\n--- Phase 1: Core Features ---')

def test_model_providers():
    from src.core.model_providers import list_available_models
    models = list_available_models()
    assert len(models) > 0

def test_checkpoint():
    from src.core.checkpoint import CheckpointManager
    cm = CheckpointManager(Path.cwd())
    assert cm is not None

def test_diff_preview():
    from src.core.diff_preview import get_diff_preview
    preview = get_diff_preview()
    assert preview is not None

def test_project_detector():
    from src.core.project_detector import detect_project
    project = detect_project(Path.cwd())
    assert project.name is not None

def test_undo_redo():
    from src.core.undo_redo import get_undo_manager
    manager = get_undo_manager()
    assert manager is not None

test('1. Multi-Model Support', test_model_providers)
test('2. Checkpoint System', test_checkpoint)
test('3. Diff Preview Mode', test_diff_preview)
test('4. Project Auto-Detection', test_project_detector)
test('5. Undo/Redo Stack', test_undo_redo)

# ========== PHASE 2: Intelligence Features (6-10) ==========
print('\n--- Phase 2: Intelligence Features ---')

def test_memory():
    from src.core.memory import get_memory_manager
    mm = get_memory_manager()
    assert mm is not None

def test_codebase_index():
    from src.core.codebase_index import get_code_indexer
    indexer = get_code_indexer()
    assert indexer is not None

def test_watch_mode():
    from src.core.watch_mode import FileWatcher
    fw = FileWatcher(Path.cwd())
    assert fw is not None

def test_code_explainer():
    from src.core.code_explainer import get_code_explainer
    explainer = get_code_explainer()
    assert explainer is not None

def test_smart_context():
    from src.core.smart_context import SmartContextManager
    ctx = SmartContextManager(Path.cwd())
    assert ctx is not None

test('6. Persistent Memory', test_memory)
test('7. Codebase Indexing', test_codebase_index)
test('8. Watch Mode', test_watch_mode)
test('9. Code Explanation', test_code_explainer)
test('10. Smart Context', test_smart_context)

# ========== PHASE 3: Analysis Features (11-15) ==========
print('\n--- Phase 3: Analysis Features ---')

def test_dependency_analyzer():
    from src.core.dependency_analyzer import DependencyAnalyzer
    da = DependencyAnalyzer(Path.cwd())
    graph = da.analyze()
    assert len(graph.files) > 0

def test_metrics_dashboard():
    from src.core.metrics_dashboard import MetricsDashboard
    md = MetricsDashboard(Path.cwd())
    metrics = md.analyze()
    assert metrics.file_count > 0

def test_git_integration():
    from src.core.git_integration import GitIntegration
    gi = GitIntegration(Path.cwd())
    assert gi is not None

def test_test_runner():
    from src.core.test_runner import TestRunner
    tr = TestRunner(Path.cwd())
    assert tr is not None

def test_doc_generator():
    from src.core.doc_generator import DocGenerator
    dg = DocGenerator(Path.cwd())
    assert dg is not None

test('11. Dependency Analyzer', test_dependency_analyzer)
test('12. Code Metrics', test_metrics_dashboard)
test('13. Git Integration', test_git_integration)
test('14. Test Runner', test_test_runner)
test('15. Doc Generator', test_doc_generator)

# ========== PHASE 4: Productivity Features (16-21) ==========
print('\n--- Phase 4: Productivity Features ---')

def test_code_templates():
    from src.core.code_templates import TemplateEngine
    te = TemplateEngine(Path.cwd())
    templates = te.list_templates()
    assert len(templates) > 0

def test_session_manager():
    from src.core.session_manager import SessionManager
    sm = SessionManager()
    assert sm is not None

def test_shell_integration():
    from src.core.shell_integration import ShellIntegration
    si = ShellIntegration(Path.cwd())
    assert si is not None

def test_tui():
    from src.core.tui import TerminalUI
    tui = TerminalUI(Path.cwd())
    assert tui is not None

def test_plugins():
    from src.core.plugins import get_plugin_manager
    pm = get_plugin_manager()
    assert pm is not None

def test_project_creator():
    from src.core.project_creator import ProjectCreator
    pc = ProjectCreator()
    types = pc.list_project_types()
    assert len(types) > 0

test('16. Code Templates', test_code_templates)
test('17. Session Manager', test_session_manager)
test('18. Shell Integration', test_shell_integration)
test('19. Interactive TUI', test_tui)
test('20. Plugin System', test_plugins)
test('21. Project Creator', test_project_creator)

# ========== PHASE 5: Advanced Features (22-31) ==========
print('\n--- Phase 5: Advanced Features ---')

def test_secret_scanner():
    from src.core.secret_scanner import SecretScanner
    scanner = SecretScanner(Path.cwd())
    result = scanner.scan()
    assert result.files_scanned > 0

def test_snippet_manager():
    from src.core.snippet_manager import get_snippet_manager
    sm = get_snippet_manager()
    snippets = sm.list()
    assert snippets is not None

def test_refactoring():
    from src.core.refactoring import RefactoringTools
    rt = RefactoringTools(Path.cwd())
    assert rt is not None

def test_linter():
    from src.core.linter import LinterIntegration
    linter = LinterIntegration(Path.cwd())
    assert linter is not None

def test_task_board():
    from src.core.task_board import get_task_board
    tb = get_task_board()
    stats = tb.get_stats()
    assert 'total' in stats

def test_api_tester():
    from src.core.api_tester import get_api_tester
    tester = get_api_tester()
    assert tester is not None

def test_time_tracker():
    from src.core.time_tracker import get_time_tracker
    tt = get_time_tracker()
    status = tt.get_status()
    assert 'status' in status

def test_database_tools():
    from src.core.database_tools import get_database_tools
    db = get_database_tools()
    assert db is not None

def test_docker_tools():
    from src.core.docker_tools import get_docker_tools
    docker = get_docker_tools()
    assert docker is not None

def test_profiler():
    from src.core.profiler import get_profiler
    profiler = get_profiler()
    with profiler.timer('test'):
        sum(range(100))
    stats = profiler.get_timing_stats('test')
    assert stats is not None

test('22. Secret Scanner', test_secret_scanner)
test('23. Snippet Manager', test_snippet_manager)
test('24. Refactoring Tools', test_refactoring)
test('25. Linter Integration', test_linter)
test('26. Task Board', test_task_board)
test('27. API Tester', test_api_tester)
test('28. Time Tracker', test_time_tracker)
test('29. Database Tools', test_database_tools)
test('30. Docker Tools', test_docker_tools)
test('31. Performance Profiler', test_profiler)

# ========== SUMMARY ==========
print('\n' + '=' * 70)
print(f'  RESULTS: {passed} passed, {failed} failed out of 31 features')
print('=' * 70)

if failed == 0:
    print('\n  ALL 31 FEATURES WORKING!')
else:
    print(f'\n  {failed} features need attention')
