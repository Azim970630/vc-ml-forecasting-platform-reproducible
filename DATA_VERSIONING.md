# Data Versioning & Reproducibility Guide

This guide explains how the ML Forecasting Platform ensures complete reproducibility through **data versioning**, **code versioning**, and **experiment tracking**.

## Overview

**The Problem**: When running ML experiments, you need to know:
- Exactly which data was used for training?
- Can I reproduce this experiment and get the same results?
- What changed between two experiments?

**The Solution**: Three-layer versioning system:

```
Layer 1: Data Versioning    → SHA-256 hashing of DataFrames
Layer 2: Code Versioning    → Git commit hashes
Layer 3: Experiment Tracking → MLflow logging
```

Together, these enable **complete reproducibility**.

## How It Works

### Layer 1: Data Versioning via Content Hashing

Every data transformation is hashed using SHA-256:

```
Training Pipeline
├─ Load raw data
│  └─ Compute hash: c54d29c9...  ← Captures exact data state
├─ Engineer features
│  └─ Compute hash: e971c052...  ← Captures feature engineering state
├─ Split train/test
│  ├─ Train hash: e03560ee...
│  └─ Test hash: 0ea5701f...
└─ Train model
```

**Key Properties**:
- **Deterministic**: Same data → same hash (always)
- **Unique**: Different data → different hash (2^256 possibilities)
- **Sensitive**: Detects any changes (value, order, precision)

### Layer 2: Code Versioning via Git

Git commit hash is captured with each training run:

```
git commit abc123... → Training Run
  ↓
MLflow logs: code_version = abc123...
  ↓
Later: git checkout abc123... + rerun = exact same code
```

### Layer 3: Experiment Tracking with MLflow

All versions are logged to MLflow:

```
MLflow Run
├─ Parameters
│  ├─ data_raw_data_hash: c54d29c9...
│  ├─ data_featured_data_hash: e971c052...
│  ├─ data_train_data_hash: e03560ee...
│  ├─ data_test_data_hash: 0ea5701f...
│  └─ code_version: abc123...
├─ Metrics
│  ├─ mae: 18.56
│  ├─ rmse: 20.17
│  ├─ mape: 9.64
│  └─ smape: 10.21
└─ Artifacts
   ├─ lightgbm_model.pkl (trained model)
   └─ data_lineage.json (complete history)
```

## Using Data Versioning

### Running Training with Automatic Versioning

```bash
python3 train.py
```

Output:
```
Raw data hash: c54d29c9
Featured data hash: e971c052
Train hash: e03560ee
Test hash: 0ea5701f

Experiment run ID: 541d0c7fdb9a43999a5d12be2c7f9d31
Code version: 91b64a1504835d4564107a144217de38cb979a9d
```

All hashes are automatically:
- Logged to MLflow
- Saved to `.dvc_metadata/` folder
- Stored in `data_lineage.json` artifact

### Viewing Data Lineage in MLflow

```bash
mlflow ui
```

Then in browser:
1. Open http://localhost:5000
2. Click on a run
3. Go to **Artifacts** tab
4. View `data_lineage.json` to see complete data history

Example:
```json
{
  "timestamp": "2026-04-08T15:15:51",
  "code_version": "91b64a1504835d4...",
  "datasets": {
    "raw_data": {
      "hash": "c54d29c9...",
      "shape": [200, 3],
      "rows": 200,
      "columns": ["timestamp", "series_id", "target"],
      "metadata": {"source": "offline"}
    },
    "featured_data": {
      "hash": "e971c052...",
      "shape": [200, 25],
      "rows": 200
    },
    "train_data": {
      "hash": "e03560ee...",
      "shape": [160, 25]
    },
    "test_data": {
      "hash": "0ea5701f...",
      "shape": [40, 25]
    }
  }
}
```

## Reproducing Experiments

### Complete Reproduction Workflow

To reproduce an experiment exactly:

#### Step 1: Get the run ID

Open MLflow UI and find the run you want to reproduce. Copy its run ID.

#### Step 2: Checkout code version

```bash
# First, find the code version
python3 reproduce_experiment.py --run-id YOUR_RUN_ID
```

Output shows:
```
Code version: 91b64a1504835d4...
```

Then checkout:
```bash
git checkout 91b64a1504835d4
```

#### Step 3: Run training again

```bash
python3 train.py
```

#### Step 4: Compare results

The metrics should match (or be very close due to stochastic behavior):

