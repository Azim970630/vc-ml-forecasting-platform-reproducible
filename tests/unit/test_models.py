import pytest
import tempfile
from pathlib import Path
from models import LightGBMForecaster, ARIMAForecaster, ModelRegistry


class TestLightGBMForecaster:
    def test_fit(self, featured_data, config):
        model = LightGBMForecaster()
        model.fit(featured_data, config["model"])
        assert model.model is not None

    def test_save_load(self, featured_data, config):
        model = LightGBMForecaster()
        model.fit(featured_data, config["model"])

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"
            model.save(str(model_path))
            assert model_path.exists()

            loaded_model = LightGBMForecaster.load(str(model_path))
            predictions = loaded_model.predict(horizon=7, features=featured_data)
            assert len(predictions) > 0


class TestModelRegistry:
    def test_get_lightgbm(self):
        model_class = ModelRegistry.get("lightgbm")
        assert model_class == LightGBMForecaster

    def test_unknown_model(self):
        with pytest.raises(ValueError, match="not found in registry"):
            ModelRegistry.get("unknown_model")
