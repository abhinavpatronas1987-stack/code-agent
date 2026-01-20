"""Linter Integration - Feature 25.

Integrate with popular linters:
- Python: ruff, flake8, pylint, mypy
- JavaScript/TypeScript: eslint
- Go: golangci-lint
- Rust: clippy
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class LinterType(Enum):
    """Supported linters."""
    RUFF = "ruff"
    FLAKE8 = "flake8"
    PYLINT = "pylint"
    MYPY = "mypy"
    ESLINT = "eslint"
    GOLANGCI_LINT = "golangci-lint"
    CLIPPY = "clippy"


class IssueSeverity(Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class LintIssue:
    """A linting issue."""
    file_path: str
    line: int
    column: int
    code: str
    message: str
    severity: IssueSeverity
    linter: str
    fixable: bool = False
    fix_suggestion: str = ""


@dataclass
class LintResult:
    """Result of linting."""
    linter: str
    success: bool
    issues: List[LintIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    files_checked: int = 0
    execution_time: float = 0.0
    message: str = ""


class LinterIntegration:
    """Integration with various linters."""

    # Linter configurations
    LINTER_CONFIGS = {
        LinterType.RUFF: {
            "command": ["ruff", "check", "--output-format=json"],
            "fix_command": ["ruff", "check", "--fix"],
            "languages": ["python"],
            "extensions": [".py"],
        },
        LinterType.FLAKE8: {
            "command": ["flake8", "--format=json"],
            "languages": ["python"],
            "extensions": [".py"],
        },
        LinterType.PYLINT: {
            "command": ["pylint", "--output-format=json"],
            "languages": ["python"],
            "extensions": [".py"],
        },
        LinterType.MYPY: {
            "command": ["mypy", "--show-error-codes", "--no-error-summary"],
            "languages": ["python"],
            "extensions": [".py"],
        },
        LinterType.ESLINT: {
            "command": ["eslint", "--format=json"],
            "fix_command": ["eslint", "--fix"],
            "languages": ["javascript", "typescript"],
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
        },
        LinterType.GOLANGCI_LINT: {
            "command": ["golangci-lint", "run", "--out-format=json"],
            "languages": ["go"],
            "extensions": [".go"],
        },
        LinterType.CLIPPY: {
            "command": ["cargo", "clippy", "--message-format=json"],
            "languages": ["rust"],
            "extensions": [".rs"],
        },
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize linter integration."""
        self.working_dir = working_dir or Path.cwd()

    def detect_available_linters(self) -> List[LinterType]:
        """Detect which linters are available."""
        available = []

        for linter, config in self.LINTER_CONFIGS.items():
            cmd = config["command"][0]
            try:
                subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    timeout=5,
                )
                available.append(linter)
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        return available

    def detect_project_linters(self) -> List[LinterType]:
        """Detect recommended linters for project."""
        recommended = []

        # Check for Python
        if list(self.working_dir.glob("**/*.py")):
            if self._is_available("ruff"):
                recommended.append(LinterType.RUFF)
            elif self._is_available("flake8"):
                recommended.append(LinterType.FLAKE8)

        # Check for JavaScript/TypeScript
        if list(self.working_dir.glob("**/*.js")) or list(self.working_dir.glob("**/*.ts")):
            if self._is_available("eslint"):
                recommended.append(LinterType.ESLINT)

        # Check for Go
        if list(self.working_dir.glob("**/*.go")):
            if self._is_available("golangci-lint"):
                recommended.append(LinterType.GOLANGCI_LINT)

        # Check for Rust
        if (self.working_dir / "Cargo.toml").exists():
            if self._is_available("cargo"):
                recommended.append(LinterType.CLIPPY)

        return recommended

    def _is_available(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run(
                [command, "--version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def lint(
        self,
        linter: Optional[LinterType] = None,
        path: Optional[Path] = None,
        fix: bool = False,
    ) -> LintResult:
        """
        Run linter on code.

        Args:
            linter: Specific linter to use (auto-detect if None)
            path: Path to lint (default: working_dir)
            fix: Attempt to auto-fix issues

        Returns:
            LintResult with issues
        """
        import time
        start_time = time.time()

        # Auto-detect linter if not specified
        if linter is None:
            available = self.detect_project_linters()
            if not available:
                return LintResult(
                    linter="none",
                    success=False,
                    message="No suitable linter found for this project"
                )
            linter = available[0]

        config = self.LINTER_CONFIGS.get(linter)
        if not config:
            return LintResult(
                linter=linter.value,
                success=False,
                message=f"Unknown linter: {linter.value}"
            )

        target = str(path or self.working_dir)

        # Run linter
        if fix and "fix_command" in config:
            cmd = config["fix_command"] + [target]
        else:
            cmd = config["command"] + [target]

        result = LintResult(linter=linter.value, success=True)

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse output based on linter
            if linter == LinterType.RUFF:
                result.issues = self._parse_ruff_output(proc.stdout)
            elif linter == LinterType.ESLINT:
                result.issues = self._parse_eslint_output(proc.stdout)
            elif linter == LinterType.MYPY:
                result.issues = self._parse_mypy_output(proc.stdout)
            elif linter == LinterType.GOLANGCI_LINT:
                result.issues = self._parse_golangci_output(proc.stdout)
            else:
                # Generic parsing
                result.issues = self._parse_generic_output(proc.stdout, linter.value)

            # Count by severity
            for issue in result.issues:
                if issue.severity == IssueSeverity.ERROR:
                    result.error_count += 1
                elif issue.severity == IssueSeverity.WARNING:
                    result.warning_count += 1
                else:
                    result.info_count += 1

        except subprocess.TimeoutExpired:
            result.success = False
            result.message = "Linter timed out"
        except FileNotFoundError:
            result.success = False
            result.message = f"Linter '{linter.value}' not found"
        except Exception as e:
            result.success = False
            result.message = str(e)

        result.execution_time = time.time() - start_time
        return result

    def _parse_ruff_output(self, output: str) -> List[LintIssue]:
        """Parse ruff JSON output."""
        issues = []
        try:
            if not output.strip():
                return issues
            data = json.loads(output)
            for item in data:
                issues.append(LintIssue(
                    file_path=item.get("filename", ""),
                    line=item.get("location", {}).get("row", 0),
                    column=item.get("location", {}).get("column", 0),
                    code=item.get("code", ""),
                    message=item.get("message", ""),
                    severity=IssueSeverity.ERROR if item.get("code", "").startswith("E") else IssueSeverity.WARNING,
                    linter="ruff",
                    fixable=item.get("fix") is not None,
                ))
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_eslint_output(self, output: str) -> List[LintIssue]:
        """Parse eslint JSON output."""
        issues = []
        try:
            if not output.strip():
                return issues
            data = json.loads(output)
            for file_data in data:
                file_path = file_data.get("filePath", "")
                for msg in file_data.get("messages", []):
                    severity = IssueSeverity.ERROR if msg.get("severity") == 2 else IssueSeverity.WARNING
                    issues.append(LintIssue(
                        file_path=file_path,
                        line=msg.get("line", 0),
                        column=msg.get("column", 0),
                        code=msg.get("ruleId", ""),
                        message=msg.get("message", ""),
                        severity=severity,
                        linter="eslint",
                        fixable=msg.get("fix") is not None,
                    ))
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_mypy_output(self, output: str) -> List[LintIssue]:
        """Parse mypy output."""
        issues = []
        import re

        for line in output.splitlines():
            # Pattern: file:line: error: message
            match = re.match(r"([^:]+):(\d+):\s*(error|warning|note):\s*(.+)", line)
            if match:
                severity_map = {
                    "error": IssueSeverity.ERROR,
                    "warning": IssueSeverity.WARNING,
                    "note": IssueSeverity.INFO,
                }
                issues.append(LintIssue(
                    file_path=match.group(1),
                    line=int(match.group(2)),
                    column=0,
                    code="mypy",
                    message=match.group(4),
                    severity=severity_map.get(match.group(3), IssueSeverity.WARNING),
                    linter="mypy",
                ))

        return issues

    def _parse_golangci_output(self, output: str) -> List[LintIssue]:
        """Parse golangci-lint JSON output."""
        issues = []
        try:
            if not output.strip():
                return issues
            data = json.loads(output)
            for item in data.get("Issues", []):
                pos = item.get("Pos", {})
                issues.append(LintIssue(
                    file_path=pos.get("Filename", ""),
                    line=pos.get("Line", 0),
                    column=pos.get("Column", 0),
                    code=item.get("FromLinter", ""),
                    message=item.get("Text", ""),
                    severity=IssueSeverity.WARNING,
                    linter="golangci-lint",
                ))
        except json.JSONDecodeError:
            pass
        return issues

    def _parse_generic_output(self, output: str, linter: str) -> List[LintIssue]:
        """Parse generic linter output."""
        issues = []
        import re

        for line in output.splitlines():
            # Try common patterns
            patterns = [
                r"([^:]+):(\d+):(\d+):\s*(\w+):\s*(.+)",  # file:line:col: type: msg
                r"([^:]+):(\d+):\s*(\w+):\s*(.+)",  # file:line: type: msg
                r"([^:]+)\((\d+)\):\s*(.+)",  # file(line): msg
            ]

            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    issues.append(LintIssue(
                        file_path=groups[0],
                        line=int(groups[1]),
                        column=int(groups[2]) if len(groups) > 4 else 0,
                        code=linter,
                        message=groups[-1],
                        severity=IssueSeverity.WARNING,
                        linter=linter,
                    ))
                    break

        return issues

    def fix(self, linter: Optional[LinterType] = None, path: Optional[Path] = None) -> LintResult:
        """Run linter with auto-fix."""
        return self.lint(linter, path, fix=True)

    def get_report(self, result: LintResult) -> str:
        """Generate lint report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  LINT REPORT")
        lines.append("=" * 60)
        lines.append("")

        lines.append(f"Linter: {result.linter}")
        lines.append(f"Status: {'[OK]' if result.success else '[FAILED]'}")
        lines.append(f"Time: {result.execution_time:.2f}s")
        lines.append("")

        if result.message:
            lines.append(f"Message: {result.message}")
            lines.append("")

        total_issues = len(result.issues)
        if total_issues > 0:
            lines.append(f"Issues Found: {total_issues}")
            lines.append(f"  Errors: {result.error_count}")
            lines.append(f"  Warnings: {result.warning_count}")
            lines.append(f"  Info: {result.info_count}")
            lines.append("")

            # Group by file
            by_file: Dict[str, List[LintIssue]] = {}
            for issue in result.issues:
                if issue.file_path not in by_file:
                    by_file[issue.file_path] = []
                by_file[issue.file_path].append(issue)

            lines.append("Issues by File:")
            lines.append("-" * 60)

            for file_path, file_issues in list(by_file.items())[:10]:
                lines.append(f"\n{file_path} ({len(file_issues)} issues)")
                for issue in file_issues[:5]:
                    severity_mark = {
                        IssueSeverity.ERROR: "[E]",
                        IssueSeverity.WARNING: "[W]",
                        IssueSeverity.INFO: "[I]",
                        IssueSeverity.HINT: "[H]",
                    }[issue.severity]
                    fixable = " (fixable)" if issue.fixable else ""
                    lines.append(f"  {severity_mark} L{issue.line}: {issue.code} - {issue.message[:60]}{fixable}")
                if len(file_issues) > 5:
                    lines.append(f"  ... and {len(file_issues) - 5} more")

            if len(by_file) > 10:
                lines.append(f"\n... and {len(by_file) - 10} more files")

        else:
            lines.append("[OK] No issues found!")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_linter: Optional[LinterIntegration] = None


def get_linter(working_dir: Optional[Path] = None) -> LinterIntegration:
    """Get or create linter integration."""
    global _linter
    if _linter is None:
        _linter = LinterIntegration(working_dir)
    return _linter


# Convenience functions
def run_lint(
    linter: Optional[str] = None,
    path: Optional[Path] = None,
    fix: bool = False,
) -> LintResult:
    """Run linter on code."""
    linter_type = LinterType(linter) if linter else None
    return get_linter().lint(linter_type, path, fix)


def detect_linters() -> List[str]:
    """Detect available linters."""
    return [l.value for l in get_linter().detect_available_linters()]
