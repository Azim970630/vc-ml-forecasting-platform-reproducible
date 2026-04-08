# API Reference — ML Forecasting Platform

Complete reference for all classes, functions, and modules.

## Module: config_loader

### Function: load_config

```python
def load_config(config_dir: str = "config") -> dict
```

Load all YAML configuration files and merge into single dict.

**Parameters**:
- `config_dir` (str): Directory containing YAML files. Default: `"config"`

**Returns**:
- `dict`: Merged configuration

**Example**:
```python
from config_loader import load_config

config = load_config()
print(config['model']['type'])  # 'lightgbm'
```

---

## Module: data_sources

### Class: BaseDataSource

Abstract base class for data sources.

```python
class BaseDataSource(ABC):
    @abstractmethod
    def load(self, config: dict) -> pd.DataFrame: ...
    
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool: ...
```

**Methods**:

#### load(config)
Load raw data from source.

**Parameters**:
- `config` (dict): Source-specific configuration

**Returns**:
- `pd.DataFrame`: With columns `[timestamp, series_id, target]`

**Raises**:
- `ValueError`: If data format invalid
- `FileNotFoundError`: If file not found (OfflineCSVSource)

#### validate(df)
Validate data quality.

**Parameters**:
- `df` (pd.DataFrame): DataFrame to validate

**Returns**:
- `bool`: True if valid

**Raises**:
- `ValueError`: If validation fails

---

### Class: DummyGenerator

Generate synthetic time series data.

```python
class DummyGenerator(BaseDataSource):
    def load(self, config: dict) -> pd.DataFrame: ...
    def validate(self, df: pd.DataFrame) -> bool: ...
```

**Configuration** (`config['data']['dummy']`):
```yaml
n_series: 5          # int
n_timesteps: 365     # int
frequency: D         # str (pandas freq)
date_start: "2023-01-01"  # str
seasonality: 12      # int
trend: true          # bool
noise_level: 0.05    # float
random_seed: 42      # int
```

**Example**:
```python
from data_sources import DummyGenerator

gen = DummyGenerator()
df = gen.load({
    'n_series': 3,
    'n_timesteps': 100,
    'seasonality': 12,
    'trend': True,
    'random_seed': 42
})
```

---

### Class: OfflineCSVSource

Load time series from CSV file.

```python
class OfflineCSVSource(BaseDataSource):
    def load(self, config: dict) -> pd.DataFrame: ...
    def validate(self, df: pd.DataFrame) -> bool: ...
```

**Configuration** (`config['data']['offline']`):
```yaml
file_path: "data/raw/sales.csv"
datetime_column: "date"
target_column: "sales"
series_id_column: "store"
```

**CSV Format**:
```
date,store,sales
2023-01-01,A,150.5
2023-01-02,A,152.3
...
```

**Example**:
```python
from data_sources import OfflineCSVSource

csv = OfflineCSVSource()
df = csv.load({
    'file_path': 'data/raw/sales.csv',
    'datetime_column': 'date',
    'target_column': 'sales',
    'series_id_column': 'store'
})
```

---

## Module: features

### Class: BaseFeatureTransformer

Abstract base for feature transformers.

```python
class BaseFeatureTransformer(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "BaseFeatureTransformer": ...
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...
    
    @abstractmethod
    def get_feature_names(self) -> list[str]: ...
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame: ...
```

**Methods**:

#### fit(df)
Learn parameters from data.

#### transform(df)
Apply transformation.

#### get_feature_names()
Return created feature names.

#### fit_transform(df)
Fit and transform in one call.

---

### Class: LagFeatureTransformer

Create lagged features.

```python
class LagFeatureTransformer(BaseFeatureTransformer):
    def __init__(self, lags: list[int] = None): ...
```

**Parameters**:
- `lags` (list[int]): Lag values. Default: `[1, 7, 28]`

**Output Columns**: `target_lag_{lag}` for each lag

**Example**:
```python
from features import LagFeatureTransformer

transformer = LagFeatureTransformer(lags=[1, 7, 14])
df_features = transformer.fit_transform(df)
print(df_features.columns)
# [..., 'target_lag_1', 'target_lag_7', 'target_lag_14']
```

---

### Class: RollingStatTransformer

Create rolling window features.

```python
class RollingStatTransformer(BaseFeatureTransformer):
    def __init__(self, windows: list[int] = None, stats: list[str] = None): ...
```

