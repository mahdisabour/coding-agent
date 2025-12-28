"""Interactive session management for multi-turn conversations."""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from coding_agent.agent.graph import run_agent
from coding_agent.config import get_settings
from coding_agent.utils.memory import ConversationMemory
from coding_agent.utils.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)
console = Console()


class InteractiveSession:
    """Manages an interactive multi-turn coding session."""

    def __init__(
        self,
        project_root: str,
        memory: ConversationMemory | None = None,
        usage_tracker: UsageTracker | None = None,
    ):
        """Initialize interactive session.

        Args:
            project_root: Root directory of the project
            memory: Optional existing conversation memory
            usage_tracker: Optional usage tracker
        """
        self.project_root = project_root
        self.memory = memory or ConversationMemory(project_root=project_root)
        self.settings = get_settings()

        if usage_tracker is None and self.settings.track_usage:
            usage_tracker = UsageTracker(
                model_name=self.settings.model_name,
                cost_per_million_input=self.settings.cost_per_million_input_tokens,
                cost_per_million_output=self.settings.cost_per_million_output_tokens,
            )
        self.usage_tracker = usage_tracker

    async def process_turn(self, user_message: str) -> dict:
        """Process a single conversation turn.

        Args:
            user_message: User's input message

        Returns:
            Dictionary with turn results
        """
        logger.info(f"Processing turn {len(self.memory._turns) + 1}")

        # Get context from memory
        context_summary = self.memory.get_context_summary()

        # Enhance the task with context
        enhanced_task = self._build_contextualized_task(user_message, context_summary)

        # Run the agent
        final_state = await run_agent(
            task=enhanced_task,
            project_root=self.project_root,
            usage_tracker=self.usage_tracker,
        )

        # Extract results
        agent_response = self._extract_response(final_state)
        plan = final_state.get("plan")
        verification_passed = final_state.get("verification_passed", False)
        iterations = final_state.get("iteration", 0)
        errors = final_state.get("errors", [])

        # Calculate tokens and cost for this turn
        turn_input_tokens = final_state.get("total_input_tokens", 0)
        turn_output_tokens = final_state.get("total_output_tokens", 0)

        turn_cost = 0.0
        if self.usage_tracker:
            turn_cost = (
                (turn_input_tokens / 1_000_000) * self.usage_tracker.cost_per_million_input
                + (turn_output_tokens / 1_000_000) * self.usage_tracker.cost_per_million_output
            )

        # Add to memory
        turn = self.memory.add_turn(
            user_message=user_message,
            agent_response=agent_response,
            plan=plan,
            verification_passed=verification_passed,
            iterations=iterations,
            errors=errors,
            input_tokens=turn_input_tokens,
            output_tokens=turn_output_tokens,
            cost=turn_cost,
        )

        # Track file accesses from execution results
        for result in final_state.get("execution_results", []):
            if "args" in result and "file_path" in result["args"]:
                self.memory.track_file_access(result["args"]["file_path"])

        return {
            "turn": turn,
            "final_state": final_state,
            "response": agent_response,
        }

    def _build_contextualized_task(self, user_message: str, context_summary: str) -> str:
        """Build task with conversation context.

        Args:
            user_message: Current user message
            context_summary: Summary of conversation context

        Returns:
            Contextualized task description
        """
        if not self.memory._turns:
            # First turn - no context needed
            return user_message

        # Include relevant context
        return f"""Context from previous conversation:
{context_summary}

Current task:
{user_message}

Note: Consider the conversation history when planning and executing this task."""

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
                # Skip verification and reflection messages for cleaner output
                content = msg.content
                if not content.startswith("Verification:") and not content.startswith("Reflection:"):
                    return content

        return "Task processed."

    def display_turn_summary(self, turn_result: dict) -> None:
        """Display summary of the completed turn.

        Args:
            turn_result: Result dictionary from process_turn
        """
        turn = turn_result["turn"]

        # Create summary table
        table = Table(title=f"Turn {turn.turn_number} Summary", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        status = "✓ Success" if turn.verification_passed else "✗ Failed"
        status_style = "green" if turn.verification_passed else "red"

        table.add_row("Status", f"[{status_style}]{status}[/{status_style}]")
        table.add_row("Iterations", str(turn.iterations))
        table.add_row("Errors", str(len(turn.errors)))
        table.add_row("Input Tokens", f"{turn.input_tokens:,}")
        table.add_row("Output Tokens", f"{turn.output_tokens:,}")
        table.add_row("Cost", f"${turn.cost:.4f}")

        console.print("\n")
        console.print(table)

        if turn.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in turn.errors[:3]:  # Show first 3 errors
                console.print(f"  - {error}")

    def display_session_stats(self) -> None:
        """Display cumulative session statistics."""
        stats = self.memory.get_session_stats()

        table = Table(title="Session Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Total Turns", str(stats["total_turns"]))
        table.add_row("Successful", f"[green]{stats['successful_turns']}[/green]")
        table.add_row("Failed", f"[red]{stats['failed_turns']}[/red]")
        table.add_row("Success Rate", f"{stats['success_rate']:.1%}")
        table.add_row("", "")  # Separator
        table.add_row("Total Input Tokens", f"{stats['total_input_tokens']:,}")
        table.add_row("Total Output Tokens", f"{stats['total_output_tokens']:,}")
        table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
        table.add_row("", "")  # Separator
        table.add_row("Total Cost", f"[bold]${stats['total_cost']:.4f}[/bold]")
        table.add_row("Avg Cost/Turn", f"${stats['avg_cost_per_turn']:.4f}")
        table.add_row("", "")  # Separator
        table.add_row("Total Iterations", str(stats["total_iterations"]))
        table.add_row("Total Errors", str(stats["total_errors"]))

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
