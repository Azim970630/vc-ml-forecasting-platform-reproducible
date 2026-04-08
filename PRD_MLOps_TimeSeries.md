# Product Requirements Document (PRD)
## MLOps Platform — Time Series Forecasting System

| Field | Detail |
|---|---|
| **Document Version** | v1.0.0 |
| **Status** | Draft |
| **Domain** | Time Series Forecasting (Demand, Sales, Prices) |
| **Deployment Target** | Local + Cloud (Hybrid) |
| **Last Updated** | 2026-04-08 |
| **Author** | TBD |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Goals & Success Metrics](#2-project-goals--success-metrics)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 Data Source & Ingestion
   - 4.2 Feature Store & Feature Engineering
   - 4.3 Model Zoo (Pluggable Model Types)
   - 4.4 Experiment Tracking
   - 4.5 Pipeline Orchestration
   - 4.6 Model Versioning & Promotion
   - 4.7 Model Serving (Batch & Real-Time)
   - 4.8 Drift Monitoring
   - 4.9 CI/CD with GitHub Actions
   - 4.10 Testing Strategy
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Proposed Directory Structure](#6-proposed-directory-structure)
7. [Technology Stack](#7-technology-stack)
8. [Data Flow Diagram](#8-data-flow-diagram)
9. [Versioning Strategy](#9-versioning-strategy)
10. [GitHub Actions CI/CD Workflows](#10-github-actions-cicd-workflows)
11. [Testing Plan](#11-testing-plan)
12. [Milestones & Delivery Phases](#12-milestones--delivery-phases)
13. [Risks & Mitigations](#13-risks--mitigations)
14. [Glossary](#14-glossary)

---

## 1. Executive Summary

This document specifies the requirements for a **production-grade, locally-runnable MLOps platform** for Time Series Forecasting. The system is designed to support demand forecasting, sales prediction, and price trend analysis with full observability, reproducibility, and flexibility.

The platform emphasises:
- **Flexibility** — swap data sources, model types, and feature pipelines without changing core infrastructure.
- **Reproducibility** — every experiment, dataset version, and model artifact is versioned and tracked.
- **Production-readiness** — the system supports both batch and real-time inference, drift monitoring, and automated CI/CD pipelines.
- **Hybrid deployment** — runs fully on a local machine for development; seamlessly extends to cloud environments (AWS / GCP / Azure) for production workloads.

---

## 2. Project Goals & Success Metrics

### 2.1 Goals

| # | Goal |
|---|---|
| G1 | Enable rapid experimentation across classical, ML-based, and deep learning time series models |
| G2 | Ensure full reproducibility of all experiments, data, and model artifacts |
| G3 | Provide automated CI/CD to enforce code quality and prevent regressions |
| G4 | Support both batch and real-time inference serving |
| G5 | Detect model and data drift automatically to trigger retraining |
| G6 | Allow any team member to swap model type, data source, or feature pipeline via config |

### 2.2 Success Metrics

| Metric | Target |
|---|---|
| Model training pipeline execution time | < 10 min for datasets up to 1M rows (local) |
| Real-time inference latency (p95) | < 200ms |
| Experiment reproducibility | 100% — same config must produce same results |
| CI/CD pipeline pass rate | ≥ 95% on main branch |
| Drift detection alert lead time | ≤ 24 hours from drift occurrence |
| Unit test coverage | ≥ 80% |

---

## 3. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Online Data │  │ Offline Data │  │    Dummy Generator  │   │
│  │  (APIs/DB)   │  │  (CSV/Parq.) │  │    (Synthetic)      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘   │
│         └─────────────────┴──────────────────────┘              │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │  Data       │  DVC-tracked                  │
│                    │  Ingestion  │  versioned snapshots          │
│                    └──────┬──────┘                               │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      FEATURE LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Feature Store (Feast / custom SQLite local store)       │   │
│  │  Custom Feature Engineering Pipelines (pluggable)        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     TRAINING LAYER                              │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │  Classical TS │  │  ML Models    │  │  Deep Learning   │    │
│  │  ARIMA, ETS   │  │  XGBoost,LGB  │  │  LSTM, NHiTS     │    │
│  │  Prophet      │  │  LightTS      │  │  PatchTST, TFT   │    │
│  └───────────────┘  └───────────────┘  └──────────────────┘    │
│                                                                  │
│  Experiment Tracking: MLflow                                     │
│  Orchestration: Prefect (local) / Airflow (cloud)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   MODEL REGISTRY & PROMOTION                    │
│  MLflow Model Registry  →  Staging  →  Production              │
│  DVC for model artifact versioning + Git tags                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      SERVING LAYER                              │
│  ┌──────────────────────┐    ┌─────────────────────────────┐   │
│  │  Batch Inference     │    │  Real-Time Inference         │   │
│  │  Scheduled Prefect   │    │  FastAPI REST endpoint       │   │
│  │  job → CSV/DB output │    │  Docker-containerised        │   │
│  └──────────────────────┘    └─────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    MONITORING LAYER                             │
│  Evidently AI — Data Drift + Model Performance Drift            │
│  Alerting via email / Slack webhook / log file                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Functional Requirements

---

### 4.1 Data Source & Ingestion

**Requirement ID:** FR-DATA

The system MUST support three interchangeable data source modes, selected via configuration.

#### 4.1.1 Supported Sources

| Mode | Description | Config Key |
|---|---|---|
| `online` | Pull from REST APIs, databases (PostgreSQL, MySQL), or cloud storage (S3, GCS) | `data.source: online` |
| `offline` | Load from local files — CSV, Parquet, JSON, Excel | `data.source: offline` |
| `dummy` | Generate synthetic time series data using configurable parameters | `data.source: dummy` |

#### 4.1.2 Data Source Interface

All data sources MUST implement a common `BaseDataSource` abstract interface:

```python
class BaseDataSource(ABC):
    @abstractmethod
    def load(self, config: DataConfig) -> pd.DataFrame:
        """Return a raw DataFrame with at minimum: timestamp, target columns."""
        ...

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Assert schema, nulls, and time continuity."""
        ...
```

#### 4.1.3 Dummy Data Generator

When `data.source: dummy`, the generator must support:
- Configurable number of series, date range, frequency (daily/weekly/hourly)
- Seasonal patterns, trend injection, and noise level
- Reproducible output via random seed

#### 4.1.4 Data Versioning

- All ingested datasets MUST be tracked using **DVC** (Data Version Control).
- Raw and processed datasets are stored as DVC-managed artifacts in a local or remote cache (S3, GCS, or local directory).
- Each pipeline run logs the DVC data hash to MLflow for full lineage.

---

### 4.2 Feature Store & Feature Engineering

**Requirement ID:** FR-FEATURE

#### 4.2.1 Feature Store

- Use **Feast** (local SQLite registry for development, Redis/BigQuery for cloud) as the feature store.
- Feature definitions are declared in `features/feature_definitions.py` using Feast's `FeatureView` API.
- The system supports both **offline features** (for training) and **online features** (for real-time inference).

#### 4.2.2 Custom Feature Engineering Pipelines

- Feature engineering pipelines MUST be modular and pluggable via a registry pattern.
- Each feature transformer inherits from `BaseFeatureTransformer`:

```python
class BaseFeatureTransformer(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "BaseFeatureTransformer": ...

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

    @abstractmethod
    def get_feature_names(self) -> list[str]: ...
```

- Built-in transformers provided out-of-the-box:

| Transformer | Description |
|---|---|
| `LagFeatureTransformer` | Lag features (t-1, t-7, t-28) |
| `RollingStatTransformer` | Rolling mean, std, min, max |
| `CalendarFeatureTransformer` | Day of week, month, quarter, holidays |
| `FourierTransformer` | Fourier terms for seasonality |
| `TargetEncoderTransformer` | Categorical encoding |

- Users define their feature pipeline in `config/features.yaml`:

```yaml
feature_pipeline:
  - name: LagFeatureTransformer
    params:
      lags: [1, 7, 14, 28]
  - name: RollingStatTransformer
    params:
      windows: [7, 14, 28]
      stats: [mean, std]
  - name: CalendarFeatureTransformer
    params:
      include_holidays: true
      country: MY
```

#### 4.2.3 Adding Custom Transformers

To add a new transformer:
1. Create a class in `features/custom/` inheriting `BaseFeatureTransformer`.
2. Register it in `features/registry.py`.
3. Reference it by name in `config/features.yaml`.

No changes to core pipeline code are required.

---

### 4.3 Model Zoo (Pluggable Model Types)

**Requirement ID:** FR-MODEL

The system supports three categories of models, all interchangeable via `config/model.yaml`.

#### 4.3.1 Model Categories

**Category A — Classical Time Series Models**

| Model | Library | Config Key |
|---|---|---|
| ARIMA / SARIMA | `statsmodels` | `model.type: arima` |
| Exponential Smoothing (ETS) | `statsmodels` | `model.type: ets` |
| Prophet | `prophet` | `model.type: prophet` |
| Theta | `statsforecast` | `model.type: theta` |

**Category B — Classical ML Models (Tabular)**

| Model | Library | Config Key |
|---|---|---|
| XGBoost | `xgboost` | `model.type: xgboost` |
| LightGBM | `lightgbm` | `model.type: lightgbm` |
| Random Forest | `scikit-learn` | `model.type: random_forest` |
| Linear Regression (baseline) | `scikit-learn` | `model.type: linear` |

**Category C — Deep Learning Models**

| Model | Library | Config Key |
|---|---|---|
| LSTM | `pytorch` | `model.type: lstm` |
| N-HiTS | `neuralforecast` | `model.type: nhits` |
| PatchTST | `neuralforecast` | `model.type: patchtst` |
| Temporal Fusion Transformer (TFT) | `neuralforecast` | `model.type: tft` |

#### 4.3.2 Model Interface

All models MUST implement `BaseForecaster`:

```python
class BaseForecaster(ABC):
    @abstractmethod
    def fit(self, train: pd.DataFrame, config: ModelConfig) -> None: ...

    @abstractmethod
    def predict(self, horizon: int, features: pd.DataFrame) -> pd.DataFrame: ...

    @abstractmethod
    def save(self, path: str) -> None: ...

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "BaseForecaster": ...

    @abstractmethod
    def get_hyperparameter_space(self) -> dict: ...
```

#### 4.3.3 Model Configuration

Switch models without changing any code:

```yaml
# config/model.yaml
model:
  type: lightgbm          # Change this to switch model
  horizon: 28             # Forecast horizon (days)
  frequency: D            # D = daily, W = weekly, H = hourly
  hyperparameters:
    n_estimators: 500
    learning_rate: 0.05
    num_leaves: 63
  cross_validation:
    strategy: expanding_window
    n_splits: 5
    gap: 7
```

#### 4.3.4 Hyperparameter Tuning

- Optuna integration for automated hyperparameter search.
- Tuning is toggled via `training.tune: true` in config.
- All trial results are logged to MLflow.

---

### 4.4 Experiment Tracking

**Requirement ID:** FR-EXPERIMENT

- **Tool:** MLflow (local `mlruns/` directory for development; MLflow Tracking Server or Databricks for cloud).
- Every training run MUST log:

| Category | Logged Items |
|---|---|
| Parameters | All model hyperparameters, feature config, data config |
| Metrics | MAE, RMSE, MAPE, SMAPE, WAPE, training time |
| Artifacts | Trained model, feature importance plots, forecast plots, confusion matrix (if applicable) |
| Tags | `model_type`, `data_source`, `git_commit`, `dataset_version` (DVC hash), `run_environment` |
| Data Lineage | DVC dataset hash, feature pipeline version |

- MLflow UI is accessible locally at `http://localhost:5000` via `mlflow ui`.
- Experiments are namespaced by project and model category (e.g., `ts-forecasting/deep-learning`).

---

### 4.5 Pipeline Orchestration

**Requirement ID:** FR-PIPELINE

- **Local:** Prefect 2.x with a local agent.
- **Cloud:** Prefect Cloud or Apache Airflow (configurable via `orchestration.backend`).

#### 4.5.1 Core Pipelines

| Pipeline | Description | Schedule |
|---|---|---|
| `data_ingestion_pipeline` | Ingest, validate, version raw data | Daily / on-demand |
| `feature_engineering_pipeline` | Transform raw data → feature store | After ingestion |
| `training_pipeline` | Train, evaluate, log to MLflow | On-demand / scheduled |
| `evaluation_pipeline` | Cross-validate and compare model versions | After training |
| `promotion_pipeline` | Promote model from Staging → Production | Manual trigger |
| `batch_inference_pipeline` | Run batch predictions on schedule | Daily / weekly |
| `monitoring_pipeline` | Compute drift metrics and alert | Daily |
| `retraining_pipeline` | Triggered by drift alerts or schedule | On alert / weekly |

#### 4.5.2 Pipeline Configuration

```yaml
# config/pipeline.yaml
orchestration:
  backend: prefect          # prefect | airflow
  schedules:
    data_ingestion: "0 6 * * *"     # 6am daily
    batch_inference: "0 8 * * *"    # 8am daily
    monitoring: "0 9 * * *"         # 9am daily
  retries: 2
  retry_delay_seconds: 60
```

---

### 4.6 Model Versioning & Promotion

**Requirement ID:** FR-REGISTRY

#### 4.6.1 Versioning

- **Code versioning:** Git with semantic versioning tags (`v1.2.3`).
- **Data versioning:** DVC with remote storage (local path, S3, or GCS).
- **Model versioning:** MLflow Model Registry with automatic version increments.

#### 4.6.2 Promotion Stages

```
Experiment Run → [None] → Staging → Production → Archived
```

| Stage | Description | Trigger |
|---|---|---|
| `None` | New run, not yet evaluated | Automatic on training |
| `Staging` | Passed evaluation thresholds | Automated evaluation gate |
| `Production` | Approved for serving | Manual approval or CI gate |
| `Archived` | Superseded or deprecated | On new Production promotion |

#### 4.6.3 Promotion Gates

A model is eligible for `Staging` only if:
- MAE improves over the current Production model by ≥ 2%, OR
- No Production model exists yet.
- All unit tests and integration tests pass.

Promotion to `Production` requires:
- Manual approval via MLflow UI, OR
- Automated gate in CI/CD if configured (`promotion.auto_promote: true`).

---

### 4.7 Model Serving

**Requirement ID:** FR-SERVING

#### 4.7.1 Batch Inference

- Orchestrated via Prefect pipeline (`batch_inference_pipeline`).
- Loads the `Production` model from MLflow Registry.
- Reads input features from the Feature Store (offline).
- Outputs predictions to: CSV file, database table, or cloud storage — configurable.

```yaml
# config/serving.yaml
batch_inference:
  output_format: parquet       # csv | parquet | database
  output_path: outputs/predictions/
  schedule: "0 8 * * *"
```

#### 4.7.2 Real-Time Inference

- FastAPI REST service with the following endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/predict` | POST | Single or batch prediction request |
| `/model/info` | GET | Current production model metadata |
| `/model/reload` | POST | Reload model from registry (zero-downtime) |

- Request schema:

```json
{
  "series_id": "store_001",
  "horizon": 7,
  "features": {
    "date": "2026-04-08",
    "is_holiday": false,
    "price_index": 1.12
  }
}
```

- The service is Dockerised and deployable locally or to cloud (ECS, Cloud Run, etc.).
- Model is loaded from MLflow Registry at startup; supports hot-reloading via `/model/reload`.

---

### 4.8 Model & Data Drift Monitoring

**Requirement ID:** FR-MONITORING

- **Tool:** Evidently AI.

#### 4.8.1 Data Drift Monitoring

- Compare the distribution of incoming production features against the training reference dataset.
- Metrics computed: Population Stability Index (PSI), Wasserstein distance, Jensen-Shannon divergence.
- Drift is flagged if PSI > 0.2 for any key feature.

#### 4.8.2 Model Performance Drift (Concept Drift)

- Compare rolling production predictions against actuals (where ground truth is available).
- Metrics tracked: MAE drift, MAPE drift, prediction bias.
- Alert triggered if MAE degrades > 10% from baseline.

#### 4.8.3 Monitoring Reports

- Evidently generates HTML and JSON reports, stored in `monitoring/reports/`.
- Reports are logged as MLflow artifacts.
- Alerts dispatched via: log file, email (SMTP), or Slack webhook — configurable.

```yaml
# config/monitoring.yaml
monitoring:
  reference_dataset: data/processed/reference.parquet
  drift_threshold:
    psi: 0.2
    mae_degradation_pct: 10
  alert_channels:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK_URL}
    - type: email
      recipients: [mlops-team@company.com]
  trigger_retraining_on_drift: true
```

---

### 4.9 CI/CD with GitHub Actions

**Requirement ID:** FR-CICD

Three GitHub Actions workflow files are required:

#### Workflow 1: `ci.yaml` — Continuous Integration

**Triggers:** Push to any branch, Pull Request to `main`

**Steps:**
1. Checkout code
2. Set up Python environment
3. Install dependencies (cached)
4. Run linting — `ruff` + `black --check`
5. Run type checking — `mypy`
6. Run unit tests — `pytest tests/unit/`
7. Run integration tests — `pytest tests/integration/`
8. Upload coverage report to Codecov

#### Workflow 2: `cd.yaml` — Continuous Deployment

**Triggers:** Push to `main` (after CI passes), manual `workflow_dispatch`

**Steps:**
1. Run full test suite
2. Build Docker image for serving API
3. Run smoke test on Docker container
4. Push image to container registry (GHCR or ECR)
5. Trigger promotion evaluation pipeline
6. Deploy to staging environment (if cloud configured)

#### Workflow 3: `model_retrain.yaml` — Scheduled Retraining

**Triggers:** Cron schedule (`0 2 * * 0` — weekly Sunday 2am), manual `workflow_dispatch`, or drift alert webhook

**Steps:**
1. Pull latest data via DVC
2. Run feature engineering pipeline
3. Train model with latest data
4. Evaluate against current Production model
5. Auto-promote to Staging if gates pass
6. Notify team via Slack

---

### 4.10 Testing Strategy

**Requirement ID:** FR-TESTING

| Test Type | Tool | Scope | Location |
|---|---|---|---|
| Unit tests | `pytest` | Individual functions, transformers, models | `tests/unit/` |
| Integration tests | `pytest` | Pipeline end-to-end with dummy data | `tests/integration/` |
| Data validation tests | `great_expectations` / `pandera` | Schema, nulls, ranges | `tests/data/` |
| Model performance tests | `pytest` | Forecast accuracy thresholds | `tests/model/` |
| API tests | `pytest` + `httpx` | FastAPI endpoint contracts | `tests/api/` |
| Drift detection tests | `pytest` | Evidently report generation | `tests/monitoring/` |

**Minimum coverage requirement: 80%** (enforced in CI via `--cov-fail-under=80`).

---

## 5. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | **Performance** — Training pipeline (1M rows, LightGBM) | < 10 minutes local |
| NFR-02 | **Latency** — Real-time inference (p95) | < 200ms |
| NFR-03 | **Scalability** — Batch inference | Up to 10M rows via chunked processing |
| NFR-04 | **Reproducibility** — Same config + data version = same result | 100% |
| NFR-05 | **Portability** — Runs on macOS, Linux, Windows (via Docker) | All three OS |
| NFR-06 | **Security** — Secrets (API keys, DB passwords) via `.env` / Vault | Never hardcoded |
| NFR-07 | **Observability** — All pipeline runs emit structured logs (JSON) | Always |
| NFR-08 | **Configurability** — Any parameter changeable via YAML config, no code changes | Always |
| NFR-09 | **Maintainability** — Code style enforced via `ruff` + `black` + `mypy` | CI-enforced |
| NFR-10 | **Documentation** — Every module has docstrings; README kept up to date | Always |

---

## 6. Proposed Directory Structure

```
ml-forecasting-platform/
│
├── .github/
│   └── workflows/
│       ├── ci.yaml                        # Lint, test, coverage
│       ├── cd.yaml                        # Build, push Docker, deploy
│       └── model_retrain.yaml             # Scheduled retraining
│
├── config/
│   ├── base.yaml                          # Global settings
│   ├── data.yaml                          # Data source config
│   ├── features.yaml                      # Feature pipeline config
│   ├── model.yaml                         # Model type & hyperparameters
│   ├── pipeline.yaml                      # Orchestration schedules
│   ├── serving.yaml                       # Batch & real-time serving config
│   └── monitoring.yaml                    # Drift thresholds & alerts
│
├── data/
│   ├── raw/                               # DVC-tracked raw data
│   ├── processed/                         # DVC-tracked processed features
│   └── reference/                         # Reference dataset for drift monitoring
│
├── features/
│   ├── __init__.py
│   ├── base.py                            # BaseFeatureTransformer ABC
│   ├── registry.py                        # Transformer registry
│   ├── built_in/
│   │   ├── lag_features.py
│   │   ├── rolling_stats.py
│   │   ├── calendar_features.py
│   │   └── fourier_features.py
│   └── custom/                            # Drop custom transformers here
│       └── .gitkeep
│
├── models/
│   ├── __init__.py
│   ├── base.py                            # BaseForecaster ABC
│   ├── registry.py                        # Model registry
│   ├── classical/
│   │   ├── arima.py
│   │   ├── prophet_model.py
│   │   └── ets.py
│   ├── ml/
│   │   ├── xgboost_model.py
│   │   ├── lightgbm_model.py
│   │   └── random_forest.py
│   └── deep_learning/
│       ├── lstm.py
│       ├── nhits.py
│       └── tft.py
│
├── pipelines/
│   ├── __init__.py
│   ├── data_ingestion.py
│   ├── feature_engineering.py
│   ├── training.py
│   ├── evaluation.py
│   ├── promotion.py
│   ├── batch_inference.py
│   └── monitoring.py
│
├── data_sources/
│   ├── __init__.py
│   ├── base.py                            # BaseDataSource ABC
│   ├── online_source.py
│   ├── offline_source.py
│   └── dummy_generator.py
│
├── serving/
│   ├── api/
│   │   ├── main.py                        # FastAPI app
│   │   ├── routers/
│   │   │   ├── predict.py
│   │   │   └── model_info.py
│   │   └── schemas.py                     # Pydantic request/response models
│   ├── batch/
│   │   └── batch_runner.py
│   └── Dockerfile
│
├── monitoring/
│   ├── drift_detector.py
│   ├── alerting.py
│   └── reports/                           # Generated HTML/JSON reports
│
├── feature_store/
│   ├── feature_repo/
│   │   ├── feature_store.yaml             # Feast config
│   │   └── feature_definitions.py
│   └── store_client.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_features.py
│   │   ├── test_models.py
│   │   └── test_data_sources.py
│   ├── integration/
│   │   ├── test_training_pipeline.py
│   │   └── test_inference_pipeline.py
│   ├── data/
│   │   └── test_data_validation.py
│   ├── api/
│   │   └── test_api_endpoints.py
│   └── monitoring/
│       └── test_drift_detection.py
│
├── notebooks/
│   └── exploration/                       # Exploratory analysis notebooks
│
├── scripts/
│   ├── setup_feature_store.py
│   ├── run_pipeline.py                    # CLI entry point
│   └── promote_model.py
│
├── outputs/
│   ├── predictions/                       # Batch prediction outputs
│   └── plots/                             # Training & evaluation plots
│
├── mlruns/                                # MLflow local tracking (git-ignored)
├── .dvc/                                  # DVC config
├── .env.example                           # Environment variable template
├── .gitignore
├── dvc.yaml                               # DVC pipeline stages
├── dvc.lock                               # DVC reproducibility lock
├── pyproject.toml                         # Project metadata, ruff, mypy config
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml                     # Local dev stack (MLflow, API)
└── README.md
```

---

## 7. Technology Stack

| Layer | Tool / Library | Version (min) | Purpose |
|---|---|---|---|
| **Language** | Python | 3.11+ | Core language |
| **Data** | pandas, polars | latest | Data manipulation |
| **Classical TS** | statsmodels, prophet, statsforecast | latest | ARIMA, ETS, Prophet, Theta |
| **ML Models** | scikit-learn, xgboost, lightgbm | latest | Tree-based models |
| **Deep Learning** | pytorch, neuralforecast | latest | LSTM, NHiTS, TFT, PatchTST |
| **Feature Store** | Feast | 0.36+ | Feature management |
| **Experiment Tracking** | MLflow | 2.x | Run tracking & model registry |
| **Data Versioning** | DVC | 3.x | Dataset & model artifact versioning |
| **Orchestration** | Prefect 2 | latest | Pipeline orchestration (local) |
| **Orchestration (cloud)** | Apache Airflow | 2.x | Cloud pipeline alternative |
| **Serving** | FastAPI, uvicorn | latest | Real-time inference API |
| **Containerisation** | Docker, docker-compose | latest | Reproducible environments |
| **Drift Monitoring** | Evidently AI | latest | Data & model drift |
| **Hyperparameter Tuning** | Optuna | latest | Automated tuning |
| **Data Validation** | pandera | latest | Schema & type validation |
| **Testing** | pytest, pytest-cov, httpx | latest | Test suite |
| **Linting** | ruff, black, mypy | latest | Code quality |
| **CI/CD** | GitHub Actions | — | Automation |
| **Config Management** | Hydra / PyYAML | latest | YAML-based configuration |
| **Secrets** | python-dotenv | latest | Local secrets via `.env` |

---

## 8. Data Flow Diagram

```
[Data Source]
    │
    ▼ load() + validate()
[Raw Dataset]  ──DVC version──▶  [DVC Remote Cache]
    │
    ▼ feature pipeline (per features.yaml)
[Feature Store (Feast)]
    │              │
    │ (offline)    │ (online)
    ▼              ▼
[Training]    [Real-time Serving]
    │
    ▼ MLflow log
[MLflow Experiment]
    │
    ▼ if eval gates pass
[MLflow Model Registry — Staging]
    │
    ▼ manual/auto promotion
[MLflow Model Registry — Production]
    │              │
    ▼              ▼
[Batch Inference]  [FastAPI Service]
    │                    │
    ▼                    ▼
[Output Store]     [API Response]
    │
    ▼ compare predictions vs actuals
[Evidently Drift Monitor]
    │
    ▼ if drift detected
[Alert] ──▶ [Retraining Pipeline Trigger]
```

---

## 9. Versioning Strategy

| Artifact | Tool | Strategy |
|---|---|---|
| Source code | Git | Semantic versioning (`vMAJOR.MINOR.PATCH`) + feature branches |
| Raw data | DVC | Content-addressable hash; `dvc push` to remote on each ingestion run |
| Processed features | DVC | Separate DVC stage; tracked independently from raw |
| Model artifacts | MLflow + DVC | MLflow auto-increments version numbers; model binary also pushed to DVC remote |
| Feature definitions | Git | Treated as code; changes trigger full retraining |
| Config files | Git | Changes create new experiment lineage |
| Docker images | GHCR / ECR | Tagged with `git SHA` + `vX.Y.Z` |

**Reproducibility guarantee:** Any historical experiment can be replicated by checking out the Git commit, restoring data via `dvc checkout`, and re-running the training pipeline with the logged MLflow run config.

---

## 10. GitHub Actions CI/CD Workflows

### `ci.yaml`

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check .

      - name: Format check with black
        run: black --check .

      - name: Type check with mypy
        run: mypy src/

      - name: Run unit tests
        run: pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

### `cd.yaml`

```yaml
name: CD

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: serving/
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/forecast-api:latest
            ghcr.io/${{ github.repository }}/forecast-api:${{ github.sha }}

      - name: Smoke test API container
        run: |
          docker run -d -p 8000:8000 \
            -e MLFLOW_TRACKING_URI=${{ secrets.MLFLOW_TRACKING_URI }} \
            ghcr.io/${{ github.repository }}/forecast-api:${{ github.sha }}
          sleep 10
          curl --fail http://localhost:8000/health

      - name: Notify Slack
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: '{"text":"✅ CD pipeline passed. New image deployed: ${{ github.sha }}"}'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### `model_retrain.yaml`

```yaml
name: Scheduled Model Retraining

on:
  schedule:
    - cron: "0 2 * * 0"   # Every Sunday at 2am UTC
  workflow_dispatch:
    inputs:
      force_promote:
        description: "Force promotion to staging even if gates don't pass"
        required: false
        default: "false"

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Configure DVC remote
        run: |
          dvc remote modify myremote access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          dvc remote modify myremote secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}

      - name: Pull latest data
        run: dvc pull data/raw

      - name: Run feature engineering pipeline
        run: python scripts/run_pipeline.py --pipeline feature_engineering
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

      - name: Run training pipeline
        run: python scripts/run_pipeline.py --pipeline training
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

      - name: Run promotion evaluation
        run: python scripts/promote_model.py --auto
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

      - name: Notify team
        uses: slackapi/slack-github-action@v1
        with:
          payload: '{"text":"🔄 Weekly retraining complete. Check MLflow for results."}'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 11. Testing Plan

### 11.1 Unit Tests — `tests/unit/`

| Test File | What It Tests |
|---|---|
| `test_data_sources.py` | `load()` and `validate()` for all three source types; dummy generator reproducibility |
| `test_features.py` | Each built-in transformer: fit, transform, output shape, feature names |
| `test_models.py` | Fit/predict interface for all model types with dummy data |
| `test_config.py` | Config loading, validation, and merging |
| `test_utils.py` | Shared utility functions |

### 11.2 Integration Tests — `tests/integration/`

| Test File | What It Tests |
|---|---|
| `test_training_pipeline.py` | Full train pipeline: dummy data → features → model → MLflow log |
| `test_inference_pipeline.py` | Batch inference: load production model → predict → write output |
| `test_feature_store.py` | Feature materialisation and retrieval from Feast |

### 11.3 API Tests — `tests/api/`

| Test | What It Tests |
|---|---|
| `test_health` | `/health` returns 200 |
| `test_predict_single` | `/predict` returns correct schema |
| `test_predict_batch` | `/predict` handles batch requests |
| `test_model_info` | `/model/info` returns model metadata |

### 11.4 Data Validation Tests — `tests/data/`

Using `pandera` schemas to assert:
- Required columns present (`timestamp`, `target`, `series_id`)
- No nulls in critical columns
- Timestamp monotonicity
- Target values within plausible range (configurable bounds)

### 11.5 Monitoring Tests — `tests/monitoring/`

- Evidently report generation does not raise on reference + current data.
- Drift flagged correctly when distributions are artificially shifted.
- Alert function is called when drift exceeds threshold.

---

## 12. Milestones & Delivery Phases

| Phase | Deliverable | Duration |
|---|---|---|
| **Phase 1** | Project scaffold, config system, data sources (all 3), dummy generator | Week 1 |
| **Phase 2** | Feature engineering framework, built-in transformers, Feature Store (Feast) | Week 2 |
| **Phase 3** | Model Zoo — Classical TS + ML models, BaseForecaster interface | Week 3 |
| **Phase 4** | MLflow integration, experiment tracking, DVC data versioning | Week 4 |
| **Phase 5** | Prefect pipeline orchestration, all core pipelines wired up | Week 5 |
| **Phase 6** | Model Registry, promotion gates, model serving (batch + FastAPI) | Week 6 |
| **Phase 7** | Deep Learning models (LSTM, NHiTS, TFT) | Week 7 |
| **Phase 8** | Drift monitoring (Evidently), alerting, retraining trigger | Week 8 |
| **Phase 9** | CI/CD GitHub Actions (all 3 workflows), full test suite | Week 9 |
| **Phase 10** | Documentation, README, end-to-end smoke test, cloud deployment guide | Week 10 |

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Deep learning models too slow for local training | Medium | Medium | Provide CPU-compatible fallbacks; optional GPU support via config |
| Feast complexity for simple local setups | Medium | Low | Abstract Feature Store behind `store_client.py`; provide SQLite-backed local mode |
| DVC remote misconfiguration breaks reproducibility | Low | High | CI validates DVC lock file on every PR |
| Model drift goes undetected without ground truth | Medium | High | Fall back to input data drift as a proxy signal |
| Config drift (code ≠ config) | Medium | Medium | Pydantic config validation at pipeline startup |
| Dependency conflicts between TS libraries | High | Medium | Pin all dependencies in `requirements.txt`; use isolated Docker environments |

---

## 14. Glossary

| Term | Definition |
|---|---|
| **DVC** | Data Version Control — open-source tool for versioning data, models, and ML pipelines |
| **MLflow** | Open-source platform for managing ML lifecycle: tracking, registry, serving |
| **Feast** | Open-source Feature Store for managing and serving ML features |
| **Prefect** | Modern workflow orchestration tool with a Python-native API |
| **Evidently** | Open-source ML monitoring tool for data and model drift detection |
| **PSI** | Population Stability Index — metric for measuring feature distribution shift |
| **Horizon** | Number of future time steps to forecast |
| **Feature View** | Feast concept: a logical group of features from a single data source |
| **Staging** | MLflow model stage: evaluated and candidate for production |
| **Production** | MLflow model stage: actively serving predictions |
| **Batch Inference** | Running predictions on a large dataset on a schedule |
| **Real-time Inference** | On-demand prediction via REST API with low latency |
| **MAPE** | Mean Absolute Percentage Error — common forecast accuracy metric |
| **SMAPE** | Symmetric MAPE — handles near-zero actuals better than MAPE |
| **TFT** | Temporal Fusion Transformer — attention-based deep learning forecasting model |
| **NHiTS** | Neural Hierarchical Interpolation for Time Series — efficient DL forecaster |

---

*End of Document — PRD v1.0.0*
