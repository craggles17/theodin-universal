#!/usr/bin/env python3
"""Generate HTML dashboard from experiment results."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

RESULTS_DIR = Path(__file__).parent.parent / "results"
OUTPUT_FILE = RESULTS_DIR / "dashboard.html"


def load_results() -> list[dict]:
    """Load all experiment result JSON files."""
    results = []
    for json_file in RESULTS_DIR.glob("*.json"):
        with open(json_file) as f:
            results.append(json.load(f))
    return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)


def generate_dashboard() -> None:
    """Generate interactive dashboard HTML."""
    results = load_results()
    
    if not results:
        # Create placeholder dashboard
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Theodin Universal - Experiment Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
        }
        h1 { color: #2563eb; }
        .status { padding: 20px; background: #fef3c7; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🧠 Theodin Universal - Experiment Dashboard</h1>
    <div class="status">
        <h2>Status: Initializing</h2>
        <p>No experiment results yet. Run experiments to see results here.</p>
        <pre>./scripts/run_experiment.py cross_language --language python_to_js</pre>
    </div>
</body>
</html>
"""
        with open(OUTPUT_FILE, "w") as f:
            f.write(html)
        print(f"✓ Placeholder dashboard created: {OUTPUT_FILE}")
        return
    
    # Group results by experiment type
    cross_lang = [r for r in results if "cross_language" in r.get("experiment", "")]
    cross_domain = [r for r in results if "cross_domain" in r.get("experiment", "")]
    zero_shot = [r for r in results if "zero_shot" in r.get("experiment", "")]
    
    # Create plots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Cross-Language Transfer",
            "Cross-Domain Transfer",
            "Zero-Shot Generalization",
            "Coding System Improvements",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "table"}],
        ],
    )
    
    # Plot 1: Cross-language results
    if cross_lang:
        languages = [r.get("language_pair", "unknown") for r in cross_lang[:5]]
        improvements = [r.get("improvement_pct", 0) * 100 for r in cross_lang[:5]]
        
        fig.add_trace(
            go.Bar(
                x=languages,
                y=improvements,
                name="Improvement %",
                marker_color="#2563eb",
            ),
            row=1, col=1,
        )
    
    # HTML template
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Theodin Universal - Experiment Results</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            color: #1f2937;
            background: #f9fafb;
        }}
        h1 {{ color: #1e40af; margin-bottom: 10px; }}
        .subtitle {{ color: #6b7280; margin-bottom: 30px; }}
        .metric {{ 
            display: inline-block;
            background: white;
            padding: 15px 25px;
            margin: 10px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #2563eb; }}
        .metric-label {{ font-size: 14px; color: #6b7280; }}
        .chart {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f3f4f6; font-weight: 600; }}
        tr:hover {{ background: #f9fafb; }}
        .badge {{ 
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-pending {{ background: #fef3c7; color: #92400e; }}
        .footer {{ text-align: center; margin-top: 40px; color: #9ca3af; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>🧠 Theodin Universal - Experiment Dashboard</h1>
    <p class="subtitle">Proof that theodin improves ANY coding system</p>
    
    <div>
        <div class="metric">
            <div class="metric-value">{len(results)}</div>
            <div class="metric-label">Total Experiments</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(cross_lang)}</div>
            <div class="metric-label">Cross-Language</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(cross_domain)}</div>
            <div class="metric-label">Cross-Domain</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(zero_shot)}</div>
            <div class="metric-label">Zero-Shot</div>
        </div>
    </div>
    
    <div class="chart" id="plot"></div>
    
    <div class="chart">
        <h2>Recent Experiments</h2>
        <table>
            <thead>
                <tr>
                    <th>Experiment</th>
                    <th>Date</th>
                    <th>Baseline</th>
                    <th>Theodin</th>
                    <th>Improvement</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for result in results[:10]:
        exp_name = result.get("experiment", "unknown")
        timestamp = result.get("timestamp", "")
        date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "Unknown"
        baseline = result.get("baseline_score", 0)
        theodin = result.get("theodin_score", 0)
        improvement = result.get("improvement_pct", 0)
        status = "success" if improvement > 0 else "pending"
        badge_class = "badge-success" if improvement > 0 else "badge-pending"
        
        html += f"""
                <tr>
                    <td><strong>{exp_name}</strong></td>
                    <td>{date}</td>
                    <td>{baseline:.2%}</td>
                    <td>{theodin:.2%}</td>
                    <td><strong>{improvement:+.2%}</strong></td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                </tr>
"""
    
    html += f"""
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}<br>
        <a href="https://github.com/ctr26/theodin-universal">GitHub</a> | 
        <a href="https://github.com/ctr26/theodin">Main Theodin Repo</a>
    </div>
    
    <script>
        var data = {fig.to_json() if cross_lang else "[]"};
        Plotly.newPlot('plot', data);
    </script>
</body>
</html>
"""
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)
    
    print(f"✓ Dashboard generated: {OUTPUT_FILE}")
    print(f"  Total experiments: {len(results)}")
    print(f"  Cross-language: {len(cross_lang)}")
    print(f"  Cross-domain: {len(cross_domain)}")
    print(f"  Zero-shot: {len(zero_shot)}")


if __name__ == "__main__":
    generate_dashboard()
