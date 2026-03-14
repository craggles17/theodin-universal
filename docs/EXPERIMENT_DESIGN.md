# Theodin Universal - Experiment Design

## Thesis

**theodin learns transferable cloud infrastructure patterns** that improve code quality across:
- **Cloud Providers**: GCP → AWS → Azure
- **Infrastructure**: Terraform → Pulumi → CDK
- **SDKs**: google-cloud → boto3 → azure-sdk
- **Domains**: Data pipelines → ML ops → API services

## Why Cloud Infrastructure?

1. **High-stakes code**: Infrastructure bugs are expensive
2. **Pattern transfer**: GCP patterns should help with AWS
3. **Diverse repos**: Rich PR history in cloud SDK repos
4. **Measurable impact**: Test coverage, bug fixes, security improvements

---

## Experiment 1: Cross-Cloud SDK Transfer

### Hypothesis
Rules learned from GCP SDK PRs improve AWS SDK code quality.

### Training Data
**Repos** (1000+ PRs each):
- `googleapis/python-aiplatform` (Vertex AI SDK)
- `googleapis/python-bigquery`
- `googleapis/python-storage`
- `googleapis/python-firestore`

**Collection criteria**:
- PRs with tests modified
- Bug fixes (labels: `type: bug`, `priority: p0/p1`)
- Security fixes
- API improvements

### Test Data
**Repos** (held out):
- `boto/boto3` (AWS SDK)
- `boto/botocore`
- `aws/aws-cdk-python`

**Test cases**:
- Open issues with `good first issue`, `bug` labels
- Recent PRs (for validation)
- SWE-bench style: issue → expected diff

### Metrics
| Metric | Baseline | Theodin | Target |
|--------|----------|---------|--------|
| Test coverage | Current | +10% | ✓ |
| Bug fix accuracy | Claude Code baseline | +15% | ✓ |
| Security issue detection | Manual baseline | +20% | ✓ |
| Code quality score (ruff) | Baseline | -25% violations | ✓ |

### Procedure
```bash
# 1. Collect GCP SDK training data
uv run theodin collect \
  --repos googleapis/python-aiplatform,googleapis/python-bigquery,googleapis/python-storage \
  --labels "type: bug,priority: p0,priority: p1" \
  --require-tests \
  --limit 1000 \
  --output data/gcp_sdk_train.jsonl

# 2. Learn rules with Vertex AI (Gemini 1.5 Pro)
uv run theodin learn \
  --input data/gcp_sdk_train.jsonl \
  --provider vertex \
  --model gemini-1.5-pro \
  --output rules/gcp_to_aws_learned.md

# 3. Collect AWS SDK test cases
uv run theodin collect \
  --repos boto/boto3,boto/botocore \
  --labels "good first issue,bug" \
  --limit 50 \
  --output data/aws_sdk_test.jsonl

# 4. Evaluate baseline (no rules)
uv run theodin evaluate \
  --input data/aws_sdk_test.jsonl \
  --provider vertex \
  --rules "" \
  --output results/baseline_aws.json

# 5. Evaluate with learned rules
uv run theodin evaluate \
  --input data/aws_sdk_test.jsonl \
  --provider vertex \
  --rules rules/gcp_to_aws_learned.md \
  --output results/theodin_aws.json

# 6. Statistical analysis
python scripts/analyze_results.py \
  --baseline results/baseline_aws.json \
  --theodin results/theodin_aws.json \
  --output results/cross_cloud_analysis.html
```

---

## Experiment 2: Infrastructure-as-Code (IaC) Transfer

### Hypothesis
Patterns from Terraform repos improve Pulumi/CDK code.

### Training Data
**Repos**:
- `hashicorp/terraform-provider-google`
- `hashicorp/terraform-provider-aws`
- `hashicorp/terraform-provider-azurerm`

**Focus**: Resource configuration patterns, state management, error handling

### Test Data
**Repos**:
- `pulumi/pulumi-gcp`
- `pulumi/pulumi-aws`
- `aws/aws-cdk` (Python constructs)

### Key Patterns to Learn
- Resource dependency management
- Error recovery strategies
- State consistency checks
- Security best practices (IAM, networking)
- Cost optimization patterns

---

## Experiment 3: Data Pipeline Code (Domain-Specific)

### Hypothesis
theodin learns data engineering patterns that generalize across cloud platforms.

### Training Data
**Repos**:
- `apache/beam` (Python SDK)
- `dagster-io/dagster`
- `apache/airflow`
- `prefecthq/prefect`

**Focus**: 
- Pipeline orchestration
- Error handling in distributed systems
- Retry logic
- Data validation
- Performance optimization

### Test Data
**Repos** (held out during training):
- GCP Dataflow examples
- AWS Glue scripts
- Azure Data Factory pipelines (Python activities)

### Real-World Test Cases
1. Fix memory leaks in long-running pipelines
2. Add proper retry logic with exponential backoff
3. Improve error messages in data validation
4. Add data quality checks
5. Optimize shuffle operations

---

## Experiment 4: ML Ops Code Quality

### Hypothesis
Vertex AI SDK patterns transfer to other ML platforms.

### Training Data
**Repos**:
- `googleapis/python-aiplatform`
- `kubeflow/pipelines` (Python SDK)
- `tensorflow/tfx`

**Focus**:
- Model versioning
- Experiment tracking
- Pipeline parameterization
- Resource management (GPU/TPU)
- Monitoring/alerting

### Test Data
**Repos**:
- `aws/sagemaker-python-sdk`
- `Azure/azureml-sdk-for-python`
- `mlflow/mlflow`

