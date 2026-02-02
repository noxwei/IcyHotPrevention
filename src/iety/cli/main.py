"""IETY CLI - Command line interface for the IETY system."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from iety.cli.dashboard import Dashboard

app = typer.Typer(
    name="iety",
    help="Immigration Enforcement Transparency Infrastructure CLI",
    no_args_is_help=True,
)
console = Console()


def run_async(coro):
    """Helper to run async functions."""
    return asyncio.run(coro)


@app.command()
def status():
    """Show system status including budget, sync state, and database stats."""
    run_async(_status())


async def _status():
    """Async status implementation."""
    from iety.db.engine import get_session
    from iety.agents.orchestrator import create_orchestrator

    async for session in get_session():
        orchestrator = await create_orchestrator(session)
        status = await orchestrator.get_status()

        dashboard = Dashboard(console)
        dashboard.render_status(status)


@app.command()
def cost():
    """Show current month's cost breakdown and budget status."""
    run_async(_cost())


async def _cost():
    """Async cost implementation."""
    from iety.db.engine import get_session
    from iety.cost.tracker import CostTracker
    from iety.cost.circuit_breaker import BudgetCircuitBreaker

    async for session in get_session():
        tracker = CostTracker(session)
        breaker = BudgetCircuitBreaker(session)

        summary = await tracker.get_monthly_summary()
        budget_status = await breaker.get_status()

        # Budget panel
        budget_table = Table(title="Monthly Budget Status", show_header=False)
        budget_table.add_column("Metric", style="cyan")
        budget_table.add_column("Value", style="green")

        budget_table.add_row("Current Spend", f"${summary.total_cost:.2f}")
        budget_table.add_row("Budget Limit", f"${summary.budget_limit:.2f}")
        budget_table.add_row("Remaining", f"${summary.budget_limit - summary.total_cost:.2f}")
        budget_table.add_row("Percent Used", f"{summary.budget_percent_used:.1%}")
        budget_table.add_row("Status", budget_status.state.value.upper())

        console.print(budget_table)

        # Service breakdown
        if summary.services:
            service_table = Table(title="Cost by Service")
            service_table.add_column("Service", style="cyan")
            service_table.add_column("Cost", style="green", justify="right")

            for service, cost in sorted(summary.services.items()):
                service_table.add_row(service, f"${cost:.4f}")

            console.print(service_table)

        # Daily costs
        daily = await tracker.get_daily_costs(days=7)
        if daily:
            daily_table = Table(title="Last 7 Days")
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Cost", style="green", justify="right")

            for day, cost in daily:
                daily_table.add_row(str(day), f"${cost:.4f}")

            console.print(daily_table)


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Data source: usaspending, sec, legal, gdelt"),
    max_batches: Optional[int] = typer.Option(None, "--max-batches", "-n", help="Max batches"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write to database"),
    reset: bool = typer.Option(False, "--reset", help="Reset checkpoint and start fresh"),
):
    """Run data ingestion pipeline for a source."""
    run_async(_ingest(source, max_batches, dry_run, reset))


async def _ingest(source: str, max_batches: Optional[int], dry_run: bool, reset: bool):
    """Async ingest implementation."""
    from iety.db.engine import get_session

    pipelines = {
        "usaspending": "iety.ingestion.usaspending.pipeline:USASpendingPipeline",
        "sec": "iety.ingestion.sec.companyfacts:SECCompanyFactsPipeline",
        "legal": "iety.ingestion.legal.courtlistener:CourtListenerPipeline",
        "gdelt": "iety.ingestion.gdelt.poller:GDELTPoller",
    }

    if source not in pipelines:
        console.print(f"[red]Unknown source: {source}[/red]")
        console.print(f"Available: {', '.join(pipelines.keys())}")
        raise typer.Exit(1)

    console.print(f"[cyan]Starting {source} ingestion...[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN - no data will be written[/yellow]")

    async for session in get_session():
        # Import and create pipeline
        module_path, class_name = pipelines[source].rsplit(":", 1)
        module = __import__(module_path, fromlist=[class_name])
        pipeline_cls = getattr(module, class_name)
        pipeline = pipeline_cls(session)

        try:
            stats = await pipeline.run(
                max_batches=max_batches,
                dry_run=dry_run,
                reset_checkpoint=reset,
            )

            # Display results
            table = Table(title=f"{source.upper()} Ingestion Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Records Fetched", str(stats.records_fetched))
            table.add_row("Records Transformed", str(stats.records_transformed))
            table.add_row("Records Upserted", str(stats.records_upserted))
            table.add_row("Records Skipped", str(stats.records_skipped))
            table.add_row("Errors", str(stats.errors))
            table.add_row("Batches", str(stats.batches_processed))
            table.add_row("Duration", f"{stats.duration_seconds:.1f}s")

            console.print(table)

        except Exception as e:
            console.print(f"[red]Ingestion failed: {e}[/red]")
            raise typer.Exit(1)
        finally:
            await pipeline.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    search_type: str = typer.Option("hybrid", "--type", "-t", help="vector, keyword, or hybrid"),
    schema: Optional[str] = typer.Option(None, "--schema", "-s", help="Filter by schema"),
):
    """Search indexed content using hybrid vector+keyword search."""
    run_async(_search(query, limit, search_type, schema))


