import pandas as pd
import numpy as np
from data_sources.base import BaseDataSource


class DummyGenerator(BaseDataSource):
    """Generates synthetic time series data."""

    def load(self, config: dict) -> pd.DataFrame:
        """Generate synthetic time series data."""
        np.random.seed(config.get("random_seed", 42))

        n_series = config.get("n_series", 5)
        n_timesteps = config.get("n_timesteps", 365)
        frequency = config.get("frequency", "D")
        date_start = config.get("date_start", "2023-01-01")
        seasonality = config.get("seasonality", 12)
        trend = config.get("trend", True)
        noise_level = config.get("noise_level", 0.05)

        date_range = pd.date_range(start=date_start, periods=n_timesteps, freq=frequency)

        data = []
        for series_id in range(1, n_series + 1):
            t = np.arange(n_timesteps)
            target = 100 + (0.5 * t if trend else 0)
            target += 10 * np.sin(2 * np.pi * t / seasonality)
            target += np.random.normal(0, noise_level * 100, n_timesteps)
            target = np.maximum(target, 1)

            for idx, date in enumerate(date_range):
                data.append({
                    "timestamp": date,
                    "series_id": f"series_{series_id:02d}",
                    "target": target[idx],
                })

        df = pd.DataFrame(data)
        self.validate(df)
        return df

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the generated data."""
        required_cols = {"timestamp", "series_id", "target"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

        if df["timestamp"].isnull().any():
            raise ValueError("timestamp column has null values")

        if df["target"].isnull().any():
            raise ValueError("target column has null values")

        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            raise ValueError("timestamp column is not datetime")

        for series_id in df["series_id"].unique():
            series_df = df[df["series_id"] == series_id].reset_index(drop=True)
            if not series_df["timestamp"].is_monotonic_increasing:
                raise ValueError(f"timestamps not monotonic for {series_id}")

        return True