### Coding Systems Test
Apply learned rules to:
- **Cursor**: `.cursorrules` for ML ops projects
- **Claude Code**: `CLAUDE.md` for SageMaker development
- **Aider**: `CONVENTIONS.md` for Azure ML
- **Codex**: `RULES.md` for Vertex AI

**Before/After Metrics**:
- SWE-bench scores on ML platform issues
- Time to implement feature requests
- Bug introduction rate
- Code review feedback volume

---

## Experiment 5: Zero-Shot Cloud Provider

### Hypothesis
Train on GCP + AWS, test on Azure (never seen).

### Setup
**Train**: All GCP and AWS repos (2000+ PRs)  
**Test**: Azure SDK repos (completely held out)

**Measure**: How well do GCP/AWS patterns transfer to Azure?

### Test Cases
- `azure-sdk-for-python` open issues
- Recent merged PRs (validation set)
- Security vulnerabilities from CVE database

---

## Data Collection Protocol

### PR Quality Tiers

| Tier | Criteria | Weight |
|------|----------|--------|
| Gold | Issue → PR + tests + security label | 3x |
| Silver | Issue → PR + tests | 2x |
| Bronze | PR with good commit message | 1x |
| Skip | Dependency bumps, typo fixes | 0x |

### Fairness Protocol

For each issue → PR pair:

1. **Clone repo at issue-opening commit**
   ```bash
   git clone <repo>
   git checkout <issue_commit_sha>
   ```

2. **Extract full codebase context**:
   - Complete file tree
   - README, CONTRIBUTING, docs/
   - All test files
   - CI config (.github/, .gitlab-ci.yml)
   - Linting rules (pyproject.toml, .ruff.toml)

3. **Build prompt**:
   ```
   Repository: <name>
   Issue #<num>: <title>
   
   <issue_body>
   
   Labels: <labels>
   
   Relevant files:
   <tree + file contents>
   
   Task: Generate a unified diff that fixes this issue.
   ```

4. **Evaluate**:
   - Compare generated diff to actual merged PR
   - Measure: exact match, semantic equivalence, test pass rate

---

## Statistical Rigor

### Sample Sizes
- **Training**: 1000+ PRs per cloud provider
- **Test**: 50+ issues per experiment (α=0.05, power=0.8)

### Significance Testing
- Paired t-test (baseline vs theodin on same test set)
- Bonferroni correction for multiple comparisons
- Report: p-value, effect size (Cohen's d), confidence intervals

### Validation
- **K-fold cross-validation** (k=5) on training data
- **Temporal split**: train on PRs before 2025, test on 2025-2026
- **Repo holdout**: leave one cloud provider out

---

## Implementation Checklist

### Phase 1: Setup (This Week)
- [ ] Install gcloud CLI
- [ ] Configure Vertex AI authentication
- [ ] Test theodin Vertex provider
- [ ] Create `configs/vertex.yaml`

### Phase 2: Data Collection (Week 1)
- [ ] Collect GCP SDK PRs (googleapis repos)
- [ ] Collect AWS SDK PRs (boto3, botocore)
- [ ] Collect Azure SDK PRs (azure-sdk-for-python)
- [ ] Filter by quality tiers
- [ ] Extract issue → PR pairs

### Phase 3: Training (Week 2)
- [ ] Run theodin learn on GCP data
- [ ] Validate learned rules (manual review)
- [ ] Generate CLAUDE.md, .cursorrules formats
- [ ] Document learned patterns

### Phase 4: Evaluation (Week 3)
- [ ] Run baseline (no rules) on AWS test set
- [ ] Run theodin (with rules) on AWS test set
- [ ] Measure metrics (coverage, accuracy, quality)
- [ ] Statistical analysis
- [ ] Generate reports

### Phase 5: Coding Systems (Week 4)
- [ ] Test rules with Cursor
- [ ] Test rules with Claude Code
- [ ] Test rules with Aider
- [ ] Test rules with Codex
- [ ] Before/after SWE-bench comparison

### Phase 6: Publication
- [ ] Write up results
- [ ] Create interactive dashboard
- [ ] Blog post / paper
- [ ] Open source datasets
- [ ] Demo video

---

## Success Criteria

### Minimum Viable Proof
- ✅ **One successful cross-cloud transfer** (GCP → AWS)
- ✅ **Statistically significant improvement** (p < 0.05)
- ✅ **Real-world applicability** (works on open GitHub issues)

### Strong Proof
- ✅ All 5 experiments show improvement
- ✅ Zero-shot generalization works
- ✅ Improves at least 2 coding systems (Cursor + Claude Code)

### Publication-Ready
- ✅ All experiments + ablations complete
- ✅ Open-source datasets released
- ✅ Interactive dashboard live
- ✅ Reproducible with CI/CD
- ✅ Peer-reviewed or conference accepted

---

## Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Setup + Data Collection | GCP/AWS/Azure PR datasets |
| 2 | Training + Rule Learning | `gcp_to_aws_learned.md` |
| 3 | Evaluation | Statistical results |
| 4 | Coding Systems Testing | Before/after comparisons |
| 5 | Dashboard + Blog Post | Public results |

**Total**: 5 weeks to publication-ready proof

---

## Open Questions

1. **Sample size**: Is 1000 PRs enough, or need 5000+?
2. **Model choice**: Gemini 1.5 Pro vs Flash vs Opus for learning?
3. **Rule format**: CLAUDE.md style vs structured YAML?
4. **Evaluation**: Human review vs automated metrics?

**Decision**: Start with 1000 PRs, Gemini 1.5 Pro, CLAUDE.md format, automated metrics first (then add human review for top results).

---

Last updated: 2026-03-14
