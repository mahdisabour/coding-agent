"""Evaluation runner for SWE-bench and other datasets."""

import json
import logging
from datetime import datetime
from pathlib import Path

from datasets import load_dataset
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn

from coding_agent.agent.graph import run_agent
from coding_agent.config import get_settings
from coding_agent.evaluation.metrics import calculate_metrics
from coding_agent.utils.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)
console = Console()


async def run_evaluation(
    dataset_name: str = "SWE-bench/SWE-bench_Lite",
    split: str = "test",
    limit: int | None = None,
    output_file: Path = Path("eval_results.json"),
) -> dict:
    """Run evaluation on a dataset.

    Args:
        dataset_name: HuggingFace dataset identifier
        split: Dataset split to use
        limit: Optional limit on number of instances
        output_file: Path to save results

    Returns:
        Evaluation results dictionary
    """
    logger.info(f"Loading dataset: {dataset_name}")
    console.print(f"\n[cyan]Loading dataset {dataset_name}...[/cyan]")

    try:
        dataset = load_dataset(dataset_name, split=split)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Limit dataset if specified
    if limit:
        dataset = dataset.select(range(min(limit, len(dataset))))

    console.print(f"[green]Loaded {len(dataset)} instances[/green]\n")

    settings = get_settings()
    results = []
    total_usage = UsageTracker(
        model_name=settings.model_name,
        cost_per_million_input=settings.cost_per_million_input_tokens,
        cost_per_million_output=settings.cost_per_million_output_tokens,
    )

    # Progress tracking
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Evaluating...", total=len(dataset))

        for idx, instance in enumerate(dataset):
            instance_id = instance.get("instance_id", f"instance_{idx}")
            problem_statement = instance.get("problem_statement", "")

            console.print(f"\n[bold]Instance {idx + 1}/{len(dataset)}: {instance_id}[/bold]")

            # Create usage tracker for this instance
            instance_tracker = UsageTracker(
                model_name=settings.model_name,
                cost_per_million_input=settings.cost_per_million_input_tokens,
                cost_per_million_output=settings.cost_per_million_output_tokens,
            )

            start_time = datetime.now()

            try:
                # Run agent on the problem
                # For SWE-bench, we would typically:
                # 1. Clone the repo at the specified version
                # 2. Set up the environment
                # 3. Run the agent to create a patch
                # 4. Apply and test the patch

                # Simplified version - just run the agent
                final_state = await run_agent(
                    task=problem_statement,
                    project_root=".",  # In real eval, use cloned repo path
                    usage_tracker=instance_tracker,
                )

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Collect results
                result = {
                    "instance_id": instance_id,
                    "success": final_state["verification_passed"],
                    "iterations": final_state["iteration"],
                    "errors": final_state["errors"],
                    "duration_seconds": duration,
                    "usage": instance_tracker.get_total_stats(),
                }

                # Accumulate usage
                for stat in instance_tracker._stats:
                    total_usage.record_usage(
                        stat.node_name,
                        stat.input_tokens,
                        stat.output_tokens,
                    )

            except Exception as e:
                logger.error(f"Error evaluating {instance_id}: {e}")
                result = {
                    "instance_id": instance_id,
                    "success": False,
                    "error": str(e),
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                }

            results.append(result)
            progress.update(task, advance=1)

            # Save intermediate results
            _save_results(results, output_file, total_usage)

    # Calculate final metrics
    metrics = calculate_metrics(results)

    # Final output
    final_output = {
        "dataset": dataset_name,
        "split": split,
        "total_instances": len(dataset),
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "total_usage": total_usage.get_total_stats(),
        "results": results,
    }

    _save_results([final_output], output_file.with_suffix(".final.json"), total_usage)

    # Display summary
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]EVALUATION SUMMARY[/bold cyan]")
    console.print("=" * 60)
    console.print(f"Total Instances: {metrics['total']}")
    console.print(f"Successful: {metrics['successful']} ({metrics['success_rate']:.1%})")
    console.print(f"Failed: {metrics['failed']}")
    console.print(f"Avg Iterations: {metrics['avg_iterations']:.2f}")
    console.print(f"Total Duration: {metrics['total_duration_seconds']:.2f}s")
    console.print("=" * 60)

    return final_output


def _save_results(results: list, output_file: Path, usage_tracker: UsageTracker) -> None:
    """Save results to file.

    Args:
        results: List of result dictionaries
        output_file: Path to output file
        usage_tracker: Usage tracker instance
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "usage": usage_tracker.get_total_stats(),
    }

    with output_file.open("w") as f:
        json.dump(output, f, indent=2)

    logger.debug(f"Results saved to {output_file}")