**Parameters**:
- `windows` (list[int]): Window sizes. Default: `[7, 14]`
- `stats` (list[str]): Statistics to compute. Default: `['mean', 'std']`

**Supported Stats**: `['mean', 'std', 'min', 'max']`

**Output Columns**: `target_rolling_{stat}_{window}` for each combo

**Example**:
```python
from features import RollingStatTransformer

transformer = RollingStatTransformer(
    windows=[7, 14],
    stats=['mean', 'std']
)
df_features = transformer.fit_transform(df)
```

---

### Class: CalendarFeatureTransformer

Extract temporal features.

```python
class CalendarFeatureTransformer(BaseFeatureTransformer):
    def __init__(self, include_holidays: bool = False, country: str = "US"): ...
```

**Parameters**:
- `include_holidays` (bool): Include holiday indicator
- `country` (str): ISO country code

**Output Columns**:
- `day_of_week` (0-6)
- `month` (1-12)
- `quarter` (1-4)
- `day_of_year` (1-365)
- `is_holiday` (optional, 0 or 1)

**Example**:
```python
from features import CalendarFeatureTransformer

transformer = CalendarFeatureTransformer(
    include_holidays=True,
    country="US"
)
df_features = transformer.fit_transform(df)
```

---

### Class: FeatureRegistry

Manage feature transformers.

```python
class FeatureRegistry:
    @classmethod
    def get(cls, name: str) -> type: ...
    
    @classmethod
    def build_pipeline(cls, config_list: list[dict]) -> list: ...
    
    @classmethod
    def apply_pipeline(cls, df: pd.DataFrame, pipeline: list) -> pd.DataFrame: ...
```

**Methods**:

#### get(name)
Get transformer class by name.

**Parameters**:
- `name` (str): Transformer name

**Returns**:
- `type`: Transformer class

**Raises**:
- `ValueError`: If transformer not found

#### build_pipeline(config_list)
Instantiate transformers from config.

**Parameters**:
- `config_list` (list[dict]): List of `{'name': str, 'params': dict}`

**Returns**:
- `list`: Instantiated transformers

#### apply_pipeline(df, pipeline)
Apply transformers sequentially.

**Parameters**:
- `df` (pd.DataFrame): Input data
- `pipeline` (list): Transformer instances

**Returns**:
- `pd.DataFrame`: Transformed data

**Example**:
```python
from features import FeatureRegistry

config = [
    {'name': 'LagFeatureTransformer', 'params': {'lags': [1, 7]}},
    {'name': 'CalendarFeatureTransformer', 'params': {}},
]

pipeline = FeatureRegistry.build_pipeline(config)
df_features = FeatureRegistry.apply_pipeline(df, pipeline)
```

---

## Module: models

### Class: BaseForecaster

Abstract base for forecasting models.

```python
class BaseForecaster(ABC):
    @abstractmethod
    def fit(self, train: pd.DataFrame, config: dict) -> None: ...
    
    @abstractmethod
    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame: ...
    
    @abstractmethod
    def save(self, path: str) -> None: ...
    
    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "BaseForecaster": ...
```

---

### Class: LightGBMForecaster

LightGBM gradient boosting model.

```python
class LightGBMForecaster(BaseForecaster):
    def fit(self, train: pd.DataFrame, config: dict) -> None: ...
    def predict(self, horizon: int, features: pd.DataFrame) -> pd.DataFrame: ...
    def save(self, path: str) -> None: ...
    @classmethod
    def load(cls, path: str) -> "LightGBMForecaster": ...
```

**Example**:
```python
from models import LightGBMForecaster

model = LightGBMForecaster()
model.fit(train_df, config)
predictions = model.predict(horizon=7, features=test_features)
model.save("my_model.pkl")

# Later...
loaded_model = LightGBMForecaster.load("my_model.pkl")
```

---

### Class: ARIMAForecaster

ARIMA time series model.

```python
class ARIMAForecaster(BaseForecaster):
    def fit(self, train: pd.DataFrame, config: dict) -> None: ...
    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame: ...
    def save(self, path: str) -> None: ...
    @classmethod
    def load(cls, path: str) -> "ARIMAForecaster": ...
```

**Configuration** (`config['model']['arima']`):
```yaml
order: [1, 1, 1]              # (p, d, q)
seasonal_order: [0, 0, 0, 0]  # (P, D, Q, s)
```

