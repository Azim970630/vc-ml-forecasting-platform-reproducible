import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_data():
    """Create sample time series data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    data = []

    for series_id in ["series_01", "series_02"]:
        for i, date in enumerate(dates):
            data.append({
                "timestamp": date,
                "series_id": series_id,
                "target": 100 + i + np.random.normal(0, 5),
            })

    return pd.DataFrame(data)


@pytest.fixture
def featured_data(sample_data):
    """Create sample data with features."""
    df = sample_data.copy()
    df["target_lag_1"] = df.groupby("series_id")["target"].shift(1)
    df["target_lag_7"] = df.groupby("series_id")["target"].shift(7)
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    return df.fillna(0)


@pytest.fixture
def config():
    """Default configuration for testing."""
    return {
        "mlflow": {
            "tracking_uri": "./mlruns",
            "experiment_name": "test-experiment",
            "run_name": "test-run",
        },
        "paths": {
            "data_dir": "data/",
            "models_dir": "models/",
            "outputs_dir": "outputs/",
        },
        "model": {
            "type": "lightgbm",
            "horizon": 7,
            "frequency": "D",
            "lightgbm": {
                "n_estimators": 10,
                "learning_rate": 0.05,
            },
            "training": {
                "test_size": 0.2,
                "random_seed": 42,
            },
        },
        "data": {
            "source": "dummy",
            "dummy": {
                "n_series": 2,
                "n_timesteps": 100,
                "frequency": "D",
                "seasonality": 12,
                "trend": True,
                "random_seed": 42,
            },
        },
    }
