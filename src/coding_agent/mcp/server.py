"""MCP server for exposing tools."""

import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from coding_agent.tools import (
    create_file,
    list_directory,
    read_file,
    run_command,
    search_code,
    search_files,
    search_symbols,
    update_file,
)

logger = logging.getLogger(__name__)


def create_mcp_server() -> Server:
    """Create and configure the MCP server.

    Returns:
        Configured MCP server instance
    """
    server = Server("coding-agent-mcp")

    # Register tools
    tools = [
        read_file,
        create_file,
        update_file,
        list_directory,
        search_files,
        run_command,
        search_code,
        search_symbols,
    ]

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name=tool.name,
                description=tool.description or "",
                inputSchema={
                    "type": "object",
                    "properties": tool.args_schema.model_json_schema()["properties"]
                    if hasattr(tool, "args_schema") and tool.args_schema
                    else {},
                },
            )
            for tool in tools
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
        """Execute a tool by name.

        Args:
            name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool_map = {tool.name: tool for tool in tools}

        if name not in tool_map:
            raise ValueError(f"Unknown tool: {name}")

        try:
            result = await tool_map[name].ainvoke(arguments)
            return [{"type": "text", "text": str(result)}]
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [{"type": "text", "text": f"Error: {str(e)}"}]

    return server


async def run_mcp_server() -> None:
    """Run the MCP server."""
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
