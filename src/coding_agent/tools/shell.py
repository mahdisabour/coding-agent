"""Shell command execution tool."""

import logging
import subprocess
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def run_command(command: str, project_root: str = ".", timeout: int = 60) -> str:
    """Execute a shell command in the project directory.

    Args:
        command: Shell command to execute
        project_root: Root directory of the project
        timeout: Command timeout in seconds

    Returns:
        Command output (stdout and stderr combined)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=Path(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")

        output.append(f"\nReturn code: {result.returncode}")

        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error executing command '{command}': {e}")
        return f"Error executing command: {str(e)}"
