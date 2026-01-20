"""Plugin System - Feature 19.

Extensible plugin architecture:
- Load custom tools
- Plugin discovery
- Plugin configuration
- Hot reload support
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

from src.config.settings import get_settings


class PluginType(Enum):
    """Types of plugins."""
    TOOL = "tool"  # Adds new tools to agent
    COMMAND = "command"  # Adds CLI commands
    HOOK = "hook"  # Hooks into events
    FORMATTER = "formatter"  # Custom output formatters
    PROVIDER = "provider"  # Model providers


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class LoadedPlugin:
    """A loaded plugin instance."""
    info: PluginInfo
    module: Any
    instance: Any = None
    tools: List[Any] = field(default_factory=list)
    commands: Dict[str, Callable] = field(default_factory=dict)


class PluginManager:
    """Manage plugins for Code Agent."""

    PLUGIN_MANIFEST = "plugin.json"

    def __init__(self):
        """Initialize plugin manager."""
        settings = get_settings()

        # Plugin directories
        self.system_plugins_dir = Path(__file__).parent.parent / "plugins"
        self.user_plugins_dir = settings.data_dir / "plugins"
        self.project_plugins_dir = Path.cwd() / ".agent" / "plugins"

        # Ensure directories exist
        self.user_plugins_dir.mkdir(parents=True, exist_ok=True)

        # Loaded plugins
        self.plugins: Dict[str, LoadedPlugin] = {}
        self.tools: List[Any] = []
        self.commands: Dict[str, Callable] = {}

        # Plugin config
        self.config_file = settings.data_dir / "plugin_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load plugin configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"enabled_plugins": [], "plugin_settings": {}}

    def _save_config(self):
        """Save plugin configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            pass

    def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins."""
        plugins = []

        for plugins_dir in [self.system_plugins_dir, self.user_plugins_dir, self.project_plugins_dir]:
            if not plugins_dir.exists():
                continue

            for item in plugins_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / self.PLUGIN_MANIFEST
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                data = json.load(f)
                                plugins.append(PluginInfo(**data))
                        except (json.JSONDecodeError, IOError, TypeError):
                            pass

        return plugins

    def load_plugin(self, plugin_name: str) -> Optional[LoadedPlugin]:
        """
        Load a plugin by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            LoadedPlugin if successful
        """
        # Find plugin directory
        plugin_dir = None
        for plugins_dir in [self.system_plugins_dir, self.user_plugins_dir, self.project_plugins_dir]:
            candidate = plugins_dir / plugin_name
            if candidate.exists() and (candidate / self.PLUGIN_MANIFEST).exists():
                plugin_dir = candidate
                break

        if not plugin_dir:
            return None

        # Load manifest
        manifest_path = plugin_dir / self.PLUGIN_MANIFEST
        try:
            with open(manifest_path, 'r') as f:
                info = PluginInfo(**json.load(f))
        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"Error loading plugin manifest: {e}")
            return None

        # Check dependencies
        for dep in info.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                print(f"Plugin {plugin_name} requires: {dep}")
                return None

        # Load the module
        entry_point = plugin_dir / info.entry_point
        if not entry_point.exists():
            print(f"Entry point not found: {entry_point}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(plugin_name, entry_point)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Error loading plugin module: {e}")
            return None

        # Create plugin instance
        loaded = LoadedPlugin(info=info, module=module)

        # Extract tools if it's a tool plugin
        if info.plugin_type == PluginType.TOOL.value:
            if hasattr(module, 'TOOLS'):
                loaded.tools = module.TOOLS
                self.tools.extend(loaded.tools)
            elif hasattr(module, 'get_tools'):
                loaded.tools = module.get_tools()
                self.tools.extend(loaded.tools)

        # Extract commands if it's a command plugin
        if info.plugin_type == PluginType.COMMAND.value:
            if hasattr(module, 'COMMANDS'):
                loaded.commands = module.COMMANDS
                self.commands.update(loaded.commands)
            elif hasattr(module, 'get_commands'):
                loaded.commands = module.get_commands()
                self.commands.update(loaded.commands)

        # Store plugin
        self.plugins[plugin_name] = loaded

        # Add to enabled list
        if plugin_name not in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].append(plugin_name)
            self._save_config()

        return loaded

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self.plugins:
            return False

        loaded = self.plugins[plugin_name]

        # Remove tools
        for tool in loaded.tools:
            if tool in self.tools:
                self.tools.remove(tool)

        # Remove commands
        for cmd in loaded.commands:
            if cmd in self.commands:
                del self.commands[cmd]

        # Remove from modules
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]

        del self.plugins[plugin_name]

        # Remove from enabled list
        if plugin_name in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].remove(plugin_name)
            self._save_config()

        return True

    def reload_plugin(self, plugin_name: str) -> Optional[LoadedPlugin]:
        """Reload a plugin (hot reload)."""
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)

    def load_enabled_plugins(self):
        """Load all enabled plugins."""
        for plugin_name in self.config.get("enabled_plugins", []):
            self.load_plugin(plugin_name)

    def get_plugin_tools(self) -> List[Any]:
        """Get all tools from loaded plugins."""
        return self.tools

    def get_plugin_commands(self) -> Dict[str, Callable]:
        """Get all commands from loaded plugins."""
        return self.commands

    def list_plugins(self) -> List[Dict]:
        """List all plugins with their status."""
        discovered = {p.name: p for p in self.discover_plugins()}
        result = []

        for name, info in discovered.items():
            result.append({
                "name": name,
                "version": info.version,
                "description": info.description,
                "type": info.plugin_type,
                "author": info.author,
                "loaded": name in self.plugins,
                "enabled": name in self.config.get("enabled_plugins", []),
            })

        return result

    def create_plugin_template(self, name: str, plugin_type: str = "tool") -> Path:
        """
        Create a new plugin from template.

        Args:
            name: Plugin name
            plugin_type: Type of plugin (tool, command, hook)

        Returns:
            Path to created plugin directory
        """
        plugin_dir = self.user_plugins_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest
        manifest = {
            "name": name,
            "version": "1.0.0",
            "description": f"A {plugin_type} plugin for Code Agent",
            "author": "Your Name",
            "plugin_type": plugin_type,
            "entry_point": "main.py",
            "dependencies": [],
            "config_schema": {},
        }

        with open(plugin_dir / "plugin.json", 'w') as f:
            json.dump(manifest, f, indent=2)

        # Create entry point based on type
        if plugin_type == "tool":
            code = '''"""Custom tool plugin for Code Agent."""

from agno.tools.decorator import tool


@tool(name="my_custom_tool")
def my_custom_tool(arg: str) -> str:
    """
    Description of your custom tool.

    Args:
        arg: Description of argument

    Returns:
        Result description
    """
    return f"Processed: {arg}"


# Export tools
TOOLS = [my_custom_tool]
'''
        elif plugin_type == "command":
            code = '''"""Custom command plugin for Code Agent."""


def hello_command(args: str) -> str:
    """A hello world command."""
    return f"Hello, {args or 'World'}!"


def goodbye_command(args: str) -> str:
    """A goodbye command."""
    return f"Goodbye, {args or 'World'}!"


# Export commands (key is command name, value is function)
COMMANDS = {
    "hello": hello_command,
    "goodbye": goodbye_command,
}
'''
        else:
            code = '''"""Custom plugin for Code Agent."""

def initialize():
    """Called when plugin is loaded."""
    print("Plugin initialized!")


def cleanup():
    """Called when plugin is unloaded."""
    print("Plugin cleanup!")
'''

        with open(plugin_dir / "main.py", 'w') as f:
            f.write(code)

        # Create README
        readme = f"""# {name}

