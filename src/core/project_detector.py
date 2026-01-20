"""Project Auto-Detection - Feature 1.

Automatically detect:
- Programming languages
- Frameworks
- Package managers
- Testing frameworks
- Build tools
- CI/CD configuration
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    UNKNOWN = "unknown"


@dataclass
class ProjectInfo:
    """Detected project information."""
    path: str
    name: str
    languages: List[str] = field(default_factory=list)
    primary_language: str = "unknown"
    frameworks: List[str] = field(default_factory=list)
    package_manager: Optional[str] = None
    test_framework: Optional[str] = None
    build_tool: Optional[str] = None
    linters: List[str] = field(default_factory=list)
    ci_cd: List[str] = field(default_factory=list)
    version_control: Optional[str] = None
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    docker: bool = False
    has_tests: bool = False
    has_docs: bool = False
    file_count: int = 0
    total_lines: int = 0
    config_files: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    dependencies: Dict[str, int] = field(default_factory=dict)
    todos_found: int = 0
    potential_issues: List[str] = field(default_factory=list)


class ProjectDetector:
    """Detect project type and configuration."""

    # File patterns for language detection
    LANGUAGE_PATTERNS = {
        Language.PYTHON: ["*.py", "*.pyx", "*.pyi"],
        Language.JAVASCRIPT: ["*.js", "*.jsx", "*.mjs"],
        Language.TYPESCRIPT: ["*.ts", "*.tsx"],
        Language.RUST: ["*.rs"],
        Language.GO: ["*.go"],
        Language.JAVA: ["*.java"],
        Language.CSHARP: ["*.cs"],
        Language.CPP: ["*.cpp", "*.cc", "*.cxx", "*.hpp", "*.h"],
        Language.RUBY: ["*.rb"],
        Language.PHP: ["*.php"],
        Language.SWIFT: ["*.swift"],
        Language.KOTLIN: ["*.kt", "*.kts"],
    }

    # Config files for detection
    CONFIG_PATTERNS = {
        # Python
        "pyproject.toml": {"language": "python", "package_manager": "pip/poetry"},
        "setup.py": {"language": "python", "package_manager": "pip"},
        "setup.cfg": {"language": "python", "package_manager": "pip"},
        "requirements.txt": {"language": "python", "package_manager": "pip"},
        "Pipfile": {"language": "python", "package_manager": "pipenv"},
        "poetry.lock": {"language": "python", "package_manager": "poetry"},
        "conda.yaml": {"language": "python", "package_manager": "conda"},
        "pytest.ini": {"test_framework": "pytest"},
        "tox.ini": {"test_framework": "tox"},
        ".flake8": {"linter": "flake8"},
        "mypy.ini": {"linter": "mypy"},
        ".pylintrc": {"linter": "pylint"},
        "ruff.toml": {"linter": "ruff"},

        # JavaScript/TypeScript
        "package.json": {"language": "javascript", "package_manager": "npm"},
        "package-lock.json": {"package_manager": "npm"},
        "yarn.lock": {"package_manager": "yarn"},
        "pnpm-lock.yaml": {"package_manager": "pnpm"},
        "tsconfig.json": {"language": "typescript"},
        ".eslintrc": {"linter": "eslint"},
        ".eslintrc.js": {"linter": "eslint"},
        ".eslintrc.json": {"linter": "eslint"},
        "jest.config.js": {"test_framework": "jest"},
        "vitest.config.ts": {"test_framework": "vitest"},
        ".prettierrc": {"linter": "prettier"},

        # Rust
        "Cargo.toml": {"language": "rust", "package_manager": "cargo", "build_tool": "cargo"},
        "Cargo.lock": {"language": "rust"},
        "clippy.toml": {"linter": "clippy"},

        # Go
        "go.mod": {"language": "go", "package_manager": "go mod"},
        "go.sum": {"language": "go"},
        "Makefile": {"build_tool": "make"},

        # Java
        "pom.xml": {"language": "java", "package_manager": "maven", "build_tool": "maven"},
        "build.gradle": {"language": "java", "package_manager": "gradle", "build_tool": "gradle"},
        "build.gradle.kts": {"language": "kotlin", "build_tool": "gradle"},

        # C#
        "*.csproj": {"language": "csharp", "build_tool": "dotnet"},
        "*.sln": {"language": "csharp", "build_tool": "dotnet"},
        "nuget.config": {"package_manager": "nuget"},

        # C/C++
        "CMakeLists.txt": {"language": "cpp", "build_tool": "cmake"},
        "Makefile": {"build_tool": "make"},
        "meson.build": {"build_tool": "meson"},

        # Docker
        "Dockerfile": {"docker": True},
        "docker-compose.yml": {"docker": True},
        "docker-compose.yaml": {"docker": True},

        # CI/CD
        ".github/workflows": {"ci_cd": "github_actions"},
        ".gitlab-ci.yml": {"ci_cd": "gitlab_ci"},
        "Jenkinsfile": {"ci_cd": "jenkins"},
        ".circleci/config.yml": {"ci_cd": "circleci"},
        ".travis.yml": {"ci_cd": "travis"},
        "azure-pipelines.yml": {"ci_cd": "azure_devops"},
        "bitbucket-pipelines.yml": {"ci_cd": "bitbucket"},

        # Version control
        ".git": {"version_control": "git"},
        ".hg": {"version_control": "mercurial"},
        ".svn": {"version_control": "svn"},
    }

    # Framework detection in config files
    FRAMEWORK_PATTERNS = {
        # Python
        "django": {"framework": "Django", "files": ["manage.py", "settings.py"]},
        "flask": {"framework": "Flask"},
        "fastapi": {"framework": "FastAPI"},
        "streamlit": {"framework": "Streamlit"},
        "pytorch": {"framework": "PyTorch"},
        "tensorflow": {"framework": "TensorFlow"},
        "numpy": {"framework": "NumPy"},
        "pandas": {"framework": "Pandas"},
        "sqlalchemy": {"framework": "SQLAlchemy"},
        "pytest": {"test_framework": "pytest"},

        # JavaScript
        "react": {"framework": "React"},
        "vue": {"framework": "Vue.js"},
        "angular": {"framework": "Angular"},
        "next": {"framework": "Next.js"},
        "nuxt": {"framework": "Nuxt.js"},
        "express": {"framework": "Express.js"},
        "nestjs": {"framework": "NestJS"},
        "svelte": {"framework": "Svelte"},

        # Rust
        "actix-web": {"framework": "Actix Web"},
        "axum": {"framework": "Axum"},
        "tokio": {"framework": "Tokio"},
        "rocket": {"framework": "Rocket"},

        # Go
        "gin-gonic": {"framework": "Gin"},
        "echo": {"framework": "Echo"},
        "fiber": {"framework": "Fiber"},
    }

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize detector."""
        self.project_path = Path(project_path) if project_path else Path.cwd()

    def detect(self) -> ProjectInfo:
        """
        Detect project information.

        Returns:
            ProjectInfo with all detected information
        """
        info = ProjectInfo(
            path=str(self.project_path),
            name=self.project_path.name,
        )

        # Detect config files and their implications
        self._detect_config_files(info)

        # Detect languages by file extensions
        self._detect_languages(info)

        # Detect frameworks from dependencies
        self._detect_frameworks(info)

        # Detect entry points
        self._detect_entry_points(info)

        # Count files and lines
        self._count_files(info)

        # Find TODOs and issues
        self._find_todos(info)

        # Check for tests and docs
        self._check_tests_docs(info)

        # Detect versions
        self._detect_versions(info)

        return info

    def _detect_config_files(self, info: ProjectInfo):
        """Detect configuration files."""
        for root, dirs, files in os.walk(self.project_path):
            # Don't go too deep
            depth = len(Path(root).relative_to(self.project_path).parts)
            if depth > 3:
                continue

            # Skip common non-project dirs
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                'env', 'dist', 'build', '.tox', '.pytest_cache'
            ]]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.project_path)

                for pattern, detection in self.CONFIG_PATTERNS.items():
                    if file == pattern or str(rel_path) == pattern:
                        info.config_files.append(str(rel_path))

                        if "language" in detection:
                            if detection["language"] not in info.languages:
                                info.languages.append(detection["language"])

                        if "package_manager" in detection:
                            info.package_manager = detection["package_manager"]

                        if "build_tool" in detection:
                            info.build_tool = detection["build_tool"]

                        if "test_framework" in detection:
                            info.test_framework = detection["test_framework"]

                        if "linter" in detection:
                            if detection["linter"] not in info.linters:
                                info.linters.append(detection["linter"])

                        if "ci_cd" in detection:
                            if detection["ci_cd"] not in info.ci_cd:
                                info.ci_cd.append(detection["ci_cd"])

                        if "version_control" in detection:
                            info.version_control = detection["version_control"]

                        if "docker" in detection:
                            info.docker = True

            # Check for CI/CD directories
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                rel_dir = str(dir_path.relative_to(self.project_path))
                if rel_dir in self.CONFIG_PATTERNS:
                    detection = self.CONFIG_PATTERNS[rel_dir]
                    if "ci_cd" in detection:
                        if detection["ci_cd"] not in info.ci_cd:
                            info.ci_cd.append(detection["ci_cd"])

    def _detect_languages(self, info: ProjectInfo):
        """Detect languages by file extensions."""
        lang_counts: Dict[str, int] = {}

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                'env', 'dist', 'build'
            ]]

            for file in files:
                for lang, patterns in self.LANGUAGE_PATTERNS.items():
                    for pattern in patterns:
                        if file.endswith(pattern[1:]):  # Remove * from pattern
                            lang_counts[lang.value] = lang_counts.get(lang.value, 0) + 1

        # Add detected languages
        for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
            if lang not in info.languages:
                info.languages.append(lang)
            info.dependencies[lang] = count

        # Set primary language
        if info.languages:
            info.primary_language = info.languages[0]

    def _detect_frameworks(self, info: ProjectInfo):
        """Detect frameworks from dependencies."""
        # Check package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                    for dep_name in deps:
                        for pattern, detection in self.FRAMEWORK_PATTERNS.items():
                            if pattern in dep_name.lower():
                                if "framework" in detection and detection["framework"] not in info.frameworks:
                                    info.frameworks.append(detection["framework"])
                                if "test_framework" in detection:
                                    info.test_framework = detection["test_framework"]
            except (json.JSONDecodeError, IOError):
                pass

        # Check pyproject.toml / requirements.txt
        pyproject = self.project_path / "pyproject.toml"
        requirements = self.project_path / "requirements.txt"

        deps_to_check = []

        if pyproject.exists():
            try:
                content = pyproject.read_text()
                # Simple pattern matching for dependencies
                deps_to_check.extend(re.findall(r'"([a-zA-Z0-9_-]+)"', content))
            except IOError:
                pass

        if requirements.exists():
            try:
                content = requirements.read_text()
                for line in content.splitlines():
                    if line and not line.startswith("#"):
                        dep = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        deps_to_check.append(dep)
            except IOError:
                pass

        for dep in deps_to_check:
            for pattern, detection in self.FRAMEWORK_PATTERNS.items():
                if pattern in dep.lower():
                    if "framework" in detection and detection["framework"] not in info.frameworks:
                        info.frameworks.append(detection["framework"])
                    if "test_framework" in detection:
                        info.test_framework = detection["test_framework"]

        # Check Cargo.toml
        cargo = self.project_path / "Cargo.toml"
        if cargo.exists():
            try:
                content = cargo.read_text()
                for pattern, detection in self.FRAMEWORK_PATTERNS.items():
                    if pattern in content.lower():
                        if "framework" in detection and detection["framework"] not in info.frameworks:
                            info.frameworks.append(detection["framework"])
            except IOError:
                pass

    def _detect_entry_points(self, info: ProjectInfo):
        """Detect likely entry points."""
        entry_patterns = [
            "main.py", "app.py", "run.py", "__main__.py", "manage.py",
            "index.js", "index.ts", "app.js", "app.ts", "server.js", "server.ts",
            "main.rs", "main.go", "Main.java", "Program.cs", "main.cpp",
        ]

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.venv', 'venv'
            ]]

            for file in files:
                if file in entry_patterns:
                    rel_path = Path(root).relative_to(self.project_path) / file
                    info.entry_points.append(str(rel_path))

    def _count_files(self, info: ProjectInfo):
        """Count files and lines of code."""
        file_count = 0
        total_lines = 0

        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go',
                          '.java', '.cs', '.cpp', '.c', '.h', '.rb', '.php'}

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                'env', 'dist', 'build'
            ]]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in code_extensions:
                    file_count += 1
                    try:
                        total_lines += sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='ignore'))
                    except IOError:
                        pass

        info.file_count = file_count
        info.total_lines = total_lines

    def _find_todos(self, info: ProjectInfo):
        """Find TODO comments."""
        todo_count = 0
        todo_pattern = re.compile(r'(TODO|FIXME|XXX|HACK|BUG):', re.IGNORECASE)

        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', '.java', '.cs', '.cpp', '.c'}

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.venv', 'venv'
            ]]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in code_extensions:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        todo_count += len(todo_pattern.findall(content))
                    except IOError:
                        pass

        info.todos_found = todo_count

    def _check_tests_docs(self, info: ProjectInfo):
        """Check for tests and documentation."""
        test_dirs = ['tests', 'test', 'spec', '__tests__']
        doc_dirs = ['docs', 'doc', 'documentation']
        doc_files = ['README.md', 'README.rst', 'README.txt', 'CHANGELOG.md']

        for item in self.project_path.iterdir():
            if item.is_dir():
                if item.name.lower() in test_dirs:
                    info.has_tests = True
                if item.name.lower() in doc_dirs:
                    info.has_docs = True
            elif item.is_file():
                if item.name in doc_files:
                    info.has_docs = True

    def _detect_versions(self, info: ProjectInfo):
        """Detect runtime versions."""
        # Python version from pyproject.toml or .python-version
        pyproject = self.project_path / "pyproject.toml"
        python_version = self.project_path / ".python-version"

        if python_version.exists():
            try:
                info.python_version = python_version.read_text().strip()
            except IOError:
                pass

        if pyproject.exists() and not info.python_version:
            try:
                content = pyproject.read_text()
                match = re.search(r'python\s*[>=<]+\s*"?([0-9.]+)"?', content)
                if match:
                    info.python_version = match.group(1)
            except IOError:
                pass

        # Node version from .nvmrc or package.json
        nvmrc = self.project_path / ".nvmrc"
        package_json = self.project_path / "package.json"

        if nvmrc.exists():
            try:
                info.node_version = nvmrc.read_text().strip()
            except IOError:
                pass

        if package_json.exists() and not info.node_version:
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    engines = data.get("engines", {})
                    if "node" in engines:
                        info.node_version = engines["node"]
            except (json.JSONDecodeError, IOError):
                pass

    def format_report(self, info: ProjectInfo) -> str:
        """Format detection results as a report."""
        lines = [
            "=" * 60,
            f"  PROJECT ANALYSIS: {info.name}",
            "=" * 60,
            "",
            f"📁 Path: {info.path}",
            "",
            "📊 Overview:",
            f"   • Files: {info.file_count} code files",
            f"   • Lines: {info.total_lines:,} lines of code",
            f"   • TODOs: {info.todos_found} found",
            "",
            f"🔤 Languages: {', '.join(info.languages) if info.languages else 'None detected'}",
            f"   Primary: {info.primary_language}",
            "",
        ]

        if info.frameworks:
            lines.append(f"🏗️ Frameworks: {', '.join(info.frameworks)}")
            lines.append("")

        lines.append("🔧 Build & Dependencies:")
        if info.package_manager:
            lines.append(f"   • Package Manager: {info.package_manager}")
        if info.build_tool:
            lines.append(f"   • Build Tool: {info.build_tool}")
        if info.test_framework:
            lines.append(f"   • Test Framework: {info.test_framework}")
        if info.linters:
            lines.append(f"   • Linters: {', '.join(info.linters)}")
        lines.append("")

        if info.ci_cd:
            lines.append(f"🚀 CI/CD: {', '.join(info.ci_cd)}")
            lines.append("")

        if info.docker:
            lines.append("🐳 Docker: Yes")
            lines.append("")

        if info.version_control:
            lines.append(f"📝 Version Control: {info.version_control}")

        lines.append("")
        lines.append("✅ Checks:")
        lines.append(f"   • Has Tests: {'Yes' if info.has_tests else 'No'}")
        lines.append(f"   • Has Docs: {'Yes' if info.has_docs else 'No'}")

        if info.entry_points:
            lines.append("")
            lines.append("🚪 Entry Points:")
            for ep in info.entry_points[:5]:
                lines.append(f"   • {ep}")

        if info.python_version or info.node_version:
            lines.append("")
            lines.append("📌 Versions:")
            if info.python_version:
                lines.append(f"   • Python: {info.python_version}")
            if info.node_version:
                lines.append(f"   • Node: {info.node_version}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def detect_project(path: Optional[Path] = None) -> ProjectInfo:
    """Detect project information."""
    detector = ProjectDetector(path)
    return detector.detect()


def get_project_report(path: Optional[Path] = None) -> str:
    """Get formatted project report."""
    detector = ProjectDetector(path)
    info = detector.detect()
    return detector.format_report(info)
