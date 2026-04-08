import pickle
import pandas as pd
import numpy as np
import lightgbm as lgb
from models.base import BaseForecaster


class LightGBMForecaster(BaseForecaster):
    """LightGBM-based time series forecaster."""

    def __init__(self):
        self.model = None
        self.feature_names_ = None
        self.target_col = "target"

    def fit(self, train: pd.DataFrame, config: dict) -> None:
        """Fit the LightGBM model."""
        hyperparams = config.get("lightgbm", {})

        feature_cols = [col for col in train.columns if col not in ["target", "timestamp", "series_id"]]
        X = train[feature_cols].fillna(0)
        y = train[self.target_col]

        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]

        if len(X) == 0:
            raise ValueError("No valid training data after removing NaNs")

        self.feature_names_ = feature_cols
        self.model = lgb.LGBMRegressor(**hyperparams)
        self.model.fit(X, y)

    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame:
        """Make predictions using the fitted model."""
        if self.model is None:
            raise ValueError("Model not fitted yet. Call fit() first.")

        if features is None:
            raise ValueError("features DataFrame is required for LightGBM predictions")

        X = features[self.feature_names_].fillna(0)
        predictions = self.model.predict(X)

        result = features[["timestamp", "series_id"]].copy()
        result["prediction"] = predictions

        return result

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> "LightGBMForecaster":
        with open(path, "rb") as f:
            return pickle.load(f)
