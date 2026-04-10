# Quick Reference: Reproducibility & Data Recovery

## TL;DR - Reproduce an Experiment

```bash
# 0. Set Azure connection (one-time setup)
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=adlsgdigdatalakedev;AccountKey=...;EndpointSuffix=core.windows.net"

# 1. Find the run in MLflow (note the run_id)
mlflow ui
# Find run: 541d0c7fdb9a43999a5d12be2c7f9d31

# 2. Get reproduction info
python3 reproduce_experiment.py --run-id 541d0c7fdb9a43999a5d12be2c7f9d31

# 3. Checkout code version
git checkout 91b64a1504835d4

# 4. Pull exact data from Azure (uses env var automatically)
dvc pull

# 5. Re-run training
python3 train.py

# 6. Compare metrics in MLflow
mlflow ui
# Results should match!
```

## How It Works

```
Git + DVC + MLflow = Perfect Reproducibility

┌─ Git              ┌─ DVC              ┌─ MLflow
│ - Code versions   │ - Data versions    │ - Metrics
│ - Commit hashes   │ - File hashes      │ - Run IDs
│ - History         │ - Azure Blob       │ - Artifacts
└─────────────────┬┴────────────────────┴──────────────
                  │
            When you pull data:
            dvc pull reads .dvc file
            .dvc file has hash: eb7667ee...
            DVC finds in Azure: files/md5/eb/7667eed5...
            Downloads & verifies hash matches
            ✓ You have exact data
```

## Commands Cheat Sheet

### Viewing & Tracking

```bash
# View DVC status
dvc status
# Shows what needs pulling/pushing

# List tracked files
git ls-files | grep '.dvc'
# Shows all .dvc pointer files

# Check Azure remote
dvc remote list -v
# Should show: azure    azure://mlops-data
```

### Pulling Data by Hash

```bash
# Pull all data
dvc pull

# Pull specific file
dvc pull data/raw/sales_data.csv.dvc

# Force re-download (corrupt file recovery)
dvc pull -f

# Pull with verbose output
dvc pull -v
# Shows: Fetching 'data/raw/sales_data.csv' from 'azure'...
```

### Pushing Data

```bash
# Push all data to Azure
dvc push

# Push specific file
dvc push data/raw/sales_data.csv.dvc

# Check what would be pushed (dry run)
dvc push --dry
```

### Checking Hashes

```bash
# Compute SHA-256 hash of file
python3 << 'EOF'
from data_versioning import compute_file_hash
hash = compute_file_hash("data/raw/sales_data.csv")
print(f"SHA-256: {hash}")
EOF

# Check DVC file hash (MD5)
cat data/raw/sales_data.csv.dvc
# Look for: md5: eb7667eed5abf29cf3e2a508261bfb35

# Get expected hash from MLflow
mlflow ui
# Run → Artifacts → data_lineage.json
# Look for: "raw_data": {"hash": "c54d29c9..."}
```

## Reproducibility Workflow

### Scenario 1: New Team Member Sets Up

```bash
# Clone repo
git clone <repo>
cd <repo>

# Install dependencies
pip install -r requirements.txt
pip install dvc-azure

# Set Azure connection (from team/manager)
export AZURE_STORAGE_CONNECTION_STRING="[connection string from manager]"

# Pull all data from Azure
dvc pull
# ✓ Now has exact same data as original experiments

# Train
python3 train.py
# Results will match historical runs!
```

### Scenario 2: Reproduce Historical Run

```bash
# Set Azure connection first (from team/manager)
export AZURE_STORAGE_CONNECTION_STRING="[connection string]"

# Get run ID from MLflow
RUN_ID="541d0c7fdb9a43999a5d12be2c7f9d31"

# Get details
python3 reproduce_experiment.py --run-id $RUN_ID
# Shows: Code version, Data hashes, Metrics

# Checkout exact code
git checkout 91b64a1504835d4

# Verify .dvc file exists (should be in git history)
cat data/raw/sales_data.csv.dvc
# ✓ Pointer exists, will use hash: eb7667ee...

# Pull exact data from Azure (uses env var)
dvc pull
# ✓ Downloads using hash eb7667ee...
# ✓ Verifies hash matches after download

# Verify data integrity
python3 << 'EOF'
from data_versioning import compute_file_hash
hash = compute_file_hash("data/raw/sales_data.csv")
expected = "c54d29c9..."  # From MLflow logs
assert hash.startswith(expected[:8]), "Hash mismatch!"
print("✓ Data integrity verified")
EOF

# Re-run training
python3 train.py
# ✓ Should produce identical metrics
```

### Scenario 3: Audit - Prove Reproducibility

