"""Tests for usage tracker."""

from coding_agent.utils.usage_tracker import UsageTracker


def test_usage_tracker_initialization():
    """Test usage tracker initialization."""
    tracker = UsageTracker(
        model_name="gpt-4-turbo-preview",
        cost_per_million_input=10.0,
        cost_per_million_output=30.0,
    )
    assert tracker.model_name == "gpt-4-turbo-preview"
    assert tracker.cost_per_million_input == 10.0
    assert tracker.cost_per_million_output == 30.0


def test_record_usage():
    """Test recording usage."""
    tracker = UsageTracker()

    stats = tracker.record_usage(
        node_name="planner",
        input_tokens=100,
        output_tokens=50,
    )

    assert stats.node_name == "planner"
    assert stats.input_tokens == 100
    assert stats.output_tokens == 50
    assert stats.total_tokens == 150


def test_get_total_stats():
    """Test getting total statistics."""
    tracker = UsageTracker()

    # Record multiple operations
    tracker.record_usage("planner", 100, 50)
    tracker.record_usage("executor", 200, 100)
    tracker.record_usage("planner", 150, 75)

    stats = tracker.get_total_stats()

    assert stats["total_input_tokens"] == 450
    assert stats["total_output_tokens"] == 225
    assert stats["total_tokens"] == 675
    assert stats["total_operations"] == 3

    # Check per-node breakdown
    assert "planner" in stats["node_breakdown"]
    assert stats["node_breakdown"]["planner"]["calls"] == 2
    assert stats["node_breakdown"]["planner"]["input_tokens"] == 250


def test_count_tokens():
    """Test token counting."""
    tracker = UsageTracker()

    text = "Hello, world!"
    token_count = tracker.count_tokens(text)

    assert isinstance(token_count, int)
    assert token_count > 0
