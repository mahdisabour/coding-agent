"""MCP server entry point."""

import asyncio
import logging

from coding_agent.mcp.server import run_mcp_server
from coding_agent.utils.logging import setup_logging


def main() -> None:
    """Run the MCP server."""
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)

    logger.info("Starting MCP server...")

    try:
        asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
