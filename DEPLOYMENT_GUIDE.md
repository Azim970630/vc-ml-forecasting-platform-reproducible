# Deployment Guide

Deploy the ML Forecasting Platform to production environments.

## Local Deployment

### Running the Platform Locally

Already done in your setup. The platform runs entirely locally:

```bash
source venv/bin/activate
python3 test_mvp.py       # Training
mlflow ui                 # Experiment tracking
python3 batch_inference.py # Predictions
```

**Requirements**:
- Python 3.11+
- 500MB disk space
- <1GB RAM for 100 series × 365 days

---

## Production Readiness Checklist

Before deploying to production, ensure:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Model accuracy acceptable: Check MAE/RMSE in MLflow
- [ ] Data validation in place: CSV schema checks
- [ ] Error handling robust: Fallback logic for model failures
- [ ] Monitoring setup: MLflow tracking enabled
- [ ] Documentation complete: README, guides, API reference
- [ ] Reproducibility verified: Same seed produces same results
- [ ] Performance tested: Training time acceptable
- [ ] Security reviewed: No hardcoded secrets
- [ ] Logging configured: For debugging production issues

---

## Docker Deployment

### Create Docker Image

**Step 1: Create Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port for MLflow UI
EXPOSE 5000

# Default command: training
CMD ["python3", "test_mvp.py"]
```

**Step 2: Build Image**

```bash
docker build -t ml-forecasting:latest .
```

**Step 3: Run Container**

```bash
# Training
docker run -v $(pwd)/mlruns:/app/mlruns ml-forecasting:latest

# MLflow UI
docker run -p 5000:5000 -v $(pwd)/mlruns:/app/mlruns ml-forecasting:latest mlflow ui

# Batch inference
docker run -v $(pwd):/app ml-forecasting:latest python3 -c "from pipelines.batch_inference import run_batch_inference; run_batch_inference()"
```

---

## Cloud Deployment

### AWS EC2 Deployment

**Step 1: Launch EC2 Instance**

```bash
# Instance type: t3.medium (2 vCPU, 4GB RAM)
# AMI: Ubuntu 22.04 LTS
# Storage: 20GB EBS
```

**Step 2: SSH and Setup**

```bash
ssh -i key.pem ubuntu@<instance-ip>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Clone repository
git clone <your-repo> ml-platform
cd ml-platform

# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 3: Run as Systemd Service**

Create `/etc/systemd/system/ml-training.service`:

```ini
[Unit]
Description=ML Forecasting Training Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ml-platform
Environment="PATH=/home/ubuntu/ml-platform/venv/bin"
ExecStart=/home/ubuntu/ml-platform/venv/bin/python3 test_mvp.py
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl start ml-training
sudo systemctl enable ml-training
sudo systemctl status ml-training
```

### Google Cloud Run Deployment

For FastAPI serving (future feature):

```bash
# Build and push to Cloud Build
gcloud builds submit --tag gcr.io/my-project/ml-forecasting

# Deploy to Cloud Run
gcloud run deploy ml-forecasting \
  --image gcr.io/my-project/ml-forecasting:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 3600
```

---

## Model Serving in Production

### Option 1: Batch Predictions

**Schedule daily retraining + inference**:

```bash
#!/bin/bash
# daily_forecast.sh

cd /app/ml-platform
source venv/bin/activate

# 1. Retrain model
python3 test_mvp.py

# 2. Generate predictions
python3 << 'PYTHON'
from pipelines.batch_inference import run_batch_inference
predictions = run_batch_inference()
predictions.to_csv("outputs/predictions_$(date +%Y%m%d).csv")
PYTHON

# 3. Upload to database or storage
aws s3 cp outputs/ s3://my-bucket/forecasts/

# 4. Send notifications
# ... (email, Slack, etc.)
```

Schedule with cron:

```bash
# Run daily at 2 AM
0 2 * * * /app/ml-platform/daily_forecast.sh
```

### Option 2: Real-Time API (Future)

```python
# serving/api/main.py
from fastapi import FastAPI
from models import LightGBMForecaster
import pandas as pd

app = FastAPI()

# Load model at startup
model = LightGBMForecaster.load("models/lightgbm_model.pkl")

@app.post("/predict")
def predict(series_id: str, horizon: int):
    """Make real-time forecast"""
    # Load recent data
    # Engineer features
    # Make prediction
    # Return JSON
    return {
        "series_id": series_id,
        "forecast": predictions.tolist()
    }

@app.get("/health")
def health():
    """Health check"""
    return {"status": "healthy"}
```

Deploy:

```bash
docker build -f serving/Dockerfile -t ml-api .
docker run -p 8000:8000 ml-api
```

---

## MLflow Model Registry

### Register Production Model

```python
from mlflow import log_model
import mlflow

mlflow.set_experiment("production")
with mlflow.start_run():
    # ... training code ...
    
    # Register model
    mlflow.register_model(
        model_uri="runs:/<run_id>/lightgbm_model",
        name="time-series-forecaster"
    )
```

### Promote to Production

In MLflow UI:
1. Models → time-series-forecaster
2. Latest → Stage dropdown → Production

Or via API:

