# Setup Guide - theodin-universal

## Prerequisites

### 1. Google Cloud Setup

**Install gcloud CLI**:
```bash
# Download and install
curl https://sdk.cloud.google.com | bash

# Reload shell
exec -l $SHELL

# Verify installation
gcloud --version
```

**Configure GCP Project**:
```bash
# Set your project ID (get from https://console.cloud.google.com/)
export GOOGLE_CLOUD_PROJECT=your-project-id-here
echo "export GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" >> ~/.zshrc

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com

# Authenticate
gcloud auth login
gcloud auth application-default login

# Verify config
gcloud config list
```

**Create Vertex AI Config**:
```bash
cd ~/projects/theodin
mkdir -p configs
cat > configs/vertex.yaml <<EOF
provider: vertex
project_id: \${GOOGLE_CLOUD_PROJECT}
location: us-central1
model_id: gemini-1.5-pro
temperature: 0.3
max_tokens: 4096
EOF
```

**Test Vertex Provider**:
```bash
cd ~/projects/theodin
uv run python -c "
from theodin.providers.vertex import get_vertex_provider
import os

project = os.environ.get('GOOGLE_CLOUD_PROJECT')
if not project:
    print('ERROR: GOOGLE_CLOUD_PROJECT not set')
    exit(1)

print(f'Testing Vertex AI with project: {project}')
provider = get_vertex_provider()
response = provider.generate('Hello from theodin!')
print(f'Response: {response}')
print('✓ Vertex AI working!')
"
```

### 2. GitHub Setup

**Install GitHub CLI** (if not already):
```bash
# Check if installed
which gh || curl -sS https://webi.sh/gh | sh

# Authenticate
gh auth login
```

**Configure for PR collection**:
```bash
# Set larger rate limits for API
gh config set rate_limit 5000

# Verify
gh api rate_limit
```

### 3. theodin Installation

```bash
cd ~/projects/theodin
uv sync

# Verify installation
uv run theodin --help
```

### 4. theodin-universal Installation

```bash
cd ~/projects/theodin-universal
uv sync

# Verify scripts work
uv run python scripts/run_experiment.py --help
```

---

## Quick Start: First Experiment

### Run GCP → AWS SDK Transfer

```bash
cd ~/projects/theodin-universal

# 1. Collect GCP SDK training data (this will take ~10 minutes)
uv run python scripts/collect_cloud_data.py \
  --provider gcp \
  --limit 100 \
  --output data/gcp_sdk_train.jsonl

# 2. Learn rules with Vertex AI
uv run python scripts/learn_rules.py \
  --input data/gcp_sdk_train.jsonl \
  --output rules/gcp_to_aws.md \
  --model gemini-1.5-pro

# 3. Collect AWS test cases
uv run python scripts/collect_cloud_data.py \
  --provider aws \
  --limit 20 \
  --output data/aws_sdk_test.jsonl

# 4. Run evaluation
uv run python scripts/evaluate.py \
  --test-data data/aws_sdk_test.jsonl \
  --rules rules/gcp_to_aws.md \
  --output results/gcp_to_aws.json

# 5. View results
uv run python scripts/generate_dashboard.py
open results/dashboard.html
```

---

## Environment Variables

Add to `~/.zshrc`:
```bash
# Google Cloud
export GOOGLE_CLOUD_PROJECT=your-project-id

# Optional: Set default region
export GOOGLE_CLOUD_REGION=us-central1

# GitHub token (for higher rate limits)
export GITHUB_TOKEN=ghp_your_token_here
```

Reload: `source ~/.zshrc`

---

## Troubleshooting

### "GOOGLE_CLOUD_PROJECT not set"
```bash
echo $GOOGLE_CLOUD_PROJECT  # Should show your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### "Vertex AI API not enabled"
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services list --enabled | grep aiplatform
```

### "Authentication failed"
```bash
gcloud auth application-default login
gcloud auth list  # Should show your account
```

### "GitHub rate limit exceeded"
```bash
# Create a personal access token at https://github.com/settings/tokens
export GITHUB_TOKEN=ghp_your_token_here
gh auth login
```

### "theodin command not found"
```bash
cd ~/projects/theodin
uv sync
uv run theodin --help  # Always use 'uv run'
```

---

## Cost Estimates

### Vertex AI (Gemini 1.5 Pro)
- **Input**: $3.50 per 1M tokens
- **Output**: $10.50 per 1M tokens

**For first experiment (100 training PRs)**:
- Estimated tokens: ~500K input, ~100K output
- Cost: ~$3.25

**Full experiment suite (1000 PRs × 5 experiments)**:
- Estimated cost: ~$150-200 total

### Free Tier
- First 1000 requests/month free for Gemini Flash
- Consider using `gemini-1.5-flash` for development/testing

---

## Next Steps

1. ✅ Complete Google Cloud setup
2. ✅ Test Vertex AI integration
3. ✅ Run first data collection
4. ✅ Generate first learned rules
5. ✅ Evaluate on AWS SDK test set
6. ✅ View results dashboard

See [`docs/EXPERIMENT_DESIGN.md`](EXPERIMENT_DESIGN.md) for full methodology.
