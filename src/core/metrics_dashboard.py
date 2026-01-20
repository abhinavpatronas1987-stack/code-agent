"""Code Metrics Dashboard - Feature 11.

Comprehensive code metrics:
- Lines of code
- Cyclomatic complexity
- Code coverage info
- Technical debt indicators
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from src.config.settings import get_settings


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: str
    language: str
    lines_total: int = 0
    lines_code: int = 0
    lines_comments: int = 0
    lines_blank: int = 0
    functions: int = 0
    classes: int = 0
    complexity: int = 0
    todos: int = 0
    issues: List[str] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Aggregated metrics for the project."""
    name: str
    analyzed_at: str
    file_count: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0
    total_todos: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    files: List[FileMetrics] = field(default_factory=list)
    issues: List[Dict] = field(default_factory=list)


class MetricsDashboard:
    """Generate code metrics dashboard."""

    # Language detection by extension
    LANGUAGES = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.rs': 'Rust',
        '.go': 'Go',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell',
        '.ps1': 'PowerShell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.md': 'Markdown',
    }

    # Comment patterns by language
    COMMENT_PATTERNS = {
        'Python': (r'#.*$', r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"),
        'JavaScript': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'TypeScript': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'Rust': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'Go': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'Java': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'C#': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'C++': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'C': (r'//.*$', r'/\*[\s\S]*?\*/'),
        'Ruby': (r'#.*$', r'=begin[\s\S]*?=end'),
        'Shell': (r'#.*$',),
        'SQL': (r'--.*$', r'/\*[\s\S]*?\*/'),
        'HTML': (r'<!--[\s\S]*?-->',),
        'CSS': (r'/\*[\s\S]*?\*/',),
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize dashboard."""
        self.working_dir = working_dir or Path.cwd()
        self.metrics: Optional[ProjectMetrics] = None

    def analyze(self) -> ProjectMetrics:
        """
        Analyze the entire project.

        Returns:
            ProjectMetrics with all analysis
        """
        self.metrics = ProjectMetrics(
            name=self.working_dir.name,
            analyzed_at=datetime.now().isoformat(),
        )

        # Find all code files
        for ext in self.LANGUAGES:
            for file_path in self.working_dir.rglob(f'*{ext}'):
                # Skip ignored directories
                parts = file_path.parts
                if any(p.startswith('.') or p in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build')
                       for p in parts):
                    continue

                file_metrics = self._analyze_file(file_path)
                if file_metrics:
                    self.metrics.files.append(file_metrics)
                    self._aggregate_metrics(file_metrics)

        # Calculate averages
        if self.metrics.files:
            complexities = [f.complexity for f in self.metrics.files if f.complexity > 0]
            if complexities:
                self.metrics.avg_complexity = sum(complexities) / len(complexities)
                self.metrics.max_complexity = max(complexities)

        self.metrics.file_count = len(self.metrics.files)

        # Detect issues
        self._detect_issues()

        return self.metrics

    def _analyze_file(self, file_path: Path) -> Optional[FileMetrics]:
        """Analyze a single file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return None

        language = self.LANGUAGES.get(file_path.suffix.lower(), 'Unknown')

        try:
            rel_path = str(file_path.relative_to(self.working_dir))
        except ValueError:
            rel_path = str(file_path)

        metrics = FileMetrics(
            path=rel_path,
            language=language,
        )

        lines = content.splitlines()
        metrics.lines_total = len(lines)

        # Count line types
        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()

            if not stripped:
                metrics.lines_blank += 1
            elif self._is_comment_line(stripped, language, in_multiline_comment):
                metrics.lines_comments += 1
            else:
                metrics.lines_code += 1

        # Count structures and complexity
        if language == 'Python':
            metrics.functions = len(re.findall(r'^[\s]*(?:async\s+)?def\s+\w+', content, re.MULTILINE))
            metrics.classes = len(re.findall(r'^[\s]*class\s+\w+', content, re.MULTILINE))
            metrics.complexity = self._calculate_python_complexity(content)
        elif language in ('JavaScript', 'TypeScript'):
            metrics.functions = len(re.findall(r'(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>)', content))
            metrics.classes = len(re.findall(r'\bclass\s+\w+', content))
            metrics.complexity = self._calculate_js_complexity(content)
        elif language in ('Go', 'Rust', 'Java', 'C#', 'C++', 'C'):
            metrics.functions = len(re.findall(r'\bfunc\s+\w+|\b\w+\s+\w+\s*\([^)]*\)\s*\{', content))
            metrics.classes = len(re.findall(r'\b(?:class|struct|type)\s+\w+', content))
            metrics.complexity = self._calculate_c_style_complexity(content)

        # Count TODOs
        metrics.todos = len(re.findall(r'\b(?:TODO|FIXME|HACK|XXX)\b', content, re.IGNORECASE))

        return metrics

    def _is_comment_line(self, line: str, language: str, in_multiline: bool) -> bool:
        """Check if a line is a comment."""
        patterns = self.COMMENT_PATTERNS.get(language, ())

        for pattern in patterns:
            if re.match(pattern, line):
                return True

        # Simple heuristics
        if language == 'Python' and (line.startswith('#') or line.startswith('"""') or line.startswith("'''")):
            return True
        if language in ('JavaScript', 'TypeScript', 'Go', 'Rust', 'Java', 'C#', 'C++', 'C'):
            if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
                return True

        return False

    def _calculate_python_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity for Python."""
        complexity = 1  # Base complexity

        # Decision points
        complexity += len(re.findall(r'\bif\b', content))
        complexity += len(re.findall(r'\belif\b', content))
        complexity += len(re.findall(r'\bfor\b', content))
        complexity += len(re.findall(r'\bwhile\b', content))
        complexity += len(re.findall(r'\band\b', content))
        complexity += len(re.findall(r'\bor\b', content))
        complexity += len(re.findall(r'\bexcept\b', content))
        complexity += len(re.findall(r'\bwith\b', content))

        return complexity

    def _calculate_js_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity for JavaScript/TypeScript."""
        complexity = 1

        complexity += len(re.findall(r'\bif\b', content))
        complexity += len(re.findall(r'\belse\s+if\b', content))
        complexity += len(re.findall(r'\bfor\b', content))
        complexity += len(re.findall(r'\bwhile\b', content))
        complexity += len(re.findall(r'\bswitch\b', content))
        complexity += len(re.findall(r'\bcase\b', content))
        complexity += len(re.findall(r'&&', content))
        complexity += len(re.findall(r'\|\|', content))
        complexity += len(re.findall(r'\bcatch\b', content))
        complexity += len(re.findall(r'\?(?![?.])', content))  # Ternary

        return complexity

    def _calculate_c_style_complexity(self, content: str) -> int:
        """Calculate complexity for C-style languages."""
        complexity = 1

        complexity += len(re.findall(r'\bif\b', content))
        complexity += len(re.findall(r'\belse\s+if\b', content))
        complexity += len(re.findall(r'\bfor\b', content))
        complexity += len(re.findall(r'\bwhile\b', content))
        complexity += len(re.findall(r'\bswitch\b', content))
        complexity += len(re.findall(r'\bcase\b', content))
        complexity += len(re.findall(r'&&', content))
        complexity += len(re.findall(r'\|\|', content))
        complexity += len(re.findall(r'\bcatch\b', content))

        return complexity

    def _aggregate_metrics(self, file_metrics: FileMetrics):
        """Aggregate file metrics into project metrics."""
        self.metrics.total_lines += file_metrics.lines_total
        self.metrics.code_lines += file_metrics.lines_code
        self.metrics.comment_lines += file_metrics.lines_comments
        self.metrics.blank_lines += file_metrics.lines_blank
        self.metrics.total_functions += file_metrics.functions
        self.metrics.total_classes += file_metrics.classes
        self.metrics.total_todos += file_metrics.todos

        # Track languages
        lang = file_metrics.language
        self.metrics.languages[lang] = self.metrics.languages.get(lang, 0) + 1

    def _detect_issues(self):
        """Detect code quality issues."""
        issues = []

        for file_metrics in self.metrics.files:
            # Large files
            if file_metrics.lines_code > 500:
                issues.append({
                    'type': 'large_file',
                    'severity': 'warning',
                    'file': file_metrics.path,
                    'message': f'File has {file_metrics.lines_code} lines of code',
                })

            # High complexity
            if file_metrics.complexity > 50:
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'warning',
                    'file': file_metrics.path,
                    'message': f'Cyclomatic complexity is {file_metrics.complexity}',
                })

            # Low comment ratio
            if file_metrics.lines_code > 100:
                comment_ratio = file_metrics.lines_comments / file_metrics.lines_code if file_metrics.lines_code > 0 else 0
                if comment_ratio < 0.1:
                    issues.append({
                        'type': 'low_comments',
                        'severity': 'info',
                        'file': file_metrics.path,
                        'message': f'Low comment ratio ({comment_ratio:.1%})',
                    })

            # Many TODOs
            if file_metrics.todos > 5:
                issues.append({
                    'type': 'many_todos',
                    'severity': 'info',
                    'file': file_metrics.path,
                    'message': f'{file_metrics.todos} TODOs/FIXMEs found',
                })

        self.metrics.issues = issues

    def get_dashboard(self) -> str:
        """Generate ASCII dashboard."""
        if not self.metrics:
            self.analyze()

        lines = []

        # Header
        lines.append("╔" + "═" * 58 + "╗")
        lines.append("║" + "  CODE METRICS DASHBOARD".center(58) + "║")
        lines.append("╚" + "═" * 58 + "╝")

        # Project info
        lines.append(f"\n📁 Project: {self.metrics.name}")
        lines.append(f"📅 Analyzed: {self.metrics.analyzed_at[:19]}")

        # Summary box
        lines.append("\n┌─────────────────────────────────────────────────────────┐")
        lines.append("│  SUMMARY                                                │")
        lines.append("├─────────────────────────────────────────────────────────┤")
        lines.append(f"│  Files:          {self.metrics.file_count:>6}                              │")
        lines.append(f"│  Total Lines:    {self.metrics.total_lines:>6}                              │")
        lines.append(f"│  Code Lines:     {self.metrics.code_lines:>6}  ({self._percent(self.metrics.code_lines, self.metrics.total_lines):>5.1f}%)            │")
        lines.append(f"│  Comment Lines:  {self.metrics.comment_lines:>6}  ({self._percent(self.metrics.comment_lines, self.metrics.total_lines):>5.1f}%)            │")
        lines.append(f"│  Blank Lines:    {self.metrics.blank_lines:>6}  ({self._percent(self.metrics.blank_lines, self.metrics.total_lines):>5.1f}%)            │")
        lines.append("└─────────────────────────────────────────────────────────┘")

        # Structure
        lines.append("\n┌─────────────────────────────────────────────────────────┐")
        lines.append("│  STRUCTURE                                              │")
        lines.append("├─────────────────────────────────────────────────────────┤")
        lines.append(f"│  Functions:      {self.metrics.total_functions:>6}                              │")
        lines.append(f"│  Classes:        {self.metrics.total_classes:>6}                              │")
        lines.append(f"│  Avg Complexity: {self.metrics.avg_complexity:>6.1f}                              │")
        lines.append(f"│  Max Complexity: {self.metrics.max_complexity:>6}                              │")
        lines.append(f"│  TODOs/FIXMEs:   {self.metrics.total_todos:>6}                              │")
        lines.append("└─────────────────────────────────────────────────────────┘")

        # Languages
        if self.metrics.languages:
            lines.append("\n📊 Languages:")
            sorted_langs = sorted(self.metrics.languages.items(), key=lambda x: x[1], reverse=True)
            max_count = max(self.metrics.languages.values())

            for lang, count in sorted_langs[:8]:
                bar_len = int((count / max_count) * 30)
                bar = "█" * bar_len
                pct = self._percent(count, self.metrics.file_count)
                lines.append(f"   {lang:12} {bar:30} {count:>4} ({pct:.1f}%)")

        # Top complex files
        complex_files = sorted(self.metrics.files, key=lambda x: x.complexity, reverse=True)[:5]
        if complex_files and complex_files[0].complexity > 10:
            lines.append("\n⚡ Most Complex Files:")
            for f in complex_files:
                lines.append(f"   {f.complexity:>4} │ {f.path[:45]}")

        # Issues
        if self.metrics.issues:
            warnings = [i for i in self.metrics.issues if i['severity'] == 'warning']
            infos = [i for i in self.metrics.issues if i['severity'] == 'info']

            lines.append(f"\n⚠️  Quality Issues ({len(self.metrics.issues)} total):")
            for issue in warnings[:5]:
                lines.append(f"   [{issue['severity'].upper()}] {issue['file']}")
                lines.append(f"          {issue['message']}")
        else:
            lines.append("\n✅ No quality issues detected!")

        lines.append("\n" + "═" * 60)

        return "\n".join(lines)

    def _percent(self, part: int, total: int) -> float:
        """Calculate percentage."""
        return (part / total * 100) if total > 0 else 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics as dictionary."""
        if not self.metrics:
            self.analyze()

        return {
            'name': self.metrics.name,
            'analyzed_at': self.metrics.analyzed_at,
            'files': self.metrics.file_count,
            'total_lines': self.metrics.total_lines,
            'code_lines': self.metrics.code_lines,
            'comment_lines': self.metrics.comment_lines,
            'functions': self.metrics.total_functions,
            'classes': self.metrics.total_classes,
            'avg_complexity': self.metrics.avg_complexity,
            'max_complexity': self.metrics.max_complexity,
            'todos': self.metrics.total_todos,
            'languages': self.metrics.languages,
            'issues': len(self.metrics.issues),
        }


# Global dashboard
_metrics_dashboard: Optional[MetricsDashboard] = None


def get_metrics_dashboard(working_dir: Optional[Path] = None) -> MetricsDashboard:
    """Get or create metrics dashboard."""
    global _metrics_dashboard
    if _metrics_dashboard is None:
        _metrics_dashboard = MetricsDashboard(working_dir)
    return _metrics_dashboard


# Convenience functions
def analyze_metrics(working_dir: Optional[Path] = None) -> ProjectMetrics:
    """Analyze project metrics."""
    dashboard = MetricsDashboard(working_dir or Path.cwd())
    return dashboard.analyze()


def get_metrics_report(working_dir: Optional[Path] = None) -> str:
    """Get metrics dashboard as string."""
    dashboard = MetricsDashboard(working_dir or Path.cwd())
    dashboard.analyze()
    return dashboard.get_dashboard()


def get_metrics_summary(working_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Get metrics summary."""
    dashboard = MetricsDashboard(working_dir or Path.cwd())
    dashboard.analyze()
    return dashboard.get_summary()
