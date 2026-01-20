"""Code Templates - Feature 15.

Code scaffolding and templates:
- Project templates
- File templates
- Component generators
- Boilerplate generation
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Template:
    """A code template."""
    name: str
    description: str
    language: str
    category: str
    content: str
    variables: List[str] = field(default_factory=list)


# Built-in templates
TEMPLATES = {
    # Python templates
    "python_class": Template(
        name="python_class",
        description="Python class with docstring",
        language="python",
        category="class",
        variables=["class_name", "description"],
        content='''"""${description}"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ${class_name}:
    """${description}"""

    def __init__(self):
        """Initialize ${class_name}."""
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"${class_name}()"
''',
    ),
    "python_function": Template(
        name="python_function",
        description="Python function with docstring",
        language="python",
        category="function",
        variables=["function_name", "description"],
        content='''def ${function_name}() -> None:
    """${description}

    Args:
        None

    Returns:
        None
    """
    pass
''',
    ),
    "python_async_function": Template(
        name="python_async_function",
        description="Async Python function",
        language="python",
        category="function",
        variables=["function_name", "description"],
        content='''async def ${function_name}() -> None:
    """${description}

    Args:
        None

    Returns:
        None
    """
    pass
''',
    ),
    "python_test": Template(
        name="python_test",
        description="Python test file with pytest",
        language="python",
        category="test",
        variables=["module_name"],
        content='''"""Tests for ${module_name}."""

import pytest
from ${module_name} import *


class Test${module_name}:
    """Test suite for ${module_name}."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_example(self):
        """Test example case."""
        assert True

    def test_another_example(self):
        """Test another case."""
        assert True
''',
    ),
    "python_cli": Template(
        name="python_cli",
        description="Python CLI application",
        language="python",
        category="application",
        variables=["app_name", "description"],
        content='''"""${description}"""

import argparse
import sys


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="${description}"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    print("${app_name} running...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
    ),
    "python_api": Template(
        name="python_api",
        description="FastAPI endpoint",
        language="python",
        category="api",
        variables=["resource_name"],
        content='''"""API endpoints for ${resource_name}."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter(prefix="/${resource_name}", tags=["${resource_name}"])


class ${resource_name}Base(BaseModel):
    """Base schema for ${resource_name}."""
    name: str


class ${resource_name}Create(${resource_name}Base):
    """Schema for creating ${resource_name}."""
    pass


class ${resource_name}Response(${resource_name}Base):
    """Response schema for ${resource_name}."""
    id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[${resource_name}Response])
async def list_${resource_name}():
    """List all ${resource_name}."""
    return []


@router.get("/{id}", response_model=${resource_name}Response)
async def get_${resource_name}(id: int):
    """Get ${resource_name} by ID."""
    raise HTTPException(status_code=404, detail="Not found")


@router.post("/", response_model=${resource_name}Response, status_code=status.HTTP_201_CREATED)
async def create_${resource_name}(data: ${resource_name}Create):
    """Create new ${resource_name}."""
    return ${resource_name}Response(id=1, **data.dict())


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_${resource_name}(id: int):
    """Delete ${resource_name}."""
    pass
''',
    ),
    # TypeScript templates
    "ts_component": Template(
        name="ts_component",
        description="React TypeScript component",
        language="typescript",
        category="component",
        variables=["component_name"],
        content='''import React from 'react';

interface ${component_name}Props {
  title?: string;
  children?: React.ReactNode;
}

export const ${component_name}: React.FC<${component_name}Props> = ({
  title,
  children,
}) => {
  return (
    <div className="${component_name}">
      {title && <h2>{title}</h2>}
      {children}
    </div>
  );
};

export default ${component_name};
''',
    ),
    "ts_hook": Template(
        name="ts_hook",
        description="React custom hook",
        language="typescript",
        category="hook",
        variables=["hook_name"],
        content='''import { useState, useEffect, useCallback } from 'react';

interface Use${hook_name}Options {
  initialValue?: string;
}

interface Use${hook_name}Return {
  value: string;
  setValue: (value: string) => void;
  reset: () => void;
}

