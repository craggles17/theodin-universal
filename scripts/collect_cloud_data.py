#!/usr/bin/env python3
"""Collect cloud SDK PR data for training/testing.

Usage:
    python scripts/collect_cloud_data.py --provider gcp --limit 100
    python scripts/collect_cloud_data.py --provider aws --limit 50
    python scripts/collect_cloud_data.py --provider azure --limit 50
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()

# Cloud SDK repository mappings
CLOUD_REPOS = {
    "gcp": [
        "googleapis/python-aiplatform",
        "googleapis/python-bigquery",
        "googleapis/python-storage",
        "googleapis/python-firestore",
        "googleapis/python-dataflow-client",
    ],
    "aws": [
        "boto/boto3",
        "boto/botocore",
        "aws/aws-cdk-python",
        "awslabs/aws-lambda-powertools-python",
    ],
    "azure": [
        "Azure/azure-sdk-for-python",
        "Azure/azure-functions-python-library",
    ],
}

# Labels to prioritize (in order of importance)
PRIORITY_LABELS = [
    "type: bug",
    "priority: p0",
    "priority: p1",
    "type: security",
    "good first issue",
]


def run_gh_command(cmd: list[str]) -> dict[str, Any]:
    """Run gh CLI command and return JSON output."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        console.print(f"[red]Error:[/red] {result.stderr}")
        return {}
    
    try:
        return json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        return {}


@app.command()
def collect(
    provider: str = typer.Option(..., help="Cloud provider: gcp, aws, or azure"),
    limit: int = typer.Option(100, help="Number of PRs to collect per repo"),
    output: Path = typer.Option(..., help="Output JSONL file"),
    require_tests: bool = typer.Option(True, help="Only include PRs that modify tests"),
    min_files: int = typer.Option(1, help="Minimum files changed"),
    max_files: int = typer.Option(50, help="Maximum files changed (filter out massive refactors)"),
) -> None:
    """Collect cloud SDK PR data."""
    if provider not in CLOUD_REPOS:
        console.print(f"[red]Unknown provider:[/red] {provider}")
        console.print(f"Available: {', '.join(CLOUD_REPOS.keys())}")
        raise typer.Exit(1)
    
    repos = CLOUD_REPOS[provider]
    console.print(f"[bold cyan]Collecting {provider.upper()} SDK PRs[/bold cyan]")
    console.print(f"Repos: {', '.join(repos)}\n")
    
    output.parent.mkdir(parents=True, exist_ok=True)
    collected = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for repo in repos:
            task = progress.add_task(f"Collecting from {repo}...", total=None)
            
            # Fetch merged PRs with gh CLI
            cmd = [
                "gh", "pr", "list",
                "--repo", repo,
                "--state", "merged",
                "--limit", str(limit),
                "--json", "number,title,body,labels,mergedAt,files,commits",
            ]
            
            prs = run_gh_command(cmd)
            
            if not isinstance(prs, list):
                console.print(f"[yellow]Warning:[/yellow] No PRs found for {repo}")
                progress.update(task, completed=True)
                continue
            
            # Filter PRs
            filtered = []
            for pr in prs:
                # Skip if no files info
                if "files" not in pr or not pr["files"]:
                    continue
                
                file_count = len(pr["files"])
                
                # Apply filters
                if file_count < min_files or file_count > max_files:
                    continue
                
                # Check if tests were modified
                if require_tests:
                    test_files = [
                        f for f in pr["files"]
                        if "test" in f.get("path", "").lower()
                    ]
                    if not test_files:
                        continue
                
                # Extract labels
                labels = [l.get("name", "") for l in pr.get("labels", [])]
                
                # Calculate priority score
                priority_score = 0
                for i, label in enumerate(PRIORITY_LABELS):
                    if label in labels:
                        priority_score += (len(PRIORITY_LABELS) - i)
                
                filtered.append({
                    "repo": repo,
                    "provider": provider,
                    "number": pr["number"],
                    "title": pr["title"],
                    "body": pr.get("body", ""),
                    "labels": labels,
                    "merged_at": pr.get("mergedAt", ""),
                    "file_count": file_count,
                    "files": [f.get("path") for f in pr["files"]],
                    "commits": pr.get("commits", []),
                    "priority_score": priority_score,
                })
            
            # Sort by priority score (highest first)
            filtered.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # Write to JSONL
            with open(output, "a") as f:
                for pr_data in filtered:
                    f.write(json.dumps(pr_data) + "\n")
                    collected += 1
            
            progress.update(
                task,
                description=f"✓ {repo}: {len(filtered)} PRs",
                completed=True,
            )
    
    console.print(f"\n[green]✓[/green] Collected {collected} PRs → {output}")
    
    # Show distribution
    with open(output) as f:
        data = [json.loads(line) for line in f]
    
    console.print("\n[bold]Distribution:[/bold]")
    for repo in repos:
        count = sum(1 for d in data if d["repo"] == repo)
        console.print(f"  {repo}: {count}")
    
    # Priority breakdown
    console.print("\n[bold]Priority Breakdown:[/bold]")
    high_priority = sum(1 for d in data if d["priority_score"] >= 3)
    medium_priority = sum(1 for d in data if 1 <= d["priority_score"] < 3)
    low_priority = sum(1 for d in data if d["priority_score"] == 0)
    console.print(f"  High (bugs, security): {high_priority}")
    console.print(f"  Medium: {medium_priority}")
    console.print(f"  Low: {low_priority}")


if __name__ == "__main__":
    app()
