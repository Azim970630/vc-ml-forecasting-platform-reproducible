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

## Pulling Data by Hash (DVC Recovery)

### How DVC Tracks Files by Hash

Every data file is stored in DVC's cache and Azure using its SHA-256 hash:

```bash
# File added to DVC
dvc add data/raw/sales_data.csv

# Creates: data/raw/sales_data.csv.dvc
cat data/raw/sales_data.csv.dvc
# Output:
# outs:
# - hash: md5
#   md5: eb7667eed5abf29cf3e2a508261bfb35
#   path: data/raw/sales_data.csv
#   size: 7800
```

The `.dvc` file is a **pointer** that says:
- "This file's hash is `eb7667eed5abf29cf3e2a508261bfb35`"
- "The actual data is stored in Azure Blob Storage at `azure://mlops-data`"

### Pulling Exact Data by Hash

When you run `dvc pull`, it uses the hash to find and restore the exact file:

```bash
# Step 1: Ensure .dvc file is tracked in git
git add data/raw/sales_data.csv.dvc
git commit -m "Track sales data with DVC"

# Step 2: Later, restore the exact file
dvc pull data/raw/sales_data.csv.dvc

# Step 3: Verify it matches
# DVC automatically verifies the hash:
# - Downloads file from Azure
# - Computes hash locally
# - Verifies: hash_computed == hash_in_dvc_file
# - If match → File is correct
# - If mismatch → Error (corrupted transfer)
```

**What Gets Restored**:
```
Before pull:
├─ data/raw/sales_data.csv      [doesn't exist]
├─ data/raw/sales_data.csv.dvc  [exists - pointer file]

After dvc pull:
├─ data/raw/sales_data.csv      [restored from Azure]
│  └─ hash: eb7667eed5abf29cf3e2a508261bfb35
├─ data/raw/sales_data.csv.dvc  [unchanged - pointer file]
```

### Pull All Data for Reproducibility

```bash
# In a reproduction workflow:
git checkout abc123...           # Get exact code version
dvc pull                        # Get exact data version (all files)

# This restores ALL .dvc-tracked files to match their hashes:
# - data/raw/sales_data.csv
# - Any other files added with: dvc add ...

# Then run:
python3 train.py
# Uses exact same code + data → exact same results
```

### Pull Specific File by Hash

```bash
# If you only need one file
dvc pull data/raw/sales_data.csv.dvc

# Or if .dvc file is deleted but you have the hash:
dvc pull --force  # Re-download all
```

### Verify Hash Integrity

```python
import json
from data_versioning import compute_file_hash

# Read expected hash from .dvc file
with open('data/raw/sales_data.csv.dvc', 'r') as f:
    dvc_content = f.read()
    expected_hash = dvc_content.split('md5: ')[1].split('\n')[0]

# Compute actual hash of pulled file
actual_hash = compute_file_hash("data/raw/sales_data.csv")

# Compare (first 8 chars usually enough for identification)
if actual_hash.startswith(expected_hash[:8]):
    print(f"✓ Hash verified: {expected_hash[:8]}")
    print("✓ Data integrity confirmed")
else:
    print(f"✗ Hash mismatch!")
    print(f"  Expected: {expected_hash}")
    print(f"  Actual:   {actual_hash}")
    raise ValueError("Data corruption detected")
```

### Status Check: What Needs to Be Pulled

```bash
# See which files are missing or have changed hashes
dvc status

# Example output:
# data/raw/sales_data.csv.dvc:
#   changed outs:
#     deleted:    data/raw/sales_data.csv
#     modified:   data/raw/sales_data.csv (modified)
#
# This means:
# - File was deleted locally but exists in .dvc file
# - dvc pull will restore it from Azure

# Pull to fix:
dvc pull
# ✓ data/raw/sales_data.csv restored from Azure
```

### Advanced: Manual Hash-Based Recovery

If DVC cache is corrupted, you can recover by hash directly from Azure:

```python
from azure.storage.blob import BlobServiceClient
from pathlib import Path

# Get connection string from DVC config
import configparser
config = configparser.ConfigParser()
config.read('.dvc/config')
conn_str = config['remote "azure"']['connection_string']

# Connect to Azure
blob_service = BlobServiceClient.from_connection_string(conn_str)
container = blob_service.get_container_client("mlops-data")

# Find file by hash in Azure storage structure
# DVC stores as: files/md5/eb/7667eed5abf29cf3e2a508261bfb35
hash_val = "eb7667eed5abf29cf3e2a508261bfb35"
blob_path = f"files/md5/{hash_val[:2]}/{hash_val[2:]}"

# Download
blob_client = container.get_blob_client(blob_path)
with open('data/raw/sales_data.csv', 'wb') as f:
    download_stream = blob_client.download_blob()
    f.write(download_stream.readall())

print(f"✓ Recovered file from Azure using hash: {hash_val}")
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

#### Step 3: Restore Data from Azure Blob Storage

```bash
# Pull data from Azure (DVC matches by hash automatically)
dvc pull

