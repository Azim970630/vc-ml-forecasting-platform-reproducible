import pandas as pd
from features.base import BaseFeatureTransformer


class LagFeatureTransformer(BaseFeatureTransformer):
    """Creates lagged target features."""

    def __init__(self, lags: list = None):
        self.lags = lags or [1, 7, 28]
        self.feature_names_ = []

    def fit(self, df: pd.DataFrame) -> "LagFeatureTransformer":
        self.feature_names_ = [f"target_lag_{lag}" for lag in self.lags]
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        for lag in self.lags:
            lag_col_name = f"target_lag_{lag}"
            result[lag_col_name] = result.groupby("series_id")["target"].shift(lag)
        return result

    def get_feature_names(self) -> list:
        return self.feature_names_
