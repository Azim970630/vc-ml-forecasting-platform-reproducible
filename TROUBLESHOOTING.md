# Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### "Python version 3.11 or higher required"

**Error**:
```
Python 3.10 is not compatible. Requires Python 3.11+
```

**Solution**:
```bash
# Check Python version
python3 --version

# Install Python 3.11+
# On macOS:
brew install python@3.11

# On Ubuntu:
sudo apt-get install python3.11

# Use specific version
python3.11 -m venv venv
```

---

### "pip: command not found"

**Error**:
```
-bash: pip: command not found
```

**Solution**:
```bash
# Use python3 -m pip instead
python3 -m pip install -r requirements.txt

# Or check PATH
which python3
which pip3
```

---

### "Module not found" after pip install

**Error**:
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution**:
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
python3 -c "import pandas; print(pandas.__version__)"
```

---

## Data Issues

### "No such file: data/raw/sales.csv"

**Error**:
```
FileNotFoundError: Data file not found: data/raw/sales.csv
```

**Solution**:
```bash
# Create directory
mkdir -p data/raw

# Create sample CSV
python3 << 'PYTHON'
import pandas as pd
import numpy as np

dates = pd.date_range("2023-01-01", periods=100, freq="D")
data = []
for store in ["A", "B"]:
    for date in dates:
        data.append({
            "date": date,
            "store": store,
            "sales": 100 + np.random.normal(0, 5)
        })
df = pd.DataFrame(data)
df.to_csv("data/raw/sales.csv", index=False)
print("✅ CSV created")
PYTHON

# Update config/data.yaml
# Change source: dummy → source: offline
```

---

### "timestamp column is not datetime"

**Error**:
```
ValueError: timestamp column is not datetime
```

**Solution**:
Your CSV datetime column isn't being parsed. Fix in `config/data.yaml`:

```yaml
offline:
  file_path: data/raw/sales.csv
  datetime_column: date    # ← Check column name is correct
  target_column: sales
  series_id_column: store
```

Or pre-process CSV:
```bash
python3 << 'PYTHON'
import pandas as pd

df = pd.read_csv("data/raw/sales.csv")
df['date'] = pd.to_datetime(df['date'])  # Ensure datetime
df.to_csv("data/raw/sales.csv", index=False)
PYTHON
```

---

### "timestamps not monotonic"

**Error**:
```
ValueError: timestamps not monotonic for series_A
```

**Solution**:
Your data isn't sorted by date. Fix before saving CSV:

```python
df = df.sort_values(['series_id', 'date'])
df.to_csv("data/raw/sales.csv", index=False)
```

---

## Model Training Issues

### "No valid training data after removing NaNs"

**Error**:
```
ValueError: No valid training data after removing NaNs
```

**Solution**:
Too many NaN values in features. Check:

1. Lag features create NaNs at the beginning:
   ```python
   # First 28 rows have NaN for lag_28
   # This is expected, but affects training size
   ```

2. Reduce training data loss:
   ```yaml
   # config/features.yaml
   feature_pipeline:
     - name: LagFeatureTransformer
       params:
         lags: [1, 7]  # ← Use fewer/smaller lags
   ```

3. Increase dataset size:
   ```yaml
   # config/data.yaml
   dummy:
     n_timesteps: 1000  # ← More data
   ```

---

### "LightGBMError: no meaningful features"

**Error**:
```
lightgbm.basic.LightGBMError: Forced splits file includes feature index 0, 
but maximum feature index in dataset is -1
```

**Solution**:
No valid features after NaN removal. Usually happens when:

1. All lags are NaN: Use smaller dataset
2. No calendar features configured: Add them
3. Too many NaNs: Reduce lag window

**Fix**:
```yaml
# config/features.yaml
feature_pipeline:
  - name: LagFeatureTransformer
    params:
      lags: [1, 7]  # ← Smaller lags
  - name: CalendarFeatureTransformer
    params: {}     # ← Add calendar features
```

---

## MLflow Issues

### "No such file or directory: './mlruns'"

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: './mlruns'
```

**Solution**:
MLflow directory doesn't exist yet—this is normal on first run.

```bash
# Just run training, it will create mlruns/
python3 test_mvp.py

# mlruns directory is created automatically
```

---

### MLflow UI shows no runs

**Error**:
- Started `mlflow ui` but see empty experiment list

**Solution**:

1. Make sure MLflow server is running:
   ```bash
   mlflow ui
   # Should see: On http://127.0.0.1:5000
   ```

2. Open browser to `http://localhost:5000` (not just UI address)

3. Check runs exist:
   ```bash
   find mlruns -name "metrics.json"
   # Should see files like: mlruns/0/.../metrics/mae
   ```

4. If no runs, run training:
   ```bash
   python3 test_mvp.py
   ```

5. Refresh browser (Ctrl+R or Cmd+R)

---

### "Port 5000 already in use"

**Error**:
```
Address already in use (:5000)
```

**Solution**:
```bash
# Use a different port
mlflow ui --port 5001

# Then open: http://localhost:5001
```

Or kill existing process:
```bash
# Find process on port 5000
lsof -i :5000

# Kill it
kill -9 <PID>
```

---

## Feature Engineering Issues

### "Transformer not found in registry"