```bash
# Auditor asks: "Prove that model trained on Day 1 is reproducible"

# 0. Set Azure connection (provided by ops)
export AZURE_STORAGE_CONNECTION_STRING="[connection string]"

# 1. Get original run from MLflow
mlflow ui
# Run ID: 541d0c7fdb9a43999a5d12be2c7f9d31
# Original metrics: MAE=18.564, RMSE=20.169
# Code version: 91b64a1504835d4...
# Data hash: c54d29c9...

# 2. Show chain of custody
cat .dvc/config
# Shows: azure remote configured (no secrets in config)

git log --oneline data/raw/sales_data.csv.dvc | head -5
# Shows: 91b64a1 Track sales data with DVC

# 3. Reproduce step-by-step
git checkout 91b64a1504835d4    # Exact code
dvc pull                        # Exact data (from Azure via env var)
python3 train.py                # Exact training

# 4. Compare results
mlflow ui
# New run: xyz-789
# Metrics: MAE=18.564, RMSE=20.169
# ✓ MATCHES EXACTLY

# 5. Report
echo "✓ Reproducibility verified:"
echo "  - Code version: 91b64a1504835d4 (matches MLflow)"
echo "  - Data hash: c54d29c9... (verified from Azure by DVC hash)"
echo "  - Metrics match: MAE 18.564 (original) == 18.564 (reproduced)"
echo "✓ Experiment is fully reproducible and auditable"
```

## Troubleshooting

### "dvc pull" fails with "No such container: mlops-data"

**Cause**: Azure container doesn't exist yet

**Fix**:
```bash
python3 << 'EOF'
from azure.storage.blob import BlobServiceClient
conn_str = "your-connection-string"
blob_service = BlobServiceClient.from_connection_string(conn_str)
blob_service.create_container(name="mlops-data")
print("✓ Container created")
EOF
dvc pull  # Retry
```

### "dvc pull" downloads but hash doesn't match

**Cause**: File corrupted during transfer or wrong version

**Fix**:
```bash
# Force re-download
dvc pull -f

# Verify after
python3 << 'EOF'
from data_versioning import compute_file_hash
hash = compute_file_hash("data/raw/sales_data.csv")
print(f"Hash: {hash}")
EOF
```

### ".dvc file missing but I have old data"

**Cause**: Accidentally deleted .dvc file

**Fix**:
```bash
# Recover from git
git checkout data/raw/sales_data.csv.dvc

# Or re-add data
dvc add data/raw/sales_data.csv
git add data/raw/sales_data.csv.dvc
git commit -m "Re-track with DVC"
```

### "Can't checkout old code version"

**Cause**: That commit doesn't exist in your repo

**Fix**:
```bash
# Fetch from origin
git fetch origin

# List all commits
git log --all --oneline | grep 91b64a1

# Checkout if it exists
git checkout 91b64a1504835d4
```

### "MLflow not showing old runs"

**Cause**: Different tracking URI or mlruns/ folder was deleted

**Fix**:
```bash
# Check current tracking URI
cat config/base.yaml | grep tracking_uri

# Verify mlruns exists
ls -la mlruns/

# Or set explicit URI
export MLFLOW_TRACKING_URI=file:./mlruns
mlflow ui
```

## Key Files

```
.dvc/config
  ↓ Contains
  ├─ remote = azure
  ├─ url = azure://mlops-data
  └─ connection_string = ...

data/raw/sales_data.csv.dvc
  ↓ Contains
  ├─ path: data/raw/sales_data.csv
  ├─ md5: eb7667eed5abf29cf3e2a508261bfb35  ← Used by DVC to find in Azure
  └─ size: 7800

.dvc_metadata/
  ├─ raw_data_train_c54d29c9.json  ← SHA-256 hash for audit trail
  ├─ featured_data_train_e971c052.json
  └─ etc.

mlruns/
  └─ [run_id]/
     ├─ params/
     │  └─ code_version: 91b64a1504835d4...
     │  └─ data_raw_data_hash: c54d29c9...
     └─ artifacts/
        └─ data_lineage.json  ← Complete history
```

## Azure Blob Storage Access

```bash
# Container: mlops-data
# Account: adlsgdigdatalakedev
# Storage structure:
#   files/
#   └─ md5/
#      └─ eb/
#         └─ 7667eed5abf29cf3e2a508261bfb35  ← Your data file

# View files in Azure (if needed)
export AZURE_STORAGE_CONNECTION_STRING="[your-connection-string]"

python3 << 'EOF'
from azure.storage.blob import BlobServiceClient
import os
conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
blob_service = BlobServiceClient.from_connection_string(conn_str)
container = blob_service.get_container_client("mlops-data")
for blob in container.list_blobs():
    print(f"  {blob.name} ({blob.size} bytes)")
EOF
```

## Setting Up Connection String (Team Setup)

**For local development** (keep in shell profile, not git):
```bash
# Add to ~/.bashrc or ~/.zshrc
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=adlsgdigdatalakedev;AccountKey=...;EndpointSuffix=core.windows.net"
source ~/.bashrc  # Or ~/.zshrc
```

**For CI/CD** (GitHub Actions, etc.):
```yaml
# Add to GitHub Secrets, don't hardcode in workflows
env:
  AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
```

**Verify it's set**:
```bash
echo $AZURE_STORAGE_CONNECTION_STRING
# Should show your connection string (not empty)

dvc status
# Should work without errors
```

---

**See Also**:
- [DATA_VERSIONING.md](DATA_VERSIONING.md) - Core concepts
- [PRODUCTION_REPRODUCIBILITY.md](PRODUCTION_REPRODUCIBILITY.md) - Production setup
- [README.md](README.md) - Project overview
