"""Test Runner Integration - Feature 13.

Test framework integration:
- Auto-detect test framework
- Run tests with streaming output
- Parse test results
- Coverage integration
"""

import subprocess
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TestFramework(Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"
    VITEST = "vitest"
    GO_TEST = "go test"
    CARGO_TEST = "cargo test"
    UNKNOWN = "unknown"


class TestStatus(Enum):
    """Test result status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    status: TestStatus
    duration: float = 0.0
    message: str = ""
    file: str = ""
    line: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class TestSuite:
    """Collection of test results."""
    framework: TestFramework
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    tests: List[TestResult] = field(default_factory=list)
    coverage: Optional[float] = None
    started_at: str = ""
    finished_at: str = ""


class TestRunner:
    """Run and analyze tests."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize test runner."""
        self.working_dir = working_dir or Path.cwd()
        self.framework = self._detect_framework()
        self.last_results: Optional[TestSuite] = None

    def _detect_framework(self) -> TestFramework:
        """Auto-detect test framework."""
        # Check for pytest
        if (self.working_dir / "pytest.ini").exists() or \
           (self.working_dir / "pyproject.toml").exists() or \
           (self.working_dir / "conftest.py").exists():
            # Check if pytest is available
            try:
                result = subprocess.run(
                    ["pytest", "--version"],
                    capture_output=True,
                    cwd=self.working_dir,
                )
                if result.returncode == 0:
                    return TestFramework.PYTEST
            except FileNotFoundError:
                pass

        # Check for unittest
        tests_dir = self.working_dir / "tests"
        if tests_dir.exists():
            for f in tests_dir.rglob("test_*.py"):
                return TestFramework.UNITTEST

        # Check for Jest
        package_json = self.working_dir / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "jest" in deps:
                    return TestFramework.JEST
                if "vitest" in deps:
                    return TestFramework.VITEST
                if "mocha" in deps:
                    return TestFramework.MOCHA
            except (json.JSONDecodeError, IOError):
                pass

        # Check for Go
        if (self.working_dir / "go.mod").exists():
            return TestFramework.GO_TEST

        # Check for Rust
        if (self.working_dir / "Cargo.toml").exists():
            return TestFramework.CARGO_TEST

        return TestFramework.UNKNOWN

    def run(
        self,
        pattern: Optional[str] = None,
        verbose: bool = False,
        coverage: bool = False,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> TestSuite:
        """
        Run tests.

        Args:
            pattern: Test pattern to run
            verbose: Verbose output
            coverage: Include coverage
            on_output: Callback for streaming output

        Returns:
            TestSuite with results
        """
        suite = TestSuite(
            framework=self.framework,
            started_at=datetime.now().isoformat(),
        )

        if self.framework == TestFramework.PYTEST:
            suite = self._run_pytest(pattern, verbose, coverage, on_output)
        elif self.framework == TestFramework.UNITTEST:
            suite = self._run_unittest(pattern, verbose, on_output)
        elif self.framework == TestFramework.JEST:
            suite = self._run_jest(pattern, verbose, coverage, on_output)
        elif self.framework == TestFramework.GO_TEST:
            suite = self._run_go_test(pattern, verbose, coverage, on_output)
        elif self.framework == TestFramework.CARGO_TEST:
            suite = self._run_cargo_test(pattern, verbose, on_output)
        else:
            suite.tests.append(TestResult(
                name="detection",
                status=TestStatus.ERROR,
                message="Could not detect test framework",
            ))

        suite.finished_at = datetime.now().isoformat()
        self.last_results = suite
        return suite

    def _run_pytest(
        self,
        pattern: Optional[str],
        verbose: bool,
        coverage: bool,
        on_output: Optional[Callable],
    ) -> TestSuite:
        """Run pytest."""
        suite = TestSuite(framework=TestFramework.PYTEST)

        args = ["pytest", "-v", "--tb=short"]
        if pattern:
            args.extend(["-k", pattern])
        if coverage:
            args.extend(["--cov=.", "--cov-report=term-missing"])

        try:
            process = subprocess.Popen(
                args,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            output_lines = []
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line)
                if on_output:
                    on_output(line)

            process.wait()
            output = "".join(output_lines)

            # Parse results
            suite = self._parse_pytest_output(output)

        except FileNotFoundError:
            suite.tests.append(TestResult(
                name="pytest",
                status=TestStatus.ERROR,
                message="pytest not found",
            ))

        return suite

    def _parse_pytest_output(self, output: str) -> TestSuite:
        """Parse pytest output."""
        suite = TestSuite(framework=TestFramework.PYTEST)

        # Parse individual tests
        for line in output.splitlines():
            # Match test lines: test_file.py::test_name PASSED/FAILED
            match = re.match(r'(.+?)::(\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)', line)
            if match:
                file = match.group(1)
                name = match.group(2)
                status_str = match.group(3)

                status_map = {
                    "PASSED": TestStatus.PASSED,
                    "FAILED": TestStatus.FAILED,
                    "SKIPPED": TestStatus.SKIPPED,
                    "ERROR": TestStatus.ERROR,
                }

                suite.tests.append(TestResult(
                    name=name,
                    file=file,
                    status=status_map.get(status_str, TestStatus.ERROR),
                ))

        # Parse summary line
        summary_match = re.search(
            r'(\d+)\s+passed.*?(\d+)\s+failed|(\d+)\s+passed',
            output
        )
        if summary_match:
            suite.passed = int(summary_match.group(1) or summary_match.group(3) or 0)
            suite.failed = int(summary_match.group(2) or 0)

        # Parse coverage
        cov_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if cov_match:
            suite.coverage = float(cov_match.group(1))

        suite.total = len(suite.tests)
        suite.passed = len([t for t in suite.tests if t.status == TestStatus.PASSED])
        suite.failed = len([t for t in suite.tests if t.status == TestStatus.FAILED])
        suite.skipped = len([t for t in suite.tests if t.status == TestStatus.SKIPPED])

        return suite

    def _run_unittest(
        self,
        pattern: Optional[str],
        verbose: bool,
        on_output: Optional[Callable],
    ) -> TestSuite:
        """Run unittest."""
        suite = TestSuite(framework=TestFramework.UNITTEST)

        args = ["python", "-m", "unittest"]
        if verbose:
            args.append("-v")
        if pattern:
            args.append(pattern)
        else:
            args.append("discover")

        try:
            process = subprocess.Popen(
                args,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in iter(process.stdout.readline, ''):
                if on_output:
                    on_output(line)

            process.wait()

        except Exception as e:
            suite.tests.append(TestResult(
                name="unittest",
                status=TestStatus.ERROR,
                message=str(e),
            ))

        return suite

    def _run_jest(
        self,
        pattern: Optional[str],
        verbose: bool,
        coverage: bool,
        on_output: Optional[Callable],
    ) -> TestSuite:
        """Run Jest."""
        suite = TestSuite(framework=TestFramework.JEST)

        args = ["npx", "jest"]
        if pattern:
            args.append(pattern)
        if coverage:
            args.append("--coverage")
        args.append("--json")

        try:
            result = subprocess.run(
                args,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
            )

            if on_output:
                on_output(result.stdout)

            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                suite.total = data.get("numTotalTests", 0)
                suite.passed = data.get("numPassedTests", 0)
                suite.failed = data.get("numFailedTests", 0)
            except json.JSONDecodeError:
                pass

        except Exception as e:
            suite.tests.append(TestResult(
                name="jest",
                status=TestStatus.ERROR,
                message=str(e),
            ))

        return suite

    def _run_go_test(
        self,
        pattern: Optional[str],
        verbose: bool,
        coverage: bool,
        on_output: Optional[Callable],
    ) -> TestSuite:
        """Run Go tests."""
        suite = TestSuite(framework=TestFramework.GO_TEST)

        args = ["go", "test"]
        if verbose:
            args.append("-v")
        if coverage:
            args.append("-cover")
        if pattern:
            args.append(f"-run={pattern}")
        args.append("./...")

        try:
            process = subprocess.Popen(
                args,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in iter(process.stdout.readline, ''):
                if on_output:
                    on_output(line)

            process.wait()

        except Exception as e:
            suite.tests.append(TestResult(
                name="go test",
                status=TestStatus.ERROR,
                message=str(e),
            ))

        return suite

    def _run_cargo_test(
        self,
        pattern: Optional[str],
        verbose: bool,
        on_output: Optional[Callable],
    ) -> TestSuite:
        """Run Cargo tests."""
        suite = TestSuite(framework=TestFramework.CARGO_TEST)

        args = ["cargo", "test"]
        if pattern:
            args.append(pattern)
        if verbose:
            args.append("--")
            args.append("--nocapture")

        try:
            process = subprocess.Popen(
                args,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in iter(process.stdout.readline, ''):
                if on_output:
                    on_output(line)

            process.wait()

        except Exception as e:
            suite.tests.append(TestResult(
                name="cargo test",
                status=TestStatus.ERROR,
                message=str(e),
            ))

        return suite

    def get_report(self) -> str:
        """Generate test results report."""
        if not self.last_results:
            return "No test results available. Run tests first."

        suite = self.last_results
        lines = []

        lines.append("=" * 50)
        lines.append("  TEST RESULTS")
        lines.append("=" * 50)
        lines.append(f"\nFramework: {suite.framework.value}")
        lines.append(f"Started: {suite.started_at[:19]}")

        # Summary
        lines.append(f"\nSummary:")
        lines.append(f"  Total:   {suite.total}")
        lines.append(f"  Passed:  {suite.passed}")
        lines.append(f"  Failed:  {suite.failed}")
        lines.append(f"  Skipped: {suite.skipped}")

        if suite.coverage is not None:
            lines.append(f"\nCoverage: {suite.coverage:.1f}%")

        # Failed tests
        failed = [t for t in suite.tests if t.status == TestStatus.FAILED]
        if failed:
            lines.append(f"\nFailed Tests ({len(failed)}):")
            for test in failed[:10]:
                lines.append(f"  X {test.name}")
                if test.message:
                    lines.append(f"    {test.message[:80]}")

        # Passed tests (abbreviated)
        passed = [t for t in suite.tests if t.status == TestStatus.PASSED]
        if passed and len(passed) <= 10:
            lines.append(f"\nPassed Tests ({len(passed)}):")
            for test in passed:
                lines.append(f"  + {test.name}")

        lines.append("\n" + "=" * 50)

        return "\n".join(lines)


# Global instance
_test_runner: Optional[TestRunner] = None


def get_test_runner(working_dir: Optional[Path] = None) -> TestRunner:
    """Get or create test runner."""
    global _test_runner
    if _test_runner is None:
        _test_runner = TestRunner(working_dir)
    return _test_runner


# Convenience functions
def run_tests(
    pattern: Optional[str] = None,
    coverage: bool = False,
    working_dir: Optional[Path] = None,
) -> TestSuite:
    """Run tests."""
    runner = TestRunner(working_dir or Path.cwd())
    return runner.run(pattern=pattern, coverage=coverage)


def get_test_report(working_dir: Optional[Path] = None) -> str:
    """Get test results report."""
    runner = get_test_runner(working_dir)
    if not runner.last_results:
        runner.run()
    return runner.get_report()
