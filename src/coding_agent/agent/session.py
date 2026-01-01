"""Interactive session management for multi-turn conversations."""

import logging
import asyncio
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from coding_agent.agent.graph import run_agent
from coding_agent.config import get_settings
from coding_agent.utils.memory import ConversationMemory
from langgraph.checkpoint.memory import MemorySaver
from uuid import uuid4
from langchain_core.messages import HumanMessage, ToolMessage
from coding_agent.agent.graph import create_agent_graph_with_project_root, SAFE_TOOLS

logger = logging.getLogger(__name__)
console = Console()


class InteractiveSession:
    """Manages an interactive multi-turn coding session."""

    def __init__(
        self,
        project_root: str,
        memory: ConversationMemory | None = None,
    ):
        """Initialize interactive session.

        Args:
            project_root: Root directory of the project
            memory: Optional existing conversation memory
        """
        self.project_root = project_root
        self.memory = memory or ConversationMemory(project_root=project_root)
        self.settings = get_settings()

        self.checkpointer = MemorySaver()
        self.thread_id = str(uuid4())

        self.graph = create_agent_graph_with_project_root(
            project_root, 
            checkpointer=self.checkpointer
        )

    async def _get_user_approval(self, tool_name: str, tool_args: dict) -> str:
        """Helper to ask the user for permission."""
        console.print(f"\n[bold yellow]⚠️  The Agent wants to run: {tool_name}[/bold yellow]")
        console.print(f"Args: {tool_args}")
        
        response = await asyncio.to_thread(
            Prompt.ask, 
            "Allow this action?", 
            choices=["y", "n"], 
            default="y"
        )
        return "yes" if response == "y" else "no"

    async def process_turn(self, user_message: str) -> dict:
        """Process a single conversation turn.

        Args:
            user_message: User's input message

        Returns:
            Dictionary with turn results
        """
        logger.info(f"Processing turn {len(self.memory._turns) + 1}")

        config = {"configurable": {"thread_id": self.thread_id}}

        snapshot = self.graph.get_state(config)
        
        messages_to_send = []
        
        if len(snapshot.values) > 0:
            # CASE A: WARM START (Graph has memory)
            messages_to_send = [HumanMessage(content=user_message)]
            inputs = {"messages": messages_to_send, "task": user_message, "project_root": self.project_root}
            logger.info("Resuming existing LangGraph thread")
            
        else:
            # CASE B: COLD START (Graph is empty)
            context_messages = self.memory.get_context_messages()
            messages_to_send = context_messages + [HumanMessage(content=user_message)]
            inputs = {"messages": messages_to_send, "task": user_message, "project_root": self.project_root,
                       "total_input_tokens": 0, "total_output_tokens": 0,}
            logger.info(f"Initializing LangGraph thread with {len(context_messages)} past messages")

        # We use astream to advance the graph until it finishes OR hits an interrupt
        async for event in self.graph.astream(inputs, config, stream_mode="values"):
            pass

        # THE INTERRUPT LOOP (Handle pauses for Tools)
        while True:
            snapshot = self.graph.get_state(config)
            
            if not snapshot.next:
                break
            
            last_message = snapshot.values["messages"][-1]
            
            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                async for event in self.graph.astream(None, config, stream_mode="values"):
                    pass
                continue

            tool_call = last_message.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name in SAFE_TOOLS:
                console.print(f"[dim]Auto-approving safe tool: {tool_name}[/dim]")
                
                async for event in self.graph.astream(None, config, stream_mode="values"):
                    pass
            
            else:
                decision = await self._get_user_approval(tool_name, tool_args)
                
                if decision == "yes":
                    console.print("[green]Approved.[/green]")
                    # RESUME standard execution
                    async for event in self.graph.astream(None, config, stream_mode="values"):
                        pass
                
                else:
                    console.print("[red]Rejected.[/red]")
                    
                    # REJECT: We must "fake" a tool failure to the agent.
                    rejection_message = ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=f"Error: User blocked the execution of {tool_name}."
                    )
                    
                    # We inject this message into the state using update_state
                    self.graph.update_state(
                        config, 
                        {"messages": [rejection_message]}, 
                        as_node="tools"
                    )
                    
                    # RESUME: The agent will now see the error message and try again
                    async for event in self.graph.astream(None, config, stream_mode="values"):
                        pass
        
        final_state = self.graph.get_state(config).values

        # Extract results
        agent_response = self._extract_response(final_state)

        # Get tokens from state
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

        turn_input_tokens = final_state.get("total_input_tokens", 0)
        turn_output_tokens = final_state.get("total_output_tokens", 0)

        # Calculate cost
        turn_cost = (
            (turn_input_tokens / 1_000_000) * self.settings.cost_per_million_input_tokens
            + (turn_output_tokens / 1_000_000) * self.settings.cost_per_million_output_tokens
        )

        # Add to memory (with simplified fields)
        turn = self.memory.add_turn(
            user_message=user_message,
            agent_response=agent_response,
            input_tokens=turn_input_tokens,
            output_tokens=turn_output_tokens,
            cost=turn_cost,
        )

        return {
            "turn": turn,
            "final_state": final_state,
            "response": agent_response,
        }

    def _extract_response(self, final_state: dict) -> str:
        """Extract human-readable response from agent state.

        Args:
            final_state: Final agent state

        Returns:
            Response string
        """
        messages = final_state.get("messages", [])
        if not messages:
            return "No response generated."

        # Get the last AI message
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content

        return "Task processed."

    def display_turn_summary(self, turn_result: dict) -> None:
        """Display summary of the completed turn.

        Args:
            turn_result: Result dictionary from process_turn
        """
        turn = turn_result["turn"]

        # Simple completion message
        console.print(f"\n[green]✓ Turn {turn.turn_number} completed[/green]")
        console.print(f"[dim]Cost: ${turn.cost:.4f}[/dim]")

    def display_session_stats(self) -> None:
        """Display cumulative session statistics."""
        stats = self.memory.get_session_stats()

        table = Table(title="Session Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Total Turns", str(stats["total_turns"]))
        table.add_row("", "")  # Separator
        table.add_row("Total Input Tokens", f"{stats['total_input_tokens']:,}")
        table.add_row("Total Output Tokens", f"{stats['total_output_tokens']:,}")
        table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
        table.add_row("", "")  # Separator
        table.add_row("Total Cost", f"[bold]${stats['total_cost']:.4f}[/bold]")
        table.add_row("Avg Cost/Turn", f"${stats['avg_cost_per_turn']:.4f}")

        console.print("\n")
        console.print(table)
        console.print()

    def save_session(self, output_path: Path | None = None) -> Path:
        """Save the current session.

        Args:
            output_path: Optional output path

        Returns:
            Path where session was saved
        """
        return self.memory.save_session(output_path)

    @classmethod
    def load_session(cls, session_path: Path, project_root: str | None = None) -> "InteractiveSession":
        """Load a saved session.

        Args:
            session_path: Path to session file
            project_root: Optional override for project root

        Returns:
            Loaded InteractiveSession
        """
        memory = ConversationMemory.load_session(session_path, project_root)
        return cls(project_root=memory.project_root, memory=memory)

    def get_context_info(self) -> str:
        """Get information about current context.

        Returns:
            Context information string
        """
        stats = self.memory.get_session_stats()
        context_messages = self.memory.get_context_messages()

        info_parts = [
            f"Project: {self.project_root}",
            f"Turns: {stats['total_turns']}",
            f"Context window: {len(context_messages)} messages",
            f"Recent files: {len(self.memory._recent_files)}",
        ]

        if stats["total_tokens"] > 0:
            info_parts.append(f"Total tokens: {stats['total_tokens']:,}")

        return " | ".join(info_parts)