A {plugin_type} plugin for Code Agent.

## Installation

Copy this folder to `~/.code-agent/plugins/` or run:

```
/plugin install {name}
```

## Usage

{f"Use the tools in your prompts." if plugin_type == "tool" else ""}
{f"Run /{name} <args> to use this command." if plugin_type == "command" else ""}

## Configuration

Edit `plugin.json` to configure the plugin.
"""

        with open(plugin_dir / "README.md", 'w') as f:
            f.write(readme)

        return plugin_dir

    def get_plugin_config(self, plugin_name: str) -> Dict:
        """Get configuration for a plugin."""
        return self.config.get("plugin_settings", {}).get(plugin_name, {})

    def set_plugin_config(self, plugin_name: str, settings: Dict):
        """Set configuration for a plugin."""
        if "plugin_settings" not in self.config:
            self.config["plugin_settings"] = {}
        self.config["plugin_settings"][plugin_name] = settings
        self._save_config()


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# Convenience functions
def load_plugin(name: str) -> Optional[LoadedPlugin]:
    """Load a plugin."""
    return get_plugin_manager().load_plugin(name)


def list_plugins() -> List[Dict]:
    """List all plugins."""
    return get_plugin_manager().list_plugins()


def create_plugin(name: str, plugin_type: str = "tool") -> Path:
    """Create a new plugin."""
    return get_plugin_manager().create_plugin_template(name, plugin_type)
