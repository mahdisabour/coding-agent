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

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Professional CLI-based coding agent with LangGraph.

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
                )
            )

        # Display results
        console.print("\n" + "=" * 60)
        console.print("[bold green]Task completed![/bold green]")

        # Display usage statistics
        if settings.track_usage and not no_tracking:
            input_tokens = final_state.get("total_input_tokens", 0)
            output_tokens = final_state.get("total_output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            cost = (
                (input_tokens / 1_000_000) * settings.cost_per_million_input_tokens
                + (output_tokens / 1_000_000) * settings.cost_per_million_output_tokens
            )

            console.print("\n" + "=" * 60)
            console.print("[bold]Token Usage[/bold]")
            console.print("=" * 60)
            console.print(f"Input Tokens:  {input_tokens:,}")
            console.print(f"Output Tokens: {output_tokens:,}")
            console.print(f"Total Tokens:  {total_tokens:,}")
            console.print(f"Estimated Cost: ${cost:.4f}")
            console.print("=" * 60)

    except KeyboardInterrupt:
        console.print("\n[yellow]Agent interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.error("Agent execution failed", exc_info=True)
        raise click.Abort()


@cli.command()
def version():
    """Display version information."""
    console.print("[bold cyan]Coding Agent[/bold cyan] version 0.1.0")
    console.print("\nA professional CLI-based coding agent with:")
    console.print("  - LangGraph ReAct workflow")
    console.print("  - Multi-turn conversation support")
    console.print("  - Token usage and cost tracking")


if __name__ == "__main__":
    cli()
