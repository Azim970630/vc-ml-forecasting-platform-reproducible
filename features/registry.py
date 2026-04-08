import pandas as pd
from features.base import BaseFeatureTransformer
from features.built_in.lag_features import LagFeatureTransformer
from features.built_in.rolling_stats import RollingStatTransformer
from features.built_in.calendar_features import CalendarFeatureTransformer


class FeatureRegistry:
    """Registry for feature transformers."""

    _registry = {
        "LagFeatureTransformer": LagFeatureTransformer,
        "RollingStatTransformer": RollingStatTransformer,
        "CalendarFeatureTransformer": CalendarFeatureTransformer,
    }

    @classmethod
    def get(cls, name: str) -> BaseFeatureTransformer:
        if name not in cls._registry:
            raise ValueError(f"Transformer '{name}' not found in registry")
        return cls._registry[name]

    @classmethod
    def build_pipeline(cls, config_list: list) -> list:
        pipeline = []
        for config in config_list:
            name = config.get("name")
            params = config.get("params", {})
            transformer_class = cls.get(name)
            transformer = transformer_class(**params)
            pipeline.append(transformer)
        return pipeline

    @classmethod
    def apply_pipeline(cls, df: pd.DataFrame, pipeline: list) -> pd.DataFrame:
        result = df.copy()
        for transformer in pipeline:
            result = transformer.fit_transform(result)
        return result
