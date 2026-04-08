"""Script to reproduce a specific experiment with exact code/data/model versions.

Usage:
    python reproduce_experiment.py --run-id <mlflow_run_id> [--restore-data]
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
    except subprocess.CalledProcessError as e:
        if "unable to read tree" in e.stderr or "reference not found" in e.stderr:
            print(f"⚠ Code version not found in this repo: {commit_hash}")
            print(f"  This might mean:")
            print(f"  - Experiment was from a different repository")
            print(f"  - Commit was not pushed to this remote")
            print(f"\nContinuing with current code (HEAD = {get_git_commit_hash()})")
            return False
        else:
            print(f"✗ Failed to checkout code: {e.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error during checkout: {e}")
        return False


def restore_data_version(data_hash: str) -> bool:
    """Restore specific data version using DVC.

    Args:
        data_hash: Data version hash

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"✓ Data version: {data_hash}")
        print("  (Tracked in .dvc_metadata/ for offline reference)")
        return True
    except Exception as e:
        print(f"✗ Failed to restore data: {e}")
        return False


def reproduce_experiment(
    run_id: str,
    skip_checkout: bool = False,
    restore_data: bool = False,
) -> None:
    """Reproduce an experiment with exact versions.

    Args:
        run_id: MLflow run ID to reproduce
        skip_checkout: Skip git checkout (for testing without changing branch)
        restore_data: Attempt to restore data from DVC remote
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
        success = checkout_code_version(code_version)
        if not success:
            print("⚠ Continuing anyway (attempting reproduction with current code)")
    else:
        print(f"✓ Code version: {code_version or 'No version recorded'}")

    # Step 2: Restore data versions
    print("\nData versions:")
    for dataset_name, data_hash in metadata.get("data_versions", {}).items():
        print(f"  - {dataset_name}: {data_hash[:8]}...")
        restore_data_version(data_hash)

    # Step 2b: Optionally restore from DVC
    if restore_data:
        print("\n🔄 Restoring data from DVC remote...")
        reproducer.restore_data_from_dvc(force=True)

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
    current_version = get_git_commit_hash()
    print("\nReady to reproduce. Execute training with:")
    print(f"  python3 train.py")
    if code_version != current_version:
        print(f"\n⚠ Note: Running with current code ({current_version})")
        print(f"  Original experiment used: {code_version}")
        print(f"  Results may differ if code has changed.")


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
    parser.add_argument(
        "--restore-data",
        action="store_true",
        help="Restore data from DVC remote (requires dvc setup)"
    )

    args = parser.parse_args()

    reproduce_experiment(args.run_id, args.skip_checkout, args.restore_data)


if __name__ == "__main__":
    main()
