# Theodin Universal - Proof that theodin improves ANY coding system

## Thesis
Theodin learns transferable coding patterns from PR history that improve code quality across:
- Languages (Python -> JS -> Rust -> Go)
- Domains (Web -> Scientific -> CLI)
- Frameworks (Django -> FastAPI -> React)
- Coding Systems (Cursor, Claude Code, Aider, Codex)

## Experiments

### 1. Cross-Language Transfer
Train on Python PRs, test on JavaScript/Rust/Go

### 2. Cross-Domain Transfer
Train on scientific computing, test on web frameworks

### 3. Zero-Shot Generalization
Train on repos A/B/C, test on unseen repo D

### 4. Coding System Improvement
Apply theodin-learned rules to existing coding tools

## Results
[Auto-updated from CI]

## How to Reproduce
```bash
git clone https://github.com/ctr26/theodin-universal.git
cd theodin-universal
uv sync
./scripts/run_experiment.py --experiment cross_language --language python_to_js
```

## Links
- [Main theodin repo](https://github.com/ctr26/theodin)
- [Live dashboard](results/dashboard.html)
