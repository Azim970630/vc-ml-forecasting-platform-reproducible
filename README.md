# ML Forecasting Platform with Data Versioning

An end-to-end MLOps platform for time series forecasting with **code versioning** (Git), **model tracking** (MLflow), and **data versioning** (DVC + content hashing).

## Key Features

### 🔄 Complete Reproducibility
- **Data Versioning** — SHA-256 hashing of data at each pipeline stage
- **Code Versioning** — Git commits captured with each experiment
- **Model Tracking** — MLflow logs models, metrics, and artifacts
- **Lineage Tracking** — Complete history of what data/code produced which results

### 🏗️ Extensible Architecture
- **Pluggable Data Sources** — DummyGenerator, OfflineCSVSource, easily add more
- **Pluggable Feature Engineering** — Registry pattern for composable transformers
- **Swappable Models** — LightGBM, ARIMA, easily add new forecasters

### 📊 Production-Ready
- **Batch Inference Pipeline** — Load models and generate forecasts
- **Comprehensive Testing** — Unit + integration tests with 12+ test cases
- **CI/CD Ready** — GitHub Actions workflows for automated testing and training
- **Full Documentation** — User guide, API reference, deployment guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. Restore Data with DVC (Production Use)

If cloning fresh or reproducing from production:

```bash
# Restore exact data from remote storage (Azure Blob Storage, S3, GCS, etc.)
dvc pull
```

This restores the exact data files tracked with DVC. For local development without remote setup, the dummy data generator will create sample data automatically.

### 3. Run Training with Data Versioning

```bash
python3 train.py
```

This will:
- Load data and track its version (SHA-256 hash)
- Engineer features and track version
- Split data and track each split's version
- Train the model
- Log everything to MLflow (including data hashes + code version)

Output:
```
Raw data hash: c54d29c9
Featured data hash: e971c052
Train hash: e03560ee
Test hash: 0ea5701f

Experiment run ID: 541d0c7fdb9a43...
Code version: 91b64a1504835d4...
```

### 4. Reproduce a Production Experiment

To recreate exact same inference results from any past production experiment:

```bash
python3 reproduce_experiment.py --run-id 541d0c7fdb9a43999a5d12be2c7f9d31 --restore-data
```

This will:
- ✓ Restore the exact code version (via git checkout)
- ✓ Restore the exact data version (via dvc pull)
- Show data hashes for verification
- Provide instructions to re-run with original parameters

### 5. View in MLflow

```bash
mlflow ui
```

Browse to http://localhost:5000 to see:
- All experiment runs with dates/metrics
- Data versions and code versions logged as parameters
- Model artifacts and performance metrics
- Complete lineage artifact (`data_lineage.json`)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Data Source  →  Feature Engineering  →  Model Training   │
│  (+ hash)          (+ hash)               (+ code version) │
│                                                             │
│                    ↓                                        │
│            MLflow Experiment Run                          │
│            - Data hashes (parameters)                     │
│            - Code version (parameter)                     │
│            - Model artifacts                             │
│            - Metrics                                      │
│            - Lineage (artifact)                           │
│                                                             │
│                    ↓                                        │
│          .dvc_metadata/ (detailed versions)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                Reproduction Pipeline                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Given Run ID  →  Query MLflow  →  Checkout Code/Data  →   │
│                                      Run Training           │
│                                      (Exact Same Result)    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Components

### Data Versioning (`data_versioning.py`)
- `DataVersionTracker` — Track data versions at each stage
- `ExperimentReproducer` — Reproduce past experiments
- `compute_dataframe_hash()` — SHA-256 hashing
- `get_git_commit_hash()` — Capture code version

### Data Sources (`data_sources/`)
- `DummyGenerator` — Generate synthetic time series (configurable trend/seasonality)
- `OfflineCSVSource` — Load data from CSV files
- `BaseDataSource` — Abstract interface for custom sources

### Feature Engineering (`features/`)
- `LagFeatureTransformer` — Lagged target features (lag-1, lag-7, lag-30, etc.)
- `RollingStatTransformer` — Rolling statistics (mean, std, min, max)
- `CalendarFeatureTransformer` — Temporal features (day of week, month, etc.)
- `FeatureRegistry` — Registry pattern for composable pipelines

### Models (`models/`)
- `LightGBMForecaster` — Gradient boosting model with multi-step ahead forecasting
- `ARIMAForecaster` — Classical statistical model (ARIMA)
- `BaseForecaster` — Abstract interface for custom models
- `ModelRegistry` — Registry pattern for model selection

### Pipelines
- `training.py` — End-to-end training with data versioning + MLflow logging
- `batch_inference.py` — Load model and generate batch predictions

### Testing (`tests/`)
- Unit tests for data sources, features, and models
- Integration tests for full training pipeline
- Test fixtures and configuration

## Configuration

All configuration via YAML files in `config/`:

```yaml
# config/data.yaml - Data source configuration
data:
  source: dummy  # or 'offline'
  dummy:
    n_rows: 200
    seasonality: true
  offline:
    filepath: data/raw_data.csv
    columns:
      timestamp: Date
      value: Price

# config/model.yaml - Model and training configuration
model:
  type: lightgbm  # or 'arima'
  training:
    test_size: 0.2
    random_seed: 42
```

## Data Versioning Workflow

### When Training Runs
1. Load data → compute hash → store metadata
2. Engineer features → compute hash → store metadata
3. Split train/test → compute hashes → store metadata
4. Train model
5. Log all hashes + code version to MLflow
6. Save complete lineage to `data_lineage.json`

