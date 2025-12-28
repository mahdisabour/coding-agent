"""LangGraph workflow for the coding agent."""

import logging
from typing import Literal

from langgraph.graph import END, StateGraph

from coding_agent.agent.nodes import (
    executor_node,
    planner_node,
    reflector_node,
    verifier_node,
)
from coding_agent.agent.state import AgentState
from coding_agent.config import get_settings
from coding_agent.utils.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


def should_continue(state: AgentState) -> Literal["plan", "execute", "verify", "reflect", "end"]:
    """Determine the next node based on state.

    Args:
        state: Current agent state

    Returns:
        Name of the next node to execute
    """
    return state.get("next_node", "end")


def create_agent_graph(usage_tracker: UsageTracker | None = None) -> StateGraph:
    """Create the LangGraph workflow for the coding agent.

    The workflow follows this pattern:
    1. Plan: Analyze task and create execution plan
    2. Execute: Use tools to implement the plan
    3. Verify: Check if the solution is correct
    4. Reflect: (Optional) If failed, analyze and retry
    5. End: Finish execution

    Args:
        usage_tracker: Optional usage tracker for monitoring token usage

    Returns:
        Compiled StateGraph workflow
    """
    settings = get_settings()

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("plan", lambda state: planner_node(state, usage_tracker))
    workflow.add_node("execute", lambda state: executor_node(state, usage_tracker))
    workflow.add_node("verify", lambda state: verifier_node(state, usage_tracker))

    if settings.enable_reflection:
        workflow.add_node("reflect", lambda state: reflector_node(state, usage_tracker))

    # Set entry point
    workflow.set_entry_point("plan")

    # Add conditional edges based on state
    workflow.add_conditional_edges(
        "plan",
        should_continue,
        {
            "execute": "execute",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "verify": "verify",
            "end": END,
        },
    )

    if settings.enable_reflection:
        workflow.add_conditional_edges(
            "verify",
            should_continue,
            {
                "reflect": "reflect",
                "plan": "plan",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "reflect",
            should_continue,
            {
                "plan": "plan",
                "end": END,
            },
        )
    else:
        workflow.add_conditional_edges(
            "verify",
            should_continue,
            {
                "plan": "plan",
                "end": END,
            },
        )

    # Compile the graph
    return workflow.compile()


async def run_agent(
    task: str,
    project_root: str,
    usage_tracker: UsageTracker | None = None,
) -> AgentState:
    """Run the agent on a given task.

    Args:
        task: Description of the task to solve
        project_root: Root directory of the project
        usage_tracker: Optional usage tracker

    Returns:
        Final agent state
    """
    logger.info(f"Starting agent for task: {task}")
    logger.info(f"Project root: {project_root}")

    # Create the graph
    graph = create_agent_graph(usage_tracker)

    # Initialize state
    initial_state: AgentState = {
        "messages": [],
        "task": task,
        "project_root": project_root,
        "plan": None,
        "execution_results": [],
        "verification_passed": False,
        "reflection": None,
        "iteration": 0,
        "next_node": "plan",
        "errors": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "node_usage": {},
    }

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    logger.info("Agent execution completed")
    return final_state
