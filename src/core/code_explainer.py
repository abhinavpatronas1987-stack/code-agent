"""Code Explanation System - Feature 9.

Deep code explanation with:
- Function/class analysis
- Control flow diagrams (ASCII)
- Complexity metrics
- Dependency visualization
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class CodeBlock:
    """A block of code to explain."""
    content: str
    language: str
    file_path: Optional[str] = None
    start_line: int = 1
    end_line: Optional[int] = None


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int
    lines: int
    calls: List[str]
    is_async: bool = False
    is_generator: bool = False
    decorators: List[str] = None


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    bases: List[str]
    methods: List[str]
    attributes: List[str]
    docstring: Optional[str]
    lines: int


class CodeExplainer:
    """Explain code in detail."""

    def __init__(self):
        """Initialize explainer."""
        pass

    def explain_file(self, file_path: str) -> str:
        """
        Explain an entire file.

        Args:
            file_path: Path to file

        Returns:
            Formatted explanation
        """
        path = Path(file_path)
        if not path.exists():
            return f"File not found: {file_path}"

        try:
            content = path.read_text(encoding='utf-8')
        except IOError as e:
            return f"Error reading file: {e}"

        language = self._detect_language(path)

        return self.explain_code(content, language, file_path)

    def explain_code(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None,
    ) -> str:
        """
        Explain a code snippet.

        Args:
            code: Code to explain
            language: Programming language
            file_path: Optional file path

        Returns:
            Formatted explanation
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("  CODE ANALYSIS")
        lines.append("=" * 60)

        if file_path:
            lines.append(f"\n📁 File: {file_path}")

        lines.append(f"📝 Language: {language}")
        lines.append(f"📏 Lines: {code.count(chr(10)) + 1}")

        # Get metrics
        metrics = self._calculate_metrics(code, language)
        lines.append(f"\n📊 Metrics:")
        lines.append(f"   • Complexity: {metrics['complexity']}/10")
        lines.append(f"   • Functions: {metrics['functions']}")
        lines.append(f"   • Classes: {metrics['classes']}")
        lines.append(f"   • Imports: {metrics['imports']}")

        # Extract components
        if language == "python":
            components = self._analyze_python(code)
        elif language in ("javascript", "typescript"):
            components = self._analyze_javascript(code)
        else:
            components = self._analyze_generic(code)

        # Document components
        if components.get('imports'):
            lines.append(f"\n📦 Imports ({len(components['imports'])}):")
            for imp in components['imports'][:10]:
                lines.append(f"   • {imp}")

        if components.get('classes'):
            lines.append(f"\n🏛️ Classes ({len(components['classes'])}):")
            for cls in components['classes']:
                lines.append(f"\n   class {cls['name']}:")
                if cls.get('docstring'):
                    lines.append(f"      \"{cls['docstring'][:60]}...\"")
                lines.append(f"      • Methods: {', '.join(cls.get('methods', []))}")
                if cls.get('bases'):
                    lines.append(f"      • Inherits: {', '.join(cls['bases'])}")

        if components.get('functions'):
            lines.append(f"\n🔧 Functions ({len(components['functions'])}):")
            for func in components['functions']:
                async_marker = "async " if func.get('is_async') else ""
                lines.append(f"\n   {async_marker}def {func['name']}({', '.join(func.get('params', []))}):")
                if func.get('docstring'):
                    lines.append(f"      \"{func['docstring'][:60]}...\"")
                lines.append(f"      • Lines: {func.get('lines', '?')}")
                lines.append(f"      • Complexity: {func.get('complexity', '?')}")
                if func.get('calls'):
                    lines.append(f"      • Calls: {', '.join(func['calls'][:5])}")

        # Control flow diagram for main logic
        if language == "python":
            flow_diagram = self._generate_flow_diagram(code)
            if flow_diagram:
                lines.append("\n🔄 Control Flow:")
                lines.append(flow_diagram)

        # Dependencies diagram
        if components.get('imports'):
            dep_diagram = self._generate_dependency_diagram(components['imports'])
            lines.append("\n📡 Dependencies:")
            lines.append(dep_diagram)

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def _detect_language(self, path: Path) -> str:
        """Detect language from file extension."""
        ext_map = {
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
        }
        return ext_map.get(path.suffix.lower(), 'unknown')

    def _calculate_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code metrics."""
        lines = code.splitlines()

        # Count various elements
        functions = 0
        classes = 0
        imports = 0
        branches = 0
        loops = 0

        for line in lines:
            stripped = line.strip()

            if language == "python":
                if stripped.startswith('def '):
                    functions += 1
                elif stripped.startswith('class '):
                    classes += 1
                elif stripped.startswith(('import ', 'from ')):
                    imports += 1
                elif stripped.startswith(('if ', 'elif ', 'else:')):
                    branches += 1
                elif stripped.startswith(('for ', 'while ')):
                    loops += 1

            elif language in ("javascript", "typescript"):
                if 'function ' in stripped or '=>' in stripped:
                    functions += 1
                elif stripped.startswith('class '):
                    classes += 1
                elif stripped.startswith('import '):
                    imports += 1
                elif 'if ' in stripped or 'else' in stripped:
                    branches += 1
                elif 'for ' in stripped or 'while ' in stripped:
                    loops += 1

        # Calculate complexity (simplified cyclomatic)
        complexity = min(10, 1 + branches + loops + (functions // 3))

        return {
            'complexity': complexity,
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'branches': branches,
            'loops': loops,
            'lines': len(lines),
        }

    def _analyze_python(self, code: str) -> Dict[str, List]:
        """Analyze Python code."""
        result = {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
        }

        lines = code.splitlines()
        current_class = None
        current_func = None
        func_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if stripped.startswith('import '):
                result['imports'].append(stripped[7:].split('#')[0].strip())
            elif stripped.startswith('from '):
                match = re.match(r'from\s+(\S+)\s+import', stripped)
                if match:
                    result['imports'].append(match.group(1))

            # Classes
            if stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)(?:\(([^)]*)\))?:', stripped)
                if match:
                    current_class = {
                        'name': match.group(1),
                        'bases': [b.strip() for b in (match.group(2) or '').split(',') if b.strip()],
                        'methods': [],
                        'docstring': None,
                        'line': i + 1,
                    }
                    result['classes'].append(current_class)

            # Functions
            if stripped.startswith('def ') or stripped.startswith('async def '):
                is_async = stripped.startswith('async ')
                pattern = r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)'
                match = re.match(pattern, stripped)
                if match:
                    func_name = match.group(1)
                    params = [p.strip().split(':')[0].split('=')[0].strip()
                              for p in match.group(2).split(',') if p.strip()]

                    func_info = {
                        'name': func_name,
                        'params': params,
                        'is_async': is_async,
                        'docstring': None,
                        'line': i + 1,
                        'lines': 0,
                        'complexity': 1,
                        'calls': [],
                    }

                    if current_class:
                        current_class['methods'].append(func_name)

                    result['functions'].append(func_info)
                    current_func = func_info
                    func_start = i

            # Track function calls within functions
            if current_func and '(' in stripped:
                calls = re.findall(r'(\w+)\s*\(', stripped)
                for call in calls:
                    if call not in ('if', 'for', 'while', 'def', 'class', 'return', 'print'):
                        if call not in current_func['calls']:
                            current_func['calls'].append(call)

            # Track complexity
            if current_func:
                if any(kw in stripped for kw in ['if ', 'elif ', 'for ', 'while ', 'except ', 'and ', 'or ']):
                    current_func['complexity'] += 1

        return result

    def _analyze_javascript(self, code: str) -> Dict[str, List]:
        """Analyze JavaScript/TypeScript code."""
        result = {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
        }

        lines = code.splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Imports
            if stripped.startswith('import '):
                match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', stripped)
                if match:
                    result['imports'].append(match.group(1))

            # Classes
            if stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)', stripped)
                if match:
                    result['classes'].append({
                        'name': match.group(1),
                        'bases': [],
                        'methods': [],
                        'line': i + 1,
                    })

            # Functions
            if 'function ' in stripped or '=>' in stripped:
                match = re.search(r'(?:function\s+)?(\w+)\s*[=:]\s*(?:async\s+)?\(?', stripped)
                if match:
                    result['functions'].append({
                        'name': match.group(1),
                        'params': [],
                        'line': i + 1,
                        'complexity': 1,
                    })

        return result

    def _analyze_generic(self, code: str) -> Dict[str, List]:
        """Generic code analysis."""
        return {
            'imports': [],
            'classes': [],
            'functions': [],
            'variables': [],
        }

    def _generate_flow_diagram(self, code: str) -> str:
        """Generate ASCII control flow diagram."""
        lines = []
        indent = 0

        flow_elements = []

        for line in code.splitlines():
            stripped = line.strip()

            if stripped.startswith('def '):
                match = re.match(r'def\s+(\w+)', stripped)
                if match:
                    flow_elements.append(('function', match.group(1), indent))

            elif stripped.startswith('if '):
                flow_elements.append(('condition', 'if', indent))
                indent += 1

            elif stripped.startswith('elif '):
                indent -= 1
                flow_elements.append(('condition', 'elif', indent))
                indent += 1

            elif stripped.startswith('else:'):
                indent -= 1
                flow_elements.append(('condition', 'else', indent))
                indent += 1

            elif stripped.startswith('for '):
                flow_elements.append(('loop', 'for', indent))
                indent += 1

            elif stripped.startswith('while '):
                flow_elements.append(('loop', 'while', indent))
                indent += 1

            elif stripped.startswith('return '):
                flow_elements.append(('return', 'return', indent))

            elif stripped.startswith('try:'):
                flow_elements.append(('try', 'try', indent))
                indent += 1

            elif stripped.startswith('except'):
                indent -= 1
                flow_elements.append(('except', 'except', indent))
                indent += 1

        # Build ASCII diagram
        if not flow_elements:
            return "   (No significant control flow detected)"

        diagram_lines = []
        for elem_type, label, level in flow_elements[:15]:  # Limit to 15 elements
            prefix = "   " + "│  " * level

            if elem_type == 'function':
                diagram_lines.append(f"{prefix}┌─ {label}()")
            elif elem_type == 'condition':
                diagram_lines.append(f"{prefix}◇─ {label}")
            elif elem_type == 'loop':
                diagram_lines.append(f"{prefix}↻─ {label}")
            elif elem_type == 'return':
                diagram_lines.append(f"{prefix}←─ return")
            elif elem_type == 'try':
                diagram_lines.append(f"{prefix}⚡─ try")
            elif elem_type == 'except':
                diagram_lines.append(f"{prefix}✗─ except")

        return "\n".join(diagram_lines)

    def _generate_dependency_diagram(self, imports: List[str]) -> str:
        """Generate ASCII dependency diagram."""
        if not imports:
            return "   (No dependencies)"

        lines = ["   ┌─ Your Code"]

        # Group by type
        stdlib = []
        third_party = []
        local = []

        python_stdlib = {'os', 'sys', 'json', 're', 'typing', 'pathlib', 'datetime',
                        'collections', 'functools', 'itertools', 'hashlib', 'time',
                        'threading', 'subprocess', 'shutil', 'enum', 'dataclasses'}

        for imp in imports:
            base = imp.split('.')[0]
            if base in python_stdlib:
                stdlib.append(imp)
            elif imp.startswith('.') or imp.startswith('src'):
                local.append(imp)
            else:
                third_party.append(imp)

        if stdlib:
            lines.append("   │")
            lines.append("   ├─ Standard Library")
            for imp in stdlib[:5]:
                lines.append(f"   │  └─ {imp}")

        if third_party:
            lines.append("   │")
            lines.append("   ├─ Third Party")
            for imp in third_party[:5]:
                lines.append(f"   │  └─ {imp}")

        if local:
            lines.append("   │")
            lines.append("   └─ Local Modules")
            for imp in local[:5]:
                lines.append(f"      └─ {imp}")

        return "\n".join(lines)

    def explain_function(self, code: str, function_name: str) -> str:
        """Explain a specific function."""
        # Find the function in code
        pattern = rf'(?:async\s+)?def\s+{function_name}\s*\([^)]*\).*?(?=\n(?:async\s+)?def\s|\nclass\s|\Z)'
        match = re.search(pattern, code, re.DOTALL)

        if not match:
            return f"Function '{function_name}' not found"

        func_code = match.group(0)
        return self.explain_code(func_code, "python")


# Global instance
_code_explainer: Optional[CodeExplainer] = None


def get_code_explainer() -> CodeExplainer:
    """Get code explainer instance."""
    global _code_explainer
    if _code_explainer is None:
        _code_explainer = CodeExplainer()
    return _code_explainer


# Convenience functions
def explain_file(file_path: str) -> str:
    """Explain a file."""
    return get_code_explainer().explain_file(file_path)


def explain_code(code: str, language: str = "python") -> str:
    """Explain code snippet."""
    return get_code_explainer().explain_code(code, language)
