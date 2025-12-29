"""Agent nodes for LangGraph workflow."""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from coding_agent.agent.prompts import (
    EXECUTOR_PROMPT,
    PLANNER_PROMPT,
    REFLECTOR_PROMPT,
    VERIFIER_PROMPT,
)
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
)
from coding_agent.utils.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


def _create_llm(usage_tracker: UsageTracker | None = None) -> ChatOpenAI:
    """Create a ChatOpenAI instance with current settings.

    Args:
        usage_tracker: Optional usage tracker for token counting

    Returns:
        Configured ChatOpenAI instance
    """
    settings = get_settings()
    return ChatOpenAI(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_api_base,
    )


def _track_usage(
    state: AgentState,
    node_name: str,
    response: Any,
    usage_tracker: UsageTracker | None,
) -> None:
    """Track token usage for a node.

    Args:
        state: Current agent state
        node_name: Name of the node
        response: LLM response
        usage_tracker: Usage tracker instance
    """
    if not usage_tracker or not hasattr(response, "usage_metadata"):
        return

    usage = response.usage_metadata
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    usage_tracker.record_usage(node_name, input_tokens, output_tokens)

    # Update state
    state["total_input_tokens"] += input_tokens
    state["total_output_tokens"] += output_tokens

    if node_name not in state["node_usage"]:
        state["node_usage"][node_name] = {"input_tokens": 0, "output_tokens": 0}

    state["node_usage"][node_name]["input_tokens"] += input_tokens
    state["node_usage"][node_name]["output_tokens"] += output_tokens


def planner_node(state: AgentState, usage_tracker: UsageTracker | None = None) -> AgentState:
    """Create a plan to solve the task.

    Args:
        state: Current agent state
        usage_tracker: Optional usage tracker

    Returns:
        Updated state with plan
    """
    logger.info("Planning phase...")

    llm = _create_llm(usage_tracker)

    prompt = PLANNER_PROMPT.format(
        task=state["task"],
        project_root=state["project_root"],
        iteration=state["iteration"],
    )

    messages = [SystemMessage(content=prompt), HumanMessage(content="Create the plan.")]

    response = llm.invoke(messages)
    _track_usage(state, "planner", response, usage_tracker)

    state["plan"] = response.content
    state["messages"].append(AIMessage(content=f"Plan created:\n{response.content}"))
    state["next_node"] = "execute"

    logger.info("Plan created")
    return state


def executor_node(state: AgentState, usage_tracker: UsageTracker | None = None) -> AgentState:
    """Execute the plan using available tools.

    Args:
        state: Current agent state
        usage_tracker: Optional usage tracker

    Returns:
        Updated state with execution results
    """
    logger.info("Execution phase...")

    llm = _create_llm(usage_tracker)

    # Bind tools to the LLM
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

    # Update tool project_root to current project
    for tool in tools:
        if hasattr(tool, "bind"):
            tool = tool.bind(project_root=state["project_root"])

    llm_with_tools = llm.bind_tools(tools)

    prompt = EXECUTOR_PROMPT.format(
        task=state["task"],
        plan=state.get("plan", "No plan available"),
        project_root=state["project_root"],
    )

    messages = [SystemMessage(content=prompt), HumanMessage(content="Execute the plan.")]

    # Execute with tool calling
    response = llm_with_tools.invoke(messages)
    _track_usage(state, "executor", response, usage_tracker)

    # Process tool calls if any
    execution_log = []

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Add project_root to args
            tool_args["project_root"] = state["project_root"]

            # Find and execute the tool
            tool_map = {t.name: t for t in tools}
            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                    execution_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": str(result),
                    })
                except Exception as e:
                    error_msg = f"Error executing {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    execution_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "error": error_msg,
                    })
                    state["errors"].append(error_msg)

    state["execution_results"] = execution_log
    state["messages"].append(AIMessage(content=f"Executed plan:\n{response.content}"))
    state["next_node"] = "verify"

    logger.info(f"Execution completed: {len(execution_log)} tool calls")
    return state


def verifier_node(state: AgentState, usage_tracker: UsageTracker | None = None) -> AgentState:
    """Verify the execution results.

    Args:
        state: Current agent state
        usage_tracker: Optional usage tracker

    Returns:
        Updated state with verification status
    """
    logger.info("Verification phase...")

    llm = _create_llm(usage_tracker)

    prompt = VERIFIER_PROMPT.format(
        task=state["task"],
        plan=state.get("plan", "No plan available"),
        execution_results="\n".join(
            [f"{i+1}. {r}" for i, r in enumerate(state["execution_results"])]
        ),
        project_root=state["project_root"],
    )

    messages = [SystemMessage(content=prompt), HumanMessage(content="Verify the solution.")]

    response = llm.invoke(messages)
    _track_usage(state, "verifier", response, usage_tracker)

    verification_result = response.content
    print(f"{verification_result=}")
    passed = "PASS" in verification_result.upper().split("\n")[0]

    state["verification_passed"] = passed
    state["messages"].append(AIMessage(content=f"Verification:\n{verification_result}"))

    if passed:
        state["next_node"] = "end"
        logger.info("Verification passed")
    else:
        settings = get_settings()
        if state["iteration"] >= settings.max_iterations:
            state["next_node"] = "end"
            logger.warning("Max iterations reached")
        else:
            state["next_node"] = "reflect" if settings.enable_reflection else "plan"
            logger.info("Verification failed, continuing...")

    return state


def reflector_node(state: AgentState, usage_tracker: UsageTracker | None = None) -> AgentState:
    """Reflect on failures and provide guidance for next iteration.

    Args:
        state: Current agent state
        usage_tracker: Optional usage tracker

    Returns:
        Updated state with reflection
    """
    logger.info("Reflection phase...")

    llm = _create_llm(usage_tracker)

    prompt = REFLECTOR_PROMPT.format(
        task=state["task"],
        plan=state.get("plan", "No plan available"),
        execution_results="\n".join(
            [f"{i+1}. {r}" for i, r in enumerate(state["execution_results"])]
        ),
        verification_result=state["messages"][-1].content if state["messages"] else "N/A",
        errors="\n".join(state["errors"]) if state["errors"] else "None",
        iteration=state["iteration"],
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content="Reflect on the failure."),
    ]

    response = llm.invoke(messages)
    _track_usage(state, "reflector", response, usage_tracker)

    state["reflection"] = response.content
    state["messages"].append(AIMessage(content=f"Reflection:\n{response.content}"))
    state["iteration"] += 1
    state["next_node"] = "plan"

    logger.info("Reflection completed")
    return state
