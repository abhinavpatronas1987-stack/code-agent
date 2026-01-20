"""Git integration tools for version control operations."""

import subprocess
from pathlib import Path
from typing import Optional

from agno.tools.decorator import tool

from src.tools.terminal import get_working_dir


def run_git_command(args: list[str], cwd: Path | None = None) -> tuple[str, str, int]:
    """Run a git command and return stdout, stderr, and return code."""
    cwd = cwd or get_working_dir()
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", "Git is not installed or not in PATH", 1
    except Exception as e:
        return "", str(e), 1


@tool
def git_status() -> str:
    """
    Get the current git repository status.

    Shows:
    - Current branch
    - Staged changes
    - Unstaged changes
    - Untracked files

    Returns:
        Formatted git status output.

    Examples:
        git_status()
    """
    # Check if in a git repo
    stdout, stderr, code = run_git_command(["rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return f"Error: Not a git repository. {stderr}"

    # Get branch name
    branch_out, _, _ = run_git_command(["branch", "--show-current"])
    branch = branch_out.strip() or "HEAD detached"

    # Get status
    stdout, stderr, code = run_git_command(["status", "--porcelain=v2", "--branch"])
    if code != 0:
        return f"Error getting status: {stderr}"

    # Parse status
    staged = []
    unstaged = []
    untracked = []

    for line in stdout.strip().split("\n"):
        if not line:
            continue
        if line.startswith("# branch"):
            continue
        if line.startswith("1 ") or line.startswith("2 "):
            parts = line.split(" ")
            xy = parts[1] if len(parts) > 1 else ""
            filename = parts[-1] if parts else ""
            if xy[0] != ".":
                staged.append(f"  {xy[0]} {filename}")
            if xy[1] != ".":
                unstaged.append(f"  {xy[1]} {filename}")
        elif line.startswith("? "):
            untracked.append(f"  {line[2:]}")

    # Format output
    output = [
        f"Branch: {branch}",
        f"Working Directory: {get_working_dir()}",
        "",
    ]

    if staged:
        output.append("Staged Changes:")
        output.extend(staged)
        output.append("")

    if unstaged:
        output.append("Unstaged Changes:")
        output.extend(unstaged)
        output.append("")

    if untracked:
        output.append("Untracked Files:")
        output.extend(untracked)
        output.append("")

    if not staged and not unstaged and not untracked:
        output.append("Working tree clean - nothing to commit")

    return "\n".join(output)


@tool
def git_diff(
    file_path: Optional[str] = None,
    staged: bool = False,
    commit: Optional[str] = None,
) -> str:
    """
    Show git diff for changes.

    Args:
        file_path: Optional specific file to diff
        staged: If True, show staged changes (--cached)
        commit: Optional commit hash to diff against

    Returns:
        Diff output showing changes.

    Examples:
        git_diff()                          # All unstaged changes
        git_diff(staged=True)               # Staged changes
        git_diff(file_path="main.py")       # Specific file
        git_diff(commit="HEAD~1")           # Against previous commit
    """
    args = ["diff"]

    if staged:
        args.append("--cached")

    if commit:
        args.append(commit)

    if file_path:
        args.append("--")
        args.append(file_path)

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error: {stderr}"

    if not stdout.strip():
        return "No changes to display."

    return stdout


@tool
def git_log(
    count: int = 10,
    oneline: bool = True,
    file_path: Optional[str] = None,
) -> str:
    """
    Show git commit history.

    Args:
        count: Number of commits to show (default 10)
        oneline: If True, show compact one-line format
        file_path: Optional file to show history for

    Returns:
        Commit history.

    Examples:
        git_log()                           # Recent 10 commits
        git_log(count=5)                    # Last 5 commits
        git_log(file_path="main.py")        # History for specific file
    """
    args = ["log", f"-{count}"]

    if oneline:
        args.append("--oneline")
    else:
        args.extend(["--format=%h %s (%an, %ar)"])

    if file_path:
        args.append("--")
        args.append(file_path)

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error: {stderr}"

    if not stdout.strip():
        return "No commits found."

    return f"Recent commits:\n{stdout}"


@tool
def git_branch(
    name: Optional[str] = None,
    create: bool = False,
    delete: bool = False,
    list_all: bool = False,
) -> str:
    """
    Manage git branches.

    Args:
        name: Branch name (for create/delete/switch)
        create: If True, create a new branch
        delete: If True, delete the branch
        list_all: If True, list all branches including remote

    Returns:
        Branch operation result.

    Examples:
        git_branch()                        # List local branches
        git_branch(list_all=True)           # List all branches
        git_branch(name="feature", create=True)  # Create branch
        git_branch(name="feature")          # Switch to branch
    """
    if create and name:
        stdout, stderr, code = run_git_command(["checkout", "-b", name])
        if code != 0:
            return f"Error creating branch: {stderr}"
        return f"Created and switched to branch: {name}"

    if delete and name:
        stdout, stderr, code = run_git_command(["branch", "-d", name])
        if code != 0:
            return f"Error deleting branch: {stderr}"
        return f"Deleted branch: {name}"

    if name:
        stdout, stderr, code = run_git_command(["checkout", name])
        if code != 0:
            return f"Error switching branch: {stderr}"
        return f"Switched to branch: {name}"

    # List branches
    args = ["branch"]
    if list_all:
        args.append("-a")

    stdout, stderr, code = run_git_command(args)
    if code != 0:
        return f"Error: {stderr}"

    return f"Branches:\n{stdout}"


@tool
def git_add(
    file_path: Optional[str] = None,
    all_files: bool = False,
) -> str:
    """
    Stage files for commit.

    Args:
        file_path: Specific file to stage
        all_files: If True, stage all changes

    Returns:
        Result of staging operation.

    Examples:
        git_add(file_path="main.py")        # Stage specific file
        git_add(all_files=True)             # Stage all changes
    """
    if all_files:
        args = ["add", "-A"]
    elif file_path:
        args = ["add", file_path]
    else:
        return "Error: Specify file_path or set all_files=True"

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error staging files: {stderr}"

    # Show what was staged
    status_out, _, _ = run_git_command(["status", "--short"])
    return f"Files staged successfully.\n\nCurrent status:\n{status_out}"


@tool
def git_commit(message: str) -> str:
    """
    Create a git commit with the staged changes.

    Args:
        message: Commit message

    Returns:
        Commit result.

    Examples:
        git_commit(message="Add new feature")
        git_commit(message="Fix bug in authentication")
    """
    if not message:
        return "Error: Commit message is required"

    # Check if there are staged changes
    stdout, _, _ = run_git_command(["diff", "--cached", "--name-only"])
    if not stdout.strip():
        return "Error: No staged changes to commit. Use git_add first."

    stdout, stderr, code = run_git_command(["commit", "-m", message])

    if code != 0:
        return f"Error creating commit: {stderr}"

    return f"Commit created successfully:\n{stdout}"


@tool
def git_push(
    remote: str = "origin",
    branch: Optional[str] = None,
    set_upstream: bool = False,
) -> str:
    """
    Push commits to remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch to push (default: current branch)
        set_upstream: If True, set upstream tracking

    Returns:
        Push result.

    Examples:
        git_push()                          # Push current branch
        git_push(set_upstream=True)         # Push and set upstream
    """
    args = ["push"]

    if set_upstream:
        args.append("-u")

    args.append(remote)

    if branch:
        args.append(branch)

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error pushing: {stderr}"

    return f"Push successful:\n{stdout or stderr}"


@tool
def git_pull(
    remote: str = "origin",
    branch: Optional[str] = None,
) -> str:
    """
    Pull changes from remote repository.

    Args:
        remote: Remote name (default: origin)
        branch: Branch to pull (default: current branch)

    Returns:
        Pull result.

    Examples:
        git_pull()                          # Pull current branch
        git_pull(branch="main")             # Pull specific branch
    """
    args = ["pull", remote]

    if branch:
        args.append(branch)

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error pulling: {stderr}"

    return f"Pull successful:\n{stdout}"


@tool
def git_stash(
    action: str = "push",
    message: Optional[str] = None,
) -> str:
    """
    Stash or restore uncommitted changes.

    Args:
        action: 'push' to stash, 'pop' to restore, 'list' to show stashes
        message: Optional message for the stash

    Returns:
        Stash operation result.

    Examples:
        git_stash()                         # Stash changes
        git_stash(message="WIP feature")    # Stash with message
        git_stash(action="pop")             # Restore stashed changes
        git_stash(action="list")            # List all stashes
    """
    if action == "push":
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
    elif action == "pop":
        args = ["stash", "pop"]
    elif action == "list":
        args = ["stash", "list"]
    else:
        return f"Error: Unknown action '{action}'. Use 'push', 'pop', or 'list'"

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error: {stderr}"

    if action == "list" and not stdout.strip():
        return "No stashes found."

    return stdout or "Stash operation completed."


@tool
def git_clone(
    url: str,
    directory: Optional[str] = None,
) -> str:
    """
    Clone a git repository.

    Args:
        url: Repository URL to clone
        directory: Optional directory name for the clone

    Returns:
        Clone result.

    Examples:
        git_clone(url="https://github.com/user/repo.git")
        git_clone(url="https://github.com/user/repo.git", directory="my-repo")
    """
    args = ["clone", url]

    if directory:
        args.append(directory)

    stdout, stderr, code = run_git_command(args)

    if code != 0:
        return f"Error cloning: {stderr}"

    return f"Repository cloned successfully:\n{stderr or stdout}"


# Export all git tools
GIT_TOOLS = [
    git_status,
    git_diff,
    git_log,
    git_branch,
    git_add,
    git_commit,
    git_push,
    git_pull,
    git_stash,
    git_clone,
]