async def _search(query: str, limit: int, search_type: str, schema: Optional[str]):
    """Async search implementation."""
    from iety.db.engine import get_session
    from iety.processing.embeddings import create_embedding_service
    from iety.processing.search import HybridSearch

    async for session in get_session():
        embedding_service = await create_embedding_service(session)
        searcher = HybridSearch(session, embedding_service)

        console.print(f"[cyan]Searching for: {query}[/cyan]")

        response = await searcher.search(
            query=query,
            limit=limit,
            search_type=search_type,
            schema_filter=schema,
        )

        # Log search
        await searcher.log_search(response)

        # Display results
        console.print(f"[green]Found {response.total_count} results in {response.latency_ms}ms[/green]")

        for i, result in enumerate(response.results, 1):
            panel = Panel(
                result.chunk_text[:500] + ("..." if len(result.chunk_text) > 500 else ""),
                title=f"[{i}] {result.source_schema}.{result.source_table} (score: {result.score:.3f})",
                subtitle=f"ID: {result.source_id}",
            )
            console.print(panel)


@app.command()
def agent(
    persona: str = typer.Argument(..., help="Agent: architect, ingestion, processor, dbadmin"),
    task: str = typer.Argument(..., help="Task to execute"),
):
    """Execute a task through a specific agent persona."""
    run_async(_agent(persona, task))


async def _agent(persona: str, task: str):
    """Async agent implementation."""
    from iety.db.engine import get_session
    from iety.agents.orchestrator import create_orchestrator

    valid_personas = ["architect", "ingestion", "processor", "dbadmin"]
    if persona not in valid_personas:
        console.print(f"[red]Unknown persona: {persona}[/red]")
        console.print(f"Available: {', '.join(valid_personas)}")
        raise typer.Exit(1)

    async for session in get_session():
        orchestrator = await create_orchestrator(session)

        console.print(f"[cyan]Delegating to @{persona}...[/cyan]")

        result = await orchestrator.delegate(task, persona)

        # Display result
        status_color = "green" if result.status == "success" else "red"
        panel = Panel(
            f"Status: [{status_color}]{result.status}[/{status_color}]\n\n"
            f"Rationale: {result.rationale}\n\n"
            f"Approved: {result.approved}",
            title=f"@{persona} Response",
        )
        console.print(panel)

        if result.outcome:
            console.print("[cyan]Outcome:[/cyan]")
            console.print(result.outcome)


@app.command()
def memories(
    persona: str = typer.Argument(..., help="Agent persona"),
    query: str = typer.Option("", "--query", "-q", help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max memories to show"),
):
    """View agent memories."""
    run_async(_memories(persona, query, limit))


async def _memories(persona: str, query: str, limit: int):
    """Async memories implementation."""
    from iety.db.engine import get_session
    from iety.agents.memory.store import MemoryStore

    async for session in get_session():
        store = MemoryStore(session)

        if query:
            console.print(f"[cyan]Searching memories for '{query}'...[/cyan]")
            # Would need embedding service for semantic search
            console.print("[yellow]Note: Semantic search requires embedding service[/yellow]")

        # Get recent memories
        memories = await store.get_recent(
            agent_type=persona,
            limit=limit,
        )

        if not memories:
            console.print(f"[yellow]No memories found for @{persona}[/yellow]")
            return

        table = Table(title=f"@{persona} Memories")
        table.add_column("Type", style="cyan")
        table.add_column("Content", style="white", max_width=60)
        table.add_column("Importance", style="green")
        table.add_column("Created", style="dim")

        for memory in memories:
            table.add_row(
                memory.memory_type,
                memory.content[:100] + ("..." if len(memory.content) > 100 else ""),
                f"{memory.importance:.2f}",
                memory.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)


@app.command()
def schema():
    """Output current PostgreSQL schema DDL."""
    run_async(_schema())


async def _schema():
    """Async schema implementation."""
    from iety.db.engine import get_session
    from sqlalchemy import text

    async for session in get_session():
        # Get all schemas
        schemas = ["usaspending", "sec", "legal", "gdelt", "integration"]

        for schema_name in schemas:
            console.print(f"\n[cyan]-- Schema: {schema_name} --[/cyan]")

            # Get tables
            sql = text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
                ORDER BY table_name
            """)

            result = await session.execute(sql, {"schema": schema_name})
            tables = [row.table_name for row in result.fetchall()]

            for table in tables:
                console.print(f"\n-- Table: {schema_name}.{table}")

                # Get columns
                col_sql = text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """)

                result = await session.execute(
                    col_sql, {"schema": schema_name, "table": table}
                )

                console.print(f"CREATE TABLE {schema_name}.{table} (")
                for row in result.fetchall():
                    nullable = "" if row.is_nullable == "YES" else " NOT NULL"
                    default = f" DEFAULT {row.column_default}" if row.column_default else ""
                    console.print(f"    {row.column_name} {row.data_type}{nullable}{default},")
                console.print(");")


@app.command()
def dashboard():
    """Launch interactive Rich dashboard."""
    run_async(_dashboard())


async def _dashboard():
    """Async dashboard implementation."""
    from iety.db.engine import get_session
    from iety.agents.orchestrator import create_orchestrator

    async for session in get_session():
        orchestrator = await create_orchestrator(session)

        dash = Dashboard(console)
        await dash.run_interactive(orchestrator)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
