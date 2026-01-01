"""LangGraph workflow for the coding agent."""

import logging

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents.middleware import SummarizationMiddleware
from langchain_openai import ChatOpenAI

from coding_agent.agent.prompts import get_system_prompt
from coding_agent.agent.state import AgentState
from coding_agent.config import get_settings
from coding_agent.tools import (
    create_file,
    list_directory,
    read_file,
    run_command,
    search_code,
    search_files,
    search_symbols,
    update_file,
    replace_in_file,
)

SAFE_TOOLS = {
    "read_file_bound",
    "list_directory_bound",
    "search_files_bound",
    "search_code_bound",
    "search_symbols_bound",
}

logger = logging.getLogger(__name__)


def _create_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_api_base,
    )


def create_agent_graph_with_project_root(project_root: str, checkpointer=None):
    """Create and compile the agent graph with tools bound to project root.

    Args:
        project_root: Root directory of the project

    Returns:
        Compiled agent graph
    """
    llm_client = _create_llm()

    # Get tools with project_root bound
    tools = _create_tools_with_project_root(project_root)

    # Create the agent with tools and system prompt
    summ = SummarizationMiddleware(
        model=llm_client,
        trigger=("tokens", 8000),
        keep=("messages", 10),
    )

    coding_agent = create_agent(
        model=llm_client,
        tools=tools,
        state_schema=AgentState,
        system_prompt=SystemMessage(
            content=[
                {
                    "type": "text",
                    "text": get_system_prompt(),
                }
            ]
        ),
        middleware=[summ],
        checkpointer=checkpointer,
        interrupt_before=["tools"] if checkpointer else [],
    )

    return coding_agent



def _create_tools_with_project_root(project_root: str):
    """Create tools bound to a specific project root.

    Args:
        project_root: Root directory of the project

    Returns:
        List of tools with project_root bound
    """
    from langchain_core.tools import tool

    # Create wrapper tools with project_root bound
    @tool
    def read_file_bound(file_path: str) -> str:
        """Read the contents of a file.

        Args:
            file_path: Path to the file relative to project root

        Returns:
            File contents as a string
        """
        return read_file.invoke({"file_path": file_path, "project_root": project_root})

    @tool
    def create_file_bound(file_path: str, content: str) -> str:
        """Create a new file with the given content.

        Args:
            file_path: Path to the file relative to project root
            content: Content to write to the file

        Returns:
            Success or error message
        """
        return create_file.invoke({"file_path": file_path, "content": content, "project_root": project_root})

    @tool
    def update_file_bound(file_path: str, content: str) -> str:
        """Update an existing file with new content.

        Args:
            file_path: Path to the file relative to project root
            content: New content for the file

        Returns:
            Success or error message
        """
        return update_file.invoke({"file_path": file_path, "content": content, "project_root": project_root})
    
    @tool
    def replace_in_file_bound(file_path: str, search_text: str, replace_text: str) -> str:
        """Replace a specific snippet of text in a file with new text.
            Use this instead of overwriting the whole file for small changes.
    
        Args:
            file_path: Path to the file relative to project root
            search_text: The exact text snippet to look for and replace
            replace_text: The new text to insert in its place
            
        Returns:
            Success or error message
        """
        return replace_in_file.invoke({"file_path": file_path, "search_text": search_text, "replace_text": replace_text, "project_root": project_root})

    @tool
    def list_directory_bound(dir_path: str = ".") -> str:
        """List contents of a directory.

        Args:
            dir_path: Directory path relative to project root

        Returns:
            Directory listing
        """
        return list_directory.invoke({"dir_path": dir_path, "project_root": project_root})

    @tool
    def search_files_bound(pattern: str) -> str:
        """Search for files matching a pattern.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of matching file paths
        """
        return search_files.invoke({"pattern": pattern, "project_root": project_root})

    @tool
    def search_code_bound(query: str, file_pattern: str = "**/*.py") -> str:
        """Search for code matching a query in files.

        Args:
            query: Regular expression or plain text to search for
            file_pattern: Glob pattern for files to search (default: all Python files)

        Returns:
            Matching lines with file paths and line numbers
        """
        return search_code.invoke({"query": query, "file_pattern": file_pattern, "project_root": project_root})

    @tool
    def search_symbols_bound(symbol_name: str, symbol_type: str = "any") -> str:
        """Search for symbol definitions (functions, classes, etc.) in Python files.

        Args:
            symbol_name: Name of the symbol to find
            symbol_type: Type of symbol: 'function', 'class', 'any'

        Returns:
            Locations where the symbol is defined
        """
        return search_symbols.invoke({"symbol_name": symbol_name, "symbol_type": symbol_type, "project_root": project_root})

    @tool
    def run_command_bound(command: str, timeout: int = 60) -> str:
        """Execute a shell command in the project directory.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Command output (stdout and stderr combined)
        """
        return run_command.invoke({"command": command, "project_root": project_root, "timeout": timeout})

    return [
        read_file_bound,
        create_file_bound,
        update_file_bound,
        replace_in_file_bound,
        list_directory_bound,
        search_files_bound,
        search_code_bound,
        search_symbols_bound,
        run_command_bound,
    ]


async def run_agent(
    task: str,
    project_root: str,
    previous_messages: list | None = None,
) -> AgentState:
    """Run the agent on a given task.

    Args:
        task: Description of the task to solve
        project_root: Root directory of the project
        previous_messages: Optional list of previous conversation messages for context

    Returns:
        Final agent state
    """
    logger.info(f"Starting agent for task: {task}")
    logger.info(f"Project root: {project_root}")

    # Create the graph with tools bound to project_root
    graph = create_agent_graph_with_project_root(project_root)

    # Build message list with conversation history
    messages = []
    if previous_messages:
        messages.extend(previous_messages)
        logger.info(f"Including {len(previous_messages)} previous messages in context")

    # Add current user message
    messages.append(HumanMessage(content=task))

    # Initialize state with conversation history
    initial_state: AgentState = {
        "messages": messages,
        "task": task,
        "project_root": project_root,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    # Extract token usage from LLM response metadata
    messages = final_state.get("messages", [])
    total_input = 0
    total_output = 0

    for msg in messages:
        # Check for usage_metadata (newer format)
        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
            total_input += msg.usage_metadata.get("input_tokens", 0)
            total_output += msg.usage_metadata.get("output_tokens", 0)
        # Fallback to response_metadata (older format)
        elif hasattr(msg, "response_metadata") and msg.response_metadata:
            usage = msg.response_metadata.get("token_usage", {})
            total_input += usage.get("prompt_tokens", 0)
            total_output += usage.get("completion_tokens", 0)

    # Update state with token counts
    final_state["total_input_tokens"] = total_input
    final_state["total_output_tokens"] = total_output

    logger.info("Agent execution completed")
    logger.info(f"Token usage - Input: {total_input}, Output: {total_output}")

    return final_state
