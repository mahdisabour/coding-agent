"""Token usage and cost tracking."""

import logging
from dataclasses import dataclass, field
from datetime import datetime

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Usage statistics for a single operation."""

    timestamp: datetime
    node_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float


@dataclass
class UsageTracker:
    """Track token usage and costs across agent execution."""

    model_name: str = "gpt-4-turbo-preview"
    cost_per_million_input: float = 10.0  # USD
    cost_per_million_output: float = 30.0  # USD

    _stats: list[UsageStats] = field(default_factory=list, init=False)
    _encoding: tiktoken.Encoding = field(init=False)

    def __post_init__(self):
        """Initialize the tokenizer."""
        try:
            self._encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            logger.warning(f"Model {self.model_name} not found, using cl100k_base encoding")
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self._encoding.encode(text))

    def record_usage(
        self,
        node_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageStats:
        """Record usage for a node execution.

        Args:
            node_name: Name of the node
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Usage statistics
        """
        total_tokens = input_tokens + output_tokens
        estimated_cost = (
            (input_tokens / 1_000_000) * self.cost_per_million_input
            + (output_tokens / 1_000_000) * self.cost_per_million_output
        )

        stats = UsageStats(
            timestamp=datetime.now(),
            node_name=node_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
        )

        self._stats.append(stats)
        logger.debug(
            f"Node {node_name}: {input_tokens} in, {output_tokens} out, "
            f"${estimated_cost:.4f}"
        )

        return stats

    def get_total_stats(self) -> dict:
        """Get aggregated statistics.

        Returns:
            Dictionary with total usage and cost
        """
        total_input = sum(s.input_tokens for s in self._stats)
        total_output = sum(s.output_tokens for s in self._stats)
        total_cost = sum(s.estimated_cost for s in self._stats)

        # Per-node breakdown
        node_stats = {}
        for stat in self._stats:
            if stat.node_name not in node_stats:
                node_stats[stat.node_name] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "calls": 0,
                }
            node_stats[stat.node_name]["input_tokens"] += stat.input_tokens
            node_stats[stat.node_name]["output_tokens"] += stat.output_tokens
            node_stats[stat.node_name]["cost"] += stat.estimated_cost
            node_stats[stat.node_name]["calls"] += 1

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "node_breakdown": node_stats,
            "total_operations": len(self._stats),
        }

    def print_summary(self) -> None:
        """Print a summary of usage statistics."""
        stats = self.get_total_stats()

        print("\n" + "=" * 60)
        print("USAGE SUMMARY")
        print("=" * 60)
        print(f"Total Input Tokens:  {stats['total_input_tokens']:,}")
        print(f"Total Output Tokens: {stats['total_output_tokens']:,}")
        print(f"Total Tokens:        {stats['total_tokens']:,}")
        print(f"Estimated Cost:      ${stats['total_cost_usd']:.4f}")
        print(f"Total Operations:    {stats['total_operations']}")

        print("\nPer-Node Breakdown:")
        print("-" * 60)
        for node, node_stat in stats["node_breakdown"].items():
            print(f"\n{node}:")
            print(f"  Calls:         {node_stat['calls']}")
            print(f"  Input Tokens:  {node_stat['input_tokens']:,}")
            print(f"  Output Tokens: {node_stat['output_tokens']:,}")
            print(f"  Cost:          ${node_stat['cost']:.4f}")
        print("=" * 60 + "\n")
