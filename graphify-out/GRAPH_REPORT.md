# Graph Report - .  (2026-04-11)

## Corpus Check
- Corpus is ~26,468 words - fits in a single context window. You may not need a graph.

## Summary
- 225 nodes · 226 edges · 61 communities detected
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `BaseForecaster` - 13 edges
2. `BaseFeatureTransformer` - 12 edges
3. `ExperimentReproducer` - 11 edges
4. `BaseDataSource` - 11 edges
5. `RollingStatTransformer` - 10 edges
6. `CalendarFeatureTransformer` - 10 edges
7. `LagFeatureTransformer` - 10 edges
8. `ARIMAForecaster` - 10 edges
9. `LightGBMForecaster` - 10 edges
10. `DataVersionTracker` - 8 edges

## Surprising Connections (you probably didn't know these)
- `End-to-end training pipeline with data versioning.` --uses--> `DataVersionTracker`  [INFERRED]
  pipelines/training.py → data_versioning.py
- `Script to reproduce a specific experiment with exact code/data/model versions.` --uses--> `ExperimentReproducer`  [INFERRED]
  reproduce_experiment.py → data_versioning.py
- `Checkout specific git commit.      Args:         commit_hash: Git commit hash` --uses--> `ExperimentReproducer`  [INFERRED]
  reproduce_experiment.py → data_versioning.py
- `Restore specific data version using DVC.      Args:         data_hash: Data vers` --uses--> `ExperimentReproducer`  [INFERRED]
  reproduce_experiment.py → data_versioning.py
- `Reproduce an experiment with exact versions.      Args:         run_id: MLflow r` --uses--> `ExperimentReproducer`  [INFERRED]
  reproduce_experiment.py → data_versioning.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (10): BaseFeatureTransformer, BaseFeatureTransformer, CalendarFeatureTransformer, Creates calendar-based features from timestamps., LagFeatureTransformer, Creates lagged target features., FeatureRegistry, Registry for feature transformers. (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (12): ARIMAForecaster, Fit ARIMA models for each series., Make multi-step ahead predictions., ARIMA-based time series forecaster., BaseForecaster, BaseForecaster, LightGBMForecaster, Fit the LightGBM model. (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (17): ExperimentReproducer, get_git_commit_hash(), Data versioning and reproducibility tracking module.  This module tracks data ve, Reproduce experiments using exact data/code versions., Initialize the reproducer.          Args:             project_root: Root directo, Get metadata for an experiment to reproduce it.          Args:             run_i, Generate instructions to reproduce an experiment.          Args:             run, Restore data from DVC remote.          Args:             force: Force restore ev (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (12): Run batch inference on new data., run_batch_inference(), load_config(), Load all configuration files., main(), Test the training pipeline., End-to-end training pipeline with data versioning., run_training_pipeline() (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (11): BaseDataSource, Abstract base class for time series forecasters., BaseDataSource, DummyGenerator, Generate synthetic time series data., Validate the generated data., Generates synthetic time series data., OfflineCSVSource (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (11): compute_dataframe_hash(), compute_file_hash(), DataVersionTracker, Track external data file version.          For production use, also track with D, Check if file is tracked by DVC.          Args:             file_path: Path to f, Log data lineage to MLflow run.          Args:             run_id: MLflow run ID, Compute hash of a file for versioning.      Args:         file_path: Path to the, Compute hash of a DataFrame for versioning.      Args:         df: Pandas DataFr (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (3): ABC, fit(), transform()

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (4): Test validation passes for valid data., Test deterministic output with same seed., Test dummy data generation., TestDummyGenerator

### Community 8 - "Community 8"
Cohesion: 0.29
Nodes (2): getCellValue(), rowComparator()

### Community 9 - "Community 9"
Cohesion: 0.29
Nodes (6): config(), featured_data(), Create sample data with features., Default configuration for testing., Create sample time series data for testing., sample_data()

### Community 10 - "Community 10"
Cohesion: 0.29
Nodes (2): TestLightGBMForecaster, TestModelRegistry

### Community 11 - "Community 11"
Cohesion: 0.29
Nodes (2): TestFeatureRegistry, TestLagFeatureTransformer

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (2): build_pipeline(), get()

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (2): Test full training pipeline with dummy data., test_training_pipeline_with_dummy_data()

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Load raw data from the source.

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Validate the loaded data.

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Data Versioning System

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Code Versioning via Git

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): MLflow Experiment Tracking

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): ExperimentReproducer Class

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): DataVersionTracker Class

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): SHA-256 Content Hashing

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): DVC Integration for Data Restoration

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Three-Layer Reproducibility Architecture

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Feature Engineering Pipeline

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Training Pipeline with Versioning

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Data Sources Registry Pattern

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Feature Registry Pattern

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Model Registry Pattern

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): LightGBM Forecaster Model

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): ARIMA Forecaster Model

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Lag Feature Transformer

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Rolling Statistics Transformer

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Calendar Feature Transformer

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Offline CSV Data Source

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Docker Deployment Strategy

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Cloud Deployment (AWS, GCP, Azure)

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): ML Governance and Auditing

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Custom Feature Development Pattern

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (1): Custom Model Development Pattern

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): Custom Data Source Development Pattern

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): Comprehensive Test Suite

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): End-to-End Testing

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): Reproducibility Verification Workflow

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): Audit Trail and Lineage

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): MLflow Model Registry

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Monitoring and Logging

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): DVC Remote Storage Configuration

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Cost Optimization for Cloud Storage

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Data Lineage JSON Artifact

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): DVC Metadata Storage (.dvc_metadata/)

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Rationale: Why SHA-256 Hashing

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Rationale: Why Store Metadata as JSON

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Rationale: Why MLflow Parameters for Data Versions

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Rationale: Why Data Lineage as Artifact

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Registry Design Pattern

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Abstract Base Class Pattern

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Composition Pattern for Pipelines

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Python Dependencies (requirements.txt)

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Development Dependencies (requirements-dev.txt)

