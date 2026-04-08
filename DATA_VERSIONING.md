# Data Versioning Guide

This guide explains how the ML Forecasting Platform tracks and manages data versions to ensure **reproducibility** of experiments.

## Overview

**Problem**: When running ML experiments, you often need to know:
- Exactly which data was used for training?
- Can I reproduce this experiment with the same result?
- What changed between two experiments?

**Solution**: The platform uses **DVC (Data Version Control)** + **MLflow** to create a complete lineage of:
- Data versions (via content hashing)
- Code versions (via git commits)
- Model artifacts and metrics

## Architecture

```
Git Repository (Code)
    ↓
    ├─ Code commit hash captured in MLflow
    ↓
Training Pipeline
    ├─ Loads raw data → compute hash
    ├─ Engineers features → compute hash
    ├─ Splits train/test → compute hash
    ↓
MLflow Run
    ├─ Logs all data hashes
    ├─ Logs code version (git commit)
    ├─ Logs model + metrics
    └─ Logs lineage artifact (data_lineage.json)
    
DVC Metadata (.dvc_metadata/)
    └─ Stores detailed version info for each data stage
```

## How It Works

### 1. Data Hashing

When training runs, the platform:
- **Computes SHA-256 hash** of each data transformation stage
- Tracks: raw data → featured data → train/test splits
- Stores hash metadata in `.dvc_metadata/` folder

```python
# Example: Track data version
tracker = DataVersionTracker()
raw_data_version = tracker.track_training_data(
    raw_data, 
    name="raw_data",
    metadata={"source": "dummy"}
)
print(raw_data_version['hash'])  # e.g., "a1b2c3d4..."
```

### 2. MLflow Integration

Each experiment logs:
- **Data hashes** as parameters (e.g., `data_raw_data_hash`, `data_train_data_hash`)
- **Code version** (git commit hash)
- **Data lineage** as artifact (`data_lineage.json`)
- Model artifacts and metrics

Example MLflow parameters:
```
data_raw_data_hash: a1b2c3d4e5f6g7h8...
data_featured_data_hash: i9j0k1l2m3n4o5p6...
data_train_data_hash: q7r8s9t0u1v2w3x4...
data_test_data_hash: y5z6a7b8c9d0e1f2...
code_version: abc123def456ghi789...
```

### 3. Complete Lineage

The `data_lineage.json` artifact contains complete information:

```json
{
  "timestamp": "2026-04-08T15:30:00",
  "code_version": "abc123def456ghi789",
  "datasets": {
    "raw_data": {
      "hash": "a1b2c3d4...",
      "timestamp": "2026-04-08T15:29:00",
      "shape": [1000, 5],
      "rows": 1000,
      "columns": ["timestamp", "value", "trend", "seasonality", "noise"]
    },
    "featured_data": {
      "hash": "i9j0k1l2...",
      "timestamp": "2026-04-08T15:29:15",
      "shape": [1000, 25],
      "columns": ["timestamp", "value", "lag_1", "lag_7", "rolling_mean_7", ...]
    },
    "train_data": {
      "hash": "q7r8s9t0...",
      "timestamp": "2026-04-08T15:29:30",
      "shape": [800, 25],
      "split": "train"
    },
    "test_data": {
      "hash": "y5z6a7b8...",
      "timestamp": "2026-04-08T15:29:30",
      "shape": [200, 25],
      "split": "test"
    }
  }
}
```

## Usage

### Running Training with Data Versioning

Simply run the training pipeline as usual:

```bash
python train.py
```

The pipeline automatically:
1. Tracks all data transformations
2. Logs hashes to MLflow
3. Saves lineage artifact
4. Displays run ID and code version

Output:
```
Raw data hash: a1b2c3d4
Featured data hash: i9j0k1l2
Train hash: q7r8s9t0
Test hash: y5z6a7b8

Experiment run ID: abc-123-def
Code version: abc123def456ghi789
```

### Reproducing an Experiment

To reproduce a specific experiment with exact same data/code/model:

```bash
python reproduce_experiment.py --run-id abc-123-def
```

Output:
```
🔄 Reproducing experiment: abc-123-def

Reproduction Plan:
------------------------------------------------------------
✓ Checked out code version: abc123def456ghi789

Data versions:
  - raw_data: a1b2c3d4...
  - featured_data: i9j0k1l2...
  - train_data: q7r8s9t0...
  - test_data: y5z6a7b8...

Model parameters:
  - model_type: lightgbm
  - data_source: dummy
  - n_train: 800
  - n_test: 200

============================================================
Instructions to reproduce:
============================================================

To reproduce experiment abc-123-def:

1. Checkout code version:
   git checkout abc123def456ghi789

2. Data versions used:
   - raw_data: a1b2c3d4...
   - featured_data: i9j0k1l2...
   - train_data: q7r8s9t0...
   - test_data: y5z6a7b8...

3. Restore data (if using DVC):
   dvc checkout

4. Run training with same configuration:
   python train.py --experiment-id abc-123-def

Note: The exact data versions and code commit ensure reproducible results.

Ready to reproduce. Execute training with:
  python train.py

This will use the exact same code/data/config from run abc-123-def
```

