from abc import ABC, abstractmethod
import pandas as pd


class BaseFeatureTransformer(ABC):
    """Abstract base class for feature transformers."""

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "BaseFeatureTransformer":
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_feature_names(self) -> list:
        pass

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
