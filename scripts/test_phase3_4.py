"""Test Phase 3 & 4 Features."""

from pathlib import Path

print('Testing Phase 3 & 4 Features...')
print('=' * 50)

# Test 1: TUI
print('\n1. Testing TUI...')
from src.core.tui import TerminalUI, show_dashboard
tui = TerminalUI(Path.cwd())
print(f'   [OK] TUI initialized, state: {tui.state.status}')

# Test 2: Plugin System
print('\n2. Testing Plugin System...')
from src.core.plugins import get_plugin_manager
pm = get_plugin_manager()
plugins = pm.list_plugins()
print(f'   [OK] Plugin manager ready, discovered: {len(plugins)} plugins')

# Test 3: Profiles
print('\n3. Testing Profiles...')
from src.core.profiles import list_profiles, get_current_profile
profiles = list_profiles()
print(f'   [OK] Found {len(profiles)} profiles')
for p in profiles[:3]:
    name = p["name"]
    desc = p["description"][:40]
    print(f'      - {name}: {desc}')

# Test 4: Smart Context
print('\n4. Testing Smart Context...')
from src.core.smart_context import SmartContextManager, get_context_summary
ctx = SmartContextManager(Path.cwd())
ctx.add_file('src/cli.py')
summary = ctx.get_summary()
print(f'   [OK] Context: {summary["total_files"]} files, {summary["total_tokens"]} tokens')

# Test 5: Dependency Analyzer
print('\n5. Testing Dependency Analyzer...')
from src.core.dependency_analyzer import DependencyAnalyzer
da = DependencyAnalyzer(Path.cwd())
graph = da.analyze()
print(f'   [OK] Analyzed {len(graph.files)} files')
print(f'   [OK] Found {len(graph.circular)} circular deps')
print(f'   [OK] Found {len(graph.unused)} files with unused imports')

# Test 6: Metrics Dashboard
print('\n6. Testing Metrics Dashboard...')
from src.core.metrics_dashboard import MetricsDashboard
md = MetricsDashboard(Path.cwd())
metrics = md.analyze()
print(f'   [OK] Files: {metrics.file_count}')
print(f'   [OK] Total Lines: {metrics.total_lines:,}')
print(f'   [OK] Code Lines: {metrics.code_lines:,}')
print(f'   [OK] Functions: {metrics.total_functions}')
print(f'   [OK] Classes: {metrics.total_classes}')
print(f'   [OK] Languages: {dict(metrics.languages)}')

print('\n' + '=' * 50)
print('All Phase 3 & 4 Features Working!')
print('=' * 50)
