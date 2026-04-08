# Contributing Guide

How to extend and contribute to the ML Forecasting Platform.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Adding Custom Features](#adding-custom-features)
3. [Adding Custom Models](#adding-custom-models)
4. [Adding Data Sources](#adding-data-sources)
5. [Code Style & Standards](#code-style--standards)
6. [Testing Your Changes](#testing-your-changes)
7. [Pull Request Process](#pull-request-process)

---

## Getting Started

### Setup Development Environment

```bash
# Clone repository (or already have it)
cd "/home/azim_ahmad/Documents/Claude Code Experiments/MLOps Beginner"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

### Project Structure Review

```
features/              # Feature transformers
├── base.py           # BaseFeatureTransformer
├── registry.py       # FeatureRegistry
└── custom/           # ← Your custom transformers go here
    └── .gitkeep

models/                # Model implementations
├── base.py           # BaseForecaster
├── registry.py       # ModelRegistry
└── custom/           # ← Your custom models go here (add this)

data_sources/          # Data loaders
├── base.py           # BaseDataSource
└── custom/           # ← Your custom sources go here (add this)

tests/                 # Tests
├── unit/             # Unit tests
└── integration/      # Integration tests
```

---

## Adding Custom Features

### Example: Add a Differencing Transformer

**Purpose**: Create lag differences (e.g., today - yesterday)

**Step 1: Create the Transformer**

Create `features/custom/diff_features.py`:

```python
import pandas as pd
from features.base import BaseFeatureTransformer


class DifferencingTransformer(BaseFeatureTransformer):
    """Create differenced (lagged) features.
    
    Example:
        Input: [100, 102, 104, 103]
        Output with diff=1: [NaN, 2, 2, -1]
    """
    
    def __init__(self, periods: list[int] = None):
        """Initialize transformer.
        
        Args:
            periods: List of difference periods. Default: [1, 7]
        """
        self.periods = periods or [1, 7]
        self.feature_names_ = []
    
    def fit(self, df: pd.DataFrame) -> "DifferencingTransformer":
        """Learn parameters (none needed, just store names)."""
        self.feature_names_ = [f"target_diff_{p}" for p in self.periods]
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create differencing features."""
        result = df.copy()
        
        for period in self.periods:
            col_name = f"target_diff_{period}"
            # Difference within each series
            result[col_name] = result.groupby("series_id")["target"].diff(period)
        
        return result
    
    def get_feature_names(self) -> list:
        """Return feature names created."""
        return self.feature_names_
```

**Step 2: Register the Transformer**

Edit `features/registry.py`:

```python
from features.custom.diff_features import DifferencingTransformer

class FeatureRegistry:
    _registry = {
        "LagFeatureTransformer": LagFeatureTransformer,
        "RollingStatTransformer": RollingStatTransformer,
        "CalendarFeatureTransformer": CalendarFeatureTransformer,
        "DifferencingTransformer": DifferencingTransformer,  # ← Add this
    }
```

**Step 3: Use in Configuration**

Edit `config/features.yaml`:

```yaml
feature_pipeline:
  - name: DifferencingTransformer
    params:
      periods: [1, 7, 30]
  
  - name: LagFeatureTransformer
    params:
      lags: [1, 7, 28]
```

**Step 4: Test It**

```bash
python3 << 'PYTHON'
from features import FeatureRegistry
from data_sources import DummyGenerator
import pandas as pd

# Generate test data
gen = DummyGenerator()
df = gen.load({'n_series': 2, 'n_timesteps': 50, 'random_seed': 42})

# Apply transformer
transformer = FeatureRegistry.get("DifferencingTransformer")(periods=[1, 7])
result = transformer.fit_transform(df)

# Check output
print(f"Input columns: {df.columns.tolist()}")
print(f"Output columns: {result.columns.tolist()}")
print(f"\nFirst 10 rows:\n{result.head(10)}")
PYTHON
```

**Step 5: Write Unit Tests**

Create `tests/unit/test_custom_features.py`:

```python
import pytest
from features.custom.diff_features import DifferencingTransformer
import pandas as pd
import numpy as np


def test_differencing_transformer_fit():
    """Test fitting the transformer."""
    transformer = DifferencingTransformer(periods=[1, 7])
    
    # Create test data
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=10),
        "series_id": ["A"] * 10,
        "target": range(100, 110)
    })
    
    transformer.fit(df)
    
    assert transformer.feature_names_ == ["target_diff_1", "target_diff_7"]


def test_differencing_transformer_transform():
    """Test transformation output."""
    transformer = DifferencingTransformer(periods=[1])
    
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=5),
        "series_id": ["A"] * 5,
        "target": [100, 102, 104, 103, 105]
    })
    
    result = transformer.fit_transform(df)
    
    assert "target_diff_1" in result.columns
    # First value is NaN (no previous)
    assert pd.isna(result.iloc[0]["target_diff_1"])
    # 102 - 100 = 2
    assert result.iloc[1]["target_diff_1"] == 2


if __name__ == "__main__":
    test_differencing_transformer_fit()
    test_differencing_transformer_transform()
    print("✅ All tests passed")
```

Run tests:

```bash
pytest tests/unit/test_custom_features.py -v
```

---

## Adding Custom Models

### Example: Add Linear Regression Model

**Step 1: Create the Model**

Create `models/custom/linear_model.py`:

```python
import pickle
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from models.base import BaseForecaster


class LinearRegressionForecaster(BaseForecaster):
    """Simple linear regression forecaster."""
    
    def __init__(self):
        self.model = None
        self.feature_names_ = None
    
    def fit(self, train: pd.DataFrame, config: dict) -> None:
        """Fit linear regression model."""
        # Extract features and target
        feature_cols = [col for col in train.columns 
                       if col not in ["target", "timestamp", "series_id"]]
        X = train[feature_cols].fillna(0)
        y = train["target"]
        
        # Remove rows with NaN target
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]
        
        # Train model
        self.model = LinearRegression()
        self.model.fit(X, y)
        self.feature_names_ = feature_cols
    
    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame:
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model not fitted")
        
        if features is None:
            raise ValueError("Features required")
        
        X = features[self.feature_names_].fillna(0)
        predictions = self.model.predict(X)
        
        return pd.DataFrame({
            "timestamp": features["timestamp"],
            "series_id": features["series_id"],
            "prediction": predictions
        })
    
    def save(self, path: str) -> None:
        """Save model."""
        with open(path, "wb") as f:
            pickle.dump(self, f)
    
    @classmethod
    def load(cls, path: str) -> "LinearRegressionForecaster":
        """Load model."""
        with open(path, "rb") as f:
            return pickle.load(f)
```

**Step 2: Register the Model**

Edit `models/registry.py`:

```python
from models.custom.linear_model import LinearRegressionForecaster

class ModelRegistry:
    _registry = {
        "lightgbm": LightGBMForecaster,
        "arima": ARIMAForecaster,
        "linear": LinearRegressionForecaster,  # ← Add this
    }
```

**Step 3: Use in Configuration**

Edit `config/model.yaml`:

```yaml
model:
  type: linear
```

**Step 4: Test It**

```bash
python3 << 'PYTHON'
from config_loader import load_config
from pipelines.training import run_training_pipeline

config = load_config()
config['model']['type'] = 'linear'

result = run_training_pipeline(config)
print(f"MAE: {result['metrics']['mae']:.2f}")
PYTHON
```

---

## Adding Data Sources

### Example: Add API Data Source

**Step 1: Create the Data Source**

Create `data_sources/custom/api_source.py`:

```python
import pandas as pd
import requests
from data_sources.base import BaseDataSource


class APIDataSource(BaseDataSource):
    """Load time series from REST API."""
    
    def load(self, config: dict) -> pd.DataFrame:
        """Fetch data from API.
        
        Args:
            config: Must contain 'url' and 'api_key'
        
        Returns:
            DataFrame with [timestamp, series_id, target]
        """
        url = config.get('url')
        api_key = config.get('api_key')
        
        if not url or not api_key:
            raise ValueError("url and api_key required in config")
        
        # Fetch data from API
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        df = pd.DataFrame(data)
        
        # Rename columns to standard format
        df = df.rename(columns={
            'timestamp_col': 'timestamp',
            'series_col': 'series_id',
            'value_col': 'target'
        })
        
        # Convert to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        self.validate(df)
        return df
    
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate API data."""
        required_cols = {'timestamp', 'series_id', 'target'}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing columns: {required_cols - set(df.columns)}")
        
        if df.isnull().any().any():
            raise ValueError("Data contains null values")
        
        return True
```

**Step 2: Register the Data Source**

Edit `data_sources/__init__.py`:

```python
from data_sources.custom.api_source import APIDataSource

__all__ = ["BaseDataSource", "DummyGenerator", "OfflineCSVSource", "APIDataSource"]
```

**Step 3: Use in Configuration**

Edit `config/data.yaml`:

```yaml
data:
  source: api
  api:
    url: "https://api.example.com/timeseries"
    api_key: "${API_KEY}"  # Use environment variable
```

---

## Code Style & Standards

### Python Style

Follow PEP 8:

```python
# ✅ Good
def calculate_mean(values: list[float]) -> float:
    """Calculate arithmetic mean of values."""
    return sum(values) / len(values)


# ❌ Bad
def calc_mean(vals):
    return sum(vals)/len(vals)
```

### Naming Conventions

- **Classes**: PascalCase (MyTransformer)
- **Functions/Methods**: snake_case (my_function)
- **Constants**: UPPER_SNAKE_CASE (MAX_ITERATIONS)
- **Private**: _leading_underscore (_private_var)

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: int, param2: str) -> bool:
    """One-line summary.
    
    Longer description if needed.
    
    Args:
        param1: First parameter
        param2: Second parameter
    
    Returns:
        True if successful, False otherwise
    
    Raises:
        ValueError: If param2 is empty
    """
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List

def process_data(
    df: pd.DataFrame,
    threshold: float = 0.5,
    debug: bool = False
) -> Optional[pd.DataFrame]:
    """Process DataFrame."""
```

---

## Testing Your Changes

### Unit Tests

Test individual components:

```python
def test_my_transformer():
    transformer = MyTransformer()
    df = create_test_data()
    result = transformer.fit_transform(df)
    assert len(result) > 0
```

### Integration Tests

Test full workflows:

```python
def test_training_with_custom_feature():
    config = load_config()
    config['feature_pipeline'].append({
        'name': 'MyTransformer',
        'params': {}
    })
    
    result = run_training_pipeline(config)
    assert 'mae' in result['metrics']
```

### Run All Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

---

## Code Review Checklist

Before submitting changes:

- [ ] Code follows style guidelines
- [ ] All functions have docstrings
- [ ] Type hints used everywhere
- [ ] Unit tests written
- [ ] All tests pass
- [ ] No print statements (use logging)
- [ ] No hardcoded values
- [ ] Error handling included
- [ ] Documentation updated

---

## Pull Request Process

### Step 1: Create Branch

```bash
git checkout -b feature/my-new-feature
```

### Step 2: Make Changes

- Follow code standards
- Write tests
- Document changes

### Step 3: Test Locally

```bash
pytest tests/ -v
```

### Step 4: Commit

```bash
git add .
git commit -m "Add my new feature

- Describe what changed
- Explain why
- Reference any issues
"
```

### Step 5: Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create pull request with:
- Clear title
- Description of changes
- Link to related issues
- Testing instructions

### Step 6: Review and Merge

Address feedback and merge when approved.

---

## Common Extension Points

### Add New Metric

Edit `utils.py`:

```python
def compute_metrics(y_true, y_pred) -> dict:
    return {
        # ... existing ...
        'new_metric': calculate_new_metric(y_true, y_pred)
    }
```

### Add New Configuration

Edit `config/base.yaml`:

```yaml
my_feature:
  param1: value1
  param2: value2
```

### Add New Pipeline

Create `pipelines/my_pipeline.py`:

```python
def run_my_pipeline(config: dict = None) -> dict:
    """My custom pipeline."""
    config = config or load_config()
    # ... implementation ...
    return results
```

---

## Questions?

- Check [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) for design patterns
- Review test files for examples
- Look at existing implementations for reference
- Check [API_REFERENCE.md](API_REFERENCE.md) for all available APIs

