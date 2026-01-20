"""Auto Documentation Generator - Feature 14.

Generate documentation automatically:
- Function/class docstrings
- API documentation
- README generation
- Changelog generation
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FunctionDoc:
    """Documentation for a function."""
    name: str
    signature: str
    docstring: str = ""
    params: List[Dict[str, str]] = field(default_factory=list)
    returns: str = ""
    raises: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class ClassDoc:
    """Documentation for a class."""
    name: str
    docstring: str = ""
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionDoc] = field(default_factory=list)
    attributes: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ModuleDoc:
    """Documentation for a module."""
    path: str
    name: str
    docstring: str = ""
    imports: List[str] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)
    functions: List[FunctionDoc] = field(default_factory=list)
    constants: List[Dict[str, str]] = field(default_factory=list)


class DocGenerator:
    """Generate documentation for code."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize doc generator."""
        self.working_dir = working_dir or Path.cwd()

    def generate_module_doc(self, file_path: str) -> ModuleDoc:
        """Generate documentation for a Python module."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_dir / file_path

        try:
            content = path.read_text(encoding='utf-8')
        except (IOError, UnicodeDecodeError):
            return ModuleDoc(path=str(path), name=path.stem)

        doc = ModuleDoc(
            path=str(path),
            name=path.stem,
        )

        # Extract module docstring
        doc.docstring = self._extract_module_docstring(content)

        # Extract imports
        doc.imports = self._extract_imports(content)

        # Extract classes
        doc.classes = self._extract_classes(content)

        # Extract top-level functions
        doc.functions = self._extract_functions(content, top_level=True)

        return doc

    def _extract_module_docstring(self, content: str) -> str:
        """Extract module-level docstring."""
        match = re.match(r'^[\s]*(?:\"\"\"|\'\'\')([\s\S]*?)(?:\"\"\"|\'\'\')', content)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        imports = []
        for match in re.finditer(r'^(?:from\s+\S+\s+)?import\s+.+$', content, re.MULTILINE):
            imports.append(match.group(0).strip())
        return imports

    def _extract_classes(self, content: str) -> List[ClassDoc]:
        """Extract class definitions."""
        classes = []

        pattern = r'^class\s+(\w+)(?:\(([^)]*)\))?:'
        for match in re.finditer(pattern, content, re.MULTILINE):
            class_name = match.group(1)
            bases = [b.strip() for b in (match.group(2) or '').split(',') if b.strip()]

            # Find class body
            start = match.end()
            class_body = self._extract_indented_block(content[start:])

            class_doc = ClassDoc(
                name=class_name,
                bases=bases,
                docstring=self._extract_first_docstring(class_body),
                methods=self._extract_methods(class_body),
            )
            classes.append(class_doc)

        return classes

    def _extract_methods(self, class_body: str) -> List[FunctionDoc]:
        """Extract methods from class body."""
        methods = []
        pattern = r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'

        for match in re.finditer(pattern, class_body):
            name = match.group(1)
            params = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""

            # Find method body
            start = match.end()
            method_body = self._extract_indented_block(class_body[start:])
            docstring = self._extract_first_docstring(method_body)

            func_doc = FunctionDoc(
                name=name,
                signature=f"{name}({params})",
                docstring=docstring,
                params=self._parse_params(params),
                returns=return_type,
            )
            methods.append(func_doc)

        return methods

    def _extract_functions(self, content: str, top_level: bool = False) -> List[FunctionDoc]:
        """Extract function definitions."""
        functions = []
        pattern = r'^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:' if top_level else r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        flags = re.MULTILINE if top_level else 0

        for match in re.finditer(pattern, content, flags):
            name = match.group(1)
            params = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""

            # Find function body
            start = match.end()
            func_body = self._extract_indented_block(content[start:])
            docstring = self._extract_first_docstring(func_body)

            func_doc = FunctionDoc(
                name=name,
                signature=f"{name}({params})",
                docstring=docstring,
                params=self._parse_params(params),
                returns=return_type,
            )
            functions.append(func_doc)

        return functions

    def _extract_indented_block(self, content: str) -> str:
        """Extract indented code block."""
        lines = content.splitlines()
        if not lines:
            return ""

        # Find base indentation
        result = []
        base_indent = None

        for line in lines:
            if not line.strip():
                result.append(line)
                continue

            indent = len(line) - len(line.lstrip())

            if base_indent is None:
                base_indent = indent
                result.append(line)
            elif indent >= base_indent:
                result.append(line)
            else:
                break

        return "\n".join(result)

    def _extract_first_docstring(self, content: str) -> str:
        """Extract first docstring from content."""
        match = re.search(r'(?:\"\"\"|\'\'\')([\s\S]*?)(?:\"\"\"|\'\'\')', content[:500])
        if match:
            return match.group(1).strip()
        return ""

    def _parse_params(self, params_str: str) -> List[Dict[str, str]]:
        """Parse function parameters."""
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if not param or param == 'self' or param == 'cls':
                continue

            # Parse name: type = default
            match = re.match(r'(\w+)(?::\s*([^=]+))?(?:=\s*(.+))?', param)
            if match:
                params.append({
                    'name': match.group(1),
                    'type': (match.group(2) or '').strip(),
                    'default': (match.group(3) or '').strip(),
                })

        return params

    def generate_docstring(
        self,
        code: str,
        style: str = "google",
    ) -> str:
        """
        Generate a docstring for code.

        Args:
            code: Function or class code
            style: Docstring style (google, numpy, sphinx)

        Returns:
            Generated docstring
        """
        # Analyze code
        is_class = code.strip().startswith("class ")
        is_async = "async def" in code

        if is_class:
            return self._generate_class_docstring(code, style)
        else:
            return self._generate_function_docstring(code, style)

    def _generate_function_docstring(self, code: str, style: str) -> str:
        """Generate docstring for a function."""
        # Extract function info
        match = re.search(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:', code)
        if not match:
            return '"""TODO: Add docstring."""'

        name = match.group(1)
        params_str = match.group(2)
        return_type = match.group(3).strip() if match.group(3) else ""

        params = self._parse_params(params_str)

        # Generate based on style
        if style == "google":
            return self._format_google_docstring(name, params, return_type)
        elif style == "numpy":
            return self._format_numpy_docstring(name, params, return_type)
        else:
            return self._format_sphinx_docstring(name, params, return_type)

    def _generate_class_docstring(self, code: str, style: str) -> str:
        """Generate docstring for a class."""
        match = re.search(r'class\s+(\w+)(?:\(([^)]*)\))?:', code)
        if not match:
            return '"""TODO: Add docstring."""'

        name = match.group(1)
        bases = [b.strip() for b in (match.group(2) or '').split(',') if b.strip()]

        # Find __init__ params
        init_match = re.search(r'def\s+__init__\s*\(([^)]*)\)', code)
        init_params = []
        if init_match:
            init_params = self._parse_params(init_match.group(1))

        lines = [f'"""{name} class.', '']

        if bases:
            lines.append(f"Inherits from: {', '.join(bases)}")
            lines.append('')

        if init_params and style == "google":
            lines.append("Attributes:")
            for p in init_params:
                ptype = f" ({p['type']})" if p['type'] else ""
                lines.append(f"    {p['name']}{ptype}: Description.")
            lines.append('')

        lines.append('"""')
        return "\n".join(lines)

    def _format_google_docstring(
        self,
        name: str,
        params: List[Dict],
        return_type: str,
    ) -> str:
        """Format Google-style docstring."""
        lines = [f'"""Brief description of {name}.', '']

        if params:
            lines.append("Args:")
            for p in params:
                ptype = f" ({p['type']})" if p['type'] else ""
                default = f" Defaults to {p['default']}." if p['default'] else ""
                lines.append(f"    {p['name']}{ptype}: Description.{default}")
            lines.append('')

        if return_type and return_type != "None":
            lines.append("Returns:")
            lines.append(f"    {return_type}: Description.")
            lines.append('')

        lines.append('"""')
        return "\n".join(lines)

    def _format_numpy_docstring(
        self,
        name: str,
        params: List[Dict],
        return_type: str,
    ) -> str:
        """Format NumPy-style docstring."""
        lines = [f'"""Brief description of {name}.', '']

        if params:
            lines.append("Parameters")
            lines.append("-" * 10)
            for p in params:
                ptype = f" : {p['type']}" if p['type'] else ""
                lines.append(f"{p['name']}{ptype}")
                lines.append("    Description.")
            lines.append('')

        if return_type and return_type != "None":
            lines.append("Returns")
            lines.append("-" * 7)
            lines.append(f"{return_type}")
            lines.append("    Description.")
            lines.append('')

        lines.append('"""')
        return "\n".join(lines)

    def _format_sphinx_docstring(
        self,
        name: str,
        params: List[Dict],
        return_type: str,
    ) -> str:
        """Format Sphinx-style docstring."""
        lines = [f'"""Brief description of {name}.', '']

        for p in params:
            ptype = f" {p['type']}" if p['type'] else ""
            lines.append(f":param{ptype} {p['name']}: Description.")

        if return_type and return_type != "None":
            lines.append(f":returns: Description.")
            lines.append(f":rtype: {return_type}")

        lines.append('"""')
        return "\n".join(lines)

    def generate_readme(self) -> str:
        """Generate README.md content for the project."""
        lines = []

        # Project name
        project_name = self.working_dir.name.replace("-", " ").replace("_", " ").title()
        lines.append(f"# {project_name}")
        lines.append("")

        # Try to detect project type
        project_type = self._detect_project_type()
        lines.append(f"{project_name} is a {project_type} project.")
        lines.append("")

        # Installation
        lines.append("## Installation")
        lines.append("")
        if (self.working_dir / "requirements.txt").exists():
            lines.append("```bash")
            lines.append("pip install -r requirements.txt")
            lines.append("```")
        elif (self.working_dir / "package.json").exists():
            lines.append("```bash")
            lines.append("npm install")
            lines.append("```")
        elif (self.working_dir / "Cargo.toml").exists():
            lines.append("```bash")
            lines.append("cargo build")
            lines.append("```")
        lines.append("")

        # Usage
        lines.append("## Usage")
        lines.append("")
        lines.append("```bash")
        lines.append("# Add usage examples here")
        lines.append("```")
        lines.append("")

        # Project structure
        lines.append("## Project Structure")
        lines.append("")
        lines.append("```")
        lines.extend(self._generate_tree())
        lines.append("```")
        lines.append("")

        # License
        lines.append("## License")
        lines.append("")
        if (self.working_dir / "LICENSE").exists():
            lines.append("See LICENSE file for details.")
        else:
            lines.append("TODO: Add license information.")

        return "\n".join(lines)

    def _detect_project_type(self) -> str:
        """Detect project type."""
        if (self.working_dir / "pyproject.toml").exists():
            return "Python"
        if (self.working_dir / "package.json").exists():
            return "JavaScript/TypeScript"
        if (self.working_dir / "Cargo.toml").exists():
            return "Rust"
        if (self.working_dir / "go.mod").exists():
            return "Go"
        return "software"

    def _generate_tree(self) -> List[str]:
        """Generate directory tree."""
        lines = []
        lines.append(self.working_dir.name + "/")

        def add_items(path: Path, prefix: str = ""):
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            dirs = [i for i in items if i.is_dir() and not i.name.startswith('.')]
            files = [i for i in items if i.is_file() and not i.name.startswith('.')]

            # Filter out common ignored dirs
            ignore = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build'}
            dirs = [d for d in dirs if d.name not in ignore]

            for i, item in enumerate(dirs[:5] + files[:10]):
                is_last = i == len(dirs[:5] + files[:10]) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")

                if item.is_dir() and len(prefix) < 12:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    add_items(item, new_prefix)

        add_items(self.working_dir)
        return lines[:30]  # Limit


# Global instance
_doc_generator: Optional[DocGenerator] = None


def get_doc_generator(working_dir: Optional[Path] = None) -> DocGenerator:
    """Get or create doc generator."""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = DocGenerator(working_dir)
    return _doc_generator


# Convenience functions
def generate_docstring(code: str, style: str = "google") -> str:
    """Generate docstring for code."""
    return get_doc_generator().generate_docstring(code, style)


def generate_readme(working_dir: Optional[Path] = None) -> str:
    """Generate README content."""
    return DocGenerator(working_dir or Path.cwd()).generate_readme()


def document_module(file_path: str) -> ModuleDoc:
    """Generate documentation for a module."""
    return get_doc_generator().generate_module_doc(file_path)