```python
from mlflow.client import MlflowClient

client = MlflowClient()
client.transition_model_version_stage(
    name="time-series-forecaster",
    version=2,
    stage="Production"
)
```

---

## Monitoring & Logging

### Setup Structured Logging

```python
import logging
import json

logger = logging.getLogger(__name__)
handler = logging.FileHandler("logs/training.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log training events
logger.info(f"Starting training with config: {config}")
logger.error(f"Training failed: {error}")
```

### Monitor MLflow Metrics

Track over time:

```python
import mlflow

# Each training run logs metrics
# Use MLflow UI to:
# - View metric trends
# - Compare runs
# - Export data for analysis

# Query programmatically
from mlflow.tracking import MlflowClient

client = MlflowClient()
runs = client.search_runs(experiment_ids=[0])
for run in runs:
    mae = run.data.metrics.get('mae')
    print(f"{run.info.run_name}: MAE={mae}")
```

### Setup Alerts

```python
# Alert if MAE degrades >10%
baseline_mae = 6.83  # From reference model

if latest_mae > baseline_mae * 1.1:
    # Send alert
    send_slack_notification(f"⚠️ Model degradation: MAE={latest_mae}")
```

---

## Database Backend

Replace filesystem storage with database for production:

### Setup PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
createdb mlflow_db

# Update MLflow config
mlflow_server \
  --backend-store-uri postgresql://user:password@localhost/mlflow_db \
  --default-artifact-root s3://my-bucket/artifacts
```

---

## Backup & Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup_mlflow.sh

DATE=$(date +%Y%m%d)

# Backup MLflow runs
tar -czf backup/mlruns_${DATE}.tar.gz mlruns/

# Backup models
cp -r models/ backup/models_${DATE}/

# Upload to S3
aws s3 cp backup/ s3://my-backups/
```

### Restore Model

```bash
# Download backup
aws s3 cp s3://my-backups/mlruns_20240101.tar.gz .

# Restore
tar -xzf mlruns_20240101.tar.gz

# Load model
from models import LightGBMForecaster
model = LightGBMForecaster.load("models/lightgbm_model.pkl")
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def load_model(model_path):
    """Cache loaded models in memory"""
    from models import LightGBMForecaster
    return LightGBMForecaster.load(model_path)
```

### Batch Processing

```python
# Process data in chunks to reduce memory
batch_size = 10000
for i in range(0, len(data), batch_size):
    batch = data.iloc[i:i+batch_size]
    predictions = model.predict(horizon=7, features=batch)
    predictions.to_csv(f"output_{i}.csv")
```

### Parallel Training

For multiple models:

```python
from multiprocessing import Pool

def train_model(config):
    return run_training_pipeline(config)

configs = [config1, config2, config3]
with Pool(3) as p:
    results = p.map(train_model, configs)
```

---

## Security Considerations

### Secrets Management

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env

# Access secrets
db_password = os.getenv("DB_PASSWORD")
s3_key = os.getenv("AWS_ACCESS_KEY_ID")

# Never hardcode!
```

Create `.env` (git-ignored):

```
DB_PASSWORD=secret123
AWS_ACCESS_KEY_ID=AKIA...
```

### Input Validation

```python
import pandas as pd
from pandera import Column, DataFrameSchema

# Define schema
schema = DataFrameSchema({
    "timestamp": Column(datetime),
    "series_id": Column(str, checks=lambda x: len(x) > 0),
    "target": Column(float, checks=lambda x: x > 0)
})

# Validate incoming data
df = schema.validate(incoming_data)
```

---

## Troubleshooting Production Issues

### Model Failing to Load

```bash
# Check model file exists and is valid
ls -lh models/lightgbm_model.pkl

# Try loading manually
python3 << 'PYTHON'
from models import LightGBMForecaster
try:
    model = LightGBMForecaster.load("models/lightgbm_model.pkl")
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error: {e}")
PYTHON
```

### Memory Issues

Monitor:

```bash
# Check memory usage
free -h

# Monitor during training
watch -n 1 free -h
```

Reduce memory:

```yaml
lightgbm:
  num_leaves: 31      # ← Reduce from 63
  max_depth: 10       # ← Add depth limit
  bagging_fraction: 0.5  # ← Downsample rows
```

---

## Rollback Procedure

If new model causes issues:

```bash
# Revert to previous model version
cp backup/models_20240101/lightgbm_model.pkl models/lightgbm_model.pkl

# Restart services
sudo systemctl restart ml-training

# Alert team
echo "⚠️ Rolled back to previous model" | mail -s "Rollback Alert" team@company.com
```

---

## Cost Optimization (AWS)

- **Compute**: Use t3.small for inference, t3.medium for training
- **Storage**: Archive old mlruns to Glacier
- **Data Transfer**: Use VPC endpoint for S3 to avoid egress charges
- **Reserved Instances**: For 24/7 serving

---

## Next Steps

1. **Add CI/CD**: GitHub Actions to test and deploy on push
2. **Add FastAPI**: Real-time serving endpoint
3. **Add Airflow**: Schedule retraining pipelines
4. **Add DVC**: Version datasets
5. **Add Monitoring**: Drift detection with Evidently

