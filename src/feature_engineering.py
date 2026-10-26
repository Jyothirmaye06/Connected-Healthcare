"""
Feature engineering module for Connected Healthcare.
Builds time-based features, chronological lag features, rolling windows,
and future prediction targets without lookahead leakage.
"""

import pandas as pd
from typing import Tuple, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FEATURE_COLUMNS, ANOMALY_FEATURE_COLUMNS


def prepare_features(df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
    """
    Constructs all model features strictly using current and past observations.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw dataframe containing hospital crowd observations.
    is_training : bool
        If True, also generates the future targets ('next_crowd', 'next_waiting_minutes')
        via shift(-1) and drops rows with missing targets or lags.
        If False (inference mode), constructs features for current observation.
    
    Returns:
    --------
    pd.DataFrame
        Engineered dataframe.
    """
    df = df.copy()

    # Ensure chronological datetime order
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df = df.sort_values(["hospital", "recorded_at"]).reset_index(drop=True)

    # 1. Time-based features
    df["hour"] = df["recorded_at"].dt.hour
    df["day_of_week"] = df["recorded_at"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # 2. Historical crowd features (strictly past observations: shift(1))
    df["previous_crowd"] = df.groupby("hospital")["people_waiting"].shift(1)

    # 3. Rolling 3-period average of past crowd (strictly past: shift(1))
    df["rolling_avg_3"] = (
        df.groupby("hospital")["people_waiting"]
        .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
    )

    # 4. Crowd change from immediate previous observation
    df["crowd_change"] = df["people_waiting"] - df["previous_crowd"]

    # 5. Crowd deviation from recent normal pattern (for anomaly detection)
    df["crowd_deviation"] = df["people_waiting"] - df["rolling_avg_3"]

    # Fill initial missing lag for first observation gracefully
    # For inference on single-row or cold start:
    df["previous_crowd"] = df["previous_crowd"].fillna(df["people_waiting"])
    df["rolling_avg_3"] = df["rolling_avg_3"].fillna(df["people_waiting"])
    df["crowd_change"] = df["crowd_change"].fillna(0.0)
    df["crowd_deviation"] = df["crowd_deviation"].fillna(0.0)

    if is_training:
        # Future targets (next observation for the same hospital)
        df["next_crowd"] = df.groupby("hospital")["people_waiting"].shift(-1)
        df["next_waiting_minutes"] = df.groupby("hospital")["waiting_minutes"].shift(-1)

        # Drop the last observation of each hospital because its target does not exist yet
        df = df.dropna(subset=["next_crowd", "next_waiting_minutes"]).copy()

    return df


def split_chronological(
    df: pd.DataFrame,
    test_ratio: float = 0.20
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Splits feature dataframe chronologically by recorded_at into train and test sets.
    Never shuffles across time, preventing future-to-past data leakage.
    """
    # Sort strictly by timestamp across all hospitals
    df = df.sort_values("recorded_at").reset_index(drop=True)

    split_idx = int(len(df) * (1.0 - test_ratio))

    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLUMNS]
    X_test = test_df[FEATURE_COLUMNS]

    y_crowd_train = train_df["next_crowd"]
    y_crowd_test = test_df["next_crowd"]

    y_wait_train = train_df["next_waiting_minutes"]
    y_wait_test = test_df["next_waiting_minutes"]

    return (
        train_df,
        test_df,
        X_train,
        X_test,
        y_crowd_train,
        y_crowd_test,
        y_wait_train,
        y_wait_test,
    )
