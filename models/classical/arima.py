import pickle
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from models.base import BaseForecaster


class ARIMAForecaster(BaseForecaster):
    """ARIMA-based time series forecaster."""

    def __init__(self):
        self.models_ = {}
        self.order = None
        self.seasonal_order = None
        self.series_ids = None

    def fit(self, train: pd.DataFrame, config: dict) -> None:
        """Fit ARIMA models for each series."""
        arima_config = config.get("arima", {})
        self.order = tuple(arima_config.get("order", [1, 1, 1]))
        self.seasonal_order = tuple(arima_config.get("seasonal_order", [0, 0, 0, 0]))

        self.series_ids = train["series_id"].unique()

        for series_id in self.series_ids:
            series_data = train[train["series_id"] == series_id].sort_values("timestamp")
            y = series_data["target"].values
            y = y[~np.isnan(y)]

            if len(y) < max(self.order) + max(self.seasonal_order[:-1]) + 2:
                try:
                    model = ARIMA(y, order=(0, 1, 0))
                    fitted = model.fit()
                except Exception:
                    fitted = None
            else:
                try:
                    model = ARIMA(y, order=self.order, seasonal_order=self.seasonal_order)
                    fitted = model.fit()
                except Exception:
                    try:
                        model = ARIMA(y, order=(0, 1, 0))
                        fitted = model.fit()
                    except Exception:
                        fitted = None

            self.models_[series_id] = fitted

    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame:
        """Make multi-step ahead predictions."""
        if not self.models_:
            raise ValueError("Model not fitted yet. Call fit() first.")

        predictions = []

        for series_id in self.series_ids:
            model = self.models_.get(series_id)

            if model is None:
                pred_values = np.zeros(horizon)
            else:
                try:
                    forecast = model.get_forecast(steps=horizon)
                    pred_values = forecast.predicted_mean.values
                except Exception:
                    pred_values = np.zeros(horizon)

            for step, pred in enumerate(pred_values):
                predictions.append({
                    "series_id": series_id,
                    "step": step + 1,
                    "prediction": max(pred, 0),
                })

        return pd.DataFrame(predictions)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> "ARIMAForecaster":
        with open(path, "rb") as f:
            return pickle.load(f)
