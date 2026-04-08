import pytest
import pandas as pd
from data_sources import DummyGenerator, OfflineCSVSource


class TestDummyGenerator:
    def test_load(self):
        """Test dummy data generation."""
        generator = DummyGenerator()
        config = {
            "n_series": 3,
            "n_timesteps": 50,
            "frequency": "D",
            "date_start": "2023-01-01",
            "random_seed": 42,
        }
        df = generator.load(config)

        assert len(df) == 3 * 50
        assert set(df.columns) == {"timestamp", "series_id", "target"}
        assert len(df["series_id"].unique()) == 3

    def test_validate_success(self):
        """Test validation passes for valid data."""
        generator = DummyGenerator()
        config = {
            "n_series": 2,
            "n_timesteps": 30,
            "frequency": "D",
            "random_seed": 42,
        }
        df = generator.load(config)
        assert generator.validate(df) is True

    def test_reproducibility(self):
        """Test deterministic output with same seed."""
        generator = DummyGenerator()
        config = {"n_series": 1, "n_timesteps": 10, "random_seed": 123}

        df1 = generator.load(config)
        df2 = generator.load(config)

        assert df1["target"].values.sum() == df2["target"].values.sum()
