"""Agent state definition for LangGraph."""

from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """State for the coding agent."""

    # Messages in the conversation
    messages: Annotated[list[BaseMessage], add_messages]

    # Current task/problem to solve
    task: str

    # Project root path
    project_root: str

    # Usage tracking (accumulated throughout the session)
    total_input_tokens: int
    total_output_tokens: int
