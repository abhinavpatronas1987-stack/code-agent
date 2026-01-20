"""Dependency Analyzer - Feature 10.

Analyze project dependencies:
- Import graph visualization
- Circular dependency detection
- Unused import detection
- Dependency upgrades
"""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from src.config.settings import get_settings


@dataclass
class ImportInfo:
    """Information about an import."""
    module: str
    names: List[str]  # Specific imports (from x import a, b)
    alias: Optional[str] = None
    line: int = 0
    is_relative: bool = False


@dataclass
class FileImports:
    """Imports for a single file."""
    file_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    stdlib: List[str] = field(default_factory=list)
    third_party: List[str] = field(default_factory=list)
    local: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Full dependency graph for the project."""
    files: Dict[str, FileImports] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from_file, to_module)
    circular: List[List[str]] = field(default_factory=list)
    unused: Dict[str, List[str]] = field(default_factory=dict)


class DependencyAnalyzer:
    """Analyze project dependencies."""

    # Python standard library modules (common ones)
    STDLIB_MODULES = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio', 'atexit',
        'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
        'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code',
        'codecs', 'codeop', 'collections', 'colorsys', 'compileall',
        'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy',
        'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses',
        'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis',
        'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno',
        'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch',
        'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq',
        'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp', 'importlib',
        'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
        'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
        'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder',
        'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator',
        'optparse', 'os', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
        'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath',
        'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
        'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
        'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
        'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd',
        'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
        'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog',
        'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
        'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token',
        'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
        'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
        'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp',
        'zipfile', 'zipimport', 'zlib', '_thread', '__future__',
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize analyzer."""
        self.working_dir = working_dir or Path.cwd()
        self.graph = DependencyGraph()

    def analyze(self) -> DependencyGraph:
        """
        Analyze all dependencies in the project.

        Returns:
            DependencyGraph with all analysis results
        """
        self.graph = DependencyGraph()

        # Find all Python files
        py_files = list(self.working_dir.rglob('*.py'))

        # Skip ignored directories
        py_files = [
            f for f in py_files
            if not any(p.startswith('.') or p in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build')
                       for p in f.parts)
        ]

        # Analyze each file
        for py_file in py_files:
            file_imports = self._analyze_file(py_file)
            self.graph.files[str(py_file)] = file_imports

            # Build edges
            for imp in file_imports.imports:
                self.graph.edges.append((str(py_file), imp.module))

        # Detect circular dependencies
        self.graph.circular = self._detect_circular()

        # Detect unused imports
        self.graph.unused = self._detect_unused()

        return self.graph

    def _analyze_file(self, file_path: Path) -> FileImports:
        """Analyze imports in a single file."""
        result = FileImports(file_path=str(file_path))

        try:
            content = file_path.read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return result

        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments and strings
            if stripped.startswith('#') or stripped.startswith('"') or stripped.startswith("'"):
                continue

            # import x, import x as y
            match = re.match(r'^import\s+(\S+)(?:\s+as\s+(\w+))?', stripped)
            if match:
                module = match.group(1)
                alias = match.group(2)
                imp = ImportInfo(
                    module=module,
                    names=[],
                    alias=alias,
                    line=i,
                    is_relative=module.startswith('.'),
                )
                result.imports.append(imp)
                self._categorize_import(result, module)
                continue

            # from x import y, z
            match = re.match(r'^from\s+(\S+)\s+import\s+(.+)', stripped)
            if match:
                module = match.group(1)
                imports_str = match.group(2)

                # Parse imported names
                names = []
                for part in imports_str.split(','):
                    part = part.strip()
                    if ' as ' in part:
                        name = part.split(' as ')[0].strip()
                    else:
                        name = part.strip('() ')
                    if name and name != '*':
                        names.append(name)

                imp = ImportInfo(
                    module=module,
                    names=names,
                    line=i,
                    is_relative=module.startswith('.'),
                )
                result.imports.append(imp)
                self._categorize_import(result, module)

        return result

    def _categorize_import(self, result: FileImports, module: str):
        """Categorize an import as stdlib, third-party, or local."""
        base_module = module.lstrip('.').split('.')[0]

        if module.startswith('.') or module.startswith('src'):
            result.local.append(module)
        elif base_module in self.STDLIB_MODULES:
            result.stdlib.append(module)
        else:
            result.third_party.append(module)

    def _detect_circular(self) -> List[List[str]]:
        """Detect circular dependencies."""
        circular = []

        # Build adjacency list
        adj: Dict[str, Set[str]] = defaultdict(set)
        for from_file, to_module in self.graph.edges:
            # Try to resolve module to file
            resolved = self._resolve_module_to_file(to_module)
            if resolved:
                adj[from_file].add(resolved)

        # DFS to find cycles
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for node in adj:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    # Simplify to relative paths
                    simplified = []
                    for p in cycle:
                        try:
                            simplified.append(str(Path(p).relative_to(self.working_dir)))
                        except ValueError:
                            simplified.append(p)
                    circular.append(simplified)

        return circular

    def _resolve_module_to_file(self, module: str) -> Optional[str]:
        """Try to resolve a module name to a file path."""
        if module.startswith('.'):
            return None  # Relative imports need more context

        # Try as package
        parts = module.replace('.', '/')
        candidates = [
            self.working_dir / f"{parts}.py",
            self.working_dir / parts / "__init__.py",
            self.working_dir / "src" / f"{parts}.py",
            self.working_dir / "src" / parts / "__init__.py",
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        return None

    def _detect_unused(self) -> Dict[str, List[str]]:
        """Detect potentially unused imports."""
        unused = {}

        for file_path, file_imports in self.graph.files.items():
            try:
                content = Path(file_path).read_text(encoding='utf-8')
            except (IOError, UnicodeDecodeError):
                continue

            file_unused = []

            for imp in file_imports.imports:
                # Check if imported names are used
                if imp.names:
                    for name in imp.names:
                        # Simple check: is the name used in the file?
                        pattern = rf'\b{re.escape(name)}\b'
                        matches = len(re.findall(pattern, content))
                        # Should appear more than just in the import
                        if matches <= 1:
                            file_unused.append(f"{imp.module}.{name}")
                elif imp.alias:
                    pattern = rf'\b{re.escape(imp.alias)}\b'
                    if len(re.findall(pattern, content)) <= 1:
                        file_unused.append(f"{imp.module} as {imp.alias}")
                else:
                    # Module import
                    module_name = imp.module.split('.')[-1]
                    pattern = rf'\b{re.escape(module_name)}\b'
                    if len(re.findall(pattern, content)) <= 1:
                        file_unused.append(imp.module)

            if file_unused:
                try:
                    rel_path = str(Path(file_path).relative_to(self.working_dir))
                except ValueError:
                    rel_path = file_path
                unused[rel_path] = file_unused

        return unused

    def get_import_graph_ascii(self) -> str:
        """Generate ASCII visualization of import graph."""
        lines = ["=" * 50]
        lines.append("  IMPORT GRAPH")
        lines.append("=" * 50)

        # Group by source file
        for file_path, file_imports in list(self.graph.files.items())[:20]:
            try:
                rel_path = str(Path(file_path).relative_to(self.working_dir))
            except ValueError:
                rel_path = file_path

            if not file_imports.imports:
                continue

            lines.append(f"\n📄 {rel_path}")

            if file_imports.stdlib:
                lines.append("   ├─ stdlib:")
                for mod in file_imports.stdlib[:5]:
                    lines.append(f"   │  └─ {mod}")

            if file_imports.third_party:
                lines.append("   ├─ third-party:")
                for mod in file_imports.third_party[:5]:
                    lines.append(f"   │  └─ {mod}")

            if file_imports.local:
                lines.append("   └─ local:")
                for mod in file_imports.local[:5]:
                    lines.append(f"      └─ {mod}")

        return "\n".join(lines)

    def get_report(self) -> str:
        """Generate a full dependency report."""
        lines = ["=" * 60]
        lines.append("  DEPENDENCY ANALYSIS REPORT")
        lines.append("=" * 60)

        # Summary
        total_files = len(self.graph.files)
        total_imports = sum(len(f.imports) for f in self.graph.files.values())
        total_stdlib = sum(len(f.stdlib) for f in self.graph.files.values())
        total_third = sum(len(f.third_party) for f in self.graph.files.values())
        total_local = sum(len(f.local) for f in self.graph.files.values())

        lines.append(f"\n📊 Summary:")
        lines.append(f"   Files analyzed: {total_files}")
        lines.append(f"   Total imports: {total_imports}")
        lines.append(f"   • Standard library: {total_stdlib}")
        lines.append(f"   • Third-party: {total_third}")
        lines.append(f"   • Local: {total_local}")

        # Third-party packages
        third_party_set: Set[str] = set()
        for f in self.graph.files.values():
            for mod in f.third_party:
                third_party_set.add(mod.split('.')[0])

        if third_party_set:
            lines.append(f"\n📦 Third-party packages ({len(third_party_set)}):")
            for pkg in sorted(third_party_set)[:15]:
                lines.append(f"   • {pkg}")

        # Circular dependencies
        if self.graph.circular:
            lines.append(f"\n⚠️ Circular Dependencies ({len(self.graph.circular)}):")
            for cycle in self.graph.circular[:5]:
                lines.append(f"   • {' → '.join(cycle[:4])}")
        else:
            lines.append(f"\n✅ No circular dependencies detected")

        # Unused imports
        total_unused = sum(len(v) for v in self.graph.unused.values())
        if self.graph.unused:
            lines.append(f"\n🗑️ Potentially Unused Imports ({total_unused}):")
            for file_path, imports in list(self.graph.unused.items())[:10]:
                lines.append(f"   {file_path}:")
                for imp in imports[:3]:
                    lines.append(f"      • {imp}")
        else:
            lines.append(f"\n✅ No unused imports detected")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


# Global analyzer
_dependency_analyzer: Optional[DependencyAnalyzer] = None


def get_dependency_analyzer(working_dir: Optional[Path] = None) -> DependencyAnalyzer:
    """Get or create dependency analyzer."""
    global _dependency_analyzer
    if _dependency_analyzer is None:
        _dependency_analyzer = DependencyAnalyzer(working_dir)
    return _dependency_analyzer


# Convenience functions
def analyze_dependencies(working_dir: Optional[Path] = None) -> DependencyGraph:
    """Analyze project dependencies."""
    analyzer = DependencyAnalyzer(working_dir or Path.cwd())
    return analyzer.analyze()


def get_dependency_report(working_dir: Optional[Path] = None) -> str:
    """Get dependency analysis report."""
    analyzer = DependencyAnalyzer(working_dir or Path.cwd())
    analyzer.analyze()
    return analyzer.get_report()


def get_import_graph(working_dir: Optional[Path] = None) -> str:
    """Get ASCII import graph."""
    analyzer = DependencyAnalyzer(working_dir or Path.cwd())
    analyzer.analyze()
    return analyzer.get_import_graph_ascii()