## Checking Data Lineage in MLflow

View the complete lineage in MLflow UI:

1. Open MLflow UI: `mlflow ui` (or check configured tracking URI)
2. Select the experiment run
3. Go to **Artifacts** → `data_lineage.json`
4. View the complete data transformation history

## DVC Integration

### Initialize DVC (Already Done)

```bash
dvc init --no-scm
dvc remote add -d myremote ./data_store
```

### Track External Data Files with DVC

To version control actual CSV files:

```bash
dvc add data/raw_data.csv
git add data/raw_data.csv.dvc .gitignore
git commit -m "Add raw data version"
```

This creates `data/raw_data.csv.dvc` which tracks the file with DVC.

### Using DVC Pipelines

Run the DVC pipeline:

```bash
dvc repro dvc.yaml
```

This:
- Executes stages in order
- Caches outputs
- Tracks dependencies
- Enables reproducible workflows

## Diagnostic Workflow

### Scenario: Inference Results Don't Match

1. **Find the experiment run**:
   ```bash
   mlflow ui  # Find run ID where you got results
   ```

2. **Reproduce exact conditions**:
   ```bash
   python reproduce_experiment.py --run-id YOUR_RUN_ID
   ```

3. **Compare data versions**:
   - Check if data_lineage.json shows different data hashes
   - Verify git commit matches
   - Check if external data files changed

4. **Debug specific stage**:
   ```python
   from data_versioning import DataVersionTracker
   tracker = DataVersionTracker()
   
   # Load the archived version info
   # Compare with current data hashes
   ```

### Scenario: Model Diagnostics

To diagnose why model performs differently:

```bash
# Get the experiment run ID
python reproduce_experiment.py --run-id abc-123-def

# This shows:
# - Exact code version used
# - Exact data hashes used
# - Model parameters
# - Ability to re-create exact conditions
```

## Best Practices

1. **Always push to git before training**
   - Ensures code version is recorded
   - Allows later git checkout for reproduction

2. **Use meaningful data sources**
   - Track whether data came from dummy generator or external file
   - Store source info in metadata

3. **Monitor data lineage**
   - Check `data_lineage.json` in MLflow artifacts
   - Detect when data changes unexpectedly

4. **Version control DVC files**
   ```bash
   git add *.dvc .dvc/config .dvcignore
   git commit -m "Add data version tracking"
   ```

5. **Document data transformations**
   - Keep feature engineering code clear
   - Comments on why certain features are created

## Troubleshooting

### "No such file or directory: .dvc_metadata"

The metadata directory is created automatically during first run. If it doesn't exist:

```bash
python -c "from data_versioning import DataVersionTracker; DataVersionTracker()"
```

### "code_version: unknown"

This means the project is not a git repository or git commit couldn't be found:

```bash
git init
git add .
git commit -m "Initial commit"
```

### Data hash changed but data looks the same

This can happen due to:
- Different row order
- Float precision differences
- Index changes

To debug:

```python
import pandas as pd
from data_versioning import compute_dataframe_hash

df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')

print(f"Hash 1: {compute_dataframe_hash(df1)}")
print(f"Hash 2: {compute_dataframe_hash(df2)}")

# Check differences
print(df1.equals(df2))
```

## Key Modules

### `data_versioning.py`

- **`compute_file_hash()`** - Hash a file
- **`compute_dataframe_hash()`** - Hash a DataFrame
- **`DataVersionTracker`** - Main class to track data versions
- **`ExperimentReproducer`** - Reproduce experiments from run IDs
- **`get_git_commit_hash()`** - Get current git commit

### `pipelines/training.py`

Enhanced to:
- Create DataVersionTracker instance
- Track all data stages
- Log complete lineage to MLflow

### `reproduce_experiment.py`

Standalone script to:
- Query MLflow for experiment metadata
- Show reproduction steps
- Checkout code version
- Display data versions

## Advanced Usage

### Custom Data Tracking

```python
from data_versioning import DataVersionTracker

tracker = DataVersionTracker()

# Track custom data with metadata
version = tracker.track_training_data(
    my_dataframe,
    name="my_custom_data",
    metadata={
        "source": "external_api",
        "date_collected": "2026-04-08",
        "rows_filtered": 150
    }
)

print(f"Version hash: {version['hash']}")
```

### Querying Lineage Programmatically

```python
from data_versioning import ExperimentReproducer
from mlflow import get_run

reproducer = ExperimentReproducer()
metadata = reproducer.get_experiment_metadata("your-run-id")

print(f"Code version: {metadata['code_version']}")
print(f"Data versions: {metadata['data_versions']}")
print(f"Model params: {metadata['model_params']}")
```

## Next Steps

1. Run a training pipeline and note the run ID
2. Check MLflow UI to see logged data hashes
3. Try reproducing with `reproduce_experiment.py`
4. Set up git repository if not already done
5. Configure DVC remote storage for team collaboration
