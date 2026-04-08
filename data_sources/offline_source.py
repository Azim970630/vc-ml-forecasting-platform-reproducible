import pandas as pd
from pathlib import Path
from data_sources.base import BaseDataSource


class OfflineCSVSource(BaseDataSource):
    """Loads time series data from offline CSV files."""

    def load(self, config: dict) -> pd.DataFrame:
        """Load data from CSV file."""
        file_path = config.get("file_path")
        if not file_path:
            raise ValueError("file_path is required in config")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        df = pd.read_csv(file_path)

        datetime_col = config.get("datetime_column", "timestamp")
        target_col = config.get("target_column", "target")
        series_col = config.get("series_id_column", "series_id")

        df = df.rename(columns={
            datetime_col: "timestamp",
            target_col: "target",
            series_col: "series_id",
        })

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[["timestamp", "series_id", "target"]].copy()

        self.validate(df)
        return df

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the loaded data."""
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
