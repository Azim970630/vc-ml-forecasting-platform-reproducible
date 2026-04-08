import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute forecast evaluation metrics."""
    valid_idx = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[valid_idx]
    y_pred = y_pred[valid_idx]

    if len(y_true) == 0:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "smape": np.nan}

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mask = y_true != 0
    if mask.any():
        mape = 100 * np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))
    else:
        mape = np.nan

    smape = 100 * 2 * np.mean(
        np.abs(y_pred - y_true) / (np.abs(y_pred) + np.abs(y_true) + 1e-8)
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape) if not np.isnan(mape) else 0,
        "smape": float(smape),
    }


def split_train_test(df: pd.DataFrame, test_size: float = 0.2) -> tuple:
    """Split data by series_id."""
    train_dfs = []
    test_dfs = []

    for series_id in df["series_id"].unique():
        series_df = df[df["series_id"] == series_id].sort_values("timestamp").reset_index(drop=True)
        split_idx = int(len(series_df) * (1 - test_size))

        train_dfs.append(series_df[:split_idx])
        test_dfs.append(series_df[split_idx:])

    train = pd.concat(train_dfs, ignore_index=True)
    test = pd.concat(test_dfs, ignore_index=True)

    return train, test