export function use${hook_name}(
  options: Use${hook_name}Options = {}
): Use${hook_name}Return {
  const { initialValue = '' } = options;
  const [value, setValue] = useState(initialValue);

  const reset = useCallback(() => {
    setValue(initialValue);
  }, [initialValue]);

  useEffect(() => {
    // Side effects here
  }, [value]);

  return {
    value,
    setValue,
    reset,
  };
}

export default use${hook_name};
''',
    ),
    "ts_service": Template(
        name="ts_service",
        description="TypeScript service class",
        language="typescript",
        category="service",
        variables=["service_name"],
        content='''/**
 * ${service_name} Service
 */

export interface ${service_name}Config {
  baseUrl?: string;
  timeout?: number;
}

export class ${service_name}Service {
  private config: ${service_name}Config;

  constructor(config: ${service_name}Config = {}) {
    this.config = {
      baseUrl: '/api',
      timeout: 5000,
      ...config,
    };
  }

  async getAll<T>(): Promise<T[]> {
    // Implementation
    return [];
  }

  async getById<T>(id: string | number): Promise<T | null> {
    // Implementation
    return null;
  }

  async create<T>(data: Partial<T>): Promise<T> {
    // Implementation
    throw new Error('Not implemented');
  }

  async update<T>(id: string | number, data: Partial<T>): Promise<T> {
    // Implementation
    throw new Error('Not implemented');
  }

  async delete(id: string | number): Promise<void> {
    // Implementation
  }
}

export default ${service_name}Service;
''',
    ),
    # Go templates
    "go_handler": Template(
        name="go_handler",
        description="Go HTTP handler",
        language="go",
        category="handler",
        variables=["handler_name", "resource_name"],
        content='''package handlers

import (
    "encoding/json"
    "net/http"
)

type ${handler_name}Handler struct {
    // Dependencies
}

func New${handler_name}Handler() *${handler_name}Handler {
    return &${handler_name}Handler{}
}

func (h *${handler_name}Handler) List(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode([]interface{}{})
}

func (h *${handler_name}Handler) Get(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    http.NotFound(w, r)
}

func (h *${handler_name}Handler) Create(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(map[string]string{"status": "created"})
}

func (h *${handler_name}Handler) Delete(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusNoContent)
}
''',
    ),
}


class TemplateEngine:
    """Code template engine."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize template engine."""
        self.working_dir = working_dir or Path.cwd()
        self.templates = dict(TEMPLATES)
        self._load_custom_templates()

    def _load_custom_templates(self):
        """Load custom templates from project."""
        templates_dir = self.working_dir / ".agent" / "templates"
        if not templates_dir.exists():
            return

        for template_file in templates_dir.glob("*.template"):
            try:
                content = template_file.read_text(encoding='utf-8')
                name = template_file.stem

                # Parse template metadata from first comment
                meta = self._parse_template_meta(content)

                self.templates[name] = Template(
                    name=name,
                    description=meta.get("description", name),
                    language=meta.get("language", "text"),
                    category=meta.get("category", "custom"),
                    variables=meta.get("variables", []),
                    content=content,
                )
            except IOError:
                pass

    def _parse_template_meta(self, content: str) -> Dict[str, Any]:
        """Parse template metadata from header."""
        meta = {}
        lines = content.splitlines()

        for line in lines:
            if line.startswith("#"):
                match = re.match(r'#\s*(\w+):\s*(.+)', line)
                if match:
                    key = match.group(1).lower()
                    value = match.group(2).strip()
                    if key == "variables":
                        meta[key] = [v.strip() for v in value.split(",")]
                    else:
                        meta[key] = value
            else:
                break

        return meta

    def list_templates(self, language: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """List available templates."""
        result = []

        for name, template in self.templates.items():
            if language and template.language != language:
                continue
            if category and template.category != category:
                continue

            result.append({
                "name": name,
                "description": template.description,
                "language": template.language,
                "category": template.category,
                "variables": template.variables,
            })

        return sorted(result, key=lambda x: (x["language"], x["category"], x["name"]))

    def render(self, template_name: str, variables: Dict[str, str]) -> str:
        """
        Render a template with variables.

        Args:
            template_name: Name of template
            variables: Variable values

        Returns:
            Rendered template content
        """
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self.templates[template_name]
        content = template.content

        # Replace variables
        for var in template.variables:
            placeholder = "${" + var + "}"
            value = variables.get(var, var)
            content = content.replace(placeholder, value)

        return content

    def create_file(
        self,
        template_name: str,
        output_path: str,
        variables: Dict[str, str],
    ) -> Path:
        """
        Create a file from template.

        Args:
            template_name: Name of template
            output_path: Output file path
            variables: Variable values

        Returns:
            Path to created file
        """
        content = self.render(template_name, variables)

        path = Path(output_path)
        if not path.is_absolute():
            path = self.working_dir / output_path

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding='utf-8')
        return path

    def create_project(
        self,
        project_type: str,
        project_name: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Create a project from templates.

        Args:
            project_type: Type of project (python, react, fastapi, etc.)
            project_name: Name of project
            output_dir: Output directory

        Returns:
            Path to created project
        """
        output = output_dir or (self.working_dir / project_name)
        output.mkdir(parents=True, exist_ok=True)

        if project_type == "python":
            self._create_python_project(output, project_name)
        elif project_type == "react":
            self._create_react_project(output, project_name)
        elif project_type == "fastapi":
            self._create_fastapi_project(output, project_name)

        return output

    def _create_python_project(self, output: Path, name: str):
        """Create Python project structure."""
        # Create directories
        (output / "src" / name.replace("-", "_")).mkdir(parents=True, exist_ok=True)
        (output / "tests").mkdir(exist_ok=True)

        # Create files
        (output / "src" / name.replace("-", "_") / "__init__.py").write_text(
            f'"""{ name } package."""\n\n__version__ = "0.1.0"\n'
        )

        (output / "pyproject.toml").write_text(f'''[project]
