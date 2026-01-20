"""Code Agent Demo - Shows all 20 features."""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def main():
    console.print()
    console.print(Panel.fit('[bold cyan]CODE AGENT - FEATURE DEMO[/bold cyan]', border_style='cyan'))
    console.print()

    # 1. Project Detection
    console.print('[bold yellow]1. PROJECT AUTO-DETECTION[/bold yellow]')
    from src.core.project_detector import detect_project
    project = detect_project(Path.cwd())
    console.print(f'   Project: {project.name}')
    console.print(f'   Languages: {project.languages}')
    console.print()

    # 2. Multi-Model Support
    console.print('[bold yellow]2. MULTI-MODEL SUPPORT[/bold yellow]')
    from src.core.model_providers import AVAILABLE_MODELS
    models = list(AVAILABLE_MODELS.values())
    console.print(f'   Available Models: {len(models)}')
    for m in models[:3]:
        console.print(f'   - {m.display_name} ({m.provider.value})')
    console.print(f'   ... and {len(models)-3} more')
    console.print()

    # 3. Checkpoint System
    console.print('[bold yellow]3. CHECKPOINT SYSTEM[/bold yellow]')
    from src.core.checkpoint import CheckpointManager
    cm = CheckpointManager(Path.cwd())
    console.print(f'   Checkpoint Manager: Ready')
    console.print(f'   Can save/restore file states')
    console.print()

    # 4. Diff Preview
    console.print('[bold yellow]4. DIFF PREVIEW MODE[/bold yellow]')
    from src.core.diff_preview import get_diff_preview
    preview = get_diff_preview()
    console.print(f'   Diff Preview: Ready')
    console.print(f'   Shows changes before applying')
    console.print()

    # 5. Undo/Redo
    console.print('[bold yellow]5. UNDO/REDO STACK[/bold yellow]')
    from src.core.undo_redo import get_undo_manager
    manager = get_undo_manager()
    console.print(f'   Undo Manager: Ready')
    console.print(f'   Tracks all file changes')
    console.print()

    # 6. Persistent Memory
    console.print('[bold yellow]6. PERSISTENT MEMORY[/bold yellow]')
    from src.core.memory import get_memory_manager
    mm = get_memory_manager()
    console.print(f'   Memory Manager: Ready')
    console.print(f'   Remembers context across sessions')
    console.print()

    # 7. Codebase Indexing
    console.print('[bold yellow]7. CODEBASE INDEXING[/bold yellow]')
    from src.core.codebase_index import get_code_indexer
    indexer = get_code_indexer()
    console.print(f'   Code Indexer: Ready')
    console.print(f'   Fast symbol search')
    console.print()

    # 8. Watch Mode
    console.print('[bold yellow]8. WATCH MODE[/bold yellow]')
    from src.core.watch_mode import FileWatcher
    fw = FileWatcher(Path.cwd())
    console.print(f'   File Watcher: Ready')
    console.print(f'   Auto-responds to file changes')
    console.print()

    # 9. Code Explainer
    console.print('[bold yellow]9. CODE EXPLANATION[/bold yellow]')
    from src.core.code_explainer import get_code_explainer
    explainer = get_code_explainer()
    console.print(f'   Code Explainer: Ready')
    console.print(f'   Explains code in plain English')
    console.print()

    # 10. Smart Context
    console.print('[bold yellow]10. SMART CONTEXT[/bold yellow]')
    from src.core.smart_context import SmartContextManager
    ctx = SmartContextManager(Path.cwd())
    console.print(f'   Context Manager: Ready')
    console.print(f'   Intelligent context selection')
    console.print()

    # 11. Dependency Analyzer
    console.print('[bold yellow]11. DEPENDENCY ANALYZER[/bold yellow]')
    from src.core.dependency_analyzer import DependencyAnalyzer
    da = DependencyAnalyzer(Path.cwd())
    graph = da.analyze()
    console.print(f'   Files Analyzed: {len(graph.files)}')
    console.print(f'   Circular Dependencies: {len(graph.circular)}')
    console.print()

    # 12. Code Metrics
    console.print('[bold yellow]12. CODE METRICS DASHBOARD[/bold yellow]')
    from src.core.metrics_dashboard import get_metrics_summary
    summary = get_metrics_summary(Path.cwd())
    console.print(f'   Files: {summary["files"]}')
    console.print(f'   Code Lines: {summary["code_lines"]:,}')
    console.print(f'   Functions: {summary["functions"]}')
    console.print(f'   Classes: {summary["classes"]}')
    console.print()

    # 13. Git Integration
    console.print('[bold yellow]13. GIT INTEGRATION[/bold yellow]')
    from src.core.git_integration import GitIntegration
    gi = GitIntegration(Path.cwd())
    console.print(f'   Is Git Repo: {gi.is_repo}')
    console.print(f'   Smart commit messages')
    console.print()

    # 14. Test Runner
    console.print('[bold yellow]14. TEST RUNNER[/bold yellow]')
    from src.core.test_runner import TestRunner
    tr = TestRunner(Path.cwd())
    console.print(f'   Framework: {tr.framework.value}')
    console.print(f'   Supports: pytest, jest, go test, cargo test')
    console.print()

    # 15. Doc Generator
    console.print('[bold yellow]15. DOC GENERATOR[/bold yellow]')
    from src.core.doc_generator import DocGenerator
    dg = DocGenerator(Path.cwd())
    console.print(f'   Doc Generator: Ready')
    console.print(f'   Auto-generates docstrings and README')
    console.print()

    # 16. Code Templates
    console.print('[bold yellow]16. CODE TEMPLATES[/bold yellow]')
    from src.core.code_templates import list_templates
    templates = list_templates()
    console.print(f'   Templates Available: {len(templates)}')
    for t in list(templates)[:3]:
        name = t.get('name', t) if isinstance(t, dict) else t
        console.print(f'   - {name}')
    console.print()

    # 17. Session Manager
    console.print('[bold yellow]17. SESSION MANAGER[/bold yellow]')
    from src.core.session_manager import SessionManager
    sm = SessionManager()
    console.print(f'   Session Manager: Ready')
    console.print(f'   Save/resume conversations')
    console.print()

    # 18. Shell Integration
    console.print('[bold yellow]18. SHELL INTEGRATION[/bold yellow]')
    from src.core.shell_integration import ShellIntegration
    si = ShellIntegration(Path.cwd())
    suggestions = si.suggest_commands('test')
    console.print(f'   Command Suggestions:')
    for s in suggestions[:2]:
        console.print(f'   - {s.command}')
    console.print()

    # 19. Interactive TUI
    console.print('[bold yellow]19. INTERACTIVE TUI[/bold yellow]')
    from src.core.tui import TerminalUI
    tui = TerminalUI(Path.cwd())
    console.print(f'   TUI Dashboard: Ready')
    console.print(f'   Rich terminal interface')
    console.print()

    # 20. Plugin System
    console.print('[bold yellow]20. PLUGIN SYSTEM[/bold yellow]')
    from src.core.plugins import get_plugin_manager
    pm = get_plugin_manager()
    console.print(f'   Plugin Manager: Ready')
    console.print(f'   Extend with custom plugins')
    console.print()

    # Profiles bonus
    console.print('[bold yellow]BONUS: CONFIGURATION PROFILES[/bold yellow]')
    from src.core.profiles import list_profiles
    profiles = list_profiles()
    console.print(f'   Built-in Profiles: {len(profiles)}')
    for p in list(profiles)[:4]:
        name = p.get('name', p) if isinstance(p, dict) else getattr(p, 'name', str(p))
        console.print(f'   - {name}')
    console.print()

    # Summary
    console.print(Panel.fit('[bold green]ALL 20 FEATURES OPERATIONAL![/bold green]', border_style='green'))
    console.print()

    # Commands table
    table = Table(title="Key Commands", show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")

    table.add_row("/help", "Show all commands")
    table.add_row("/model", "Switch AI model")
    table.add_row("/metrics", "Code metrics dashboard")
    table.add_row("/deps", "Dependency analysis")
    table.add_row("/test", "Run tests")
    table.add_row("/git", "Git status")
    table.add_row("/explain", "Explain code")
    table.add_row("/templates", "List code templates")
    table.add_row("/profile", "Switch profile")
    table.add_row("/dashboard", "Interactive TUI")

    console.print(table)
    console.print()

    console.print('[dim]Run: python -m src.cli[/dim]')
    console.print()

if __name__ == "__main__":
    main()
