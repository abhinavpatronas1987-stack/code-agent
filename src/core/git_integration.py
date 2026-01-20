"""Git Integration Enhancement - Feature 12.

Advanced Git integration:
- Smart commit messages
- Branch visualization
- Conflict resolution
- PR/MR assistance
"""

import subprocess
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GitStatus:
    """Git repository status."""
    branch: str = ""
    ahead: int = 0
    behind: int = 0
    staged: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    conflicted: List[str] = field(default_factory=list)
    is_clean: bool = True
    is_repo: bool = False


@dataclass
class GitCommit:
    """A git commit."""
    hash: str
    short_hash: str
    author: str
    email: str
    date: str
    message: str
    files_changed: int = 0


@dataclass
class GitBranch:
    """A git branch."""
    name: str
    is_current: bool = False
    is_remote: bool = False
    last_commit: str = ""
    ahead: int = 0
    behind: int = 0


class GitIntegration:
    """Advanced Git integration for Code Agent."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize Git integration."""
        self.working_dir = working_dir or Path.cwd()
        self._check_git()

    def _check_git(self):
        """Check if directory is a git repo."""
        self.is_repo = (self.working_dir / ".git").exists()

    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str]:
        """Run a git command."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if check and result.returncode != 0:
                return False, result.stderr
            return True, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "Git not found"
        except Exception as e:
            return False, str(e)

    def get_status(self) -> GitStatus:
        """Get repository status."""
        status = GitStatus()

        if not self.is_repo:
            return status

        status.is_repo = True

        # Get branch
        success, output = self._run_git(["branch", "--show-current"])
        if success:
            status.branch = output.strip()

        # Get status
        success, output = self._run_git(["status", "--porcelain", "-b"])
        if success:
            lines = output.strip().splitlines()
            for line in lines:
                if line.startswith("##"):
                    # Parse branch info
                    if "ahead" in line:
                        match = re.search(r'ahead (\d+)', line)
                        if match:
                            status.ahead = int(match.group(1))
                    if "behind" in line:
                        match = re.search(r'behind (\d+)', line)
                        if match:
                            status.behind = int(match.group(1))
                elif line:
                    code = line[:2]
                    filepath = line[3:]

                    if code[0] in ('M', 'A', 'D', 'R', 'C'):
                        status.staged.append(filepath)
                    if code[1] == 'M':
                        status.modified.append(filepath)
                    elif code[1] == 'D':
                        status.deleted.append(filepath)
                    elif code == '??':
                        status.untracked.append(filepath)
                    elif code == 'UU':
                        status.conflicted.append(filepath)

        status.is_clean = not (status.staged or status.modified or
                               status.untracked or status.deleted or status.conflicted)

        return status

    def get_log(self, limit: int = 10) -> List[GitCommit]:
        """Get recent commits."""
        commits = []

        if not self.is_repo:
            return commits

        success, output = self._run_git([
            "log", f"-{limit}",
            "--format=%H|%h|%an|%ae|%ai|%s"
        ])

        if success:
            for line in output.strip().splitlines():
                parts = line.split("|", 5)
                if len(parts) >= 6:
                    commits.append(GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        email=parts[3],
                        date=parts[4],
                        message=parts[5],
                    ))

        return commits

    def get_branches(self) -> List[GitBranch]:
        """Get all branches."""
        branches = []

        if not self.is_repo:
            return branches

        success, output = self._run_git(["branch", "-a", "-v"])
        if success:
            for line in output.strip().splitlines():
                is_current = line.startswith("*")
                line = line.lstrip("* ").strip()

                parts = line.split(None, 2)
                if len(parts) >= 2:
                    name = parts[0]
                    is_remote = name.startswith("remotes/")

                    branches.append(GitBranch(
                        name=name.replace("remotes/", ""),
                        is_current=is_current,
                        is_remote=is_remote,
                        last_commit=parts[1] if len(parts) > 1 else "",
                    ))

        return branches

    def get_diff(self, staged: bool = False, file: Optional[str] = None) -> str:
        """Get diff output."""
        if not self.is_repo:
            return ""

        args = ["diff"]
        if staged:
            args.append("--staged")
        if file:
            args.append(file)

        success, output = self._run_git(args)
        return output if success else ""

    def generate_commit_message(self, diff: Optional[str] = None) -> str:
        """Generate a smart commit message from changes."""
        if not self.is_repo:
            return ""

        if diff is None:
            diff = self.get_diff(staged=True)
            if not diff:
                diff = self.get_diff()

        if not diff:
            return ""

        # Analyze changes
        files_changed = set()
        additions = 0
        deletions = 0
        file_types = set()

        for line in diff.splitlines():
            if line.startswith("diff --git"):
                match = re.search(r'b/(.+)$', line)
                if match:
                    filepath = match.group(1)
                    files_changed.add(filepath)
                    ext = Path(filepath).suffix
                    if ext:
                        file_types.add(ext)
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        # Generate message
        if len(files_changed) == 1:
            file = list(files_changed)[0]
            filename = Path(file).name
            if additions > deletions * 2:
                action = "Add content to"
            elif deletions > additions * 2:
                action = "Remove content from"
            else:
                action = "Update"
            return f"{action} {filename}"
        elif file_types:
            types_str = ", ".join(sorted(file_types)[:3])
            if additions > deletions * 2:
                return f"Add {types_str} files"
            elif deletions > additions * 2:
                return f"Remove {types_str} files"
            return f"Update {types_str} files"
        else:
            return f"Update {len(files_changed)} files"

    def smart_commit(self, message: Optional[str] = None) -> Tuple[bool, str]:
        """Perform a smart commit."""
        if not self.is_repo:
            return False, "Not a git repository"

        status = self.get_status()
        if status.is_clean:
            return False, "Nothing to commit"

        # Auto-generate message if not provided
        if not message:
            message = self.generate_commit_message()

        # Stage modified files if nothing staged
        if not status.staged and status.modified:
            for file in status.modified:
                self._run_git(["add", file])

        return self._run_git(["commit", "-m", message])

    def get_branch_tree(self) -> str:
        """Generate ASCII branch tree."""
        if not self.is_repo:
            return "Not a git repository"

        lines = []
        lines.append("Git Branch Tree")
        lines.append("=" * 40)

        branches = self.get_branches()
        local = [b for b in branches if not b.is_remote]
        remote = [b for b in branches if b.is_remote]

        # Local branches
        lines.append("\nLocal Branches:")
        for branch in local:
            marker = "*" if branch.is_current else " "
            lines.append(f"  {marker} {branch.name} ({branch.last_commit})")

        # Remote branches
        if remote:
            lines.append("\nRemote Branches:")
            for branch in remote[:10]:
                lines.append(f"    {branch.name}")

        return "\n".join(lines)

    def get_conflict_files(self) -> List[Dict[str, Any]]:
        """Get files with merge conflicts."""
        conflicts = []

        if not self.is_repo:
            return conflicts

        status = self.get_status()
        for filepath in status.conflicted:
            full_path = self.working_dir / filepath
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    # Find conflict markers
                    ours = []
                    theirs = []
                    in_ours = False
                    in_theirs = False

                    for i, line in enumerate(content.splitlines(), 1):
                        if line.startswith("<<<<<<<"):
                            in_ours = True
                        elif line.startswith("======="):
                            in_ours = False
                            in_theirs = True
                        elif line.startswith(">>>>>>>"):
                            in_theirs = False
                        elif in_ours:
                            ours.append((i, line))
                        elif in_theirs:
                            theirs.append((i, line))

                    conflicts.append({
                        "file": filepath,
                        "ours_changes": len(ours),
                        "theirs_changes": len(theirs),
                    })
                except (IOError, UnicodeDecodeError):
                    conflicts.append({"file": filepath, "error": "Could not read"})

        return conflicts

    def get_status_report(self) -> str:
        """Generate a status report."""
        status = self.get_status()

        if not status.is_repo:
            return "Not a git repository"

        lines = []
        lines.append("Git Status Report")
        lines.append("=" * 40)
        lines.append(f"\nBranch: {status.branch}")

        if status.ahead:
            lines.append(f"  Ahead by {status.ahead} commits")
        if status.behind:
            lines.append(f"  Behind by {status.behind} commits")

        if status.is_clean:
            lines.append("\n[Clean] Working tree is clean")
        else:
            if status.staged:
                lines.append(f"\nStaged ({len(status.staged)}):")
                for f in status.staged[:5]:
                    lines.append(f"  + {f}")
            if status.modified:
                lines.append(f"\nModified ({len(status.modified)}):")
                for f in status.modified[:5]:
                    lines.append(f"  ~ {f}")
            if status.untracked:
                lines.append(f"\nUntracked ({len(status.untracked)}):")
                for f in status.untracked[:5]:
                    lines.append(f"  ? {f}")
            if status.conflicted:
                lines.append(f"\n[CONFLICT] ({len(status.conflicted)}):")
                for f in status.conflicted:
                    lines.append(f"  ! {f}")

        return "\n".join(lines)


# Global instance
_git_integration: Optional[GitIntegration] = None


def get_git_integration(working_dir: Optional[Path] = None) -> GitIntegration:
    """Get or create git integration."""
    global _git_integration
    if _git_integration is None:
        _git_integration = GitIntegration(working_dir)
    return _git_integration


# Convenience functions
def git_status(working_dir: Optional[Path] = None) -> GitStatus:
    """Get git status."""
    return GitIntegration(working_dir or Path.cwd()).get_status()


def git_log(limit: int = 10, working_dir: Optional[Path] = None) -> List[GitCommit]:
    """Get git log."""
    return GitIntegration(working_dir or Path.cwd()).get_log(limit)


def git_diff(staged: bool = False, working_dir: Optional[Path] = None) -> str:
    """Get git diff."""
    return GitIntegration(working_dir or Path.cwd()).get_diff(staged)


def git_status_report(working_dir: Optional[Path] = None) -> str:
    """Get git status report."""
    return GitIntegration(working_dir or Path.cwd()).get_status_report()
