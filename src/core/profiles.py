"""Profiles & Presets System - Feature 20.

Save and load different configurations:
- Model preferences
- Tool settings
- Project presets
- Quick switching
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

from src.config.settings import get_settings


@dataclass
class Profile:
    """A configuration profile."""
    name: str
    description: str = ""
    created_at: str = ""
    updated_at: str = ""

    # Model settings
    model: str = ""
    temperature: float = 0.1
    max_tokens: int = 4096

    # Agent settings
    max_iterations: int = 50
    timeout: int = 300

    # Tools
    enabled_tools: List[str] = field(default_factory=list)
    disabled_tools: List[str] = field(default_factory=list)

    # Plugins
    plugins: List[str] = field(default_factory=list)

    # Project settings
    working_dir: str = ""
    auto_index: bool = True
    watch_mode: bool = False

    # Display settings
    diff_mode: bool = False
    verbose: bool = False
    show_metrics: bool = True

    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


# Built-in presets
BUILTIN_PRESETS = {
    "default": Profile(
        name="default",
        description="Default balanced settings",
        model="ollama/gpt-oss:20b",
        temperature=0.1,
    ),
    "fast": Profile(
        name="fast",
        description="Fast responses with smaller model",
        model="ollama/llama3:8b",
        temperature=0.1,
        max_tokens=2048,
        timeout=60,
    ),
    "creative": Profile(
        name="creative",
        description="Higher temperature for creative tasks",
        model="ollama/gpt-oss:20b",
        temperature=0.7,
        max_tokens=4096,
    ),
    "precise": Profile(
        name="precise",
        description="Low temperature for precise code generation",
        model="ollama/gpt-oss:20b",
        temperature=0.0,
        max_tokens=4096,
    ),
    "debug": Profile(
        name="debug",
        description="Debugging mode with verbose output",
        model="ollama/gpt-oss:20b",
        verbose=True,
        show_metrics=True,
        diff_mode=True,
    ),
    "review": Profile(
        name="review",
        description="Code review focused settings",
        model="ollama/gpt-oss:20b",
        diff_mode=True,
        enabled_tools=["code_review", "analyze_error", "diagnose_file"],
    ),
    "backend": Profile(
        name="backend",
        description="Backend development preset",
        model="ollama/gpt-oss:20b",
        enabled_tools=["run_terminal_command", "read_file", "edit_file", "git_status", "git_commit", "test_project", "build_project"],
    ),
    "frontend": Profile(
        name="frontend",
        description="Frontend development preset",
        model="ollama/gpt-oss:20b",
        enabled_tools=["read_file", "write_file", "edit_file", "run_terminal_command", "search_files"],
    ),
}


class ProfileManager:
    """Manage configuration profiles."""

    def __init__(self):
        """Initialize profile manager."""
        settings = get_settings()
        self.profiles_dir = settings.data_dir / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.current_profile: Optional[str] = None
        self.profiles: Dict[str, Profile] = {}

        # Load profiles
        self._load_profiles()

    def _load_profiles(self):
        """Load all profiles from disk."""
        # Add built-in presets
        self.profiles.update(BUILTIN_PRESETS)

        # Load custom profiles
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile = Profile(**data)
                    self.profiles[profile.name] = profile
            except (json.JSONDecodeError, IOError, TypeError):
                pass

        # Load current profile setting
        current_file = self.profiles_dir / ".current"
        if current_file.exists():
            try:
                self.current_profile = current_file.read_text().strip()
            except IOError:
                pass

    def _save_profile(self, profile: Profile):
        """Save a profile to disk."""
        profile.updated_at = datetime.now().isoformat()
        profile_file = self.profiles_dir / f"{profile.name}.json"
        try:
            with open(profile_file, 'w') as f:
                json.dump(asdict(profile), f, indent=2)
        except IOError:
            pass

    def _save_current(self):
        """Save current profile selection."""
        current_file = self.profiles_dir / ".current"
        try:
            current_file.write_text(self.current_profile or "")
        except IOError:
            pass

    def create(
        self,
        name: str,
        description: str = "",
        base_profile: Optional[str] = None,
        **kwargs
    ) -> Profile:
        """
        Create a new profile.

        Args:
            name: Profile name
            description: Profile description
            base_profile: Optional profile to base on
            **kwargs: Profile settings

        Returns:
            Created profile
        """
        if base_profile and base_profile in self.profiles:
            base = self.profiles[base_profile]
            profile_data = asdict(base)
            profile_data.update(kwargs)
            profile_data["name"] = name
            profile_data["description"] = description or base.description
            profile_data["created_at"] = datetime.now().isoformat()
            profile = Profile(**profile_data)
        else:
            profile = Profile(name=name, description=description, **kwargs)

        self.profiles[name] = profile
        self._save_profile(profile)
        return profile

    def update(self, name: str, **kwargs) -> Optional[Profile]:
        """Update an existing profile."""
        if name not in self.profiles:
            return None

        if name in BUILTIN_PRESETS:
            # Can't modify built-in presets, create a copy
            return self.create(f"{name}_custom", base_profile=name, **kwargs)

        profile = self.profiles[name]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self._save_profile(profile)
        return profile

    def delete(self, name: str) -> bool:
        """Delete a profile."""
        if name in BUILTIN_PRESETS:
            return False  # Can't delete built-in

        if name not in self.profiles:
            return False

        del self.profiles[name]

        profile_file = self.profiles_dir / f"{name}.json"
        if profile_file.exists():
            profile_file.unlink()

        if self.current_profile == name:
            self.current_profile = None
            self._save_current()

        return True

    def get(self, name: str) -> Optional[Profile]:
        """Get a profile by name."""
        return self.profiles.get(name)

    def list(self) -> List[Dict]:
        """List all profiles."""
        result = []
        for name, profile in self.profiles.items():
            result.append({
                "name": name,
                "description": profile.description,
                "model": profile.model,
                "builtin": name in BUILTIN_PRESETS,
                "current": name == self.current_profile,
            })
        return sorted(result, key=lambda x: (not x["builtin"], x["name"]))

    def switch(self, name: str) -> Optional[Profile]:
        """
        Switch to a profile.

        Args:
            name: Profile name to switch to

        Returns:
            Profile if successful
        """
        if name not in self.profiles:
            return None

        self.current_profile = name
        self._save_current()
        return self.profiles[name]

    def get_current(self) -> Optional[Profile]:
        """Get currently active profile."""
        if self.current_profile and self.current_profile in self.profiles:
            return self.profiles[self.current_profile]
        return self.profiles.get("default")

    def export(self, name: str, path: Path) -> bool:
        """Export a profile to a file."""
        if name not in self.profiles:
            return False

        try:
            with open(path, 'w') as f:
                json.dump(asdict(self.profiles[name]), f, indent=2)
            return True
        except IOError:
            return False

    def import_profile(self, path: Path) -> Optional[Profile]:
        """Import a profile from a file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                profile = Profile(**data)

                # Avoid overwriting built-in
                if profile.name in BUILTIN_PRESETS:
                    profile.name = f"{profile.name}_imported"

                self.profiles[profile.name] = profile
                self._save_profile(profile)
                return profile
        except (json.JSONDecodeError, IOError, TypeError):
            return None

    def apply_to_settings(self, profile: Profile) -> Dict[str, Any]:
        """
        Get settings dict from profile.

        Returns:
            Dict that can be used to configure the agent
        """
        return {
            "model": profile.model,
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
            "timeout": profile.timeout,
            "max_iterations": profile.max_iterations,
            "enabled_tools": profile.enabled_tools,
            "disabled_tools": profile.disabled_tools,
            "plugins": profile.plugins,
            "diff_mode": profile.diff_mode,
            "verbose": profile.verbose,
        }


# Global profile manager
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get or create profile manager."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


# Convenience functions
def create_profile(name: str, **kwargs) -> Profile:
    """Create a new profile."""
    return get_profile_manager().create(name, **kwargs)


def switch_profile(name: str) -> Optional[Profile]:
    """Switch to a profile."""
    return get_profile_manager().switch(name)


def list_profiles() -> List[Dict]:
    """List all profiles."""
    return get_profile_manager().list()


def get_current_profile() -> Optional[Profile]:
    """Get current profile."""
    return get_profile_manager().get_current()
