"""Metrics calculation for evaluation."""

from typing import Any


def calculate_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate evaluation metrics from results.

    Args:
        results: List of evaluation results

    Returns:
        Dictionary of calculated metrics
    """
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total - successful

    # Calculate averages
    iterations = [r.get("iterations", 0) for r in results if "iterations" in r]
    avg_iterations = sum(iterations) / len(iterations) if iterations else 0

    durations = [r.get("duration_seconds", 0) for r in results if "duration_seconds" in r]
    total_duration = sum(durations)
    avg_duration = total_duration / len(durations) if durations else 0

    # Error analysis
    error_counts: dict[str, int] = {}
    for result in results:
        if result.get("errors"):
            for error in result["errors"]:
                error_type = error.split(":")[0] if ":" in error else "Unknown"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total if total > 0 else 0,
        "avg_iterations": avg_iterations,
        "avg_duration_seconds": avg_duration,
        "total_duration_seconds": total_duration,
        "error_breakdown": error_counts,
    }
