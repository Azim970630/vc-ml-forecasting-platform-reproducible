# Production Reproducibility with Data Versioning

A complete guide for production ML systems that need **exact data restoration** for diagnostics and auditing.

## Problem Statement

**Scenario**: Your model runs daily in production

```
Day 1: 2026-04-08
├─ Input: raw_data_2026-04-08.csv
├─ Model runs → Generates predictions.csv
└─ Logs to MLflow: run_id = abc-123

... months pass ...

Day 150: 2026-09-05
├─ Audit request: "Show me exactly what prediction was generated on Day 1"
├─ We have: run_id (abc-123) ✓
├─ We have: code version (git commit hash) ✓
├─ We have: data hash (SHA-256) ✓
└─ We DON'T have: actual data file ✗
```

**Solution**: Store data files with DVC in remote storage (S3, Azure, GCS, etc.)

## Architecture: Three-Layer Reproducibility

```
Layer 1: Data Hashing (Proof)
├─ Compute: SHA-256(raw_data.csv) → c54d29c9...
├─ Log: data_raw_data_hash = c54d29c9...
└─ Purpose: Prove which data was used (audit trail)

Layer 2: Code Versioning (Proof)
├─ Capture: git commit abc123...
├─ Log: code_version = abc123...
└─ Purpose: Prove which code was used

Layer 3: DVC Storage (Recovery)
├─ Track: dvc add raw_data.csv
├─ Store: S3/Azure/GCS/local
└─ Purpose: Retrieve exact data files for reproduction
```

## Setup for Production

### Step 1: Configure DVC with Remote Storage

Choose one:

**Option A: Local Storage (Development)**
```bash
dvc remote add myremote /mnt/data-storage
dvc remote default myremote
```

**Option B: AWS S3 (Production)**
```bash
dvc remote add s3remote s3://my-bucket/ml-data
dvc remote default s3remote
dvc remote modify s3remote --local access_key_id YOUR_KEY
dvc remote modify s3remote --local secret_access_key YOUR_SECRET
```

**Option C: Azure Blob (Production)**
```bash
dvc remote add azure remote://my-container
dvc remote default azure
```

**Option D: Google Cloud Storage (Production)**
```bash
dvc remote add gcs gs://my-bucket/ml-data
dvc remote default gcs
```

### Step 2: Track Data Files with DVC

For each data file you want to restore:

```bash
# Add to DVC
dvc add data/raw_data.csv

# Commit DVC metadata
git add data/raw_data.csv.dvc .gitignore
git commit -m "Track data with DVC"

# Push to remote
dvc push
```

This creates `data/raw_data.csv.dvc` which git tracks, but stores actual data in remote.

### Step 3: Update Training Pipeline

Ensure pipeline loads data that's DVC-tracked:

```python
# pipelines/training.py
def run_training_pipeline(config):
    # Load data (tracked with DVC)
    data = load_data(config)  # data/raw_data.csv was added with dvc add
    
    # Training continues...
    # Data versions are automatically captured
```

### Step 4: Verify Setup

```bash
# Check DVC status
dvc status

# Check what would be pushed
dvc push --dry

# Verify remote is accessible
dvc remote list
```

## Daily Production Run

```bash
# Day 1 - Production training run
python3 train.py

# This automatically:
# 1. Loads data/raw_data.csv (tracked with DVC)
# 2. Computes hash: c54d29c9...
# 3. Logs to MLflow:
#    - data_raw_data_hash: c54d29c9...
#    - code_version: abc123...
# 4. DVC file (data/raw_data.csv.dvc) ensures we can get it back

# Push data to remote (if not automatic)
dvc push
```

## Diagnostic Workflow: Reproduce Day 1

### Step 1: Get Run Information

```bash
mlflow ui
# Click on the run from Day 1
# Find run_id: abc-123

# Check the data versions used:
python3 reproduce_experiment.py --run-id abc-123
```

**Output**:
```
🔄 Reproducing experiment: abc-123

Code version: abc123def456ghi789jkl012mno345

Data versions:
  - raw_data: c54d29c9...

Model parameters:
  - model_type: lightgbm
  - n_train: 160
  - n_test: 40
```

### Step 2: Checkout Code and Data

```bash
# Checkout exact code version
git checkout abc123def456ghi789jkl012mno345

# Restore exact data from remote
python3 reproduce_experiment.py --run-id abc-123 --restore-data

# This runs: dvc pull
# Which restores data/raw_data.csv to match the hash c54d29c9...
```

### Step 3: Verify Data Matches

```bash
# Verify hash matches what was logged
python3 << 'PYEOF'
from data_versioning import compute_file_hash
hash = compute_file_hash("data/raw_data.csv")
print(f"Current data hash: {hash}")
print(f"Expected hash:     c54d29c9...")
print(f"Match: {hash.startswith('c54d29c9')}")
PYEOF
```

### Step 4: Re-run Training

```bash
# Generate new run with exact same code + data
python3 train.py

# Create new MLflow run (new run_id: xyz-789)
# But metrics should match abc-123!
```

### Step 5: Compare

```bash
mlflow ui

# Side-by-side comparison:
# Run abc-123 (original):
#   MAE: 18.564
#   Model: trained 2026-04-08
#
# Run xyz-789 (reproduction):
#   MAE: 18.564  ← Matches!
#   Model: trained 2026-09-05

# ✓ Reproducibility verified!
```

