"""Tests for agent tools."""

import tempfile
from pathlib import Path

import pytest

from coding_agent.tools.file_ops import (
    create_file,
    list_directory,
    read_file,
    search_files,
    update_file,
)
from coding_agent.tools.search import search_code, search_symbols


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_create_and_read_file(temp_project):
    """Test creating and reading a file."""
    file_path = "test.txt"
    content = "Hello, World!"

    # Create file
    result = create_file.invoke({
        "file_path": file_path,
        "content": content,
        "project_root": str(temp_project),
    })
    assert "Successfully created" in result

    # Read file
    result = read_file.invoke({
        "file_path": file_path,
        "project_root": str(temp_project),
    })
    assert content in result


def test_update_file(temp_project):
    """Test updating a file."""
    file_path = "test.txt"

    # Create initial file
    create_file.invoke({
        "file_path": file_path,
        "content": "Initial content",
        "project_root": str(temp_project),
    })

    # Update file
    new_content = "Updated content"
    result = update_file.invoke({
        "file_path": file_path,
        "content": new_content,
        "project_root": str(temp_project),
    })
    assert "Successfully updated" in result

    # Verify update
    result = read_file.invoke({
        "file_path": file_path,
        "project_root": str(temp_project),
    })
    assert new_content in result


def test_list_directory(temp_project):
    """Test listing directory contents."""
    # Create some files
    (temp_project / "file1.txt").write_text("test")
    (temp_project / "file2.py").write_text("test")
    (temp_project / "subdir").mkdir()

    result = list_directory.invoke({
        "dir_path": ".",
        "project_root": str(temp_project),
    })

    assert "file1.txt" in result
    assert "file2.py" in result
    assert "subdir" in result


def test_search_files(temp_project):
    """Test searching for files by pattern."""
    # Create test files
    (temp_project / "test.py").write_text("test")
    (temp_project / "test.txt").write_text("test")
    (temp_project / "subdir").mkdir()
    (temp_project / "subdir" / "another.py").write_text("test")

    result = search_files.invoke({
        "pattern": "*.py",
        "project_root": str(temp_project),
    })

    assert "test.py" in result
    assert "test.txt" not in result


def test_search_code(temp_project):
    """Test searching for code patterns."""
    # Create a Python file with code
    code = """
def hello_world():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""
    (temp_project / "example.py").write_text(code)

    result = search_code.invoke({
        "query": "hello_world",
        "file_pattern": "**/*.py",
        "project_root": str(temp_project),
    })

    assert "hello_world" in result
    assert "example.py" in result


def test_search_symbols(temp_project):
    """Test searching for function and class definitions."""
    # Create Python files with definitions
    code1 = """
class MyClass:
    def method(self):
        pass

def my_function():
    pass
"""
    (temp_project / "module.py").write_text(code1)

    # Search for class
    result = search_symbols.invoke({
        "symbol_name": "MyClass",
        "symbol_type": "class",
        "project_root": str(temp_project),
    })
    assert "MyClass" in result

    # Search for function
    result = search_symbols.invoke({
        "symbol_name": "my_function",
        "symbol_type": "function",
        "project_root": str(temp_project),
    })
    assert "my_function" in result
