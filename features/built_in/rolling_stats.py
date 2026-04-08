import pandas as pd
from features.base import BaseFeatureTransformer


class RollingStatTransformer(BaseFeatureTransformer):
    """Creates rolling statistics features."""

    def __init__(self, windows: list = None, stats: list = None):
        self.windows = windows or [7, 14]
        self.stats = stats or ["mean", "std"]
        self.feature_names_ = []

    def fit(self, df: pd.DataFrame) -> "RollingStatTransformer":
        self.feature_names_ = [
            f"target_rolling_{stat}_{window}"
            for window in self.windows
            for stat in self.stats
        ]
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        for window in self.windows:
            for stat in self.stats:
                col_name = f"target_rolling_{stat}_{window}"
                result[col_name] = result.groupby("series_id")["target"].transform(
                    lambda x: x.rolling(window=window, min_periods=1).agg(stat)
                )
        return result

    def get_feature_names(self) -> list:
        return self.feature_names_