## Knowledge Gaps
- **73 isolated node(s):** `Test the training pipeline.`, `Load all configuration files.`, `Data versioning and reproducibility tracking module.  This module tracks data ve`, `Compute hash of a file for versioning.      Args:         file_path: Path to the`, `Compute hash of a DataFrame for versioning.      Args:         df: Pandas DataFr` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Load raw data from the source.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Validate the loaded data.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `Data Versioning System`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Code Versioning via Git`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `MLflow Experiment Tracking`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `ExperimentReproducer Class`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `DataVersionTracker Class`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `SHA-256 Content Hashing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `DVC Integration for Data Restoration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Three-Layer Reproducibility Architecture`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Feature Engineering Pipeline`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Training Pipeline with Versioning`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Data Sources Registry Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Feature Registry Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Model Registry Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `LightGBM Forecaster Model`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `ARIMA Forecaster Model`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Lag Feature Transformer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Rolling Statistics Transformer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Calendar Feature Transformer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Offline CSV Data Source`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Docker Deployment Strategy`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Cloud Deployment (AWS, GCP, Azure)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `ML Governance and Auditing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Custom Feature Development Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `Custom Model Development Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `Custom Data Source Development Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Comprehensive Test Suite`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `End-to-End Testing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `Reproducibility Verification Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `Audit Trail and Lineage`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `MLflow Model Registry`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Monitoring and Logging`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `DVC Remote Storage Configuration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Cost Optimization for Cloud Storage`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Data Lineage JSON Artifact`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `DVC Metadata Storage (.dvc_metadata/)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Rationale: Why SHA-256 Hashing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Rationale: Why Store Metadata as JSON`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Rationale: Why MLflow Parameters for Data Versions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Rationale: Why Data Lineage as Artifact`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Registry Design Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Abstract Base Class Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Composition Pattern for Pipelines`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Python Dependencies (requirements.txt)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Development Dependencies (requirements-dev.txt)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseFeatureTransformer` connect `Community 0` to `Community 4`, `Community 6`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `BaseForecaster` connect `Community 1` to `Community 4`, `Community 6`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `BaseDataSource` connect `Community 4` to `Community 6`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `BaseForecaster` (e.g. with `ModelRegistry` and `Registry for model types.`) actually correct?**
  _`BaseForecaster` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `BaseFeatureTransformer` (e.g. with `FeatureRegistry` and `Registry for feature transformers.`) actually correct?**
  _`BaseFeatureTransformer` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ExperimentReproducer` (e.g. with `Script to reproduce a specific experiment with exact code/data/model versions.` and `Checkout specific git commit.      Args:         commit_hash: Git commit hash`) actually correct?**
  _`ExperimentReproducer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `BaseDataSource` (e.g. with `DummyGenerator` and `Generates synthetic time series data.`) actually correct?**
  _`BaseDataSource` has 8 INFERRED edges - model-reasoned connections that need verification._