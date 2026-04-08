# End-to-End Testing Guide

## 1️⃣ Test with Dummy Data + LightGBM (Default)

```bash
source venv/bin/activate
python3 test_mvp.py
```

Expected output:
```
Running training pipeline...
Loading data...
Loaded 100 rows
Engineering features...
Splitting data...
Train: 80, Test: 20
Training lightgbm model...
Evaluating model...
Metrics: {'mae': X.XX, 'rmse': X.XX, 'mape': X.XX, 'smape': X.XX}
Model saved to: models/lightgbm_model.pkl

✅ Training complete!
```

---

## 2️⃣ Test with Dummy Data + ARIMA

### Step 1: Switch Model Type
Edit `config/model.yaml`:
```yaml
model:
  type: arima  # ← Change from "lightgbm"
  horizon: 7
  frequency: D

  arima:
    order: [1, 1, 1]
    seasonal_order: [0, 0, 0, 0]
```

### Step 2: Run Training
```bash
source venv/bin/activate
python3 test_mvp.py
```

You'll see ARIMA fitting messages.

---

## 3️⃣ Test with Offline CSV Data

### Step 1: Create Sample CSV
```bash
python3 << 'PYTHON'
import pandas as pd
import numpy as np

# Generate sample data
dates = pd.date_range("2023-01-01", periods=100, freq="D")
data = []

for series_id in ["store_001", "store_002"]:
    for i, date in enumerate(dates):
        data.append({
            "date": date,
            "store": series_id,
            "sales": 100 + i + np.random.normal(0, 5),
        })

df = pd.DataFrame(data)
df.to_csv("data/raw/sales_data.csv", index=False)
print(f"✅ Created data/raw/sales_data.csv with {len(df)} rows")
print("\nFirst rows:")
print(df.head())
PYTHON
```

### Step 2: Configure Offline Source
Edit `config/data.yaml`:
```yaml
data:
  source: offline  # ← Change from "dummy"

  offline:
    file_path: data/raw/sales_data.csv
    datetime_column: date
    target_column: sales
    series_id_column: store
```

### Step 3: Run Training
```bash
python3 test_mvp.py
```

---

## 4️⃣ Switch Back to LightGBM

Edit `config/model.yaml`:
```yaml
model:
  type: lightgbm  # ← Change from "arima"
```

Then run: `python3 test_mvp.py`

---

## 5️⃣ Run Batch Inference

After training, make predictions on new data:

```bash
python3 << 'PYTHON'
from pipelines.batch_inference import run_batch_inference
from config_loader import load_config

config = load_config()
predictions = run_batch_inference(config)

print(f"\n✅ Predictions complete!")
print(f"Shape: {predictions.shape}")
print("\nFirst 10 predictions:")
print(predictions.head(10))
PYTHON
```

Output saved to: `outputs/predictions/batch_predictions.csv`

---

## 6️⃣ View Experiment Tracking in MLflow

```bash
mlflow ui
```

Then open: **http://localhost:5000**

You'll see:
- Experiment: `ts-forecasting`
- Multiple runs (one per training)
- Metrics: MAE, RMSE, MAPE, SMAPE
- Model artifacts
- Parameters logged

---

## 7️⃣ Test Different Configurations

### More Lags
Edit `config/features.yaml`:
```yaml
feature_pipeline:
  - name: LagFeatureTransformer
    params:
      lags: [1, 7, 14, 28, 365]  # ← Add 365-day lag
```

### More Rolling Windows
```yaml
  - name: RollingStatTransformer
    params:
      windows: [7, 14, 30, 90]  # ← Add 30 & 90 day windows
      stats: [mean, std, min, max]  # ← Add min/max
```

### Change LightGBM Hyperparameters
Edit `config/model.yaml`:
```yaml
  lightgbm:
    n_estimators: 1000  # ← Increase trees
    learning_rate: 0.01  # ← Lower learning rate
    num_leaves: 127  # ← More leaves
```

---

## 8️⃣ Test Matrix

Run these combinations to test the platform:

| Data | Model | Features | Result |
|------|-------|----------|--------|
| Dummy | LightGBM | Lags + Rolling + Calendar | ✅ |
| Dummy | ARIMA | Lags + Rolling + Calendar | ✅ |
| CSV | LightGBM | Lags + Rolling + Calendar | ✅ |
| CSV | ARIMA | Lags + Rolling + Calendar | ✅ |
| Dummy (small) | LightGBM | Just Lags | ✅ |
| CSV (large) | LightGBM | All Features | ✅ |

---

## 9️⃣ Run Full Test Suite

```bash
source venv/bin/activate
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=html
# Open: htmlcov/index.html
```

---

## 🔟 Troubleshooting

### "No such file: data/raw/sales_data.csv"
```bash
mkdir -p data/raw
# Then create the CSV as in Step 3.1
```

### Model not found error
Make sure you run training first:
```bash
python3 test_mvp.py  # Creates the model
```

### MLflow showing old runs
Clear and start fresh:
```bash
rm -rf mlruns mlflow.db
python3 test_mvp.py  # Creates new experiment
```

### Import errors
Reinstall dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Example: Full End-to-End Workflow

```bash
#!/bin/bash
source venv/bin/activate

echo "1. Train with Dummy Data + LightGBM"
python3 test_mvp.py

echo ""
echo "2. Make predictions"
python3 << 'PYTHON'
from pipelines.batch_inference import run_batch_inference
predictions = run_batch_inference()
print(f"Saved {len(predictions)} predictions")
PYTHON

echo ""
echo "3. Switch to ARIMA"
sed -i 's/type: lightgbm/type: arima/' config/model.yaml

echo ""
echo "4. Train with ARIMA"
python3 test_mvp.py

echo ""
echo "5. View results"
echo "Open MLflow: mlflow ui"
echo "Then visit: http://localhost:5000"
```

---

## 💡 Key Files to Modify

- `config/model.yaml` - Change model type & hyperparameters
- `config/features.yaml` - Add/remove feature transformers
- `config/data.yaml` - Switch data source
- `config/base.yaml` - Global settings

**No code changes needed!** Just edit YAML files.

