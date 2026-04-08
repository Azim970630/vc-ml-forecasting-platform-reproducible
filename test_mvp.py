#!/usr/bin/env python3
"""Quick test of the MVP."""

import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import load_config
from pipelines.training import run_training_pipeline


def main():
    """Test the training pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = load_config()
        config['paths']['models_dir'] = str(Path(tmpdir) / 'models')
        config['paths']['outputs_dir'] = str(Path(tmpdir) / 'outputs')
        config['mlflow']['tracking_uri'] = str(Path(tmpdir) / 'mlruns')
        config['data']['dummy']['n_timesteps'] = 50
        config['data']['dummy']['n_series'] = 2

        print('Running training pipeline...')
        result = run_training_pipeline(config)

        print(f'\n✅ Training complete!')
        print(f'Train size: {result["train_size"]}')
        print(f'Test size: {result["test_size"]}')
        print(f'Metrics: {result["metrics"]}')
        print(f'Model saved to: {result["model_path"]}')


if __name__ == "__main__":
    main()