**Error**:
```
ValueError: Transformer 'MyTransformer' not found in registry
```

**Solution**:
You created a custom transformer but didn't register it.

1. Check file exists: `features/custom/my_transformer.py`
2. Register in `features/registry.py`:
   ```python
   from features.custom.my_transformer import MyTransformer
   
   _registry = {
       # ...
       "MyTransformer": MyTransformer,  # ← Add this
   }
   ```
3. Then run training

---

### Custom transformer errors

**Error**:
```
AttributeError: 'DataFrame' object has no attribute 'custom_column'
```

**Solution**:
Your transformer is creating wrong column names.

```python
def transform(self, df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    # Must return df with extra columns
    result['my_feature'] = result['target'] * 2
    return result  # ← Return modified df

def get_feature_names(self) -> list:
    # Return created feature names
    return ['my_feature']
```

---

## Testing Issues

### "pytest: command not found"

**Error**:
```
-bash: pytest: command not found
```

**Solution**:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Then run tests
pytest tests/ -v
```

---

### Tests fail with "ModuleNotFoundError"

**Error**:
```
ModuleNotFoundError: No module named 'data_sources'
```

**Solution**:
Run from project root:
```bash
cd "/home/azim_ahmad/Documents/Claude Code Experiments/MLOps Beginner"
pytest tests/
```

---

### "No tests found"

**Error**:
```
collected 0 items
```

**Solution**:
```bash
# Check test files exist
ls -la tests/unit/
ls -la tests/integration/

# Ensure files are named test_*.py
# and have functions named test_*
```

---

## Configuration Issues

### "Config file not found"

**Error**:
```
FileNotFoundError: config/model.yaml not found
```

**Solution**:
```bash
# Check files exist
ls -la config/

# Create missing file
touch config/model.yaml

# Copy from template if you deleted it
# See README.md for YAML templates
```

---

### "Invalid YAML syntax"

**Error**:
```
yaml.scanner.ScannerError: mapping values not allowed here
```

**Solution**:
YAML is indentation-sensitive. Check:

```yaml
# ❌ Wrong
model:
type: lightgbm

# ✅ Correct
model:
  type: lightgbm
```

Use consistent 2-space indentation.

---

### "Config value is null"

**Error**:
```
TypeError: 'NoneType' object is not subscriptable
```

**Solution**:
Config key is missing. Check:

```python
# This fails if 'lightgbm' key missing
config['model']['lightgbm']['n_estimators']

# Solution: Add key to config/model.yaml
model:
  type: lightgbm
  lightgbm:
    n_estimators: 500  # ← Add this
```

---

## Performance Issues

### "Training is very slow"

**Solution**:

1. Reduce dataset:
   ```yaml
   dummy:
     n_timesteps: 100  # ← Smaller
   ```

2. Reduce features:
   ```yaml
   feature_pipeline:
     - name: LagFeatureTransformer
       params:
         lags: [1, 7]  # ← Fewer lags
   ```

3. Reduce LightGBM iterations:
   ```yaml
   lightgbm:
     n_estimators: 100  # ← Fewer trees
   ```

4. Use ARIMA (faster for small data):
   ```yaml
   model:
     type: arima
   ```

---

### "Out of memory"

**Error**:
```
MemoryError
```

**Solution**:

1. Reduce dataset size
2. Use fewer features
3. Process in batches instead of all at once
4. Use ARIMA instead of LightGBM

---

## Other Issues

### "KeyError: 'timestamp'"

**Error**:
```
KeyError: 'timestamp'
```

**Solution**:
DataFrame doesn't have `timestamp` column. Check:

1. Data source is returning correct columns:
   ```python
   source = DummyGenerator()
   df = source.load(config['data']['dummy'])
   print(df.columns)  # Should include 'timestamp'
   ```

2. Features were applied:
   ```python
   pipeline = FeatureRegistry.build_pipeline(config['feature_pipeline'])
   df = FeatureRegistry.apply_pipeline(df, pipeline)
   print(df.columns)  # Should still have 'timestamp'
   ```

---

### "Predictions are all zeros"

**Problem**:
ARIMA model failing.

**Solution**:
```python
# Check if model fit failed
# ARIMA can fail with certain data

# Try LightGBM instead
config['model']['type'] = 'lightgbm'

# Or try different ARIMA order
config['model']['arima']['order'] = [0, 1, 0]
```

---

## Getting Help

1. **Check logs**: Look at output messages
2. **Review docs**: Check README, USER_GUIDE, TECHNICAL_ARCHITECTURE
3. **Check tests**: Test files show working examples
4. **Inspect data**: Print intermediate DataFrames to see what's happening

Example debug script:

```python
from config_loader import load_config
from data_sources import DummyGenerator
from features import FeatureRegistry

config = load_config()

# Check data
source = DummyGenerator()
df = source.load(config['data']['dummy'])
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Nulls: {df.isnull().sum()}")

# Check features
pipeline = FeatureRegistry.build_pipeline(config['feature_pipeline'])
df = FeatureRegistry.apply_pipeline(df, pipeline)
print(f"After features: {df.shape}")
print(f"New columns: {[c for c in df.columns if c not in ['timestamp', 'series_id', 'target']]}")
```

