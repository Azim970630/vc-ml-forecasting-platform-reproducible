import pandas as pd
from pathlib import Path
from data_sources import DummyGenerator, OfflineCSVSource
from features import FeatureRegistry
from models import ModelRegistry
from config_loader import load_config


def run_batch_inference(config: dict = None, model_path: str = None) -> pd.DataFrame:
    """Run batch inference on new data."""
    if config is None:
        config = load_config()

    if model_path is None:
        models_dir = Path(config["paths"]["models_dir"])
        model_path = models_dir / f"{config['model']['type']}_model.pkl"

    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    print("Loading data for inference...")
    data_source_type = config["data"]["source"]
    if data_source_type == "dummy":
        source = DummyGenerator()
        raw_data = source.load(config["data"]["dummy"])
    elif data_source_type == "offline":
        source = OfflineCSVSource()
        raw_data = source.load(config["data"]["offline"])
    else:
        raise ValueError(f"Unknown data source: {data_source_type}")

    print("Engineering features...")
    feature_config = config.get("feature_pipeline", [])
    pipeline = FeatureRegistry.build_pipeline(feature_config)
    featured_data = FeatureRegistry.apply_pipeline(raw_data, pipeline)

    print(f"Loading model from {model_path}...")
    model_class = ModelRegistry.get(config["model"]["type"])
    model = model_class.load(str(model_path))

    print("Making predictions...")
    feature_cols = [col for col in featured_data.columns if col not in ["target", "timestamp", "series_id"]]
    inference_features = featured_data[["timestamp", "series_id"] + feature_cols].copy()

    predictions = model.predict(
        horizon=config["model"]["horizon"],
        features=inference_features
    )

    output_dir = Path(config["paths"]["outputs_dir"]) / "predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "batch_predictions.csv"

    predictions.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")

    return predictions


if __name__ == "__main__":
    predictions = run_batch_inference()
    print(f"\nInference complete!")
    print(f"Predictions shape: {predictions.shape}")
    print(f"\nFirst rows:\n{predictions.head()}")
