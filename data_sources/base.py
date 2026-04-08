from abc import ABC, abstractmethod
import pandas as pd


class BaseDataSource(ABC):
    """Abstract base class for all data sources."""

    @abstractmethod
    def load(self, config: dict) -> pd.DataFrame:
        """Load raw data from the source."""
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the loaded data."""
        pass