### When Reproducing
1. Query MLflow for experiment metadata
2. Show data versions + code version + parameters
3. Checkout exact code version
4. Restore exact data versions
5. Run training → get exact same results

## Usage Examples

### Training with Dummy Data + LightGBM
```bash
python3 train.py
```

### Reproducing Specific Experiment
```bash
python3 reproduce_experiment.py --run-id abc-123-def-456
```

### Batch Inference
```python
from pipelines.batch_inference import run_inference_pipeline
from config_loader import load_config

config = load_config()
predictions = run_inference_pipeline(config)
print(predictions)
```

### Manual Data Versioning
```python
from data_versioning import DataVersionTracker
import pandas as pd

tracker = DataVersionTracker()
df = pd.read_csv('data.csv')

# Track version
version = tracker.track_training_data(
    df,
    name="my_data",
    metadata={"source": "external_api"}
)

print(f"Hash: {version['hash']}")
print(f"Timestamp: {version['timestamp']}")
```

### Query Experiment Metadata
```python
from data_versioning import ExperimentReproducer

reproducer = ExperimentReproducer()
metadata = reproducer.get_experiment_metadata("run-id")

print(f"Code version: {metadata['code_version']}")
print(f"Data versions: {metadata['data_versions']}")
print(f"Model params: {metadata['model_params']}")
```

## Testing

Run all tests:
```bash
pytest tests/ -v --cov=. --cov-report=html
```

Run specific test suite:
```bash
pytest tests/unit/test_data_sources.py -v
pytest tests/integration/test_training_pipeline.py -v
```

View coverage:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Documentation

- **[DATA_VERSIONING.md](DATA_VERSIONING.md)** — Complete guide to data versioning, reproducibility, and diagnostics
- **[USER_GUIDE.md](USER_GUIDE.md)** — Step-by-step guide for end users
- **[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md)** — Deep dive into architecture and design decisions
- **[API_REFERENCE.md](API_REFERENCE.md)** — Complete API reference for all modules
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** — Instructions for deploying to production
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — Common issues and solutions
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Guidelines for contributors

## MLflow Setup

MLflow automatically tracks all runs to `./mlruns/` directory.

View experiments:
```bash
mlflow ui
```

Then open http://localhost:5000 in browser.

### What Gets Logged

Each experiment logs:
- **Parameters** — Data hashes, code version, model config
- **Metrics** — MAE, RMSE, MAPE, SMAPE
- **Artifacts** — Trained model, data_lineage.json
- **Tags** — reproducible=true (for easy filtering)

## DVC Integration

Data version control is initialized and ready to use:

```bash
# View DVC config
dvc config -l

# Track external data files
dvc add data/raw_data.csv

# Run DVC pipeline
dvc repro dvc.yaml
```

## GitHub Actions

Two automated workflows:

### CI Workflow (`.github/workflows/ci.yaml`)
- Runs on every push/PR
- Lints code (ruff, black)
- Runs type checking (mypy)
- Executes all tests with coverage
- Supports Python 3.11, 3.12

### Training Workflow (`.github/workflows/train.yaml`)
- Runs on code changes
- Trains model with latest code
- Uploads trained model as artifact
- Useful for automated retraining

## Directory Structure

```
.
├── config/                          # Configuration files
│   ├── base.yaml
│   ├── data.yaml
│   ├── features.yaml
│   └── model.yaml
├── data_sources/                    # Data loading layer
│   ├── base.py
│   ├── dummy_generator.py
│   └── offline_source.py
├── features/                        # Feature engineering layer
│   ├── base.py
│   ├── registry.py
│   └── built_in/
│       ├── lag_features.py
│       ├── rolling_stats.py
│       └── calendar_features.py
├── models/                          # Model layer
│   ├── base.py
│   ├── registry.py
│   ├── ml/
│   │   └── lightgbm_model.py
│   └── classical/
│       └── arima.py
├── pipelines/                       # Orchestration
│   ├── training.py
│   └── batch_inference.py
├── tests/                           # Comprehensive test suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── data_versioning.py               # Data versioning & reproducibility
├── reproduce_experiment.py           # Reproduce past experiments
├── config_loader.py                 # Configuration loader
├── utils.py                         # Utility functions
├── train.py                         # Training entry point
├── test_mvp.py                      # Quick test script
├── requirements.txt                 # Dependencies
├── requirements-dev.txt             # Dev dependencies
├── dvc.yaml                         # DVC pipeline definition
├── .dvc/                            # DVC configuration
├── .dvc_metadata/                   # Data version metadata
├── .github/workflows/               # GitHub Actions
├── README.md                        # This file
└── [Documentation files...]         # Guides and API reference
```

## Key Concepts

### Data Versioning
Every data transformation (raw → featured → train/test) is hashed using SHA-256. This allows:
- Detecting when data changes unexpectedly
- Reproducing experiments with exact same data
- Auditing which data was used for which results

### Code Versioning
Git commit hash is captured with each MLflow run. This allows:
- Checking out exact code version used in past experiments
- Reproducing with same code + data + model

### Reproducibility
With data + code versions, you can:
- Reproduce any past experiment exactly
- Debug why results differ between runs
- Audit and validate model decisions

## Requirements

- Python 3.11+
- pandas, numpy, scikit-learn
- lightgbm, statsmodels
- mlflow (experiment tracking)
- pydantic, pyyaml (configuration)
- dvc (data versioning)
- pytest, black, ruff, mypy (development)

## License

MIT License

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For issues, questions, or suggestions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Check [DATA_VERSIONING.md](DATA_VERSIONING.md) for reproducibility questions
3. Open an issue on GitHub

---

**Ready to train?** Run `python3 train.py` and check MLflow UI at http://localhost:5000
