import typer
from rich.console import Console
from rich.markdown import Markdown
from devassist.indexer import index_codebase
from devassist.agent import ask, debug, summarize, explain_diff, generate_commit, review_file

app = typer.Typer(help="🛠  Developer Assist — AI-powered code intelligence")
console = Console()


@app.command()
def index(path: str = typer.Argument(..., help="Path to the codebase to index")):
    """Index a codebase so you can ask questions about it"""
    console.print(f"\n[bold cyan]🔍 Indexing codebase at: {path}[/bold cyan]\n")
    index_codebase(path)
    console.print("[bold green]✅ Codebase indexed and ready![/bold green]\n")


@app.command()
def ask_question(question: str = typer.Argument(..., help="Question about your codebase")):
    """Ask a natural language question about your indexed codebase"""
    console.print(f"\n[bold cyan]❓ {question}[/bold cyan]\n")
    console.print("[yellow]🤔 Thinking...[/yellow]\n")
    answer = ask(question)
    console.print(Markdown(answer))
    console.print()


@app.command()
def debug_error(error: str = typer.Argument(..., help="Error message or stack trace to debug")):
    """Diagnose an error or stack trace against your codebase"""
    console.print(f"\n[bold red]🐛 Debugging: {error}[/bold red]\n")
    console.print("[yellow]🔍 Searching codebase for related code...[/yellow]\n")
    result = debug(error)
    console.print(Markdown(result))
    console.print()


@app.command()
def summary():
    """Get a high-level summary of your indexed codebase"""
    console.print("\n[bold cyan]📋 Generating codebase summary...[/bold cyan]\n")
    result = summarize(".")
    console.print(Markdown(result))
    console.print()

@app.command()
def diff(path: str = typer.Argument(".", help="Path to git repository")):
    """Explain your current git changes in plain English"""
    console.print("\n[bold cyan]📝 Analyzing git diff...[/bold cyan]\n")
    result = explain_diff(path)
    console.print(Markdown(result))
    console.print()


@app.command()
def commit(path: str = typer.Argument(".", help="Path to git repository")):
    """Generate a commit message from your staged changes"""
    console.print("\n[bold cyan]✍️  Generating commit message...[/bold cyan]\n")
    result = generate_commit(path)
    console.print(Markdown(result))
    console.print()

@app.command()
def review(filepath: str = typer.Argument(..., help="Path to the file you want reviewed")):
    """Get a senior engineer code review of any file"""
    console.print(f"\n[bold cyan]🔍 Reviewing: {filepath}[/bold cyan]\n")
    console.print("[yellow]🤔 Analyzing code...[/yellow]\n")
    result = review_file(filepath)
    console.print(Markdown(result))
    console.print()

if __name__ == "__main__":
    app()