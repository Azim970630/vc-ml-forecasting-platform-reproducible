#!/usr/bin/env python3
"""Training script that logs to MLflow."""

import sys
from config_loader import load_config
from pipelines.training import run_training_pipeline

if __name__ == "__main__":
    config = load_config()
    
    # Update paths to use local mlruns
    config['mlflow']['tracking_uri'] = "./mlruns"
    
    print("Running training pipeline with MLflow tracking...")
    result = run_training_pipeline(config)
    
    print(f"\n✅ Training complete!")
    print(f"   MAE: {result['metrics']['mae']:.2f}")
    print(f"   RMSE: {result['metrics']['rmse']:.2f}")
    print(f"   Model: {result['model_path']}")
    print(f"\nView results in MLflow: mlflow ui")
