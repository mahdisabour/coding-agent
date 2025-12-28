"""Code search tools."""

import logging
import re
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def search_code(query: str, file_pattern: str = "**/*.py", project_root: str = ".") -> str:
    """Search for code matching a query in files.

    Args:
        query: Regular expression or plain text to search for
        file_pattern: Glob pattern for files to search (default: all Python files)
        project_root: Root directory of the project

    Returns:
        Matching lines with file paths and line numbers
    """
    try:
        root = Path(project_root)
        matches = []

        for file_path in root.glob(file_pattern):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, start=1):
                    if re.search(query, line, re.IGNORECASE):
                        relative_path = file_path.relative_to(root)
                        matches.append(f"{relative_path}:{line_num}: {line.strip()}")
            except Exception as e:
                logger.debug(f"Error reading {file_path}: {e}")
                continue

        if not matches:
            return f"No matches found for query: {query}"

        # Limit results to avoid overwhelming context
        if len(matches) > 50:
            return (
                f"Found {len(matches)} matches (showing first 50):\n"
                + "\n".join(matches[:50])
            )

        return f"Found {len(matches)} matches:\n" + "\n".join(matches)
    except Exception as e:
        logger.error(f"Error searching code for '{query}': {e}")
        return f"Error searching code: {str(e)}"


@tool
def search_symbols(
    symbol_name: str,
    symbol_type: str = "any",
    project_root: str = ".",
) -> str:
    """Search for symbol definitions (functions, classes, etc.) in Python files.

    Args:
        symbol_name: Name of the symbol to find
        symbol_type: Type of symbol: 'function', 'class', 'any'
        project_root: Root directory of the project

    Returns:
        Locations where the symbol is defined
    """
    try:
        root = Path(project_root)
        patterns = []

        if symbol_type in ("function", "any"):
            patterns.append(rf"^\s*def\s+{symbol_name}\s*\(")
            patterns.append(rf"^\s*async\s+def\s+{symbol_name}\s*\(")

        if symbol_type in ("class", "any"):
            patterns.append(rf"^\s*class\s+{symbol_name}\s*[:\(]")

        matches = []

        for file_path in root.glob("**/*.py"):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.splitlines()

                for line_num, line in enumerate(lines, start=1):
                    for pattern in patterns:
                        if re.search(pattern, line):
                            relative_path = file_path.relative_to(root)
                            matches.append(f"{relative_path}:{line_num}: {line.strip()}")
                            break
            except Exception as e:
                logger.debug(f"Error reading {file_path}: {e}")
                continue

        if not matches:
            return f"No {symbol_type} definitions found for: {symbol_name}"

        return f"Found {len(matches)} definition(s):\n" + "\n".join(matches)
    except Exception as e:
        logger.error(f"Error searching for symbol '{symbol_name}': {e}")
        return f"Error searching symbols: {str(e)}"