```
MLflow Run 1 (original):
- mae: 18.56
- rmse: 20.17

MLflow Run 2 (reproduced):
- mae: 18.56  ← Should match!
- rmse: 20.17
```

### Why Exact Reproduction Works

```
Original Experiment              Reproduced Experiment
├─ Code: abc123                  └─ Code: abc123 (checked out)
├─ Data hash: c54d29c9           └─ Data hash: c54d29c9 (same input)
├─ Features hash: e971c052       └─ Features hash: e971c052 (same code)
├─ Train hash: e03560ee          └─ Train hash: e03560ee (same split)
└─ Result: MAE = 18.56           └─ Result: MAE = 18.56 ✓
```

## Diagnostic Workflows

### Scenario 1: Inference Results Don't Match

**Problem**: You got different results from the same model.

**Investigation**:
```bash
# 1. Find the original run in MLflow
mlflow ui

# 2. Check what data/code was used
python3 reproduce_experiment.py --run-id ORIGINAL_RUN_ID

# 3. Compare data hashes
# - Did raw_data hash change? → Input data changed
# - Did code_version change? → Code changed
# - Did model hash change? → Model retrained

# 4. If data changed, check what changed:
git log --oneline data/
```

### Scenario 2: Reproduce for Validation

**Problem**: Auditor asks: "Can you prove this model works the same way?"

**Solution**:
```bash
# 1. Get the run ID from audit records
RUN_ID="541d0c7fdb9a43999a5d12be2c7f9d31"

# 2. Show complete reproduction instructions
python3 reproduce_experiment.py --run-id $RUN_ID

# 3. Execute the reproduction
python3 train.py

# 4. MLflow shows side-by-side metrics match → Validation complete!
```

### Scenario 3: Debug Model Performance Regression

**Problem**: Model performance dropped between experiments.

**Solution**:
```bash
# 1. Get two run IDs (old = good, new = bad)
python3 reproduce_experiment.py --run-id OLD_RUN_ID
python3 reproduce_experiment.py --run-id NEW_RUN_ID

# 2. Compare outputs:
echo "=== Data Changes ==="
diff .dvc_metadata/raw_data_old.json .dvc_metadata/raw_data_new.json

echo "=== Code Changes ==="
git diff OLD_COMMIT..NEW_COMMIT

echo "=== Metric Changes ==="
# Use MLflow UI to compare metrics side-by-side
```

## Understanding Data Hashes

### When Does Hash Change?

Hash changes when:
- ✓ Row values change (data changed)
- ✓ Row order changes (shuffle happened)
- ✓ Columns added/removed (features changed)
- ✓ Float precision changes (numerical instability)
- ✓ Index changes (resampling occurred)

### When Does Hash Stay the Same?

