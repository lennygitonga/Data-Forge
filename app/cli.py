import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

app = typer.Typer(help="Data-Forge CLI — Automated Web Intelligence")
console = Console()

BASE_URL = "http://127.0.0.1:5000"


def get_session_cookie():
    """Load session cookie from local file if exists."""
    try:
        with open(".session", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


@app.command()
def scrape(
    site: str = typer.Argument(..., help="Website name or URL to scrape"),
    email: str = typer.Option(..., "--email", "-e", help="Email to send report to"),
    query: str = typer.Option(None, "--query", "-q", help="What to extract"),
    schedule: str = typer.Option(None, "--schedule", "-s",
                                  help="Schedule: 'every 1h', 'every 6h', 'every 24h'"),
):
    """Scrape a website and receive the report via email."""
    console.print(Panel(
        f"[bold gold1]Scraping:[/bold gold1] {site}\n"
        f"[bold gold1]Report to:[/bold gold1] {email}\n"
        f"[bold gold1]Schedule:[/bold gold1] {schedule or 'One-time'}",
        title="[bold dark_red]Data-Forge[/bold dark_red]",
        border_style="gold1"
    ))

    with console.status("[gold1]Working...[/gold1]"):
        try:
            response = httpx.post(
                f"{BASE_URL}/api/scrape",
                json={
                    "site": site,
                    "email": email,
                    "user_query": query,
                    "schedule": schedule
                },
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                console.print(f"\n[green]Report sent to {email}[/green]")
                console.print(f"[dim]Job ID: {data.get('job_id')}[/dim]")
                console.print(f"[dim]URL: {data.get('url')}[/dim]")
            else:
                console.print(f"\n[red]Error: {response.json().get('error')}[/red]")

        except Exception as e:
            console.print(f"\n[red]Failed: {str(e)}[/red]")


@app.command()
def jobs():
    """List all scrape jobs."""
    try:
        response = httpx.get(f"{BASE_URL}/api/jobs", timeout=10)

        if response.status_code != 200:
            console.print("[red]Could not fetch jobs.[/red]")
            return

        data = response.json()

        if not data:
            console.print("[dim]No jobs found.[/dim]")
            return

        table = Table(
            box=box.SIMPLE_HEAD,
            border_style="gold1",
            header_style="bold dark_red"
        )
        table.add_column("ID", style="dim", width=6)
        table.add_column("Site", style="bold")
        table.add_column("Email")
        table.add_column("Status")
        table.add_column("Schedule")
        table.add_column("Created")

        status_colors = {
            "done": "green",
            "running": "blue",
            "pending": "yellow",
            "failed": "red"
        }

        for job in data:
            status = job["status"]
            color = status_colors.get(status, "white")
            table.add_row(
                str(job["id"]),
                job["site"],
                job["email"],
                f"[{color}]{status}[/{color}]",
                job["schedule"] or "One-time",
                job["created_at"][:10]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def delete(
    job_id: int = typer.Argument(..., help="Job ID to delete")
):
    """Delete a scrape job by ID."""
    confirm = typer.confirm(f"Delete job {job_id}?")
    if not confirm:
        console.print("[dim]Cancelled.[/dim]")
        return

    try:
        response = httpx.delete(
            f"{BASE_URL}/api/jobs/{job_id}",
            timeout=10
        )
        if response.status_code == 200:
            console.print(f"[green]Job {job_id} deleted.[/green]")
        else:
            console.print(f"[red]Could not delete job {job_id}.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@app.command()
def status():
    """Check if Data-Forge server is running."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            console.print("[green]Data-Forge is running.[/green]")
        else:
            console.print("[red]Server returned an error.[/red]")
    except Exception:
        console.print("[red]Server is not running. Start it with: python run.py[/red]")


if __name__ == "__main__":
    app()