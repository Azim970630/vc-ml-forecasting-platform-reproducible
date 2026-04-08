# Technical Architecture — Data Versioning & Reproducibility

A deep dive into how the ML Forecasting Platform implements complete reproducibility through data versioning, code versioning, and experiment tracking.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Versioning System](#data-versioning-system)
3. [Reproducibility Pipeline](#reproducibility-pipeline)
4. [MLflow Integration](#mlflow-integration)
5. [DVC Integration](#dvc-integration)
6. [Design Patterns](#design-patterns)
7. [Data Flow](#data-flow)

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ML Forecasting Platform                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Data Sources    │  │  Feature Eng.    │  │    Models    │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │ • DummyGen       │  │ • Lag Features   │  │ • LightGBM   │ │
│  │ • OfflineCSV     │  │ • Rolling Stats  │  │ • ARIMA      │ │
│  │ • Custom         │  │ • Calendar       │  │ • Custom     │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│          ↓                     ↓                      ↓         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Training Pipeline with Versioning            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ 1. Load Data       → compute_dataframe_hash()            │  │
│  │ 2. Feature Eng.    → compute_dataframe_hash()            │  │
│  │ 3. Split Train/Test → compute_dataframe_hash()            │  │
│  │ 4. Train Model     → save artifacts                      │  │
│  │ 5. Log to MLflow   → log data versions + code version    │  │
│  │ 6. Save Lineage    → data_lineage.json artifact          │  │
│  └──────────────────────────────────────────────────────────┘  │
│          ↓                    ↓                      ↓         │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ .dvc_metadata│  │   MLflow Runs    │  │   Git Commits    │ │
│  │ (JSON files) │  │  (Experiment DB) │  │  (Code history)  │ │
│  └──────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Reproducibility Engine                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Given Run ID:                                            │  │
│  │ 1. Query MLflow for metadata                            │  │
│  │ 2. Extract code version + data versions                 │  │
│  │ 3. Checkout git commit                                  │  │
│  │ 4. Restore data versions (if available)                 │  │
│  │ 5. Re-run training → identical results                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Versioning System

### Core Concept: Content Hashing

**Definition**: A deterministic hash function that produces a unique fingerprint for data.

**Properties**:
- **Deterministic**: Same data → same hash (always)
- **Unique**: Different data → different hash (with extremely high probability)
- **Fast**: Computable in one pass through data

**Implementation** (`data_versioning.py`):

```python
def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """
    Compute SHA-256 hash of DataFrame
    
    Uses pandas.util.hash_pandas_object() which:
    - Hashes all values (deterministic)
    - Includes index
    - Detects row order changes
    - Detects float precision changes
    """
    hasher = hashlib.new("sha256")
    hasher.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return hasher.hexdigest()
```

### DataVersionTracker Class

**Purpose**: Track data versions at each pipeline stage

**Methods**:

```python
class DataVersionTracker:
    
    def track_training_data(data, name, split, metadata=None):
        """
        Hash a DataFrame and save metadata
        
        Returns:
        {
            "name": "raw_data",
            "hash": "c54d29c9...",
            "timestamp": "2026-04-08T15:15:51",
            "shape": [200, 3],
            "rows": 200,
            "columns": ["timestamp", "series_id", "target"],
            "metadata": {...}
        }
        
        Saves to: .dvc_metadata/raw_data_train_c54d29c9.json
        """
    
    def track_external_data(file_path, name, metadata=None):
        """
        Hash a file (for external data)
        
        Uses: hashlib.sha256() for file content
        """
    
    def log_data_lineage(run_id, datasets, code_version):
        """
        Log all data versions to MLflow run
        
        Logs parameters:
        - data_raw_data_hash
        - data_featured_data_hash
        - data_train_data_hash
        - data_test_data_hash
        - code_version
        
        Logs artifact:
        - data_lineage.json (complete history)
        """
```

### Metadata Storage

**Location**: `.dvc_metadata/` directory

**File naming**: `{dataset_name}_{split}_{hash[:8]}.json`

**Example file** (`raw_data_train_c54d29c9.json`):

```json
{
  "name": "raw_data",
  "split": "train",
  "hash": "c54d29c95a144d72d576e3c1e20848b210081b37b49fff98ab94585a1105ffa9",
  "timestamp": "2026-04-08T15:15:51.914053",
  "shape": [200, 3],
  "columns": ["timestamp", "series_id", "target"],
  "rows": 200,
  "metadata": {
    "source": "offline"
  }
}
```

### When Data Version Changes

Data version changes when:
- Row values change (input data changes)
- Row order changes (data is shuffled)
- Columns change (features are added/removed)
- Float precision changes (numerical instability)
- Index changes (during resampling)

**NOT affected by**:
- Dataframe memory location
- Variable names
- Column names (they are part of the hash)

## Reproducibility Pipeline

### ExperimentReproducer Class

**Purpose**: Enable reproducing past experiments with exact conditions

**Architecture**:

```python
class ExperimentReproducer:
    
    def get_experiment_metadata(run_id):
        """
        Query MLflow for all logged parameters
        
        Returns metadata dict with:
        {
            "run_id": "abc-123",
            "timestamp": 1234567890,
            "code_version": "91b64a1...",
            "data_versions": {
                "raw_data": "c54d29c9...",
                "featured_data": "e971c052...",
                "train_data": "e03560ee...",
                "test_data": "0ea5701f..."
            },
            "model_params": {
                "model_type": "lightgbm",
                "n_train": 160,
                "n_test": 40
            }
        }
        """
    
    def get_reproduction_instructions(run_id):
        """
        Generate markdown instructions for reproducing experiment
        
        Shows:
        1. Git checkout command
        2. Data versions used
        3. DVC restore command
        4. Training command
        """
```

### Reproduction Workflow

```
User provides Run ID
        ↓
Query MLflow for parameters
        ↓
Extract:
├─ code_version (git commit)
├─ data_versions (data hashes)
├─ model_params (configuration)
└─ artifacts (model files)
        ↓
Generate reproduction plan:
├─ git checkout {code_version}
├─ dvc checkout  (restore data)
└─ python train.py  (recreate experiment)
        ↓
Results should match original experiment
```

## MLflow Integration

### What Gets Logged

**Parameters** (captured as key-value pairs):

```
data_raw_data_hash: c54d29c95a144d72d576e3c1e20848b...
data_raw_data_timestamp: 2026-04-08T15:15:51
data_featured_data_hash: e971c05220389bbca5dccedfeb063bf2...
data_featured_data_timestamp: 2026-04-08T15:15:52
data_train_data_hash: e03560eeddafac374e10ae8490e42b92d...
data_train_data_timestamp: 2026-04-08T15:15:53
data_test_data_hash: 0ea5701f643538763b7a504911bc5f7bc...
data_test_data_timestamp: 2026-04-08T15:15:53
code_version: 91b64a1504835d4564107a144217de38cb979a9d
model_type: lightgbm
data_source: dummy
n_train: 160
n_test: 40
```

**Metrics** (model performance):

```
mae: 18.564
rmse: 20.169
mape: 9.641
smape: 10.214
```

**Artifacts** (files):

```
lightgbm_model.pkl       (trained model)
data_lineage.json        (complete lineage history)
```

**Tags** (labels):

```
reproducible: true
```

### MLflow Storage Structure

```
mlruns/
├── 0/                                    (experiment 0 = Default)
│   └── run_id/
│       ├── meta.yaml                     (run metadata)
│       ├── params/                       (parameters)
│       │   ├── code_version
│       │   ├── data_raw_data_hash
│       │   └── ...
│       ├── metrics/                      (metrics)
│       │   ├── mae
│       │   ├── rmse
│       │   └── ...
│       ├── artifacts/                    (saved files)
│       │   ├── lightgbm_model.pkl
│       │   └── data_lineage.json
│       └── tags/                         (labels)
│           └── reproducible
```

## DVC Integration

### DVC Pipeline (dvc.yaml)

```yaml
stages:
  prepare:
    cmd: python -c "..."
    deps:
      - data_sources
    outs:
      - data/raw_data.csv
  
  train:
    cmd: python train.py
    deps:
      - data/raw_data.csv
      - pipelines
      - models
      - features
    params:
      - config
    outs:
      - models
    metrics:
      - outputs/metrics.json:
          cache: false
```

### DVC Remote Storage

```bash
dvc remote add -d myremote ./data_store
```

This configures local remote storage for DVC-tracked files.

### When to Use DVC

**DVC is useful for**:
- Tracking large data files (> 100MB)
- Collaborating on data (team sharing)
- Pipeline orchestration
- Artifact deduplication

**Data versioning module is simpler**:
- Content hashing (no file storage)
- Works with in-memory DataFrames
- Integrates with MLflow parameters
- No external storage needed

## Design Patterns

### 1. Registry Pattern

**Used for**: Data sources, Features, Models

**Example**: FeatureRegistry

```python
class FeatureRegistry:
    @staticmethod
    def build_pipeline(config):
        """
        Build feature pipeline from config
        
        config = [
            {"type": "lag_features", "params": {...}},
            {"type": "rolling_stats", "params": {...}}
        ]
        
        Returns: [LagFeatureTransformer(), RollingStatTransformer()]
        """
    
    @staticmethod
    def apply_pipeline(data, pipeline):
        """
        Apply transformers in sequence
        """
```

### 2. Abstract Base Class Pattern

**Used for**: Data sources, Features, Models

**Example**: BaseForecaster

```python
class BaseForecaster(ABC):
    @abstractmethod
    def fit(self, train_df, config):
        """Fit model to training data"""
    
    @abstractmethod
    def predict(self, horizon, features=None):
        """Generate forecasts"""
    
    @abstractmethod
    def save(self, path):
        """Save model to disk"""
```

### 3. Composition Pattern

**Training Pipeline**: Composes data source + feature pipeline + model

```python
def run_training_pipeline(config):
    # 1. Data source
    source = DataSourceRegistry.get(config["data"]["source"])
    raw_data = source.load(config)
    
    # 2. Feature pipeline
    pipeline = FeatureRegistry.build_pipeline(config["feature_pipeline"])
    featured_data = FeatureRegistry.apply_pipeline(raw_data, pipeline)
    
    # 3. Model
    model_class = ModelRegistry.get(config["model"]["type"])
    model = model_class()
    model.fit(featured_data, config)
```

## Data Flow

### Training Data Flow

```
Raw Data Source
    │
    ├─ DummyGenerator: Generate synthetic time series
    │  └─ Output: DataFrame with [timestamp, series_id, target]
    │
    └─ OfflineCSVSource: Load from CSV
       └─ Output: DataFrame with [timestamp, series_id, target]
    
    ↓ [compute_dataframe_hash()]
    
Metadata stored in .dvc_metadata/
    
    ↓
    
Feature Engineering Pipeline
    │
    ├─ LagFeatureTransformer: Create lag features
    │  └─ Output: [lag_1, lag_7, lag_30, ...]
    │
    ├─ RollingStatTransformer: Rolling statistics
    │  └─ Output: [rolling_mean_7, rolling_std_7, ...]
    │
    └─ CalendarFeatureTransformer: Temporal features
       └─ Output: [day_of_week, month, ...]
    
    ↓ [compute_dataframe_hash()]
    
Metadata stored in .dvc_metadata/
    
    ↓
    
Train/Test Split
    │
    ├─ Train: 80% of data
    │
    └─ Test: 20% of data
    
    ↓ [compute_dataframe_hash() for each]
    
Metadata stored in .dvc_metadata/
    
    ↓
    
Model Training
    │
    ├─ LightGBMForecaster: Gradient boosting
    │
    └─ ARIMAForecaster: Statistical model
    
    ↓
    
Evaluate Metrics
    │
    ├─ MAE: Mean Absolute Error
    ├─ RMSE: Root Mean Squared Error
    ├─ MAPE: Mean Absolute Percentage Error
    └─ SMAPE: Symmetric Mean Absolute Percentage Error
    
    ↓
    
Log to MLflow
    │
    ├─ Parameters: data hashes, code version, config
    ├─ Metrics: MAE, RMSE, MAPE, SMAPE
    ├─ Artifacts: model.pkl, data_lineage.json
    └─ Tags: reproducible=true
```

### Reproducibility Data Flow

```
User Query: run_id = "abc-123-def"
    ↓
MLflow Database Query
    ↓
Extract Parameters
    ├─ data_raw_data_hash
    ├─ data_featured_data_hash
    ├─ data_train_data_hash
    ├─ data_test_data_hash
    └─ code_version
    
    ├─ model_type
    ├─ n_train
    ├─ n_test
    └─ ...other params
    
    ↓
Checkout Code Version
    │
    └─ git checkout {code_version}
    
    ↓
Restore Data (optional)
    │
    └─ dvc checkout (if using DVC files)
    
    ↓
Run Training
    │
    ├─ Load same data (recreate same hashes)
    ├─ Same feature engineering (recreate same hashes)
    ├─ Same train/test split (recreate same hashes)
    ├─ Same model training
    └─ Recreate exact same results
    
    ↓
Compare Results
    │
    └─ Metrics should match (or be very close)
```

## Key Design Decisions

### 1. Why SHA-256 Hashing?

- **Deterministic**: Same data = same hash
- **Collision-resistant**: Different data = different hash (2^256 possibilities)
- **Fast**: Computed in one pass
- **Standard**: Available in Python standard library

**Alternative**: Could use MD5 (faster but weaker) or Blake3 (newer, better)

### 2. Why Store Metadata as JSON?

- **Human-readable**: Easy to inspect `.dvc_metadata/` files
- **Portable**: No special tools needed to read
- **Version-controllable**: Can track in git if needed
- **Queryable**: Easy to parse for analytics

### 3. Why MLflow Parameters for Data Versions?

- **Integrated**: Data versions appear in MLflow UI
- **Queryable**: Can filter runs by data hash
- **Searchable**: Can find all runs with specific data version
- **Artifact traceable**: Links to data_lineage.json artifact

### 4. Why Also Save Data Lineage Artifact?

- **Complete history**: More detailed than parameters
- **Offline-accessible**: Don't need MLflow DB to view
- **Portable**: Can ship with model for audit trail
- **Structured**: JSON format for programmatic access

## Extension Points

### Add New Data Source

```python
# data_sources/custom_source.py
from data_sources import BaseDataSource

class CustomDataSource(BaseDataSource):
    def load(self, config):
        # Your custom logic
        return df

# Register in data_sources/__init__.py
DATA_SOURCE_REGISTRY["custom"] = CustomDataSource
```

### Add New Feature Transformer

```python
# features/built_in/my_feature.py
from features import BaseFeatureTransformer

class MyFeatureTransformer(BaseFeatureTransformer):
    def transform(self, df, params):
        # Your feature engineering
        return df_with_features

# Register in features/registry.py
FEATURE_REGISTRY["my_feature"] = MyFeatureTransformer
```

### Add New Model

```python
# models/custom/my_model.py
from models import BaseForecaster

class MyForecaster(BaseForecaster):
    def fit(self, train_df, config):
        # Your training logic
    
    def predict(self, horizon, features=None):
        # Your prediction logic
        return predictions

# Register in models/registry.py
MODEL_REGISTRY["my_model"] = MyForecaster
```

## Performance Considerations

### Data Hashing Cost

- **Time**: O(n) where n = number of rows
- **Memory**: O(1) — streaming hash computation
- **Typical**: ~100K rows hashes in < 1 second

### MLflow Overhead

- **Parameter logging**: Negligible (< 10ms per parameter)
- **Artifact logging**: Depends on model size (typically 10-500ms)

### Recommendation

- Hashing adds < 1% overhead to typical training (10-60 minutes)
- Enable by default for production reproducibility
- Optional for rapid experimentation (comment out tracker calls)

---

**See Also**: [DATA_VERSIONING.md](DATA_VERSIONING.md) for usage guide