## Example: Daily Scheduled Training

**Cron job or orchestrator (Airflow, etc.)**:

```bash
#!/bin/bash
# daily_training.sh

# Set timestamp for data
DATE=$(date +%Y-%m-%d)
DATA_FILE="data/raw_data_${DATE}.csv"

# 1. Fetch today's data from upstream
curl https://api.example.com/data > "$DATA_FILE"

# 2. Add to DVC for reproducibility
dvc add "$DATA_FILE"

# 3. Train model
python3 train.py

# 4. Push data to remote for later recovery
dvc push

# 5. Log completion
echo "Training completed: $(date)" >> logs/training.log
```

**Next day, for diagnostics**:

```bash
# User asks: "What happened on Day 1?"

# 1. Get the run
mlflow ui  # Find run_id = abc-123

# 2. Restore exact conditions
python3 reproduce_experiment.py --run-id abc-123 --restore-data

# 3. Verify data integrity
python3 << 'PYEOF'
from data_versioning import compute_file_hash
# This restores data/raw_data_2026-04-08.csv
hash = compute_file_hash("data/raw_data_2026-04-08.csv")
# Compare with logged hash to ensure correctness
PYEOF

# 4. Re-run inference or retraining
python3 train.py
```

## Data Flow Diagram

```
Production Daily Run:
├─ Upstream data → data/raw_data_2026-04-08.csv
├─ dvc add data/raw_data_2026-04-08.csv
│  └─ Creates: data/raw_data_2026-04-08.csv.dvc
├─ git commit -m "Data for 2026-04-08"
├─ python3 train.py
│  ├─ Loads: data/raw_data_2026-04-08.csv
│  ├─ Computes hash: c54d29c9...
│  └─ Logs to MLflow:
│     ├─ run_id: abc-123
│     ├─ data_hash: c54d29c9...
│     └─ code_version: abc123...
├─ dvc push
│  └─ Sends to S3/Azure/GCS/local remote
└─ Done!

Later - Diagnostic Workflow:
├─ User: "Reproduce Day 1 prediction"
├─ Query MLflow: get run_id abc-123
├─ Extract: code_version, data_hash
├─ git checkout abc123...
├─ python3 reproduce_experiment.py --run-id abc-123 --restore-data
│  └─ dvc pull
│     └─ Restores data/raw_data_2026-04-08.csv from S3/etc
├─ Verify hash: compute_file_hash() == c54d29c9... ✓
├─ python3 train.py
│  └─ Generates same predictions as Day 1
└─ ✓ Diagnostics complete!
```

## Audit Trail

Every production run creates an **immutable audit trail**:

```json
{
  "run_id": "abc-123",
  "timestamp": "2026-04-08T09:00:00",
  "code_version": "abc123def456ghi789",
  "datasets": {
    "raw_data": {
      "hash": "c54d29c9...",
      "dvc_tracked": true,
      "dvc_file": "data/raw_data_2026-04-08.csv.dvc",
      "size_bytes": 1024000
    }
  },
  "metrics": {
    "mae": 18.564,
    "rmse": 20.169
  },
  "reproducible": true
}
```

This is stored in:
- **MLflow artifacts**: `data_lineage.json`
- **DVC metadata**: `data/raw_data_2026-04-08.csv.dvc`
- **Git history**: Commit hashes

## Key Advantages

✅ **Complete Audit Trail**: Know exactly what data/code produced each result  
✅ **Diagnostic Recovery**: Restore exact conditions to debug issues  
✅ **Compliance**: Prove reproducibility for audits  
✅ **Regulatory**: Show full lineage for ML governance  
✅ **Root Cause Analysis**: Identify when/why performance changed  

## When Data Restoration Fails

If you can't restore data:

```bash
# Check DVC status
dvc status

# Check remote accessibility
dvc remote list -v

# Try manual restore
dvc pull data/raw_data_2026-04-08.csv.dvc

# If remote is down, you have:
# 1. Data hash (proof of what data was used)
# 2. Code version (can recreate training)
# 3. Detailed metadata (for investigation)
# But: Cannot regenerate exact predictions
```

**Mitigation**: 
- Keep local cache of recent data
- Backup remote storage
- Archive critical training data

## Best Practices

1. **Always commit .dvc files to git**
   ```bash
   git add *.dvc
   git commit -m "Track data with DVC"
   ```

2. **Test reproducibility regularly**
   ```bash
   # Weekly: reproduce a random past run
   python3 reproduce_experiment.py --run-id $(random_run_id) --restore-data
   ```

3. **Monitor DVC remote space**
   ```bash
   dvc remote status --check-updates
   ```

4. **Version data with meaningful names**
   ```bash
   # Good
   data/raw_data_2026-04-08.csv
   
   # Bad
   data/data.csv
   data/data_v2.csv
   ```

5. **Document data sources**
   ```python
   version = tracker.track_external_data(
       "data/raw_data_2026-04-08.csv",
       name="raw_data",
       metadata={
           "source": "upstream_api",
           "date_collected": "2026-04-08",
           "endpoint": "https://api.example.com/daily-data"
       }
   )
   ```

---

**See Also**:
- [DATA_VERSIONING.md](DATA_VERSIONING.md) — Core concepts
- [README.md](README.md) — Project overview
- [DVC Documentation](https://dvc.org/doc) — Full DVC guide
