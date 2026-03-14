#!/usr/bin/env python3
"""Run theodin universal experiments.

Usage:
    ./scripts/run_experiment.py cross_language --language python_to_js --limit 100
    ./scripts/run_experiment.py cross_domain --domain scientific_to_web
    ./scripts/run_experiment.py zero_shot --repo pytorch
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
THEODIN_DIR = PROJECT_ROOT.parent / "theodin"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


def run_command(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run shell command and return result."""
    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def save_results(experiment: str, results: dict[str, Any]) -> None:
    """Save experiment results to JSON file."""
    results["timestamp"] = datetime.now().isoformat()
    results["experiment"] = experiment
    
    output_file = RESULTS_DIR / f"{experiment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"[green]✓[/green] Results saved to {output_file}")


@app.command()
def cross_language(
    language: str = typer.Option("python_to_js", help="Language pair (e.g., python_to_js)"),
    limit: int = typer.Option(100, help="Number of PRs to collect for training"),
    test_limit: int = typer.Option(10, help="Number of test cases"),
) -> None:
    """Run cross-language transfer experiment.
    
    Train on Python PRs, test on target language (JS/Rust/Go).
    """
    console.print(f"[bold cyan]Cross-Language Transfer: {language}[/bold cyan]\n")
    
    # Define repo mappings
    repos_map = {
        "python_to_js": {
            "train": ["fastapi/fastapi", "psf/requests"],
            "test": ["expressjs/express", "axios/axios"],
        },
        "python_to_rust": {
            "train": ["fastapi/fastapi", "pallets/flask"],
            "test": ["tokio-rs/axum", "actix/actix-web"],
        },
        "python_to_go": {
            "train": ["fastapi/fastapi", "requests/requests-html"],
            "test": ["gorilla/mux", "gin-gonic/gin"],
        },
    }
    
    if language not in repos_map:
        console.print(f"[red]Error:[/red] Unknown language pair: {language}")
        console.print(f"Available: {', '.join(repos_map.keys())}")
        raise typer.Exit(1)
    
    train_repos = repos_map[language]["train"]
    test_repos = repos_map[language]["test"]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Collect training data
        task1 = progress.add_task("1. Collecting Python PRs...", total=None)
        train_data_file = DATA_DIR / f"{language}_train.jsonl"
        
        result = run_command([
            "uv", "run", "theodin", "collect",
            "--repos", ",".join(train_repos),
            "--limit", str(limit),
            "--output", str(train_data_file),
        ], cwd=THEODIN_DIR)
        
        if result.returncode != 0:
            console.print(f"[red]Error collecting training data:[/red]\n{result.stderr}")
            raise typer.Exit(1)
        
        progress.update(task1, completed=True)
        
        # Step 2: Learn rules with theodin + Vertex AI
        task2 = progress.add_task("2. Learning rules with Vertex AI...", total=None)
        rules_file = PROJECT_ROOT / "rules" / f"{language}_learned.md"
        rules_file.parent.mkdir(exist_ok=True)
        
        result = run_command([
            "uv", "run", "theodin", "learn",
            "--input", str(train_data_file),
            "--output", str(rules_file),
            "--provider", "vertex",
        ], cwd=THEODIN_DIR)
        
        if result.returncode != 0:
            console.print(f"[red]Error learning rules:[/red]\n{result.stderr}")
            raise typer.Exit(1)
        
        progress.update(task2, completed=True)
        
        # Step 3: Test on target language
        task3 = progress.add_task(f"3. Testing on {language.split('_to_')[1].upper()}...", total=None)
        test_data_file = DATA_DIR / f"{language}_test.jsonl"
        
        result = run_command([
            "uv", "run", "theodin", "collect",
            "--repos", ",".join(test_repos),
            "--limit", str(test_limit),
            "--output", str(test_data_file),
        ], cwd=THEODIN_DIR)
        
        if result.returncode != 0:
            console.print(f"[red]Error collecting test data:[/red]\n{result.stderr}")
            raise typer.Exit(1)
        
        progress.update(task3, completed=True)
        
        # Step 4: Evaluate
        task4 = progress.add_task("4. Evaluating...", total=None)
        
        # Run baseline (no rules)
        baseline_result = run_command([
            "uv", "run", "theodin", "evaluate",
            "--input", str(test_data_file),
            "--rules", "",
            "--provider", "vertex",
        ], cwd=THEODIN_DIR)
        
        # Run with learned rules
        theodin_result = run_command([
            "uv", "run", "theodin", "evaluate",
            "--input", str(test_data_file),
            "--rules", str(rules_file),
            "--provider", "vertex",
        ], cwd=THEODIN_DIR)
        
        progress.update(task4, completed=True)
    
    # Parse results (placeholder - actual parsing depends on theodin output format)
    results = {
        "language_pair": language,
        "train_repos": train_repos,
        "test_repos": test_repos,
        "train_samples": limit,
        "test_samples": test_limit,
        "baseline_score": 0.0,  # Parse from baseline_result.stdout
        "theodin_score": 0.0,   # Parse from theodin_result.stdout
        "improvement_pct": 0.0,
        "p_value": 0.0,
    }
    
    save_results(f"cross_language_{language}", results)
    
    console.print("\n[bold green]Experiment Complete![/bold green]")
    console.print(f"Baseline: {results['baseline_score']:.2%}")
    console.print(f"Theodin:  {results['theodin_score']:.2%}")
    console.print(f"Improvement: +{results['improvement_pct']:.2%}")


@app.command()
def cross_domain(
    domain: str = typer.Option("scientific_to_web", help="Domain pair (e.g., scientific_to_web)"),
    limit: int = typer.Option(100, help="Number of PRs to collect"),
) -> None:
    """Run cross-domain transfer experiment.
    
    Train on one domain (e.g., scientific), test on another (e.g., web).
    """
    console.print(f"[bold cyan]Cross-Domain Transfer: {domain}[/bold cyan]\n")
    console.print("[yellow]Not yet implemented - placeholder[/yellow]")


@app.command()
def zero_shot(
    repo: str = typer.Option("pytorch", help="Held-out repo to test on"),
    limit: int = typer.Option(500, help="Training PRs from other repos"),
) -> None:
    """Run zero-shot generalization experiment.
    
    Train on all repos EXCEPT target repo, test on target repo.
    """
    console.print(f"[bold cyan]Zero-Shot Generalization: {repo}[/bold cyan]\n")
    console.print("[yellow]Not yet implemented - placeholder[/yellow]")


@app.command()
def coding_system(
    system: str = typer.Option("cursor", help="Coding system to test (cursor/claude-code/aider/codex)"),
    benchmark: str = typer.Option("swe-bench-lite", help="Benchmark to use"),
) -> None:
    """Test theodin rules on a specific coding system.
    
    Measure before/after improvement when applying theodin-learned rules.
    """
    console.print(f"[bold cyan]Coding System Improvement: {system}[/bold cyan]\n")
    console.print("[yellow]Not yet implemented - placeholder[/yellow]")


if __name__ == "__main__":
    app()
