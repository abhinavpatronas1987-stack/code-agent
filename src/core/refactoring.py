"""Refactoring Tools - Feature 24.

Code refactoring utilities:
- Rename symbols across project
- Extract function/method
- Inline function
- Move to file
- Extract variable
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class RefactorType(Enum):
    """Types of refactoring."""
    RENAME = "rename"
    EXTRACT_FUNCTION = "extract_function"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE = "inline"
    MOVE = "move"


@dataclass
class RefactorLocation:
    """A location in code."""
    file_path: str
    line_number: int
    column_start: int
    column_end: int
    content: str


@dataclass
class RefactorChange:
    """A refactoring change."""
    file_path: str
    original_content: str
    new_content: str
    description: str


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""
    success: bool
    refactor_type: RefactorType
    changes: List[RefactorChange] = field(default_factory=list)
    locations_found: int = 0
    files_affected: int = 0
    message: str = ""
    errors: List[str] = field(default_factory=list)


class RefactoringTools:
    """Code refactoring utilities."""

    # Language-specific patterns for symbol detection
    SYMBOL_PATTERNS = {
        "python": {
            "function": r"def\s+{name}\s*\(",
            "class": r"class\s+{name}\s*[:\(]",
            "variable": r"(?<![.\w]){name}(?![.\w])",
            "method": r"def\s+{name}\s*\(self",
            "import": r"(?:from\s+\S+\s+)?import\s+.*{name}",
        },
        "javascript": {
            "function": r"(?:function\s+{name}|{name}\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            "class": r"class\s+{name}\s*(?:extends|{{)",
            "variable": r"(?:const|let|var)\s+{name}\s*=",
            "method": r"{name}\s*\([^)]*\)\s*{{",
        },
        "typescript": {
            "function": r"(?:function\s+{name}|{name}\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            "class": r"class\s+{name}\s*(?:extends|implements|{{)",
            "interface": r"interface\s+{name}\s*(?:extends|{{)",
            "type": r"type\s+{name}\s*=",
            "variable": r"(?:const|let|var)\s+{name}\s*[=:]",
        },
        "go": {
            "function": r"func\s+{name}\s*\(",
            "method": r"func\s+\([^)]+\)\s+{name}\s*\(",
            "type": r"type\s+{name}\s+",
            "variable": r"(?:var\s+{name}|{name}\s*:=)",
        },
    }

    # File extensions by language
    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "go": [".go"],
        "rust": [".rs"],
        "java": [".java"],
        "csharp": [".cs"],
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize refactoring tools."""
        self.working_dir = working_dir or Path.cwd()

    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return lang
        return None

    def find_symbol_occurrences(
        self,
        symbol_name: str,
        language: Optional[str] = None,
        scope: Optional[Path] = None,
    ) -> List[RefactorLocation]:
        """
        Find all occurrences of a symbol.

        Args:
            symbol_name: Name of the symbol to find
            language: Filter by language
            scope: Directory scope

        Returns:
            List of locations
        """
        locations = []
        search_path = scope or self.working_dir

        # Get files to search
        files = self._get_files(search_path, language)

        for file_path in files:
            file_locations = self._find_in_file(file_path, symbol_name)
            locations.extend(file_locations)

        return locations

    def _get_files(
        self,
        directory: Path,
        language: Optional[str] = None,
    ) -> List[Path]:
        """Get files to search."""
        files = []
        skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}

        if language:
            extensions = set(self.LANGUAGE_EXTENSIONS.get(language, []))
        else:
            extensions = set()
            for exts in self.LANGUAGE_EXTENSIONS.values():
                extensions.update(exts)

        for item in directory.rglob("*"):
            if any(skip in item.parts for skip in skip_dirs):
                continue
            if item.is_file() and item.suffix.lower() in extensions:
                files.append(item)

        return files

    def _find_in_file(
        self,
        file_path: Path,
        symbol_name: str,
    ) -> List[RefactorLocation]:
        """Find symbol occurrences in a file."""
        locations = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            # Simple word boundary search
            pattern = r"(?<![.\w])" + re.escape(symbol_name) + r"(?![.\w])"

            for line_num, line in enumerate(lines, 1):
                for match in re.finditer(pattern, line):
                    locations.append(RefactorLocation(
                        file_path=str(file_path.relative_to(self.working_dir)),
                        line_number=line_num,
                        column_start=match.start(),
                        column_end=match.end(),
                        content=line.strip()[:100],
                    ))

        except Exception:
            pass

        return locations

    def rename_symbol(
        self,
        old_name: str,
        new_name: str,
        language: Optional[str] = None,
        scope: Optional[Path] = None,
        preview: bool = True,
    ) -> RefactorResult:
        """
        Rename a symbol across the project.

        Args:
            old_name: Current symbol name
            new_name: New symbol name
            language: Filter by language
            scope: Directory scope
            preview: If True, don't apply changes

        Returns:
            RefactorResult with changes
        """
        result = RefactorResult(
            success=False,
            refactor_type=RefactorType.RENAME,
        )

        # Validate names
        if not old_name or not new_name:
            result.errors.append("Both old and new names are required")
            return result

        if old_name == new_name:
            result.errors.append("Old and new names are the same")
            return result

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_name):
            result.errors.append(f"Invalid identifier: {new_name}")
            return result

        # Find occurrences
        locations = self.find_symbol_occurrences(old_name, language, scope)
        result.locations_found = len(locations)

        if not locations:
            result.message = f"No occurrences of '{old_name}' found"
            return result

        # Group by file
        files_changes: Dict[str, List[RefactorLocation]] = {}
        for loc in locations:
            if loc.file_path not in files_changes:
                files_changes[loc.file_path] = []
            files_changes[loc.file_path].append(loc)

        result.files_affected = len(files_changes)

        # Create changes
        search_path = scope or self.working_dir
        for file_path, file_locs in files_changes.items():
            full_path = search_path / file_path

            try:
                original = full_path.read_text(encoding="utf-8")
                # Replace all occurrences
                pattern = r"(?<![.\w])" + re.escape(old_name) + r"(?![.\w])"
                new_content = re.sub(pattern, new_name, original)

                if original != new_content:
                    result.changes.append(RefactorChange(
                        file_path=file_path,
                        original_content=original,
                        new_content=new_content,
                        description=f"Rename '{old_name}' to '{new_name}'",
                    ))

                    # Apply if not preview
                    if not preview:
                        full_path.write_text(new_content, encoding="utf-8")

            except Exception as e:
                result.errors.append(f"Error processing {file_path}: {e}")

        result.success = True
        result.message = (
            f"Found {result.locations_found} occurrences in {result.files_affected} files"
            + (" (preview mode)" if preview else " (applied)")
        )

        return result

    def extract_function(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
        function_name: str,
        params: Optional[List[str]] = None,
    ) -> RefactorResult:
        """
        Extract code into a new function.

        Args:
            file_path: File containing code
            start_line: Starting line number
            end_line: Ending line number
            function_name: Name for new function
            params: Parameters for new function

        Returns:
            RefactorResult with changes
        """
        result = RefactorResult(
            success=False,
            refactor_type=RefactorType.EXTRACT_FUNCTION,
        )

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if start_line < 1 or end_line > len(lines):
                result.errors.append("Invalid line range")
                return result

            # Get the code to extract
            extract_lines = lines[start_line - 1:end_line]
            extract_code = "\n".join(extract_lines)

            # Detect language
            language = self.detect_language(file_path)
            params = params or []

            # Generate new function
            if language == "python":
                indent = self._detect_indent(extract_lines[0])
                new_func = self._generate_python_function(
                    function_name, params, extract_code, indent
                )
                call_code = f"{indent}{function_name}({', '.join(params)})"
            elif language in ["javascript", "typescript"]:
                indent = self._detect_indent(extract_lines[0])
                new_func = self._generate_js_function(
                    function_name, params, extract_code, indent
                )
                call_code = f"{indent}{function_name}({', '.join(params)});"
            else:
                result.errors.append(f"Language not supported: {language}")
                return result

            # Replace extracted code with function call
            new_lines = lines[:start_line - 1] + [call_code] + lines[end_line:]

            # Add new function at appropriate location
            new_lines.insert(start_line - 1, new_func)

            new_content = "\n".join(new_lines)

            result.changes.append(RefactorChange(
                file_path=str(file_path),
                original_content=content,
                new_content=new_content,
                description=f"Extract function '{function_name}'",
            ))

            result.success = True
            result.files_affected = 1
            result.message = f"Extracted {end_line - start_line + 1} lines into '{function_name}'"

        except Exception as e:
            result.errors.append(str(e))

        return result

    def _detect_indent(self, line: str) -> str:
        """Detect indentation of a line."""
        return line[:len(line) - len(line.lstrip())]

    def _generate_python_function(
        self,
        name: str,
        params: List[str],
        body: str,
        base_indent: str,
    ) -> str:
        """Generate a Python function."""
        params_str = ", ".join(params) if params else ""
        lines = [
            f"{base_indent}def {name}({params_str}):",
            f'{base_indent}    """TODO: Add docstring."""',
        ]

        # Add body with proper indentation
        for line in body.splitlines():
            if line.strip():
                lines.append(f"{base_indent}    {line.lstrip()}")
            else:
                lines.append("")

        lines.append("")
        return "\n".join(lines)

    def _generate_js_function(
        self,
        name: str,
        params: List[str],
        body: str,
        base_indent: str,
    ) -> str:
        """Generate a JavaScript function."""
        params_str = ", ".join(params) if params else ""
        lines = [
            f"{base_indent}function {name}({params_str}) {{",
        ]

        # Add body with proper indentation
        for line in body.splitlines():
            if line.strip():
                lines.append(f"{base_indent}    {line.lstrip()}")
            else:
                lines.append("")

        lines.append(f"{base_indent}}}")
        lines.append("")
        return "\n".join(lines)

    def extract_variable(
        self,
        file_path: Path,
        line_number: int,
        expression: str,
        variable_name: str,
    ) -> RefactorResult:
        """
        Extract expression into a variable.

        Args:
            file_path: File containing code
            line_number: Line with expression
            expression: Expression to extract
            variable_name: Name for variable

        Returns:
            RefactorResult
        """
        result = RefactorResult(
            success=False,
            refactor_type=RefactorType.EXTRACT_VARIABLE,
        )

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if line_number < 1 or line_number > len(lines):
                result.errors.append("Invalid line number")
                return result

            line = lines[line_number - 1]
            if expression not in line:
                result.errors.append(f"Expression '{expression}' not found on line {line_number}")
                return result

            language = self.detect_language(file_path)
            indent = self._detect_indent(line)

            # Generate variable declaration
            if language == "python":
                var_decl = f"{indent}{variable_name} = {expression}"
            elif language in ["javascript", "typescript"]:
                var_decl = f"{indent}const {variable_name} = {expression};"
            elif language == "go":
                var_decl = f"{indent}{variable_name} := {expression}"
            else:
                var_decl = f"{indent}{variable_name} = {expression}"

            # Replace expression with variable
            new_line = line.replace(expression, variable_name, 1)

            # Insert variable declaration and update line
            new_lines = lines[:line_number - 1] + [var_decl, new_line] + lines[line_number:]
            new_content = "\n".join(new_lines)

            result.changes.append(RefactorChange(
                file_path=str(file_path),
                original_content=content,
                new_content=new_content,
                description=f"Extract variable '{variable_name}'",
            ))

            result.success = True
            result.files_affected = 1
            result.message = f"Extracted expression to variable '{variable_name}'"

        except Exception as e:
            result.errors.append(str(e))

        return result

    def get_report(self, result: RefactorResult) -> str:
        """Generate refactoring report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  REFACTORING REPORT")
        lines.append("=" * 50)
        lines.append("")

        status = "[OK]" if result.success else "[FAILED]"
        lines.append(f"Status: {status}")
        lines.append(f"Type: {result.refactor_type.value}")
        lines.append(f"Locations Found: {result.locations_found}")
        lines.append(f"Files Affected: {result.files_affected}")
        lines.append("")

        if result.message:
            lines.append(f"Message: {result.message}")
            lines.append("")

        if result.changes:
            lines.append("Changes:")
            for change in result.changes[:5]:
                lines.append(f"  - {change.file_path}: {change.description}")
            if len(result.changes) > 5:
                lines.append(f"  ... and {len(result.changes) - 5} more")
            lines.append("")

        if result.errors:
            lines.append("Errors:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)


# Global instance
_refactoring: Optional[RefactoringTools] = None


def get_refactoring_tools(working_dir: Optional[Path] = None) -> RefactoringTools:
    """Get or create refactoring tools."""
    global _refactoring
    if _refactoring is None:
        _refactoring = RefactoringTools(working_dir)
    return _refactoring


# Convenience functions
def rename_symbol(
    old_name: str,
    new_name: str,
    language: Optional[str] = None,
    preview: bool = True,
) -> RefactorResult:
    """Rename a symbol across the project."""
    return get_refactoring_tools().rename_symbol(old_name, new_name, language, preview=preview)


def find_symbol(symbol_name: str, language: Optional[str] = None) -> List[RefactorLocation]:
    """Find all occurrences of a symbol."""
    return get_refactoring_tools().find_symbol_occurrences(symbol_name, language)
