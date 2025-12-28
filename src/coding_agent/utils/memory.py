"""Memory management for multi-turn conversations."""

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""

    turn_number: int
    timestamp: datetime
    user_message: str
    agent_response: str
    plan: str | None
    verification_passed: bool
    iterations: int
    errors: list[str]
    input_tokens: int
    output_tokens: int
    cost: float


@dataclass
class ConversationMemory:
    """Manages conversation history and context for multi-turn interactions."""

    project_root: str
    max_turns_in_context: int = 10
    max_tokens_per_turn: int = 8000

    _turns: list[ConversationTurn] = field(default_factory=list, init=False)
    _working_context: dict[str, Any] = field(default_factory=dict, init=False)
    _file_cache: dict[str, str] = field(default_factory=dict, init=False)
    _recent_files: deque = field(default_factory=lambda: deque(maxlen=20), init=False)

    def add_turn(
        self,
        user_message: str,
        agent_response: str,
        plan: str | None,
        verification_passed: bool,
        iterations: int,
        errors: list[str],
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> ConversationTurn:
        """Add a completed turn to memory.

        Args:
            user_message: User's input
            agent_response: Agent's response
            plan: Execution plan
            verification_passed: Whether verification passed
            iterations: Number of iterations
            errors: List of errors encountered
            input_tokens: Input token count
            output_tokens: Output token count
            cost: Estimated cost

        Returns:
            The created ConversationTurn
        """
        turn = ConversationTurn(
            turn_number=len(self._turns) + 1,
            timestamp=datetime.now(),
            user_message=user_message,
            agent_response=agent_response,
            plan=plan,
            verification_passed=verification_passed,
            iterations=iterations,
            errors=errors,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        self._turns.append(turn)
        logger.info(f"Added turn {turn.turn_number} to memory")
        return turn

    def get_context_messages(self) -> list[BaseMessage]:
        """Get recent conversation history as messages for context.

        Returns:
            List of messages representing recent conversation
        """
        # Get recent turns based on max_turns_in_context
        recent_turns = self._turns[-self.max_turns_in_context:]

        messages = []
        for turn in recent_turns:
            messages.append(HumanMessage(content=turn.user_message))

            # Include plan and response
            response_content = ""
            if turn.plan:
                response_content += f"Plan: {turn.plan}\n\n"
            response_content += f"Response: {turn.agent_response}"

            messages.append(AIMessage(content=response_content))

        return messages

    def get_context_summary(self) -> str:
        """Generate a summary of the conversation context.

        Returns:
            String summary of recent context
        """
        if not self._turns:
            return "No previous context."

        recent_turns = self._turns[-self.max_turns_in_context:]

        summary_parts = [
            f"Project: {self.project_root}",
            f"Total turns: {len(self._turns)}",
            f"Recent context (last {len(recent_turns)} turns):",
        ]

        for turn in recent_turns:
            status = "✓" if turn.verification_passed else "✗"
            summary_parts.append(
                f"\nTurn {turn.turn_number} [{status}]: {turn.user_message[:100]}..."
            )

        if self._recent_files:
            summary_parts.append(f"\n\nRecently accessed files:")
            for file_path in list(self._recent_files)[-5:]:
                summary_parts.append(f"  - {file_path}")

        return "\n".join(summary_parts)

    def update_working_context(self, key: str, value: Any) -> None:
        """Update working context with key-value pairs.

        Args:
            key: Context key
            value: Context value
        """
        self._working_context[key] = value
        logger.debug(f"Updated working context: {key}")

    def get_working_context(self, key: str, default: Any = None) -> Any:
        """Get value from working context.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return self._working_context.get(key, default)

    def track_file_access(self, file_path: str, content: str | None = None) -> None:
        """Track file accesses for context.

        Args:
            file_path: Path to the file
            content: Optional file content for caching
        """
        self._recent_files.append(file_path)
        if content is not None:
            self._file_cache[file_path] = content
        logger.debug(f"Tracked file access: {file_path}")

    def get_cached_file(self, file_path: str) -> str | None:
        """Get cached file content.

        Args:
            file_path: Path to the file

        Returns:
            Cached content or None
        """
        return self._file_cache.get(file_path)

    def get_session_stats(self) -> dict[str, Any]:
        """Get statistics for the current session.

        Returns:
            Dictionary of session statistics
        """
        if not self._turns:
            return {
                "total_turns": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "success_rate": 0.0,
            }

        total_input = sum(t.input_tokens for t in self._turns)
        total_output = sum(t.output_tokens for t in self._turns)
        total_cost = sum(t.cost for t in self._turns)
        successful = sum(1 for t in self._turns if t.verification_passed)

        return {
            "total_turns": len(self._turns),
            "successful_turns": successful,
            "failed_turns": len(self._turns) - successful,
            "success_rate": successful / len(self._turns) if self._turns else 0.0,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "avg_cost_per_turn": total_cost / len(self._turns) if self._turns else 0.0,
            "total_iterations": sum(t.iterations for t in self._turns),
            "total_errors": sum(len(t.errors) for t in self._turns),
        }

    def save_session(self, output_path: Path | None = None) -> Path:
        """Save session to file.

        Args:
            output_path: Optional output path

        Returns:
            Path where session was saved
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"session_{timestamp}.json")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        session_data = {
            "project_root": self.project_root,
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_session_stats(),
            "turns": [
                {
                    "turn_number": t.turn_number,
                    "timestamp": t.timestamp.isoformat(),
                    "user_message": t.user_message,
                    "agent_response": t.agent_response,
                    "plan": t.plan,
                    "verification_passed": t.verification_passed,
                    "iterations": t.iterations,
                    "errors": t.errors,
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "cost": t.cost,
                }
                for t in self._turns
            ],
            "recent_files": list(self._recent_files),
            "working_context": self._working_context,
        }

        with output_path.open("w") as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session saved to {output_path}")
        return output_path

    @classmethod
    def load_session(cls, session_path: Path, project_root: str | None = None) -> "ConversationMemory":
        """Load session from file.

        Args:
            session_path: Path to session file
            project_root: Optional override for project root

        Returns:
            Loaded ConversationMemory instance
        """
        with Path(session_path).open("r") as f:
            session_data = json.load(f)

        memory = cls(
            project_root=project_root or session_data["project_root"]
        )

        # Restore turns
        for turn_data in session_data.get("turns", []):
            memory._turns.append(ConversationTurn(
                turn_number=turn_data["turn_number"],
                timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                user_message=turn_data["user_message"],
                agent_response=turn_data["agent_response"],
                plan=turn_data.get("plan"),
                verification_passed=turn_data["verification_passed"],
                iterations=turn_data["iterations"],
                errors=turn_data["errors"],
                input_tokens=turn_data["input_tokens"],
                output_tokens=turn_data["output_tokens"],
                cost=turn_data["cost"],
            ))

        # Restore context
        memory._recent_files = deque(session_data.get("recent_files", []), maxlen=20)
        memory._working_context = session_data.get("working_context", {})

        logger.info(f"Session loaded from {session_path}")
        return memory

    def clear_context(self) -> None:
        """Clear conversation context but keep history."""
        self._working_context.clear()
        self._file_cache.clear()
        logger.info("Cleared working context")

    def reset_session(self) -> None:
        """Reset entire session including history."""
        self._turns.clear()
        self._working_context.clear()
        self._file_cache.clear()
        self._recent_files.clear()
        logger.info("Reset session")
