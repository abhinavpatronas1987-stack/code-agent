"""Tests for agent tools."""

import os
import tempfile
from pathlib import Path

import pytest

from src.tools.terminal import (
    run_terminal_command as _run_terminal_command,
    change_directory as _change_directory,
    get_current_directory as _get_current_directory,
    list_directory as _list_directory,
    set_working_dir,
    get_working_dir,
)
from src.tools.file_ops import (
    read_file as _read_file,
    write_file as _write_file,
    edit_file as _edit_file,
    create_file as _create_file,
    delete_file as _delete_file,
)
from src.tools.code_search import (
    search_files as _search_files,
    find_files as _find_files,
    get_file_structure as _get_file_structure,
)

# Agno wraps tools as Function objects, so we need to access the underlying entrypoint
run_terminal_command = _run_terminal_command.entrypoint
change_directory = _change_directory.entrypoint
get_current_directory = _get_current_directory.entrypoint
list_directory = _list_directory.entrypoint
read_file = _read_file.entrypoint
write_file = _write_file.entrypoint
edit_file = _edit_file.entrypoint
create_file = _create_file.entrypoint
delete_file = _delete_file.entrypoint
search_files = _search_files.entrypoint
find_files = _find_files.entrypoint
get_file_structure = _get_file_structure.entrypoint


class TestTerminalTools:
    """Tests for terminal tools."""

    def test_run_terminal_command_simple(self):
        """Test running a simple command."""
        result = run_terminal_command("echo hello")
        assert "hello" in result
        assert "Exit Code: 0" in result

    def test_change_directory(self):
        """Test changing directory."""
        original = get_working_dir()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = change_directory(tmpdir)
            assert "Changed directory to" in result
            assert get_working_dir() == Path(tmpdir).resolve()

            # Restore original
            set_working_dir(original)

    def test_get_current_directory(self):
        """Test getting current directory."""
        result = get_current_directory()
        assert "Current directory" in result

    def test_list_directory(self):
        """Test listing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello")

            set_working_dir(Path(tmpdir))
            result = list_directory()

            assert "test.txt" in result


class TestFileTools:
    """Tests for file operation tools."""

    def test_read_file(self):
        """Test reading a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_read.txt"
            file_path.write_text("line 1\nline 2\nline 3")

            result = read_file(str(file_path))
            assert "line 1" in result
            assert "line 2" in result

    def test_read_file_with_lines(self):
        """Test reading specific lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_read_lines.txt"
            content = "\n".join(f"line {i}" for i in range(10))
            file_path.write_text(content)

            result = read_file(str(file_path), start_line=3, end_line=5)
            assert "line 2" in result
            assert "line 4" in result

    def test_write_file(self):
        """Test writing a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            result = write_file(str(file_path), "hello world")

            assert "Successfully" in result
            assert file_path.read_text() == "hello world"

    def test_edit_file(self):
        """Test editing a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_edit.txt"
            file_path.write_text("old content here")

            result = edit_file(str(file_path), "old content", "new content")
            assert "Successfully edited" in result

            content = file_path.read_text()
            assert "new content" in content
            assert "old content" not in content

    def test_create_file(self):
        """Test creating a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "new_file.txt"
            result = create_file(str(file_path), "initial content")

            assert "Successfully created" in result
            assert file_path.exists()
            assert file_path.read_text() == "initial content"

    def test_delete_file(self):
        """Test deleting a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "to_delete.txt"
            file_path.write_text("temp content")

            result = delete_file(str(file_path))
            assert "Successfully deleted" in result
            assert not file_path.exists()


class TestSearchTools:
    """Tests for code search tools."""

    def test_find_files(self):
        """Test finding files by pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.py").write_text("# test 1")
            (Path(tmpdir) / "test2.py").write_text("# test 2")
            (Path(tmpdir) / "readme.md").write_text("# readme")

            set_working_dir(Path(tmpdir))
            result = find_files("*.py")

            assert "test1.py" in result
            assert "test2.py" in result
            assert "readme.md" not in result

    def test_search_files(self):
        """Test searching file contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.py").write_text("def hello():\n    pass")
            (Path(tmpdir) / "test2.py").write_text("def world():\n    pass")

            set_working_dir(Path(tmpdir))
            result = search_files("def hello")

            assert "test1.py" in result
            assert "test2.py" not in result

    def test_get_file_structure(self):
        """Test getting directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            (Path(tmpdir) / "src").mkdir()
            (Path(tmpdir) / "src" / "main.py").write_text("")
            (Path(tmpdir) / "tests").mkdir()
            (Path(tmpdir) / "tests" / "test_main.py").write_text("")

            set_working_dir(Path(tmpdir))
            result = get_file_structure()

            assert "src" in result
            assert "tests" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