Hash stays same when:
- ✗ Column names change (doesn't affect hash)
- ✗ Memory location changes (only values matter)
- ✗ Comments added to code (code changes don't affect data)

### Hash Format

```
c54d29c95a144d72d576e3c1e20848b210081b37b49fff98ab94585a1105ffa9
                                      ↑
                           First 8 chars used as ID
                           in .dvc_metadata/ filenames
```

## Metadata Storage

### Location: `.dvc_metadata/` Directory

```
.dvc_metadata/
├── raw_data_train_c54d29c9.json
├── featured_data_train_e971c052.json
├── train_data_train_e03560ee.json
└── test_data_test_0ea5701f.json
```

### File Format

Each file contains:

```json
{
  "name": "raw_data",
  "split": "train",
  "hash": "c54d29c95a144d72d576e3c1e20848b...",
  "timestamp": "2026-04-08T15:15:51.914053",
  "shape": [200, 3],
  "rows": 200,
  "columns": ["timestamp", "series_id", "target"],
  "metadata": {
    "source": "offline"
  }
}
```

### Versioning Metadata

Track metadata files in git:
```bash
git add .dvc_metadata/
git commit -m "Log data versions for experiment run"
```

This creates an audit trail of all data versions used.

## Best Practices

### 1. Always Commit Before Training

```bash
git add .
git commit -m "Feature: add new preprocessing"
python3 train.py  # Code version will be captured
```

This ensures reproducibility is possible.

### 2. Monitor Data Changes

```bash
# Check if data changed unexpectedly
ls -la .dvc_metadata/
# If new files appear, data changed!

# See what changed
git diff .dvc_metadata/
```

### 3. Document Data Sources

```python
# When tracking data, add metadata
version = tracker.track_training_data(
    df,
    name="raw_data",
    metadata={
        "source": "offline",
        "filepath": "data/raw_data.csv",
        "date_collected": "2026-04-08"
    }
)
```

### 4. Use Meaningful Git Commits

```bash
# Good ✓
git commit -m "Fix: handle null values in feature engineering"

# Bad ✗
git commit -m "update"
```

When you reproduce, you'll see the commit message in `git log`.

### 5. Review Lineage Before Inference

```bash
# Before using a model in production:
mlflow ui
# Navigate to run
# Check data_lineage.json artifact
# Verify data sources and code version
```

## Advanced Usage

### Custom Data Tracking

```python
from data_versioning import DataVersionTracker
import pandas as pd

tracker = DataVersionTracker()

# Track external data file
version = tracker.track_external_data(
    "data/my_data.csv",
    name="external_data",
    metadata={"source": "API", "endpoint": "/v1/data"}
)

print(f"File hash: {version['hash']}")
print(f"File size: {version['size_bytes']} bytes")
```

### Programmatic Lineage Query

```python
from data_versioning import ExperimentReproducer

reproducer = ExperimentReproducer()
metadata = reproducer.get_experiment_metadata("run-id")

# Extract information
print(f"Code: {metadata['code_version']}")
print(f"Data versions: {metadata['data_versions']}")
print(f"Model config: {metadata['model_params']}")

# Use for validation
if metadata['data_versions']['raw_data'] == expected_hash:
    print("✓ Data matches expected version")
else:
    print("✗ Data mismatch - reproduction unsafe")
```

### Comparing Experiments

```python
from data_versioning import ExperimentReproducer

reproducer = ExperimentReproducer()

# Get two experiments
exp1 = reproducer.get_experiment_metadata("run-1")
exp2 = reproducer.get_experiment_metadata("run-2")

# Compare
if exp1['data_versions'] == exp2['data_versions']:
    print("✓ Same data used")
else:
    print("✗ Different data - metrics not comparable")

if exp1['code_version'] == exp2['code_version']:
    print("✓ Same code used")
else:
    print("✗ Different code - model logic may differ")
```

## Troubleshooting

### Q: "code_version: unknown"

**Cause**: Project is not a git repository.

**Fix**:
```bash
git init
git add .
git commit -m "Initial commit"
python3 train.py
```

### Q: Data hash changed but data looks same

**Cause**: Minor differences (float precision, row order, index).

**Debug**:
```python
import pandas as pd
from data_versioning import compute_dataframe_hash

df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')

print(compute_dataframe_hash(df1))
print(compute_dataframe_hash(df2))
print(df1.equals(df2))
```

### Q: Can't checkout old commit

**Cause**: Commit doesn't exist in this repository (different repo history).

**Solution**: Reproducibility works within same repository only.

### Q: MLflow not showing old runs

**Cause**: Using different tracking URI or `mlruns/` was deleted.

**Fix**:
```bash
# Verify tracking URI
cat config/base.yaml | grep tracking_uri

# Check mlruns exists
ls -la mlruns/
```

## Key Modules

**`data_versioning.py`**:
- `compute_file_hash()` — Hash files
- `compute_dataframe_hash()` — Hash DataFrames
- `DataVersionTracker` — Track versions
- `ExperimentReproducer` — Reproduce experiments
- `get_git_commit_hash()` — Get git version

**`reproduce_experiment.py`**:
- `reproduce_experiment()` — Main reproduction function
- Handles missing commits gracefully
- Shows all required information

**`.dvc_metadata/`**:
- JSON files with detailed version info
- One file per data stage

**`data_lineage.json` (MLflow artifact)**:
- Complete lineage in one JSON file
- Can be shipped with model for audit trail

## Summary

| Aspect | Mechanism | Captured |
|--------|-----------|----------|
| Data version | SHA-256 hashing | ✅ Logged to MLflow |
| Code version | Git commit | ✅ Logged to MLflow |
| Metadata | `.dvc_metadata/` JSONs | ✅ Accessible offline |
| Lineage | `data_lineage.json` artifact | ✅ In MLflow |
| Reproducibility | Checkout code + rerun | ✅ Exact same results |

---

**See Also**: 
- [README.md](README.md) — Project overview
- [USER_GUIDE.md](USER_GUIDE.md) — Step-by-step usage
- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — Deep technical details
