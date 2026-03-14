#!/usr/bin/env python3
"""Run theodin experiments."""
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def cross_language(
    language: str = "python_to_js",
    limit: int = 100,
):
    """Run cross-language transfer experiment."""
    console.print(f"[bold]Running {language} experiment...[/bold]")

    # Collect Python PRs
    console.print("1. Collecting training data...")
    # Use theodin to collect PRs

    # Learn rules
    console.print("2. Learning rules with Vertex AI...")
    # Use theodin to learn

    # Test on target language
    console.print("3. Testing on target language...")
    # Run evaluation

    # Save results
    console.print("4. Saving results...")


if __name__ == "__main__":
    app()
