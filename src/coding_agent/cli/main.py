"""Main CLI interface for the coding agent."""

import asyncio
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from coding_agent.agent.graph import run_agent
from coding_agent.cli.interactive import run_interactive_session
from coding_agent.config import get_settings
from coding_agent.utils.logging import setup_logging
from coding_agent.utils.usage_tracker import UsageTracker

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Professional CLI-based coding agent with LangGraph and MCP support.

    Run 'coding-agent chat' to start an interactive session (recommended).
    """
    pass


@cli.command()
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Root directory of the project to work on",
)
@click.option(
    "--load-session",
    "-l",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Load a previous session",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def chat(
    project_root: Path,
    load_session: Path | None,
    verbose: bool,
):
    """Start an interactive multi-turn coding session (recommended).

    This is the main way to use the coding agent. It allows you to:
    - Have multi-turn conversations
    - Build on previous context
    - Track usage and costs across turns
    - Save and load sessions

    Example:
        coding-agent chat --project-root ./my-project
    """
    settings = get_settings()
    setup_logging(
        level="DEBUG" if verbose else settings.log_level,
        log_file=settings.log_file,
    )

    try:
        asyncio.run(
            run_interactive_session(
                project_root=str(project_root),
                load_session=load_session,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.error("Interactive session failed", exc_info=True)
        raise click.Abort()


@cli.command()
@click.argument("task", type=str)
@click.option(
    "--project-root",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Root directory of the project to work on",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--no-tracking",
    is_flag=True,
    help="Disable usage tracking",
)
def solve(
    task: str,
    project_root: Path,
    verbose: bool,
    no_tracking: bool,
):
    """Solve a single coding task (one-shot mode).

    For most use cases, use 'coding-agent chat' instead.

    TASK: Description of the task to solve

    Example:
        coding-agent solve "Add a hello world function" --project-root .
    """
    settings = get_settings()
    setup_logging(
        level="DEBUG" if verbose else settings.log_level,
        log_file=settings.log_file,
    )

    console.print(Panel.fit(
        f"[bold cyan]Coding Agent - Single Task Mode[/bold cyan]\n\n"
        f"Task: {task}\n"
        f"Project: {project_root}\n\n"
        f"[dim]Tip: Use 'coding-agent chat' for interactive multi-turn sessions[/dim]",
        border_style="cyan",
    ))

    # Initialize usage tracker
    usage_tracker = None
    if settings.track_usage and not no_tracking:
        usage_tracker = UsageTracker(
            model_name=settings.model_name,
            cost_per_million_input=settings.cost_per_million_input_tokens,
            cost_per_million_output=settings.cost_per_million_output_tokens,
        )

    # Run the agent
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Running agent...", total=None)

            final_state = asyncio.run(
                run_agent(
                    task=task,
                    project_root=str(project_root),
                    usage_tracker=usage_tracker,
                )
            )

        # Display results
        console.print("\n" + "=" * 60)
        if final_state["verification_passed"]:
            console.print("[bold green]Task completed successfully![/bold green]")
        else:
            console.print("[bold yellow]Task completed with issues.[/bold yellow]")

        console.print(f"\nIterations: {final_state['iteration']}")
        console.print(f"Errors: {len(final_state['errors'])}")

        if final_state["errors"]:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in final_state["errors"]:
                console.print(f"  - {error}")

        # Display usage statistics
        if usage_tracker:
            console.print()
            usage_tracker.print_summary()

    except KeyboardInterrupt:
        console.print("\n[yellow]Agent interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.error("Agent execution failed", exc_info=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--dataset",
    "-d",
    type=str,
    default="SWE-bench/SWE-bench_Lite",
    help="HuggingFace dataset identifier",
)
@click.option(
    "--split",
    "-s",
    type=str,
    default="test",
    help="Dataset split to use",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit number of instances to evaluate",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("eval_results.json"),
    help="Output file for results",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def evaluate(
    dataset: str,
    split: str,
    limit: int | None,
    output: Path,
    verbose: bool,
):
    """Run evaluation on SWE-bench Lite or other datasets.

    This command evaluates the agent on benchmark datasets.
    """
    from coding_agent.evaluation.runner import run_evaluation

    settings = get_settings()
    setup_logging(
        level="DEBUG" if verbose else settings.log_level,
        log_file=settings.log_file,
    )

    console.print(Panel.fit(
        f"[bold cyan]Evaluation Mode[/bold cyan]\n\n"
        f"Dataset: {dataset}\n"
        f"Split: {split}\n"
        f"Limit: {limit or 'All'}",
        border_style="cyan",
    ))

    try:
        asyncio.run(
            run_evaluation(
                dataset_name=dataset,
                split=split,
                limit=limit,
                output_file=output,
            )
        )

        console.print(f"\n[bold green]Evaluation complete![/bold green]")
        console.print(f"Results saved to: {output}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Evaluation interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.error("Evaluation failed", exc_info=True)
        raise click.Abort()


@cli.command()
def version():
    """Display version information."""
    console.print("[bold cyan]Coding Agent[/bold cyan] version 0.1.0")
    console.print("\nA professional CLI-based coding agent with:")
    console.print("  - LangGraph workflow")
    console.print("  - MCP server integration")
    console.print("  - SWE-bench evaluation support")
    console.print("  - Usage and cost tracking")


if __name__ == "__main__":
    cli()