# This restores: data/raw/sales_data.csv
# From Azure: azure://mlops-data
# And verifies the hash matches what's in .dvc file
```

**Understanding DVC Pull with Hashes**:
```
.dvc file contains:           Azure Blob Storage contains:
├─ file: sales_data.csv      ├─ files/md5/eb/7667eed5abf29cf3e2a508261bfb35
├─ md5: eb7667ee...          │  (hash: eb7667eed5abf29cf3e2a508261bfb35)
└─ size: 7800 bytes          └─ size: 7800 bytes

dvc pull:
1. Reads .dvc file → gets hash eb7667ee...
2. Checks local disk → file doesn't exist
3. Queries Azure → finds file with hash eb7667ee...
4. Downloads file → verifies hash matches
5. Stores locally → data/raw/sales_data.csv ready
```

**Verify Hash After Pull**:
```python
from data_versioning import compute_file_hash

hash_after_pull = compute_file_hash("data/raw/sales_data.csv")
print(f"Hash: {hash_after_pull}")
# Should match what's in .dvc file
```

#### Step 4: Run training again

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

## Complete Reproducibility Workflow: Code + Data + Hashes

### The Full Picture

```
Original Run (Day 1):
├─ Code: git commit abc123...
├─ Data: data/raw/sales_data.csv
│  ├─ SHA-256 hash: c54d29c9...
│  └─ DVC hash (md5): eb7667ee...
├─ MLflow logs:
│  ├─ code_version: abc123...
│  ├─ data_raw_data_hash: c54d29c9... (for audit)
│  └─ run_id: 541d0c7f...
├─ DVC tracking:
│  ├─ .dvc_metadata/ folder (metadata)
│  ├─ data/raw/sales_data.csv.dvc (pointer, committed to git)
│  └─ data/raw/sales_data.csv (actual file, in Azure + local cache)
└─ Result: MAE = 18.564

Reproduction (Day 150 - auditor asks: prove it was 18.564):
├─ Step 1: Query MLflow → find run_id 541d0c7f
│  ├─ Extract: code_version = abc123...
│  ├─ Extract: data_raw_data_hash = c54d29c9...
│  └─ Confirm: model performance = 18.564
├─ Step 2: Checkout git code
│  └─ git checkout abc123...
├─ Step 3: Verify .dvc file is in git
│  └─ data/raw/sales_data.csv.dvc (commit abc123 has it)
├─ Step 4: Pull exact data from Azure by hash
│  ├─ dvc pull
│  ├─ Reads: data/raw/sales_data.csv.dvc
│  ├─ Gets hash: eb7667ee...
│  ├─ Queries Azure: files/md5/eb/7667eed5abf29cf3e2a508261bfb35
│  ├─ Downloads: data/raw/sales_data.csv
│  └─ Verifies hash matches ✓
├─ Step 5: Verify data integrity
│  ├─ compute_file_hash("data/raw/sales_data.csv")
│  ├─ Get: c54d29c9... (matches MLflow log ✓)
│  └─ Confirmed: using exact data
├─ Step 6: Re-run training
│  └─ python3 train.py
└─ Result: MAE = 18.564 ✓✓✓
   (PROOF: Code + Data + Results match perfectly)
```

### Quick Reference: How Hashes Enable Reproducibility

| Component | Hash Type | Purpose | Stored Where |
|-----------|-----------|---------|--------------|
| Data file | SHA-256 | Proof of exact data used | MLflow params + .dvc_metadata/ |
| Data file | MD5 (DVC) | Locate file in Azure storage | .dvc file (pointer) |
| Code | Git SHA | Proof of exact code used | MLflow params + Git history |
| Model | N/A | Trained artifact | MLflow artifacts |

**The chain**:
```
Audit request
  ↓
MLflow logs: code_version + data_hash
  ↓
git checkout code_version
  ↓
dvc pull (uses MD5 to find file in Azure)
  ↓
Verify SHA-256 hash matches MLflow record
  ↓
Re-run training
  ↓
Results match exactly ✓
```

### Hands-On: End-to-End Reproduction

```bash
# 1. You have a run ID from 6 months ago
RUN_ID="541d0c7fdb9a43999a5d12be2c7f9d31"

# 2. Get the metadata
python3 reproduce_experiment.py --run-id $RUN_ID
# Output:
# Code version: 91b64a1504835d4...
# Data versions:
#   - raw_data: c54d29c9...
# Metrics:
#   - mae: 18.564

# 3. Checkout exact code
git checkout 91b64a1504835d4

# 4. Check what .dvc file looks like
cat data/raw/sales_data.csv.dvc
# Shows MD5 hash for Azure location

# 5. Pull data from Azure (automatic hash matching)
dvc pull
# Downloads: data/raw/sales_data.csv from Azure
# Verifies hash matches .dvc file

# 6. Verify data integrity
python3 << 'PYEOF'
from data_versioning import compute_file_hash
actual = compute_file_hash("data/raw/sales_data.csv")
expected = "c54d29c9..."
assert actual.startswith(expected[:8]), "Hash mismatch!"
print("✓ Data verified")
PYEOF

# 7. Retrain
python3 train.py
# New run ID: xyz-789

# 8. Check result
mlflow ui
# Run xyz-789: mae = 18.564
# ✓ Matches original (541d0c7f) perfectly!
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
