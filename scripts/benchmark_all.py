#!/usr/bin/env python3
"""Run full experiment suite."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()
SCRIPT_DIR = Path(__file__).parent


def run_experiment(cmd: list[str]) -> bool:
    """Run experiment and return success status."""
    console.print(f"\n[bold cyan]Running:[/bold cyan] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    return result.returncode == 0


def main() -> None:
    """Run all experiments."""
    console.print("[bold]🧪 Theodin Universal - Full Benchmark Suite[/bold]\n")
    
    experiments = [
        # Cross-language transfers
        ["python", "run_experiment.py", "cross_language", "--language", "python_to_js"],
        ["python", "run_experiment.py", "cross_language", "--language", "python_to_rust"],
        ["python", "run_experiment.py", "cross_language", "--language", "python_to_go"],
        
        # Cross-domain transfers
        ["python", "run_experiment.py", "cross_domain", "--domain", "scientific_to_web"],
        ["python", "run_experiment.py", "cross_domain", "--domain", "web_to_cli"],
        
        # Zero-shot generalization
        ["python", "run_experiment.py", "zero_shot", "--repo", "pytorch"],
        ["python", "run_experiment.py", "zero_shot", "--repo", "numpy"],
        
        # Coding systems
        ["python", "run_experiment.py", "coding_system", "--system", "cursor"],
        ["python", "run_experiment.py", "coding_system", "--system", "claude-code"],
        ["python", "run_experiment.py", "coding_system", "--system", "aider"],
        ["python", "run_experiment.py", "coding_system", "--system", "codex"],
    ]
    
    results = []
    for exp in experiments:
        success = run_experiment(exp)
        results.append((exp, success))
    
    # Summary
    console.print("\n[bold]📊 Summary[/bold]\n")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for exp, success in results:
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"{status} {' '.join(exp[2:])}")
    
    console.print(f"\n[bold]{passed}/{total} experiments completed successfully[/bold]")
    
    # Generate dashboard
    console.print("\n[bold]Generating dashboard...[/bold]")
    subprocess.run(["python", "generate_dashboard.py"], cwd=SCRIPT_DIR)


if __name__ == "__main__":
    main()
