"""Shell Integration - Feature 17.

Deep shell integration:
- Shell history analysis
- Command suggestions
- Error explanation
- Script generation
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ShellCommand:
    """A shell command."""
    command: str
    timestamp: str = ""
    cwd: str = ""
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0


@dataclass
class CommandSuggestion:
    """A command suggestion."""
    command: str
    description: str
    confidence: float  # 0.0 to 1.0
    category: str  # "fix", "alternative", "related"


class ShellIntegration:
    """Shell integration utilities."""

    # Common command patterns
    COMMAND_PATTERNS = {
        "git": {
            "status": "Show repository status",
            "add .": "Stage all changes",
            "commit -m": "Commit with message",
            "push": "Push to remote",
            "pull": "Pull from remote",
            "checkout": "Switch branches",
            "branch": "List/create branches",
            "log --oneline": "Show commit history",
            "diff": "Show changes",
            "stash": "Stash changes",
        },
        "npm": {
            "install": "Install dependencies",
            "run dev": "Start development server",
            "run build": "Build for production",
            "run test": "Run tests",
            "update": "Update packages",
        },
        "pip": {
            "install": "Install packages",
            "install -r requirements.txt": "Install from requirements",
            "freeze": "List installed packages",
            "upgrade": "Upgrade a package",
        },
        "python": {
            "-m pytest": "Run tests",
            "-m venv venv": "Create virtual environment",
            "-c": "Run inline code",
        },
        "docker": {
            "ps": "List containers",
            "build": "Build image",
            "run": "Run container",
            "compose up": "Start compose services",
            "compose down": "Stop compose services",
        },
    }

    # Common error patterns and fixes
    ERROR_FIXES = {
        r"command not found": [
            ("Install the missing command", "Check if the tool is installed and in PATH"),
            ("Use full path", "Try using the absolute path to the command"),
        ],
        r"permission denied": [
            ("Add execute permission", "chmod +x {file}"),
            ("Run with sudo", "sudo {command}"),
        ],
        r"no such file or directory": [
            ("Check path exists", "Verify the file/directory path is correct"),
            ("Create the directory", "mkdir -p {path}"),
        ],
        r"port.*already in use|address already in use": [
            ("Find process using port", "lsof -i :{port} or netstat -tlnp | grep {port}"),
            ("Kill the process", "kill -9 {pid}"),
            ("Use different port", "Change the port in configuration"),
        ],
        r"npm ERR!": [
            ("Clear npm cache", "npm cache clean --force"),
            ("Delete node_modules", "rm -rf node_modules && npm install"),
            ("Check npm version", "npm --version"),
        ],
        r"ModuleNotFoundError|ImportError": [
            ("Install the module", "pip install {module}"),
            ("Check virtual environment", "Ensure venv is activated"),
        ],
        r"git.*not a git repository": [
            ("Initialize repository", "git init"),
            ("Navigate to repo directory", "cd to the correct directory"),
        ],
    }

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize shell integration."""
        self.working_dir = working_dir or Path.cwd()
        self.history: List[ShellCommand] = []

    def run_command(
        self,
        command: str,
        timeout: int = 60,
        capture: bool = True,
    ) -> ShellCommand:
        """
        Run a shell command.

        Args:
            command: Command to run
            timeout: Timeout in seconds
            capture: Capture output

        Returns:
            ShellCommand with results
        """
        cmd = ShellCommand(
            command=command,
            timestamp=datetime.now().isoformat(),
            cwd=str(self.working_dir),
        )

        start = datetime.now()

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=capture,
                text=True,
                timeout=timeout,
            )

            cmd.exit_code = result.returncode
            cmd.stdout = result.stdout[:10000] if capture else ""
            cmd.stderr = result.stderr[:10000] if capture else ""

        except subprocess.TimeoutExpired:
            cmd.exit_code = -1
            cmd.stderr = f"Command timed out after {timeout} seconds"
        except Exception as e:
            cmd.exit_code = -1
            cmd.stderr = str(e)

        cmd.duration = (datetime.now() - start).total_seconds()
        self.history.append(cmd)

        return cmd

    def explain_error(self, error_output: str) -> List[Dict[str, str]]:
        """
        Explain an error and suggest fixes.

        Args:
            error_output: Error message to analyze

        Returns:
            List of explanations and fixes
        """
        results = []
        error_lower = error_output.lower()

        for pattern, fixes in self.ERROR_FIXES.items():
            if re.search(pattern, error_lower, re.IGNORECASE):
                for fix_name, fix_desc in fixes:
                    results.append({
                        "issue": pattern,
                        "suggestion": fix_name,
                        "details": fix_desc,
                    })

        if not results:
            results.append({
                "issue": "Unknown error",
                "suggestion": "Check the full error message",
                "details": error_output[:200],
            })

        return results

    def suggest_commands(
        self,
        context: str,
        limit: int = 5,
    ) -> List[CommandSuggestion]:
        """
        Suggest commands based on context.

        Args:
            context: Current context/task
            limit: Max suggestions

        Returns:
            List of suggestions
        """
        suggestions = []
        context_lower = context.lower()

        # Match keywords to commands
        keywords = {
            "test": [
                ("pytest", "Run Python tests", 0.9),
                ("npm test", "Run npm tests", 0.8),
                ("python -m unittest discover", "Run unittest", 0.7),
            ],
            "install": [
                ("pip install -r requirements.txt", "Install Python deps", 0.9),
                ("npm install", "Install Node deps", 0.9),
            ],
            "build": [
                ("npm run build", "Build Node project", 0.9),
                ("python setup.py build", "Build Python package", 0.7),
            ],
            "commit": [
                ("git add . && git commit -m 'Update'", "Stage and commit", 0.9),
                ("git commit --amend", "Amend last commit", 0.7),
            ],
            "push": [
                ("git push", "Push to origin", 0.9),
                ("git push -u origin main", "Push and set upstream", 0.8),
            ],
            "start": [
                ("npm run dev", "Start dev server", 0.9),
                ("python -m src.cli", "Run Python CLI", 0.8),
            ],
            "status": [
                ("git status", "Git status", 0.9),
                ("docker ps", "Docker containers", 0.7),
            ],
            "lint": [
                ("ruff check .", "Run ruff linter", 0.9),
                ("eslint .", "Run eslint", 0.8),
            ],
            "format": [
                ("black .", "Format Python with black", 0.9),
                ("prettier --write .", "Format with prettier", 0.8),
            ],
        }

        for keyword, cmds in keywords.items():
            if keyword in context_lower:
                for cmd, desc, conf in cmds:
                    suggestions.append(CommandSuggestion(
                        command=cmd,
                        description=desc,
                        confidence=conf,
                        category="related",
                    ))

        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return suggestions[:limit]

    def get_command_help(self, command: str) -> Dict[str, Any]:
        """
        Get help for a command.

        Args:
            command: Command to get help for

        Returns:
            Help information
        """
        base_cmd = command.split()[0] if command else ""

        if base_cmd in self.COMMAND_PATTERNS:
            return {
                "command": base_cmd,
                "common_uses": self.COMMAND_PATTERNS[base_cmd],
                "help_command": f"{base_cmd} --help",
            }

        return {
            "command": command,
            "suggestion": f"Try running: {command} --help",
        }

    def generate_script(
        self,
        task: str,
        script_type: str = "bash",
    ) -> str:
        """
        Generate a shell script for a task.

        Args:
            task: Task description
            script_type: Script type (bash, powershell)

        Returns:
            Generated script
        """
        task_lower = task.lower()

        if script_type == "powershell":
            return self._generate_powershell_script(task_lower)
        else:
            return self._generate_bash_script(task_lower)

    def _generate_bash_script(self, task: str) -> str:
        """Generate bash script."""
        lines = ["#!/bin/bash", "", "# Auto-generated script", f"# Task: {task}", "", "set -e", ""]

        if "test" in task:
            lines.extend([
                "echo 'Running tests...'",
                "pytest -v",
            ])
        elif "build" in task:
            lines.extend([
                "echo 'Building project...'",
                "if [ -f 'package.json' ]; then",
                "    npm run build",
                "elif [ -f 'setup.py' ]; then",
                "    python setup.py build",
                "fi",
            ])
        elif "deploy" in task:
            lines.extend([
                "echo 'Deploying...'",
                "# Add deployment commands here",
            ])
        elif "install" in task:
            lines.extend([
                "echo 'Installing dependencies...'",
                "if [ -f 'requirements.txt' ]; then",
                "    pip install -r requirements.txt",
                "fi",
                "if [ -f 'package.json' ]; then",
                "    npm install",
                "fi",
            ])
        else:
            lines.extend([
                "echo 'Starting task...'",
                "# Add commands here",
            ])

        lines.extend(["", "echo 'Done!'"])
        return "\n".join(lines)

    def _generate_powershell_script(self, task: str) -> str:
        """Generate PowerShell script."""
        lines = ["# Auto-generated PowerShell script", f"# Task: {task}", "", "$ErrorActionPreference = 'Stop'", ""]

        if "test" in task:
            lines.extend([
                "Write-Host 'Running tests...'",
                "pytest -v",
            ])
        elif "build" in task:
            lines.extend([
                "Write-Host 'Building project...'",
                "if (Test-Path 'package.json') {",
                "    npm run build",
                "}",
            ])
        else:
            lines.extend([
                "Write-Host 'Starting task...'",
                "# Add commands here",
            ])

        lines.extend(["", "Write-Host 'Done!'"])
        return "\n".join(lines)

    def analyze_history(self) -> Dict[str, Any]:
        """Analyze command history."""
        if not self.history:
            return {"message": "No command history"}

        total = len(self.history)
        successful = len([c for c in self.history if c.exit_code == 0])
        failed = len([c for c in self.history if c.exit_code and c.exit_code != 0])

        # Most used commands
        cmd_counts: Dict[str, int] = {}
        for cmd in self.history:
            base = cmd.command.split()[0] if cmd.command else ""
            cmd_counts[base] = cmd_counts.get(base, 0) + 1

        most_used = sorted(cmd_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_commands": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "N/A",
            "most_used": most_used,
            "total_duration": sum(c.duration for c in self.history),
        }

    def get_report(self) -> str:
        """Generate shell integration report."""
        lines = []
        lines.append("=" * 50)
        lines.append("  SHELL INTEGRATION")
        lines.append("=" * 50)

        analysis = self.analyze_history()

        if analysis.get("message"):
            lines.append(f"\n{analysis['message']}")
        else:
            lines.append(f"\nCommand History:")
            lines.append(f"  Total: {analysis['total_commands']}")
            lines.append(f"  Successful: {analysis['successful']}")
            lines.append(f"  Failed: {analysis['failed']}")
            lines.append(f"  Success Rate: {analysis['success_rate']}")

            if analysis.get("most_used"):
                lines.append("\nMost Used Commands:")
                for cmd, count in analysis["most_used"]:
                    lines.append(f"  {cmd}: {count}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


# Global instance
_shell_integration: Optional[ShellIntegration] = None


def get_shell_integration(working_dir: Optional[Path] = None) -> ShellIntegration:
    """Get or create shell integration."""
    global _shell_integration
    if _shell_integration is None:
        _shell_integration = ShellIntegration(working_dir)
    return _shell_integration


# Convenience functions
def run_shell(command: str, working_dir: Optional[Path] = None) -> ShellCommand:
    """Run a shell command."""
    shell = ShellIntegration(working_dir or Path.cwd())
    return shell.run_command(command)


def explain_shell_error(error: str) -> List[Dict]:
    """Explain a shell error."""
    return get_shell_integration().explain_error(error)


def suggest_shell_commands(context: str) -> List[CommandSuggestion]:
    """Get command suggestions."""
    return get_shell_integration().suggest_commands(context)