**Example**:
```python
from models import ARIMAForecaster

model = ARIMAForecaster()
model.fit(train_df, config)
predictions = model.predict(horizon=14)  # No features needed
```

---

### Class: ModelRegistry

Manage model types.

```python
class ModelRegistry:
    @classmethod
    def get(cls, name: str) -> type: ...
    
    @classmethod
    def list_models(cls) -> list[str]: ...
```

**Example**:
```python
from models import ModelRegistry

ModelClass = ModelRegistry.get("lightgbm")
model = ModelClass()

all_models = ModelRegistry.list_models()
# ['lightgbm', 'arima']
```

---

## Module: pipelines

### pipelines.training

```python
def run_training_pipeline(config: dict = None) -> dict
```

End-to-end training pipeline.

**Parameters**:
- `config` (dict): Training configuration. Default: Load from YAML

**Returns**:
- `dict`: Results with keys:
  - `model_path` (str): Path to saved model
  - `metrics` (dict): MAE, RMSE, MAPE, SMAPE
  - `train_size` (int): Number of training samples
  - `test_size` (int): Number of test samples

**Example**:
```python
from pipelines.training import run_training_pipeline

result = run_training_pipeline()
print(f"MAE: {result['metrics']['mae']:.2f}")
print(f"Model: {result['model_path']}")
```

---

### pipelines.batch_inference

```python
def run_batch_inference(config: dict = None, model_path: str = None) -> pd.DataFrame
```

Batch inference on entire dataset.

**Parameters**:
- `config` (dict): Configuration. Default: Load from YAML
- `model_path` (str): Path to model. Default: Use configured model

**Returns**:
- `pd.DataFrame`: Predictions with columns:
  - `timestamp`
  - `series_id`
  - `prediction`

**Example**:
```python
from pipelines.batch_inference import run_batch_inference

predictions = run_batch_inference()
predictions.to_csv("forecast.csv", index=False)
```

---

## Module: utils

### Function: compute_metrics

```python
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict
```

Compute forecast evaluation metrics.

**Parameters**:
- `y_true` (np.ndarray): Actual values
- `y_pred` (np.ndarray): Predicted values

**Returns**:
- `dict`: Keys: `mae`, `rmse`, `mape`, `smape`

**Example**:
```python
from utils import compute_metrics

metrics = compute_metrics(
    np.array([100, 102, 105]),
    np.array([99, 103, 104])
)
print(f"MAE: {metrics['mae']:.2f}")
```

---

### Function: split_train_test

```python
def split_train_test(df: pd.DataFrame, test_size: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]
```

Split data into train and test sets.

**Parameters**:
- `df` (pd.DataFrame): Input data
- `test_size` (float): Fraction for test. Default: 0.2

**Returns**:
- `tuple`: (train_df, test_df)

**Example**:
```python
from utils import split_train_test

train, test = split_train_test(df, test_size=0.2)
print(f"Train: {len(train)}, Test: {len(test)}")
```

---

## Common Patterns

### Train and Save Model

```python
from config_loader import load_config
from data_sources import DummyGenerator
from features import FeatureRegistry
from models import LightGBMForecaster
from utils import split_train_test

config = load_config()

# Load and prepare data
source = DummyGenerator()
raw_data = source.load(config['data']['dummy'])

# Engineer features
pipeline = FeatureRegistry.build_pipeline(config['feature_pipeline'])
featured_data = FeatureRegistry.apply_pipeline(raw_data, pipeline)

# Split data
train, test = split_train_test(featured_data, test_size=0.2)

# Train and save
model = LightGBMForecaster()
model.fit(train, config['model'])
model.save("models/my_model.pkl")
```

### Load Model and Predict

```python
from models import LightGBMForecaster

model = LightGBMForecaster.load("models/my_model.pkl")
predictions = model.predict(horizon=7, features=test_features)
```

### Custom Training Loop with MLflow

```python
import mlflow
from config_loader import load_config
from pipelines.training import run_training_pipeline

config = load_config()

mlflow.set_experiment("my-experiment")
with mlflow.start_run():
    result = run_training_pipeline(config)
    mlflow.log_metrics(result['metrics'])
    mlflow.log_params({
        'model': config['model']['type'],
        'data': config['data']['source']
    })
```

