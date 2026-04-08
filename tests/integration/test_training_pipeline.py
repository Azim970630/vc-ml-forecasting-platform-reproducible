import pytest
import tempfile
from pathlib import Path
from pipelines.training import run_training_pipeline


def test_training_pipeline_with_dummy_data(config):
    """Test full training pipeline with dummy data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config["paths"]["models_dir"] = str(Path(tmpdir) / "models")
        config["paths"]["outputs_dir"] = str(Path(tmpdir) / "outputs")
        config["mlflow"]["tracking_uri"] = str(Path(tmpdir) / "mlruns")
        config["data"]["dummy"]["n_timesteps"] = 50
        config["data"]["dummy"]["n_series"] = 2
        
        # Add feature pipeline
        config["feature_pipeline"] = [
            {"name": "LagFeatureTransformer", "params": {"lags": [1, 7]}},
            {"name": "CalendarFeatureTransformer", "params": {}},
        ]

        result = run_training_pipeline(config)

        assert "model_path" in result
        assert "metrics" in result
        assert Path(result["model_path"]).exists()

        metrics = result["metrics"]
        assert "mae" in metrics
        assert metrics["mae"] >= 0
