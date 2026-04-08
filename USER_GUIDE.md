# User Guide — ML Forecasting Platform with Data Versioning

A step-by-step guide for using the ML Forecasting Platform for training, inference, and reproducing experiments.

## Table of Contents

1. [Installation](#installation)
2. [First Training](#first-training)
3. [Viewing Results in MLflow](#viewing-results-in-mlflow)
4. [Understanding Data Versioning](#understanding-data-versioning)
5. [Reproducing Experiments](#reproducing-experiments)
6. [Batch Inference](#batch-inference)
7. [Common Workflows](#common-workflows)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project**
   ```bash
   cd MLOps\ Beginner\ \(Data\ Versioning\)
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Install development tools** (for testing, linting)
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Verify installation**
   ```bash
   python3 -c "import mlflow; import pandas; print('✓ All dependencies installed')"
   ```

## First Training

### Run Your First Training

```bash
python3 train.py
```

This will:
1. Load data (by default, uses dummy generator)
2. Engineer features (lag, rolling stats, calendar features)
3. Split into train/test
4. Train a LightGBM model
5. Log everything to MLflow with data versions
6. Display run ID and code version

**Output example:**
```
Loading data...
Loaded 200 rows
Raw data hash: c54d29c95a144d72d576e3c1e20848b
Featured data hash: e971c05220389bbca5dccedfeb063bf2
Train hash: e03560eeddafac374e10ae8490e42b92d
Test hash: 0ea5701f643538763b7a504911bc5f7bc

Engineering features...
Features: ['timestamp', 'series_id', 'target', 'lag_1', 'lag_7', 'lag_30', ...]

Training lightgbm model...
Evaluating model...
Metrics: {'mae': 18.56, 'rmse': 20.17, 'mape': 9.64, 'smape': 10.21}
Model saved to models/lightgbm_model.pkl

Experiment run ID: 541d0c7fdb9a43999a5d12be2c7f9d31
Code version: 91b64a1504835d4564107a144217de38cb979a9d

✅ Training complete!
   MAE: 18.56
   RMSE: 20.17
   Model: models/lightgbm_model.pkl

View results in MLflow: mlflow ui
```

### Understanding What Happened

**Data Versioning**: Each step computes a SHA-256 hash of the data
- Raw data hash: Identifies the original loaded data
- Featured data hash: Identifies data after feature engineering
- Train hash: Identifies the training subset
- Test hash: Identifies the test subset

**Code Version**: Git commit hash is captured
- Allows recreating exact conditions later
- If not in a git repo, shows "unknown"

**Model**: Saved to `models/lightgbm_model.pkl`
- Can be loaded later for inference
- Registered with MLflow

## Viewing Results in MLflow

MLflow is the experiment tracking system. It logs everything about your training runs.

### Start MLflow UI

```bash
mlflow ui
```

Then open http://localhost:5000 in your browser.

### What You'll See

1. **Experiments** (left sidebar)
   - Default experiment "Default"
   - Click to expand and see runs

2. **Runs** (main panel)
   - Each training run shows as a row
   - Click a run to see details

3. **Run Details Page**
   - **Parameters** — What was configured
     - `model_type: lightgbm`
     - `data_source: dummy`
     - `data_raw_data_hash: c54d29c95a...`
     - `code_version: 91b64a1504...`
   
   - **Metrics** — How well the model performed
     - `mae: 18.56`
     - `rmse: 20.17`
     - `mape: 9.64`
     - `smape: 10.21`
   
   - **Artifacts** — Files saved
     - `lightgbm_model.pkl` — The trained model
     - `data_lineage.json` — Complete data version info
   
   - **Tags** — Labels for easy filtering
     - `reproducible: true`

### Viewing Data Lineage

In the run details page, scroll down to **Artifacts** and click on `data_lineage.json` to see:

```json
{
  "timestamp": "2026-04-08T15:15:51.914053",
  "code_version": "91b64a1504835d4564107a144217de38cb979a9d",
  "datasets": {
    "raw_data": {
      "hash": "c54d29c95a144d72d576e3c1e20848b...",
      "timestamp": "2026-04-08T15:15:51",
      "shape": [200, 3],
      "rows": 200,
      "columns": ["timestamp", "series_id", "target"]
    },
    "featured_data": { ... },
    "train_data": { ... },
    "test_data": { ... }
  }
}
```

This shows exactly what data was used at each stage.

## Understanding Data Versioning

### Why Data Versioning?

When you run ML experiments, you need to know:
- **Which data was used?** If inference results differ, was it the data?
- **Can I reproduce this?** Given a past experiment, can I get the same results?
- **What changed?** Between two experiments, which data/code changed?

Data versioning answers these questions.

### How It Works

```
Training Run
├─ Load data (raw)
│  └─ Compute hash: c54d29c9...
├─ Engineer features
│  └─ Compute hash: e971c052...
├─ Split train/test
│  ├─ Train hash: e03560ee...
│  └─ Test hash: 0ea5701f...
├─ Train model
├─ Log to MLflow
│  ├─ data_raw_data_hash: c54d29c9...
│  ├─ data_featured_data_hash: e971c052...
│  ├─ data_train_data_hash: e03560ee...
│  ├─ data_test_data_hash: 0ea5701f...
│  └─ code_version: 91b64a1...
└─ Save lineage
   └─ data_lineage.json (complete history)
```

### Data Hash Explained

A data hash is a unique fingerprint of the data:
- Same data = same hash
- Different data = different hash
- Hash is deterministic (running twice with same data gives same hash)

If your data changes:
- Different order of rows → different hash
- Different values → different hash
- Different column order → different hash
- Different float precision → different hash

This sensitivity helps catch unexpected data changes!

## Reproducing Experiments

### Basic Reproduction

To recreate any past experiment exactly:

```bash
python3 reproduce_experiment.py --run-id 541d0c7fdb9a43999a5d12be2c7f9d31
```

This shows:
```
🔄 Reproducing experiment: 541d0c7fdb9a43999a5d12be2c7f9d31

Reproduction Plan:
------------------------------------------------------------
✓ Code version: 91b64a1504835d4564107a144217de38cb979a9d

Data versions:
  - raw_data: c54d29c9...
  - featured_data: e971c052...
  - train_data: e03560ee...
  - test_data: 0ea5701f...

Model parameters:
  - model_type: lightgbm
  - n_train: 160
  - n_test: 40

Ready to reproduce. Execute training with:
  python3 train.py

This will use the exact same code/data/config from run 541d0c7fdb9a43999a5d12be2c7f9d31
```

### Step-by-Step Reproduction

1. **Get the run ID from MLflow UI**
   - Open http://localhost:5000
   - Find the experiment run you want to reproduce
   - Copy the run ID

2. **Show reproduction plan**
   ```bash
   python3 reproduce_experiment.py --run-id YOUR_RUN_ID
   ```

3. **Follow the instructions**
   - Checkout code version: `git checkout <commit>`
   - Restore data (if needed): `dvc checkout`
   - Run training: `python3 train.py`

### Important Notes

- **Git repo required**: To reproduce, the project must be a git repository
- **Same environment**: Install same dependencies (requirements.txt)
- **Data availability**: Data files must be available (or use dummy generator)
- **Determinism**: Most ML libraries have stochastic behavior, so results may vary slightly

## Batch Inference

### Generate Predictions

```bash
python3 -c "
from pipelines.batch_inference import run_inference_pipeline
from config_loader import load_config

config = load_config()
predictions = run_inference_pipeline(config)
print(predictions)
"
```

This loads the trained model and generates forecasts.

### Using Batch Inference in Code

```python
from pipelines.batch_inference import run_inference_pipeline
from config_loader import load_config
import pandas as pd

# Load configuration
config = load_config()

# Run inference
predictions = run_inference_pipeline(config)

# predictions is a DataFrame with columns:
# - timestamp
# - series_id
# - prediction

# Save to CSV
predictions.to_csv('forecasts.csv', index=False)

# Analyze predictions
print(f"Generated {len(predictions)} forecasts")
print(f"Forecast range: {predictions['prediction'].min():.2f} to {predictions['prediction'].max():.2f}")
```

## Common Workflows

### Workflow 1: Train and Compare Models

```bash
# Train with LightGBM
python3 train.py

# View in MLflow (note the run ID)
mlflow ui

# Later, train with different parameters
# Edit config/model.yaml to change parameters
python3 train.py

# Compare runs in MLflow UI
```

### Workflow 2: Use External Data

```bash
# Edit config/data.yaml
# Change:
#   source: dummy
# To:
#   source: offline
#   offline:
#     filepath: data/my_data.csv
#     columns:
#       timestamp: date_column
#       value: price_column

# Run training
python3 train.py
```

### Workflow 3: Debug Why Results Changed

```bash
# You ran an experiment yesterday (run ID: abc-123)
# Today, you got different results (run ID: xyz-789)
# What changed?

# 1. Get metadata for both runs
python3 reproduce_experiment.py --run-id abc-123
python3 reproduce_experiment.py --run-id xyz-789

# 2. Compare:
# - Code versions (look for git diff)
# - Data versions (look for different hashes)
# - Model parameters (look for configuration changes)

# 3. If data changed:
#    - Check if raw_data hash differs
#    - Check what changed in source data

# 4. If code changed:
#    - Use git diff between commits
#    - git diff abc-123 xyz-789
```

### Workflow 4: Reproduce for Diagnosis

```bash
# You have inference results from experiment abc-123
# You want to understand exactly how they were generated

# 1. Get reproduction plan
python3 reproduce_experiment.py --run-id abc-123

# 2. Checkout exact code and data
git checkout 91b64a1504835d4...
dvc checkout

# 3. Re-run training
python3 train.py

# 4. Generate inference with exact same model
python3 -c "from pipelines.batch_inference import run_inference_pipeline; ..."

# 5. Results should match!
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mlflow'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: MLflow not starting

**Solution:**
```bash
# Kill existing processes
pkill -f "mlflow server"

# Start fresh
mlflow ui
```

### Issue: "code_version: unknown"

**Meaning:** The project is not a git repository.

**Solution:**
```bash
git init
git add .
git commit -m "Initial commit"
python3 train.py
```

### Issue: Data hash changed but data looks the same

**Meaning:** Minor differences (float precision, row order, index) change the hash.

**Debug:**
```python
import pandas as pd
from data_versioning import compute_dataframe_hash

df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')

print(f"Hash 1: {compute_dataframe_hash(df1)}")
print(f"Hash 2: {compute_dataframe_hash(df2)}")
print(f"DataFrames equal: {df1.equals(df2)}")
```

### Issue: Can't reproduce experiment

**Common reasons:**
1. Not in git repository → `git init && git add . && git commit -m "Initial"`
2. Different dependencies → `pip install -r requirements.txt`
3. Data files missing → Ensure data source is available or use dummy generator
4. Different Python version → Use Python 3.11+

### Issue: MLflow runs not showing

**Solution:**
```bash
# Check that tracking URI is correct
# Default: ./mlruns

# If runs exist, restart MLflow
pkill -f "mlflow server"
mlflow ui

# Verify runs exist
ls -la mlruns/
```

## Next Steps

- Read [DATA_VERSIONING.md](DATA_VERSIONING.md) for advanced reproducibility
- Read [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) for how it works
- Check [API_REFERENCE.md](API_REFERENCE.md) for all available functions
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production setup

## Quick Reference

```bash
# Training
python3 train.py

# View results
mlflow ui

# Reproduce experiment
python3 reproduce_experiment.py --run-id <run-id>

# Run inference
python3 -c "from pipelines.batch_inference import run_inference_pipeline; ..."

# Run tests
pytest tests/ -v

# Check code quality
black . --check
ruff check .
mypy .
```

## Support

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues
- Check [DATA_VERSIONING.md](DATA_VERSIONING.md) for reproducibility questions
- See README.md for project overview
