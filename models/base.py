from abc import ABC, abstractmethod
import pandas as pd


class BaseForecaster(ABC):
    """Abstract base class for time series forecasters."""

    @abstractmethod
    def fit(self, train: pd.DataFrame, config: dict) -> None:
        pass

    @abstractmethod
    def predict(self, horizon: int, features: pd.DataFrame = None) -> pd.DataFrame:
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "BaseForecaster":
        pass
