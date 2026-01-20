"""Project Creator - Feature 21.

Cross-platform project scaffolding:
- Create projects in any directory
- Works on Windows, Linux, macOS
- Multiple project templates
- Auto-detect best practices
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ProjectType(Enum):
    """Supported project types."""
    PYTHON = "python"
    PYTHON_API = "python-api"
    PYTHON_CLI = "python-cli"
    NODE = "node"
    NODE_API = "node-api"
    REACT = "react"
    VUE = "vue"
    GO = "go"
    RUST = "rust"
    GENERIC = "generic"


@dataclass
class ProjectConfig:
    """Project configuration."""
    name: str
    project_type: ProjectType
    target_dir: Path
    description: str = ""
    author: str = ""
    license: str = "MIT"
    git_init: bool = True
    create_venv: bool = True
    install_deps: bool = False

    @property
    def project_path(self) -> Path:
        """Full path to project."""
        return self.target_dir / self.name


@dataclass
class CreationResult:
    """Result of project creation."""
    success: bool
    project_path: Path
    files_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    message: str = ""


class ProjectCreator:
    """Cross-platform project creator."""

    # Project templates
    TEMPLATES = {
        ProjectType.PYTHON: {
            "files": {
                "main.py": '''"""Main entry point."""


def main():
    """Main function."""
    print("Hello, {name}!")


if __name__ == "__main__":
    main()
''',
                "requirements.txt": "# Add your dependencies here\n",
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\npython main.py\n```\n",
                ".gitignore": "__pycache__/\n*.py[cod]\n*$py.class\n.venv/\nvenv/\nenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
            },
            "dirs": ["src", "tests"],
        },
        ProjectType.PYTHON_API: {
            "files": {
                "main.py": '''"""FastAPI Application."""

from fastapi import FastAPI

app = FastAPI(title="{name}", description="{description}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {name}"}}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {{"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.23.0\npydantic>=2.0.0\n",
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Running\n\n```bash\nuvicorn main:app --reload\n```\n\n## API Docs\n\nVisit http://localhost:8000/docs\n",
                ".gitignore": "__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.env\n",
                ".env.example": "# Environment variables\nDEBUG=true\nPORT=8000\n",
            },
            "dirs": ["app", "app/routers", "app/models", "tests"],
        },
        ProjectType.PYTHON_CLI: {
            "files": {
                "cli.py": '''"""CLI Application."""

import argparse
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="{name}",
        description="{description}"
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("command", nargs="?", help="Command to run")

    args = parser.parse_args()

    if args.command:
        print(f"Running command: {{args.command}}")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
                "requirements.txt": "# CLI dependencies\nrich>=13.0.0\nclick>=8.0.0\n",
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\npython cli.py --help\npython cli.py <command>\n```\n",
                ".gitignore": "__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.env\n",
                "setup.py": '''"""Setup script."""

from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    description="{description}",
    author="{author}",
    packages=find_packages(),
    entry_points={{
        "console_scripts": [
            "{name}=cli:main",
        ],
    }},
    python_requires=">=3.8",
)
''',
            },
            "dirs": ["src", "tests"],
        },
        ProjectType.NODE: {
            "files": {
                "index.js": '''/**
 * {name}
 * {description}
 */

console.log("Hello from {name}!");

module.exports = {
  name: "{name}",
};
''',
                "package.json": '''{
  "name": "{name}",
  "version": "1.0.0",
  "description": "{description}",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "echo \\"No tests yet\\" && exit 0"
  },
  "keywords": [],
  "author": "{author}",
  "license": "{license}"
}
''',
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Usage\n\n```bash\nnpm start\n```\n",
                ".gitignore": "node_modules/\n.env\n*.log\ndist/\ncoverage/\n",
            },
            "dirs": ["src", "tests"],
        },
        ProjectType.NODE_API: {
            "files": {
                "index.js": '''/**
 * {name} - Express API
 * {description}
 */

const express = require("express");
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get("/", (req, res) => {
  res.json({ message: "Welcome to {name}" });
});

app.get("/health", (req, res) => {
  res.json({ status: "healthy" });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
''',
                "package.json": '''{
  "name": "{name}",
  "version": "1.0.0",
  "description": "{description}",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  },
  "keywords": ["api", "express"],
  "author": "{author}",
  "license": "{license}",
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.0",
    "jest": "^29.0.0"
  }
}
''',
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Development\n\n```bash\nnpm run dev\n```\n\n## Production\n\n```bash\nnpm start\n```\n\n## API Endpoints\n\n- `GET /` - Welcome message\n- `GET /health` - Health check\n",
                ".gitignore": "node_modules/\n.env\n*.log\ndist/\ncoverage/\n",
                ".env.example": "PORT=3000\nNODE_ENV=development\n",
            },
            "dirs": ["routes", "models", "middleware", "tests"],
        },
        ProjectType.REACT: {
            "files": {
                "package.json": '''{
  "name": "{name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
''',
                "vite.config.js": '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
''',
                "index.html": '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
                "src/main.jsx": '''import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',
                "src/App.jsx": '''import React from "react";

function App() {
  return (
    <div className="app">
      <h1>{name}</h1>
      <p>{description}</p>
    </div>
  );
}

export default App;
''',
                "src/index.css": '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

h1 {
  color: #333;
  margin-bottom: 1rem;
}
''',
                "README.md": "# {name}\n\n{description}\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Development\n\n```bash\nnpm run dev\n```\n\n## Build\n\n```bash\nnpm run build\n```\n",
                ".gitignore": "node_modules/\ndist/\n.env\n*.log\n",
            },
            "dirs": ["src/components", "src/hooks", "src/utils", "public"],
        },
        ProjectType.GO: {
            "files": {
                "main.go": '''package main

import "fmt"

func main() {
	fmt.Println("Hello from {name}!")
}
''',
                "go.mod": '''module {name}

go 1.21
''',
                "README.md": "# {name}\n\n{description}\n\n## Build\n\n```bash\ngo build\n```\n\n## Run\n\n```bash\ngo run main.go\n```\n",
                ".gitignore": "*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n*.test\n*.out\nvendor/\n",
            },
            "dirs": ["cmd", "pkg", "internal"],
        },
        ProjectType.RUST: {
            "files": {
                "Cargo.toml": '''[package]
name = "{name}"
version = "0.1.0"
edition = "2021"
description = "{description}"
authors = ["{author}"]
license = "{license}"

[dependencies]
''',
                "src/main.rs": '''fn main() {
    println!("Hello from {name}!");
}
''',
                "README.md": "# {name}\n\n{description}\n\n## Build\n\n```bash\ncargo build\n```\n\n## Run\n\n```bash\ncargo run\n```\n",
                ".gitignore": "/target\nCargo.lock\n",
            },
            "dirs": ["src"],
        },
        ProjectType.GENERIC: {
            "files": {
                "README.md": "# {name}\n\n{description}\n\n## Getting Started\n\nAdd your project files here.\n",
                ".gitignore": "# Add files to ignore\n*.log\n*.tmp\n.env\n",
            },
            "dirs": ["src", "docs"],
        },
    }

    def __init__(self):
        """Initialize project creator."""
        self.platform = sys.platform

    def normalize_path(self, path: str) -> Path:
        """
        Normalize path for current OS.

        Handles:
        - Windows paths (C:\\Users\\...)
        - Unix paths (/home/user/...)
        - Relative paths
        - Home directory expansion (~)
        """
        # Expand ~ to home directory
        if path.startswith("~"):
            path = os.path.expanduser(path)

        # Convert to Path object (handles OS-specific separators)
        p = Path(path)

        # Make absolute if relative
        if not p.is_absolute():
            p = Path.cwd() / p

        # Resolve any .. or . components
        p = p.resolve()

        return p

    def validate_directory(self, path: Path) -> tuple[bool, str]:
        """
        Validate target directory.

        Returns:
            (is_valid, error_message)
        """
        # Check if parent exists
        if not path.parent.exists():
            return False, f"Parent directory does not exist: {path.parent}"

        # Check if we can write to parent
        if not os.access(path.parent, os.W_OK):
            return False, f"No write permission for: {path.parent}"

        # Check if project already exists
        if path.exists():
            return False, f"Directory already exists: {path}"

        return True, ""

    def create_project(self, config: ProjectConfig) -> CreationResult:
        """
        Create a new project.

        Args:
            config: Project configuration

        Returns:
            CreationResult with status and details
        """
        result = CreationResult(
            success=False,
            project_path=config.project_path,
        )

        # Validate directory
        is_valid, error = self.validate_directory(config.project_path)
        if not is_valid:
            result.errors.append(error)
            result.message = error
            return result

        try:
            # Create project directory
            config.project_path.mkdir(parents=True, exist_ok=True)
            result.files_created.append(str(config.project_path))

            # Get template
            template = self.TEMPLATES.get(config.project_type, self.TEMPLATES[ProjectType.GENERIC])

            # Create subdirectories
            for dir_name in template.get("dirs", []):
                dir_path = config.project_path / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                result.files_created.append(str(dir_path))

            # Create files
            for file_name, content in template.get("files", {}).items():
                file_path = config.project_path / file_name

                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Replace placeholders
                content = content.format(
                    name=config.name,
                    description=config.description or f"A {config.project_type.value} project",
                    author=config.author or "Developer",
                    license=config.license,
                )

                # Write file
                file_path.write_text(content, encoding="utf-8")
                result.files_created.append(str(file_path))

            # Initialize git if requested
            if config.git_init:
                git_result = self._init_git(config.project_path)
                if git_result:
                    result.files_created.append(str(config.project_path / ".git"))

            # Create virtual environment for Python projects
            if config.create_venv and config.project_type in [
                ProjectType.PYTHON,
                ProjectType.PYTHON_API,
                ProjectType.PYTHON_CLI
            ]:
                self._create_venv(config.project_path)
                result.files_created.append(str(config.project_path / ".venv"))

            result.success = True
            result.message = f"Project '{config.name}' created successfully at {config.project_path}"

        except Exception as e:
            result.errors.append(str(e))
            result.message = f"Failed to create project: {e}"

            # Cleanup on failure
            if config.project_path.exists():
                try:
                    shutil.rmtree(config.project_path)
                except:
                    pass

        return result

    def _init_git(self, path: Path) -> bool:
        """Initialize git repository."""
        try:
            import subprocess
            subprocess.run(
                ["git", "init"],
                cwd=path,
                capture_output=True,
                check=True,
            )
            return True
        except:
            return False

    def _create_venv(self, path: Path) -> bool:
        """Create Python virtual environment."""
        try:
            import subprocess
            venv_path = path / ".venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                check=True,
            )
            return True
        except:
            return False

    def list_project_types(self) -> List[Dict[str, str]]:
        """List available project types."""
        return [
            {"type": ProjectType.PYTHON.value, "description": "Basic Python project"},
            {"type": ProjectType.PYTHON_API.value, "description": "FastAPI REST API"},
            {"type": ProjectType.PYTHON_CLI.value, "description": "Python CLI application"},
            {"type": ProjectType.NODE.value, "description": "Basic Node.js project"},
            {"type": ProjectType.NODE_API.value, "description": "Express.js REST API"},
            {"type": ProjectType.REACT.value, "description": "React + Vite application"},
            {"type": ProjectType.VUE.value, "description": "Vue.js application"},
            {"type": ProjectType.GO.value, "description": "Go project"},
            {"type": ProjectType.RUST.value, "description": "Rust project"},
            {"type": ProjectType.GENERIC.value, "description": "Generic project structure"},
        ]

    def get_report(self, result: CreationResult) -> str:
        """Generate creation report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  PROJECT CREATION REPORT")
        lines.append("=" * 50)
        lines.append("")

        status = "[OK]" if result.success else "[FAILED]"
        lines.append(f"Status: {status}")
        lines.append(f"Path: {result.project_path}")
        lines.append("")

        if result.success:
            lines.append(f"Files Created: {len(result.files_created)}")
            for f in result.files_created[:10]:
                lines.append(f"  - {Path(f).name}")
            if len(result.files_created) > 10:
                lines.append(f"  ... and {len(result.files_created) - 10} more")

        if result.errors:
            lines.append("")
            lines.append("Errors:")
            for e in result.errors:
                lines.append(f"  - {e}")

        lines.append("")
        lines.append(f"Message: {result.message}")
        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)


# Global instance
_project_creator: Optional[ProjectCreator] = None


def get_project_creator() -> ProjectCreator:
    """Get or create project creator instance."""
    global _project_creator
    if _project_creator is None:
        _project_creator = ProjectCreator()
    return _project_creator


# Convenience functions
def create_project(
    name: str,
    target_dir: str,
    project_type: str = "python",
    description: str = "",
    author: str = "",
    git_init: bool = True,
) -> CreationResult:
    """
    Create a new project.

    Args:
        name: Project name
        target_dir: Directory to create project in
        project_type: Type of project (python, python-api, node, react, go, rust)
        description: Project description
        author: Author name
        git_init: Initialize git repository

    Returns:
        CreationResult with status
    """
    creator = get_project_creator()

    # Parse project type
    try:
        ptype = ProjectType(project_type)
    except ValueError:
        ptype = ProjectType.GENERIC

    # Normalize path
    target_path = creator.normalize_path(target_dir)

    # Create config
    config = ProjectConfig(
        name=name,
        project_type=ptype,
        target_dir=target_path,
        description=description,
        author=author,
        git_init=git_init,
    )

    return creator.create_project(config)


def list_project_types() -> List[Dict[str, str]]:
    """List available project types."""
    return get_project_creator().list_project_types()
