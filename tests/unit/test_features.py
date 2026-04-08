import pytest
from features import LagFeatureTransformer, RollingStatTransformer, CalendarFeatureTransformer, FeatureRegistry


class TestLagFeatureTransformer:
    def test_fit_transform(self, sample_data):
        transformer = LagFeatureTransformer(lags=[1, 7])
        result = transformer.fit_transform(sample_data)
        assert "target_lag_1" in result.columns
        assert "target_lag_7" in result.columns

    def test_get_feature_names(self):
        transformer = LagFeatureTransformer(lags=[1, 7, 28])
        transformer.fit(None)
        names = transformer.get_feature_names()
        assert names == ["target_lag_1", "target_lag_7", "target_lag_28"]


class TestFeatureRegistry:
    def test_build_pipeline(self):
        config = [
            {"name": "LagFeatureTransformer", "params": {"lags": [1, 7]}},
            {"name": "CalendarFeatureTransformer", "params": {}},
        ]
        pipeline = FeatureRegistry.build_pipeline(config)
        assert len(pipeline) == 2

    def test_unknown_transformer(self):
        with pytest.raises(ValueError, match="not found in registry"):
            FeatureRegistry.get("UnknownTransformer")
