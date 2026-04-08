import yaml
from pathlib import Path


def load_config(config_dir: str = "config") -> dict:
    """Load all configuration files."""
    config_dir = Path(config_dir)
    merged_config = {}

    for config_file in sorted(config_dir.glob("*.yaml")):
        with open(config_file) as f:
            file_config = yaml.safe_load(f) or {}
            merged_config.update(file_config)

    return merged_config