name = "{name}"
version = "0.1.0"
description = "A Python project"
requires-python = ">=3.9"

[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]

[tool.pytest.ini_options]
testpaths = ["tests"]
''')

        (output / "README.md").write_text(f"# {name}\n\nA Python project.\n")

    def _create_react_project(self, output: Path, name: str):
        """Create React project structure."""
        (output / "src" / "components").mkdir(parents=True, exist_ok=True)
        (output / "src" / "hooks").mkdir(exist_ok=True)
        (output / "src" / "services").mkdir(exist_ok=True)

        (output / "package.json").write_text(f'''{{
  "name": "{name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest"
  }}
}}
''')

    def _create_fastapi_project(self, output: Path, name: str):
        """Create FastAPI project structure."""
        pkg = name.replace("-", "_")
        (output / "src" / pkg / "api").mkdir(parents=True, exist_ok=True)
        (output / "src" / pkg / "models").mkdir(exist_ok=True)
        (output / "tests").mkdir(exist_ok=True)

        (output / "src" / pkg / "__init__.py").write_text("")
        (output / "src" / pkg / "main.py").write_text('''"""FastAPI application."""

from fastapi import FastAPI

app = FastAPI(title="API")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
''')

    def get_template_report(self) -> str:
        """Generate template catalog report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  CODE TEMPLATES")
        lines.append("=" * 50)

        templates = self.list_templates()
        by_language: Dict[str, List] = {}

        for t in templates:
            lang = t["language"]
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(t)

        for lang, templates in sorted(by_language.items()):
            lines.append(f"\n{lang.upper()}:")
            for t in templates:
                lines.append(f"  - {t['name']}: {t['description']}")
                if t['variables']:
                    lines.append(f"    Variables: {', '.join(t['variables'])}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


# Global instance
_template_engine: Optional[TemplateEngine] = None


def get_template_engine(working_dir: Optional[Path] = None) -> TemplateEngine:
    """Get or create template engine."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine(working_dir)
    return _template_engine


# Convenience functions
def list_templates(language: Optional[str] = None) -> List[Dict]:
    """List available templates."""
    return get_template_engine().list_templates(language)


def render_template(template_name: str, variables: Dict[str, str]) -> str:
    """Render a template."""
    return get_template_engine().render(template_name, variables)


def create_from_template(
    template_name: str,
    output_path: str,
    variables: Dict[str, str],
) -> Path:
    """Create file from template."""
    return get_template_engine().create_file(template_name, output_path, variables)
