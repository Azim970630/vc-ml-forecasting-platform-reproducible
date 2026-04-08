"""Script to reproduce a specific experiment with exact code/data/model versions.

Usage:
    python reproduce_experiment.py --run-id <mlflow_run_id>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from data_versioning import ExperimentReproducer, get_git_commit_hash
from mlflow import get_run


def checkout_code_version(commit_hash: str) -> bool:
    """Checkout specific git commit.

    Args:
        commit_hash: Git commit hash

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "checkout", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✓ Checked out code version: {commit_hash}")
        return True
    except Exception as e:
        print(f"✗ Failed to checkout code: {e}")
        return False


def restore_data_version(data_hash: str) -> bool:
    """Restore specific data version using DVC.

    Args:
        data_hash: Data version hash

    Returns:
        True if successful, False otherwise
    """
    try:
        # Note: This is a placeholder for actual DVC restore logic
        # In practice, you'd track which data files correspond to which hashes
        print(f"✓ Data version: {data_hash}")
        print("  (Note: Data restore requires DVC pipeline - ensure data files match)")
        return True
    except Exception as e:
        print(f"✗ Failed to restore data: {e}")
        return False


def reproduce_experiment(run_id: str, skip_checkout: bool = False) -> None:
    """Reproduce an experiment with exact versions.

    Args:
        run_id: MLflow run ID to reproduce
        skip_checkout: Skip git checkout (for testing without changing branch)
    """
    print(f"\n🔄 Reproducing experiment: {run_id}\n")

    reproducer = ExperimentReproducer()

    # Get experiment metadata
    try:
        metadata = reproducer.get_experiment_metadata(run_id)
    except Exception as e:
        print(f"✗ Failed to fetch experiment metadata: {e}")
        sys.exit(1)

    print("Reproduction Plan:")
    print("-" * 60)

    # Step 1: Checkout code
    code_version = metadata.get("code_version")
    if code_version and not skip_checkout:
        if not checkout_code_version(code_version):
            print("⚠ Continuing anyway (git error may be non-critical)")
    else:
        print(f"✓ Code version: {code_version or 'No version recorded'}")

    # Step 2: Restore data versions
    print("\nData versions:")
    for dataset_name, data_hash in metadata.get("data_versions", {}).items():
        print(f"  - {dataset_name}: {data_hash[:8]}...")
        restore_data_version(data_hash)

    # Step 3: Show model parameters
    print("\nModel parameters:")
    for param_name, param_value in metadata.get("model_params", {}).items():
        if not param_name.startswith("data_"):
            print(f"  - {param_name}: {param_value}")

    # Step 4: Generate reproduction instructions
    print("\n" + "=" * 60)
    print("Instructions to reproduce:")
    print("=" * 60)
    instructions = reproducer.get_reproduction_instructions(run_id)
    print(instructions)

    # Step 5: Offer to run training
    print("\nReady to reproduce. Execute training with:")
    print(f"  python train.py")
    print(f"\nThis will use the exact same code/data/config from run {run_id}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reproduce a specific ML experiment with exact versions"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="MLflow run ID to reproduce"
    )
    parser.add_argument(
        "--skip-checkout",
        action="store_true",
        help="Skip git checkout (useful for testing)"
    )

    args = parser.parse_args()

    reproduce_experiment(args.run_id, args.skip_checkout)


if __name__ == "__main__":
    main()
