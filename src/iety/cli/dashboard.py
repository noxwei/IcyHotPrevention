"""Rich console dashboard for IETY."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text


class Dashboard:
    """Rich console dashboard for IETY system monitoring."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize dashboard.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()

    def render_status(self, status: dict) -> None:
        """Render system status.

        Args:
            status: Status dict from orchestrator
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        # Header
        layout["header"].update(
            Panel(
                Text("IETY System Status", style="bold white", justify="center"),
                style="cyan",
            )
        )

        # Budget panel (left)
        budget_info = status.get("architect", {}).get("budget", {})
        budget_panel = self._create_budget_panel(budget_info)
        layout["left"].update(budget_panel)

        # Sync status (right)
        sync_info = status.get("ingestion", {})
        sync_panel = self._create_sync_panel(sync_info)
        layout["right"].update(sync_panel)

        # Footer with recommendations
        recommendations = status.get("architect", {}).get("recommendations", [])
        footer_text = " | ".join(recommendations[:3]) if recommendations else "System operational"
        layout["footer"].update(
            Panel(footer_text, style="dim")
        )

        self.console.print(layout)

    def _create_budget_panel(self, budget: dict) -> Panel:
        """Create budget status panel."""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        current = budget.get("current_spend", 0)
        limit = budget.get("budget_limit", 50)
        percent = budget.get("percent_used", 0)
        state = budget.get("state", "unknown")

        # Color code state
        state_style = {
            "normal": "green",
            "warning": "yellow",
            "halted": "red",
        }.get(state, "white")

        table.add_row("Current Spend", f"${current:.2f}")
        table.add_row("Budget Limit", f"${limit:.2f}")
        table.add_row("Remaining", f"${limit - current:.2f}")
        table.add_row("Used", f"{percent:.1%}")
        table.add_row("Status", Text(state.upper(), style=state_style))

        # Service breakdown
        services = budget.get("by_service", {})
        if services:
            table.add_row("", "")
            table.add_row("[dim]By Service[/dim]", "")
            for service, cost in sorted(services.items()):
                table.add_row(f"  {service}", f"${cost:.4f}")

        return Panel(table, title="Budget Status", border_style="cyan")

    def _create_sync_panel(self, sync: dict) -> Panel:
        """Create sync status panel."""
        table = Table(show_header=True, box=None)
        table.add_column("Pipeline", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Records", style="green", justify="right")
        table.add_column("Last Sync", style="dim")

        for name, info in sorted(sync.items()):
            status = info.get("status", "unknown")
            status_style = {
                "completed": "green",
                "running": "yellow",
                "error": "red",
                "idle": "dim",
            }.get(status, "white")

            last_sync = info.get("last_sync", "Never")
            if last_sync and last_sync != "Never":
                try:
                    dt = datetime.fromisoformat(last_sync)
                    last_sync = dt.strftime("%m/%d %H:%M")
                except (ValueError, TypeError):
                    pass

            table.add_row(
                name,
                Text(status, style=status_style),
                str(info.get("records", 0)),
                last_sync,
            )

        return Panel(table, title="Pipeline Status", border_style="green")

    async def run_interactive(self, orchestrator) -> None:
        """Run interactive dashboard with live updates.

        Args:
            orchestrator: AgentOrchestrator instance
        """
        self.console.print("[cyan]Starting interactive dashboard...[/cyan]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        try:
            while True:
                # Get fresh status
                status = await orchestrator.get_status()

                # Clear and redraw
                self.console.clear()
                self.render_status(status)

                # Show time
                self.console.print(
                    f"\n[dim]Last updated: {datetime.now().strftime('%H:%M:%S')}[/dim]"
                )
                self.console.print("[dim]Refreshing in 30s... (Ctrl+C to exit)[/dim]")

                # Wait before refresh
                import asyncio
                await asyncio.sleep(30)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Dashboard stopped[/yellow]")

    def render_progress(self, tasks: list[dict]) -> None:
        """Render progress for multiple tasks.

        Args:
            tasks: List of task dicts with name, total, completed
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for task in tasks:
                progress.add_task(
                    task.get("name", "Task"),
                    total=task.get("total", 100),
                    completed=task.get("completed", 0),
                )

    def render_search_results(self, results: list[dict]) -> None:
        """Render search results.

        Args:
            results: List of search result dicts
        """
        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            source = f"{result.get('source_schema', '')}.{result.get('source_table', '')}"
            text = result.get("chunk_text", "")[:300]

            # Truncate and add ellipsis
            if len(result.get("chunk_text", "")) > 300:
                text += "..."

            panel = Panel(
                text,
                title=f"[{i}] {source}",
                subtitle=f"Score: {score:.3f}",
                border_style="green" if score > 0.5 else "yellow",
            )
            self.console.print(panel)

    def render_error(self, message: str, details: Optional[str] = None) -> None:
        """Render an error message.

        Args:
            message: Error message
            details: Optional error details
        """
        content = message
        if details:
            content += f"\n\n[dim]{details}[/dim]"

        self.console.print(Panel(content, title="Error", border_style="red"))

    def render_success(self, message: str) -> None:
        """Render a success message.

        Args:
            message: Success message
        """
        self.console.print(Panel(message, title="Success", border_style="green"))

    def render_warning(self, message: str) -> None:
        """Render a warning message.

        Args:
            message: Warning message
        """
        self.console.print(Panel(message, title="Warning", border_style="yellow"))

    def create_table(
        self,
        title: str,
        columns: list[str],
        rows: list[list[str]],
    ) -> Table:
        """Create a Rich table.

        Args:
            title: Table title
            columns: Column headers
            rows: Row data

        Returns:
            Rich Table instance
        """
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)
        return table
