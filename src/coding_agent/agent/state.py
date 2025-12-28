"""Agent state definition for LangGraph."""

from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State for the coding agent."""

    # Messages in the conversation
    messages: Annotated[list[BaseMessage], add_messages]

    # Current task/problem to solve
    task: str

    # Project root path
    project_root: str

    # Current plan
    plan: str | None

    # Execution results
    execution_results: list[dict]

    # Verification status
    verification_passed: bool

    # Reflection notes
    reflection: str | None

    # Iteration counter
    iteration: int

    # Next node to execute
    next_node: Literal["plan", "execute", "verify", "reflect", "end"] | None

    # Error tracking
    errors: list[str]

    # Usage tracking
    total_input_tokens: int
    total_output_tokens: int
    node_usage: dict[str, dict[str, int]]  # node_name -> {input_tokens, output_tokens}
