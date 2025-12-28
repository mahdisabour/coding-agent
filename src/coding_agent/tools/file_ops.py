"""File operation tools."""

import logging
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def read_file(file_path: str, project_root: str = ".") -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file relative to project root
        project_root: Root directory of the project

    Returns:
        File contents as a string
    """
    try:
        full_path = Path(project_root) / file_path
        if not full_path.exists():
            return f"Error: File {file_path} does not exist"

        if not full_path.is_file():
            return f"Error: {file_path} is not a file"

        content = full_path.read_text(encoding="utf-8")
        return f"Contents of {file_path}:\n\n{content}"
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return f"Error reading file: {str(e)}"


@tool
def create_file(file_path: str, content: str, project_root: str = ".") -> str:
    """Create a new file with the given content.

    Args:
        file_path: Path to the file relative to project root
        content: Content to write to the file
        project_root: Root directory of the project

    Returns:
        Success or error message
    """
    try:
        full_path = Path(project_root) / file_path
        if full_path.exists():
            return f"Error: File {file_path} already exists. Use update_file to modify it."

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Successfully created {file_path}"
    except Exception as e:
        logger.error(f"Error creating file {file_path}: {e}")
        return f"Error creating file: {str(e)}"


@tool
def update_file(file_path: str, content: str, project_root: str = ".") -> str:
    """Update an existing file with new content.

    Args:
        file_path: Path to the file relative to project root
        content: New content for the file
        project_root: Root directory of the project

    Returns:
        Success or error message
    """
    try:
        full_path = Path(project_root) / file_path
        if not full_path.exists():
            return f"Error: File {file_path} does not exist. Use create_file to create it."

        full_path.write_text(content, encoding="utf-8")
        return f"Successfully updated {file_path}"
    except Exception as e:
        logger.error(f"Error updating file {file_path}: {e}")
        return f"Error updating file: {str(e)}"


@tool
def list_directory(dir_path: str = ".", project_root: str = ".") -> str:
    """List contents of a directory.

    Args:
        dir_path: Directory path relative to project root
        project_root: Root directory of the project

    Returns:
        List of files and directories
    """
    try:
        full_path = Path(project_root) / dir_path
        if not full_path.exists():
            return f"Error: Directory {dir_path} does not exist"

        if not full_path.is_dir():
            return f"Error: {dir_path} is not a directory"

        items = []
        for item in sorted(full_path.iterdir()):
            item_type = "DIR" if item.is_dir() else "FILE"
            relative_path = item.relative_to(project_root)
            items.append(f"[{item_type}] {relative_path}")

        return f"Contents of {dir_path}:\n" + "\n".join(items)
    except Exception as e:
        logger.error(f"Error listing directory {dir_path}: {e}")
        return f"Error listing directory: {str(e)}"


@tool
def search_files(pattern: str, project_root: str = ".") -> str:
    """Search for files matching a pattern.

    Args:
        pattern: Glob pattern to match files (e.g., "*.py", "**/*.ts")
        project_root: Root directory of the project

    Returns:
        List of matching files
    """
    try:
        root = Path(project_root)
        matches = list(root.glob(pattern))

        if not matches:
            return f"No files found matching pattern: {pattern}"

        results = []
        for match in sorted(matches):
            relative_path = match.relative_to(root)
            results.append(str(relative_path))

        return f"Files matching '{pattern}':\n" + "\n".join(results)
    except Exception as e:
        logger.error(f"Error searching files with pattern {pattern}: {e}")
        return f"Error searching files: {str(e)}"
