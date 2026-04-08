from models.base import BaseForecaster
from models.ml.lightgbm_model import LightGBMForecaster
from models.classical.arima import ARIMAForecaster


class ModelRegistry:
    """Registry for model types."""

    _registry = {
        "lightgbm": LightGBMForecaster,
        "arima": ARIMAForecaster,
    }

    @classmethod
    def get(cls, name: str) -> BaseForecaster:
        if name not in cls._registry:
            raise ValueError(f"Model '{name}' not found in registry")
        return cls._registry[name]

    @classmethod
    def list_models(cls) -> list:
        return list(cls._registry.keys())
