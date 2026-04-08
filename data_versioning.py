"""Data versioning and reproducibility tracking module.

This module tracks data versions using content hashes, integrates with DVC,
and enables reproducible experiments by capturing exact data lineage.

For production use, combine with DVC for data file management:
1. dvc add data/raw_data.csv        # Track data with DVC
2. dvc remote add s3remote s3://...  # Configure remote storage
3. dvc push                          # Push data to remote
4. Later: dvc pull                   # Restore exact data
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from mlflow import get_run, log_dict, log_params, log_param, set_tag


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Compute hash of a file for versioning.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (sha256, md5, etc.)

    Returns:
        Hex digest of the file hash
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_dataframe_hash(df: pd.DataFrame, algorithm: str = "sha256") -> str:
    """Compute hash of a DataFrame for versioning.

    Args:
        df: Pandas DataFrame
        algorithm: Hash algorithm

    Returns:
        Hex digest of the DataFrame hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return hasher.hexdigest()


class DataVersionTracker:
    """Track data versions and lineage for reproducibility."""

    def __init__(self, project_root: str = "."):
        """Initialize the tracker.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.metadata_dir = self.project_root / ".dvc_metadata"
        self.metadata_dir.mkdir(exist_ok=True)

    def track_training_data(
        self,
        data: pd.DataFrame,
        name: str,
        split: str = "train",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track training data version.

        Args:
            data: Training DataFrame
            name: Dataset name
            split: Data split (train/test/val)
            metadata: Additional metadata

        Returns:
            Data version info including hash and timestamp
        """
        data_hash = compute_dataframe_hash(data)
        timestamp = datetime.now().isoformat()

        version_info = {
            "name": name,
            "split": split,
            "hash": data_hash,
            "timestamp": timestamp,
            "shape": data.shape,
            "columns": list(data.columns),
            "rows": len(data),
            "metadata": metadata or {},
        }

        # Save version metadata
        version_file = (
            self.metadata_dir / f"{name}_{split}_{data_hash[:8]}.json"
        )
        with open(version_file, "w") as f:
            json.dump(version_info, f, indent=2)

        return version_info

    def track_external_data(
        self,
        file_path: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track external data file version.

        For production use, also track with DVC:
            dvc add data/raw_data.csv
            dvc remote add s3remote s3://bucket/path
            dvc push

        Args:
            file_path: Path to data file
            name: Dataset name
            metadata: Additional metadata

        Returns:
            Data version info including file hash
        """
        file_hash = compute_file_hash(file_path)
        timestamp = datetime.now().isoformat()
        file_size = os.path.getsize(file_path)
        
        # Check if file is DVC-tracked
        dvc_tracked = self._is_dvc_tracked(file_path)

        version_info = {
            "name": name,
            "file_path": str(file_path),
            "hash": file_hash,
            "timestamp": timestamp,
            "size_bytes": file_size,
            "dvc_tracked": dvc_tracked,
            "metadata": metadata or {},
        }

        # Save version metadata
        version_file = (
            self.metadata_dir / f"{name}_{file_hash[:8]}.json"
        )
        with open(version_file, "w") as f:
            json.dump(version_info, f, indent=2)

        return version_info

    def _is_dvc_tracked(self, file_path: str) -> bool:
        """Check if file is tracked by DVC.

        Args:
            file_path: Path to file

        Returns:
            True if file is DVC-tracked, False otherwise
        """
        dvc_file = f"{file_path}.dvc"
        return os.path.exists(dvc_file)

    def log_data_lineage(
        self,
        run_id: str,
        datasets: Dict[str, Dict[str, Any]],
        code_version: Optional[str] = None,
    ) -> None:
        """Log data lineage to MLflow run.

        Args:
            run_id: MLflow run ID
            datasets: Dictionary of dataset versions
            code_version: Git commit hash (optional)
        """
        run = get_run(run_id)

        # Log data versions as parameters
        for dataset_name, version_info in datasets.items():
            data_hash = version_info.get("hash", "unknown")
            log_param(f"data_{dataset_name}_hash", data_hash)
            log_param(f"data_{dataset_name}_timestamp",
                     version_info.get("timestamp", "unknown"))

        # Log code version if available
        if code_version:
            log_param("code_version", code_version)

        # Log complete lineage as artifact
        lineage = {
            "timestamp": datetime.now().isoformat(),
            "datasets": datasets,
            "code_version": code_version,
        }
        log_dict(lineage, "data_lineage.json")

        # Tag for easy filtering
        set_tag("reproducible", "true")


class ExperimentReproducer:
    """Reproduce experiments using exact data/code versions."""

    def __init__(self, project_root: str = "."):
        """Initialize the reproducer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.metadata_dir = self.project_root / ".dvc_metadata"

    def get_experiment_metadata(self, run_id: str) -> Dict[str, Any]:
        """Get metadata for an experiment to reproduce it.

        Args:
            run_id: MLflow run ID

        Returns:
            Experiment metadata including data versions and code version
        """
        run = get_run(run_id)
        params = run.data.params

        metadata = {
            "run_id": run_id,
            "timestamp": run.info.start_time,
            "data_versions": {},
            "code_version": params.get("code_version"),
            "model_params": {k: v for k, v in params.items()
                            if not k.startswith("data_")},
        }

        # Extract data versions from params
        for key, value in params.items():
            if key.startswith("data_") and key.endswith("_hash"):
                dataset_name = key.replace("data_", "").replace("_hash", "")
                metadata["data_versions"][dataset_name] = value

        return metadata

    def get_reproduction_instructions(
        self,
        run_id: str,
    ) -> str:
        """Generate instructions to reproduce an experiment.

        Args:
            run_id: MLflow run ID

        Returns:
            Instructions for reproducing the experiment
        """
        metadata = self.get_experiment_metadata(run_id)

        instructions = f"""
To reproduce experiment {run_id}:

1. Checkout code version:
   git checkout {metadata['code_version']}

2. Data versions used:
"""
        for dataset, data_hash in metadata["data_versions"].items():
            instructions += f"   - {dataset}: {data_hash}\n"

        instructions += f"""
3. For production data restoration:
   
   If data was tracked with DVC (dvc add data/raw_data.csv):
   
   a) Configure DVC remote if not already done:
      dvc remote add myremote s3://bucket/path  # or other storage
   
   b) Pull the exact data used:
      dvc pull
   
   c) This restores files to match the data hashes above
   
   Note: Data files (.dvc files) must be committed to git

4. Run training with same configuration:
   python3 train.py --experiment-id {run_id}

Note: The exact data versions and code commit ensure reproducible results.
"""
        return instructions

    def restore_data_from_dvc(self, force: bool = False) -> bool:
        """Restore data from DVC remote.

        Args:
            force: Force restore even if files exist

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ["dvc", "pull"]
            if force:
                cmd.append("--force")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            print("✓ Data restored from DVC remote")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to restore data from DVC: {e.stderr}")
            return False
        except FileNotFoundError:
            print("⚠ DVC not installed or not in PATH")
            return False


def get_git_commit_hash(repo_path: str = ".") -> Optional[str]:
    """Get current git commit hash.

    Args:
        repo_path: Path to git repository

    Returns:
        Git commit hash or None if not a git repo
    """
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None
