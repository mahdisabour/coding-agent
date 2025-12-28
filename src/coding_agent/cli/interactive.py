"""Interactive CLI mode for multi-turn conversations."""

import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from coding_agent.agent.session import InteractiveSession

logger = logging.getLogger(__name__)
console = Console()


class InteractiveCLI:
    """Interactive command-line interface for the coding agent."""

    def __init__(self, session: InteractiveSession):
        """Initialize interactive CLI.

        Args:
            session: Interactive session instance
        """
        self.session = session
        self.running = True

    async def run(self) -> None:
        """Run the interactive session."""
        self._print_welcome()
        self._print_help()

        while self.running:
            try:
                # Get user input
                user_input = await self._get_input()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Process as a normal turn
                await self._process_turn(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit or continue typing[/yellow]")
                continue
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error in interactive session: {e}", exc_info=True)
                console.print(f"\n[red]Error: {str(e)}[/red]")
                console.print("[yellow]Session continues...[/yellow]\n")

        self._print_goodbye()

    def _print_welcome(self) -> None:
        """Print welcome message."""
        console.print(Panel(
            "[bold cyan]Coding Agent - Interactive Mode[/bold cyan]\n\n"
            f"Project: {self.session.project_root}\n"
            "Type your coding tasks or questions. Use /help for commands.",
            border_style="cyan",
            title="Welcome",
        ))

    def _print_help(self) -> None:
        """Print help message."""
        help_text = """[bold]Available Commands:[/bold]

[cyan]/help[/cyan]        - Show this help message
[cyan]/stats[/cyan]       - Show session statistics
[cyan]/context[/cyan]     - Show current context info
[cyan]/save[/cyan]        - Save session to file
[cyan]/load[/cyan]        - Load a previous session
[cyan]/clear[/cyan]       - Clear working context (keep history)
[cyan]/reset[/cyan]       - Reset entire session
[cyan]/exit[/cyan]        - Exit the session

[bold]Tips:[/bold]
- The agent remembers your conversation history
- Recently accessed files are tracked automatically
- Use natural language to describe tasks
- Check /stats regularly to monitor token usage
"""
        console.print(Panel(help_text, border_style="blue", title="Help"))

    def _print_goodbye(self) -> None:
        """Print goodbye message."""
        self.session.display_session_stats()

        console.print(Panel(
            "[bold cyan]Session Ended[/bold cyan]\n\n"
            "Use /save before exiting to preserve your session.\n"
            "Thank you for using Coding Agent!",
            border_style="cyan",
            title="Goodbye",
        ))

    async def _get_input(self) -> str:
        """Get user input.

        Returns:
            User input string
        """
        # Show context in prompt
        context_info = self.session.get_context_info()
        console.print(f"\n[dim]{context_info}[/dim]")

        # Get input
        user_input = await asyncio.to_thread(
            Prompt.ask,
            "\n[bold green]You[/bold green]",
        )

        return user_input.strip()

    async def _process_turn(self, user_message: str) -> None:
        """Process a conversation turn.

        Args:
            user_message: User's message
        """
        console.print(Rule(f"[bold cyan]Processing Turn {len(self.session.memory._turns) + 1}[/bold cyan]"))

        try:
            # Process the turn
            turn_result = await self.session.process_turn(user_message)

            # Display response
            console.print(f"\n[bold blue]Agent[/bold blue]:")
            console.print(Panel(
                turn_result["response"],
                border_style="blue",
                title="Response",
            ))

            # Display turn summary
            self.session.display_turn_summary(turn_result)

        except Exception as e:
            logger.error(f"Error processing turn: {e}", exc_info=True)
            console.print(f"[red]Error processing turn: {str(e)}[/red]")

    async def _handle_command(self, command: str) -> None:
        """Handle special commands.

        Args:
            command: Command string starting with /
        """
        cmd = command.lower().split()[0]

        if cmd == "/help":
            self._print_help()

        elif cmd == "/stats":
            self.session.display_session_stats()

        elif cmd == "/context":
            context_summary = self.session.memory.get_context_summary()
            console.print(Panel(
                context_summary,
                border_style="cyan",
                title="Context Summary",
            ))

        elif cmd == "/save":
            parts = command.split(maxsplit=1)
            output_path = Path(parts[1]) if len(parts) > 1 else None

            try:
                saved_path = self.session.save_session(output_path)
                console.print(f"[green]Session saved to: {saved_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error saving session: {str(e)}[/red]")

        elif cmd == "/load":
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[yellow]Usage: /load <session_file>[/yellow]")
                return

            try:
                session_path = Path(parts[1])
                loaded_session = InteractiveSession.load_session(
                    session_path,
                    project_root=self.session.project_root,
                )
                self.session = loaded_session
                console.print(f"[green]Session loaded from: {session_path}[/green]")
                stats = self.session.memory.get_session_stats()
                console.print(f"Restored {stats['total_turns']} turns")
            except Exception as e:
                console.print(f"[red]Error loading session: {str(e)}[/red]")

        elif cmd == "/clear":
            self.session.memory.clear_context()
            console.print("[green]Working context cleared (history preserved)[/green]")

        elif cmd == "/reset":
            confirm = await asyncio.to_thread(
                Prompt.ask,
                "Are you sure? This will delete all history",
                choices=["y", "n"],
                default="n",
            )
            if confirm == "y":
                self.session.memory.reset_session()
                console.print("[green]Session reset[/green]")

        elif cmd == "/exit" or cmd == "/quit" or cmd == "/q":
            console.print("\n[cyan]Exiting session...[/cyan]")
            self.running = False

        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            console.print("Type /help to see available commands")


async def run_interactive_session(
    project_root: str,
    load_session: Path | None = None,
) -> None:
    """Run an interactive coding session.

    Args:
        project_root: Root directory of the project
        load_session: Optional path to load existing session
    """
    # Create or load session
    if load_session:
        session = InteractiveSession.load_session(load_session, project_root)
        console.print(f"[green]Loaded session from {load_session}[/green]")
    else:
        session = InteractiveSession(project_root=project_root)

    # Run interactive CLI
    cli = InteractiveCLI(session)
    await cli.run()
