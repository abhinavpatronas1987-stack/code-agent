"""Codebase Indexing System - Feature 3.

Build semantic index of entire codebase for intelligent search:
- File content indexing
- Symbol extraction (functions, classes, variables)
- Dependency mapping
- Semantic search (when embeddings available)
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

from src.config.settings import get_settings


class SymbolType(Enum):
    """Types of code symbols."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    MODULE = "module"


@dataclass
class CodeSymbol:
    """A code symbol (function, class, etc.)."""
    name: str
    type: str
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent: Optional[str] = None  # Parent class/module


@dataclass
class FileIndex:
    """Index for a single file."""
    path: str
    language: str
    size: int
    modified_time: float
    content_hash: str
    symbols: List[Dict] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    lines: int = 0
    todos: List[Dict] = field(default_factory=list)


@dataclass
class CodebaseIndex:
    """Index for entire codebase."""
    project_path: str
    project_name: str
    indexed_at: str
    file_count: int
    total_lines: int
    total_symbols: int
    languages: Dict[str, int] = field(default_factory=dict)
    files: List[Dict] = field(default_factory=list)


class CodeIndexer:
    """Index codebase for intelligent search."""

    # Language detection by extension
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.cs': 'csharp',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
    }

    # Patterns for symbol extraction by language
    SYMBOL_PATTERNS = {
        'python': {
            'function': r'^(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)',
            'class': r'^class\s+(\w+)(?:\([^)]*\))?:',
            'variable': r'^(\w+)\s*=\s*(?!.*def|class)',
            'import': r'^(?:from\s+(\S+)\s+)?import\s+(.+)',
        },
        'javascript': {
            'function': r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
            'class': r'class\s+(\w+)(?:\s+extends\s+\w+)?',
            'const': r'(?:const|let|var)\s+(\w+)\s*=',
            'arrow': r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            'import': r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)',
        },
        'typescript': {
            'function': r'(?:async\s+)?function\s+(\w+)\s*[<(]',
            'class': r'class\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+\w+)?',
            'interface': r'interface\s+(\w+)',
            'type': r'type\s+(\w+)\s*=',
            'const': r'(?:const|let|var)\s+(\w+)\s*[:<]=',
            'import': r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)',
        },
        'rust': {
            'function': r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]',
            'struct': r'(?:pub\s+)?struct\s+(\w+)',
            'enum': r'(?:pub\s+)?enum\s+(\w+)',
            'impl': r'impl(?:<[^>]+>)?\s+(\w+)',
            'trait': r'(?:pub\s+)?trait\s+(\w+)',
            'use': r'use\s+([^;]+)',
        },
        'go': {
            'function': r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(',
            'struct': r'type\s+(\w+)\s+struct',
            'interface': r'type\s+(\w+)\s+interface',
            'const': r'const\s+(\w+)',
            'var': r'var\s+(\w+)',
            'import': r'import\s+(?:\(|"([^"]+)")',
        },
    }

    # Ignore patterns
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
        'dist', 'build', '.tox', '.pytest_cache', '.mypy_cache',
        'target', 'vendor', '.idea', '.vscode', 'coverage',
    }

    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.so', '*.dll',
        '*.log', '*.lock', 'package-lock.json', 'yarn.lock',
    }

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize indexer."""
        settings = get_settings()
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.project_id = self._get_project_id()

        # Storage
        self.index_dir = settings.data_dir / "codebase_index" / self.project_id
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.index_dir / "index.json"
        self.symbols_file = self.index_dir / "symbols.json"
        self.graph_file = self.index_dir / "dependency_graph.json"

        # Index data
        self.index: Optional[CodebaseIndex] = None
        self.symbols: Dict[str, CodeSymbol] = {}
        self.dependency_graph: Dict[str, List[str]] = {}

        # Load existing index
        self._load_index()

    def _get_project_id(self) -> str:
        """Get unique ID for current project."""
        path_str = str(self.project_path.resolve())
        return hashlib.md5(path_str.encode()).hexdigest()[:12]

    def _load_index(self):
        """Load existing index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = CodebaseIndex(**data)
            except (json.JSONDecodeError, IOError):
                pass

        if self.symbols_file.exists():
            try:
                with open(self.symbols_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.symbols = {k: CodeSymbol(**v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                pass

        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.dependency_graph = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_index(self):
        """Save index to disk."""
        if self.index:
            try:
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.index), f, indent=2)
            except IOError:
                pass

        try:
            with open(self.symbols_file, 'w', encoding='utf-8') as f:
                json.dump({k: asdict(v) for k, v in self.symbols.items()}, f, indent=2)
        except IOError:
            pass

        try:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                json.dump(self.dependency_graph, f, indent=2)
        except IOError:
            pass

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        name = path.name

        if path.is_dir():
            return name in self.IGNORE_DIRS

        for pattern in self.IGNORE_FILES:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True

        return False

    def _get_language(self, path: Path) -> Optional[str]:
        """Get language for file."""
        return self.LANGUAGE_MAP.get(path.suffix.lower())

    def _hash_content(self, content: str) -> str:
        """Get hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _extract_symbols(self, content: str, language: str, file_path: str) -> Tuple[List[CodeSymbol], List[str]]:
        """Extract symbols and imports from file content."""
        symbols = []
        imports = []

        patterns = self.SYMBOL_PATTERNS.get(language, {})

        for line_num, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()

            for symbol_type, pattern in patterns.items():
                if symbol_type == 'import':
                    match = re.match(pattern, stripped)
                    if match:
                        groups = match.groups()
                        import_name = groups[-1] if groups[-1] else groups[0]
                        if import_name:
                            imports.append(import_name.strip())
                else:
                    match = re.match(pattern, stripped)
                    if match:
                        name = match.group(1)
                        signature = match.group(0) if len(match.groups()) > 1 else None

                        symbols.append(CodeSymbol(
                            name=name,
                            type=symbol_type,
                            file_path=file_path,
                            line_number=line_num,
                            signature=signature,
                        ))

        return symbols, imports

    def _extract_todos(self, content: str) -> List[Dict]:
        """Extract TODO/FIXME comments."""
        todos = []
        todo_pattern = re.compile(r'(?:#|//|/\*|\*)\s*(TODO|FIXME|XXX|HACK|BUG):\s*(.+)', re.IGNORECASE)

        for line_num, line in enumerate(content.splitlines(), 1):
            match = todo_pattern.search(line)
            if match:
                todos.append({
                    "type": match.group(1).upper(),
                    "text": match.group(2).strip(),
                    "line": line_num,
                })

        return todos

    def build_index(self, force: bool = False) -> CodebaseIndex:
        """
        Build or rebuild the codebase index.

        Args:
            force: Force full rebuild even if files unchanged

        Returns:
            CodebaseIndex with all data
        """
        files: List[FileIndex] = []
        all_symbols: List[CodeSymbol] = []
        languages: Dict[str, int] = {}
        total_lines = 0

        for root, dirs, filenames in os.walk(self.project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            for filename in filenames:
                file_path = Path(root) / filename

                if self._should_ignore(file_path):
                    continue

                language = self._get_language(file_path)
                if not language:
                    continue

                try:
                    stat = file_path.stat()
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.count('\n') + 1

                    rel_path = str(file_path.relative_to(self.project_path))
                    content_hash = self._hash_content(content)

                    # Extract symbols and imports
                    symbols, imports = self._extract_symbols(content, language, rel_path)

                    # Extract TODOs
                    todos = self._extract_todos(content)

                    # Create file index
                    file_index = FileIndex(
                        path=rel_path,
                        language=language,
                        size=stat.st_size,
                        modified_time=stat.st_mtime,
                        content_hash=content_hash,
                        symbols=[asdict(s) for s in symbols],
                        imports=imports,
                        exports=[s.name for s in symbols if s.type in ('function', 'class')],
                        lines=lines,
                        todos=todos,
                    )

                    files.append(file_index)
                    all_symbols.extend(symbols)
                    total_lines += lines

                    # Update language count
                    languages[language] = languages.get(language, 0) + 1

                    # Update dependency graph
                    self.dependency_graph[rel_path] = imports

                except (IOError, UnicodeDecodeError):
                    continue

        # Store symbols by unique key
        self.symbols = {
            f"{s.file_path}:{s.name}:{s.line_number}": s
            for s in all_symbols
        }

        # Create index
        self.index = CodebaseIndex(
            project_path=str(self.project_path),
            project_name=self.project_path.name,
            indexed_at=datetime.now().isoformat(),
            file_count=len(files),
            total_lines=total_lines,
            total_symbols=len(all_symbols),
            languages=languages,
            files=[asdict(f) for f in files],
        )

        # Save
        self._save_index()

        return self.index

    def search_symbols(
        self,
        query: str,
        symbol_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[CodeSymbol]:
        """
        Search for symbols by name.

        Args:
            query: Search query (partial match)
            symbol_type: Filter by type (function, class, etc.)
            limit: Maximum results

        Returns:
            Matching symbols
        """
        query_lower = query.lower()
        results = []

        for symbol in self.symbols.values():
            if symbol_type and symbol.type != symbol_type:
                continue

            if query_lower in symbol.name.lower():
                results.append(symbol)

                if len(results) >= limit:
                    break

        # Sort by relevance (exact match first, then by name length)
        results.sort(key=lambda s: (
            0 if s.name.lower() == query_lower else 1,
            len(s.name)
        ))

        return results[:limit]

    def search_files(self, query: str, limit: int = 20) -> List[Dict]:
        """Search files by path or content patterns."""
        if not self.index:
            return []

        query_lower = query.lower()
        results = []

        for file_data in self.index.files:
            if query_lower in file_data['path'].lower():
                results.append(file_data)

                if len(results) >= limit:
                    break

        return results

    def get_file_symbols(self, file_path: str) -> List[CodeSymbol]:
        """Get all symbols in a file."""
        return [s for s in self.symbols.values() if s.file_path == file_path]

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a file."""
        return self.dependency_graph.get(file_path, [])

    def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on this file."""
        return [
            f for f, deps in self.dependency_graph.items()
            if any(file_path in d for d in deps)
        ]

    def get_all_todos(self) -> List[Dict]:
        """Get all TODOs in codebase."""
        if not self.index:
            return []

        todos = []
        for file_data in self.index.files:
            for todo in file_data.get('todos', []):
                todos.append({
                    **todo,
                    'file': file_data['path'],
                })

        return todos

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not self.index:
            return {"indexed": False}

        return {
            "indexed": True,
            "indexed_at": self.index.indexed_at,
            "file_count": self.index.file_count,
            "total_lines": self.index.total_lines,
            "total_symbols": self.index.total_symbols,
            "languages": self.index.languages,
            "todo_count": sum(len(f.get('todos', [])) for f in self.index.files),
        }

    def format_stats(self) -> str:
        """Format stats as string."""
        stats = self.get_stats()

        if not stats.get("indexed"):
            return "Codebase not indexed. Run /index to build."

        lines = [
            "=" * 50,
            "  CODEBASE INDEX",
            "=" * 50,
            "",
            f"📁 Files: {stats['file_count']}",
            f"📝 Lines: {stats['total_lines']:,}",
            f"🔤 Symbols: {stats['total_symbols']:,}",
            f"📋 TODOs: {stats['todo_count']}",
            "",
            "📊 Languages:",
        ]

        for lang, count in sorted(stats['languages'].items(), key=lambda x: -x[1]):
            lines.append(f"   • {lang}: {count} files")

        lines.extend([
            "",
            f"🕐 Indexed: {stats['indexed_at'][:19]}",
            "=" * 50,
        ])

        return "\n".join(lines)


# Global instance
_code_indexer: Optional[CodeIndexer] = None


def get_code_indexer(project_path: Optional[Path] = None) -> CodeIndexer:
    """Get or create code indexer."""
    global _code_indexer
    if _code_indexer is None or project_path:
        _code_indexer = CodeIndexer(project_path)
    return _code_indexer


# Convenience functions
def index_codebase(force: bool = False) -> CodebaseIndex:
    """Build codebase index."""
    return get_code_indexer().build_index(force)


def search_symbols(query: str, limit: int = 20) -> List[CodeSymbol]:
    """Search for symbols."""
    return get_code_indexer().search_symbols(query, limit=limit)


def get_index_stats() -> str:
    """Get formatted index stats."""
    return get_code_indexer().format_stats()
