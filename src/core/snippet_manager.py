"""Snippet Manager - Feature 23.

Save and reuse code snippets:
- Create snippets from selection
- Search snippets by tags/keywords
- Insert snippets with variables
- Share snippets
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Snippet:
    """A code snippet."""
    id: str
    name: str
    code: str
    language: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)  # ${var} placeholders
    created_at: str = ""
    updated_at: str = ""
    usage_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snippet":
        return cls(**data)


class SnippetManager:
    """Manage code snippets."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize snippet manager."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "snippets"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.snippets_file = self.storage_dir / "snippets.json"
        self.snippets: Dict[str, Snippet] = {}
        self._load()

    def _load(self):
        """Load snippets from storage."""
        if self.snippets_file.exists():
            try:
                data = json.loads(self.snippets_file.read_text(encoding="utf-8"))
                for snippet_data in data.get("snippets", []):
                    snippet = Snippet.from_dict(snippet_data)
                    self.snippets[snippet.id] = snippet
            except Exception:
                pass

    def _save(self):
        """Save snippets to storage."""
        data = {
            "version": "1.0",
            "snippets": [s.to_dict() for s in self.snippets.values()],
        }
        self.snippets_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    def _generate_id(self, name: str) -> str:
        """Generate unique ID for snippet."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{name}:{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _extract_variables(self, code: str) -> List[str]:
        """Extract ${var} placeholders from code."""
        import re
        pattern = r"\$\{(\w+)\}"
        matches = re.findall(pattern, code)
        return list(set(matches))

    def create(
        self,
        name: str,
        code: str,
        language: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Snippet:
        """
        Create a new snippet.

        Args:
            name: Snippet name
            code: Code content
            language: Programming language
            description: Description
            tags: Tags for searching

        Returns:
            Created Snippet
        """
        snippet = Snippet(
            id=self._generate_id(name),
            name=name,
            code=code,
            language=language,
            description=description,
            tags=tags or [],
            variables=self._extract_variables(code),
        )

        self.snippets[snippet.id] = snippet
        self._save()

        return snippet

    def get(self, snippet_id: str) -> Optional[Snippet]:
        """Get a snippet by ID."""
        return self.snippets.get(snippet_id)

    def get_by_name(self, name: str) -> Optional[Snippet]:
        """Get a snippet by name."""
        for snippet in self.snippets.values():
            if snippet.name.lower() == name.lower():
                return snippet
        return None

    def update(
        self,
        snippet_id: str,
        name: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Snippet]:
        """Update a snippet."""
        snippet = self.snippets.get(snippet_id)
        if not snippet:
            return None

        if name:
            snippet.name = name
        if code:
            snippet.code = code
            snippet.variables = self._extract_variables(code)
        if description:
            snippet.description = description
        if tags is not None:
            snippet.tags = tags

        snippet.updated_at = datetime.now().isoformat()
        self._save()

        return snippet

    def delete(self, snippet_id: str) -> bool:
        """Delete a snippet."""
        if snippet_id in self.snippets:
            del self.snippets[snippet_id]
            self._save()
            return True
        return False

    def list(
        self,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> List[Snippet]:
        """
        List snippets with optional filtering.

        Args:
            language: Filter by language
            tags: Filter by tags (any match)
            search: Search in name and description

        Returns:
            List of matching snippets
        """
        results = list(self.snippets.values())

        if language:
            results = [s for s in results if s.language.lower() == language.lower()]

        if tags:
            tags_lower = [t.lower() for t in tags]
            results = [s for s in results if any(t.lower() in tags_lower for t in s.tags)]

        if search:
            search_lower = search.lower()
            results = [
                s for s in results
                if search_lower in s.name.lower()
                or search_lower in s.description.lower()
                or any(search_lower in tag.lower() for tag in s.tags)
            ]

        # Sort by usage count (most used first)
        results.sort(key=lambda x: x.usage_count, reverse=True)

        return results

    def render(
        self,
        snippet_id: str,
        variables: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Render a snippet with variables.

        Args:
            snippet_id: Snippet ID or name
            variables: Variable values to substitute

        Returns:
            Rendered code
        """
        snippet = self.get(snippet_id) or self.get_by_name(snippet_id)
        if not snippet:
            return None

        code = snippet.code
        variables = variables or {}

        # Substitute variables
        for var_name in snippet.variables:
            placeholder = f"${{{var_name}}}"
            value = variables.get(var_name, placeholder)
            code = code.replace(placeholder, value)

        # Update usage count
        snippet.usage_count += 1
        snippet.updated_at = datetime.now().isoformat()
        self._save()

        return code

    def export_snippet(self, snippet_id: str) -> Optional[str]:
        """Export snippet as JSON string."""
        snippet = self.get(snippet_id)
        if snippet:
            return json.dumps(snippet.to_dict(), indent=2)
        return None

    def import_snippet(self, json_str: str) -> Optional[Snippet]:
        """Import snippet from JSON string."""
        try:
            data = json.loads(json_str)
            # Generate new ID to avoid conflicts
            data["id"] = self._generate_id(data.get("name", "imported"))
            snippet = Snippet.from_dict(data)
            self.snippets[snippet.id] = snippet
            self._save()
            return snippet
        except Exception:
            return None

    def get_languages(self) -> List[str]:
        """Get list of languages in snippets."""
        return list(set(s.language for s in self.snippets.values()))

    def get_tags(self) -> List[str]:
        """Get list of all tags."""
        tags = set()
        for snippet in self.snippets.values():
            tags.update(snippet.tags)
        return sorted(tags)

    def get_report(self) -> str:
        """Generate snippet manager report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  SNIPPET MANAGER")
        lines.append("=" * 50)
        lines.append("")

        lines.append(f"Total Snippets: {len(self.snippets)}")
        lines.append(f"Languages: {', '.join(self.get_languages()) or 'None'}")
        lines.append(f"Tags: {', '.join(self.get_tags()[:10]) or 'None'}")
        lines.append("")

        if self.snippets:
            lines.append("Recent Snippets:")
            sorted_snippets = sorted(
                self.snippets.values(),
                key=lambda x: x.updated_at,
                reverse=True
            )
            for s in sorted_snippets[:5]:
                lines.append(f"  - {s.name} ({s.language}) - {s.usage_count} uses")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)


# Built-in snippets
BUILTIN_SNIPPETS = [
    {
        "name": "python-main",
        "code": '''def main():
    """Main entry point."""
    ${code}


if __name__ == "__main__":
    main()
''',
        "language": "python",
        "description": "Python main block",
        "tags": ["python", "boilerplate", "main"],
    },
    {
        "name": "python-class",
        "code": '''class ${ClassName}:
    """${description}"""

    def __init__(self${params}):
        """Initialize ${ClassName}."""
        ${init_code}

    def ${method_name}(self):
        """${method_description}"""
        ${method_code}
''',
        "language": "python",
        "description": "Python class template",
        "tags": ["python", "class", "oop"],
    },
    {
        "name": "python-dataclass",
        "code": '''from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ${ClassName}:
    """${description}"""
    ${field_name}: ${field_type}
''',
        "language": "python",
        "description": "Python dataclass template",
        "tags": ["python", "dataclass", "typing"],
    },
    {
        "name": "python-test",
        "code": '''import pytest

class Test${ClassName}:
    """Tests for ${ClassName}."""

    def test_${test_name}(self):
        """Test ${test_description}."""
        # Arrange
        ${arrange}

        # Act
        ${act}

        # Assert
        ${assert}
''',
        "language": "python",
        "description": "Python pytest class",
        "tags": ["python", "test", "pytest"],
    },
    {
        "name": "python-fastapi-endpoint",
        "code": '''@app.${method}("/${path}")
async def ${function_name}(${params}):
    """${description}"""
    ${code}
    return ${response}
''',
        "language": "python",
        "description": "FastAPI endpoint",
        "tags": ["python", "fastapi", "api"],
    },
    {
        "name": "js-function",
        "code": '''/**
 * ${description}
 * @param {${param_type}} ${param_name} - ${param_description}
 * @returns {${return_type}} ${return_description}
 */
function ${functionName}(${params}) {
    ${code}
}
''',
        "language": "javascript",
        "description": "JavaScript function with JSDoc",
        "tags": ["javascript", "function", "jsdoc"],
    },
    {
        "name": "react-component",
        "code": '''import React from 'react';

interface ${ComponentName}Props {
    ${props}
}

export const ${ComponentName}: React.FC<${ComponentName}Props> = ({ ${destructured} }) => {
    return (
        <div className="${className}">
            ${content}
        </div>
    );
};
''',
        "language": "typescript",
        "description": "React functional component with TypeScript",
        "tags": ["react", "typescript", "component"],
    },
    {
        "name": "go-handler",
        "code": '''func ${handlerName}(w http.ResponseWriter, r *http.Request) {
    ${code}

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(${response})
}
''',
        "language": "go",
        "description": "Go HTTP handler",
        "tags": ["go", "http", "handler"],
    },
]


# Global instance
_snippet_manager: Optional[SnippetManager] = None


def get_snippet_manager() -> SnippetManager:
    """Get or create snippet manager."""
    global _snippet_manager
    if _snippet_manager is None:
        _snippet_manager = SnippetManager()
        # Add built-in snippets if empty
        if not _snippet_manager.snippets:
            for snippet_data in BUILTIN_SNIPPETS:
                _snippet_manager.create(**snippet_data)
    return _snippet_manager


# Convenience functions
def create_snippet(
    name: str,
    code: str,
    language: str,
    description: str = "",
    tags: Optional[List[str]] = None,
) -> Snippet:
    """Create a new snippet."""
    return get_snippet_manager().create(name, code, language, description, tags)


def list_snippets(
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
    search: Optional[str] = None,
) -> List[Snippet]:
    """List snippets."""
    return get_snippet_manager().list(language, tags, search)


def render_snippet(snippet_id: str, variables: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Render a snippet with variables."""
    return get_snippet_manager().render(snippet_id, variables)
