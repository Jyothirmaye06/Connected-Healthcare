"""
Unit tests for feature engineering and chronological train/test splitting.
Verifies strictly historical lags and absence of lookahead target leakage.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.feature_engineering import prepare_features, split_chronological


def test_prepare_features_lags_and_no_lookahead(sample_feature_df):
    """Verifies that previous_crowd and rolling_avg_3 use past observations only."""
    df_feat = prepare_features(sample_feature_df, is_training=False)

    hosp_a = df_feat[df_feat["hospital"] == "Hospital A"].reset_index(drop=True)

    # For index 0, lag falls back gracefully to current crowd
    assert hosp_a.loc[0, "previous_crowd"] == hosp_a.loc[0, "people_waiting"]

    # For index 1, previous_crowd MUST strictly equal index 0's people_waiting
    assert hosp_a.loc[1, "previous_crowd"] == hosp_a.loc[0, "people_waiting"]

    # For index 2, previous_crowd MUST strictly equal index 1's people_waiting
    assert hosp_a.loc[2, "previous_crowd"] == hosp_a.loc[1, "people_waiting"]

    # Crowd change check
    assert hosp_a.loc[1, "crowd_change"] == hosp_a.loc[1, "people_waiting"] - hosp_a.loc[1, "previous_crowd"]


def test_prepare_features_training_targets(sample_feature_df):
    """Verifies future target construction and dropping of terminal rows without targets."""
    df_train = prepare_features(sample_feature_df, is_training=True)

    # Each hospital has 10 samples originally. With shift(-1), the 10th row has no next target.
    # Therefore, training rows per hospital should be exactly 9 (18 total for 2 hospitals).
    assert len(df_train) == 18

    hosp_a = df_train[df_train["hospital"] == "Hospital A"].reset_index(drop=True)
    # Target next_crowd at index 0 must equal people_waiting at original index 1
    assert hosp_a.loc[0, "next_crowd"] == 32
    assert hosp_a.loc[0, "next_waiting_minutes"] == 43


def test_single_observation_graceful_handling():
    """Edge case: Single observation dataframe does not raise errors and fills lags safely."""
    single_row = pd.DataFrame([{
        "hospital": "Solo Hospital",
        "location": "Solo City",
        "people_waiting": 45,
        "waiting_minutes": 50,
        "new_patients": 5,
        "discharged_patients": 3,
        "emergency_cases": 0,
        "holiday": 0,
        "special_event": "None",
        "recorded_at": "2026-08-01 10:00:00"
    }])

    feat_df = prepare_features(single_row, is_training=False)
    assert len(feat_df) == 1
    assert feat_df.loc[0, "previous_crowd"] == 45
    assert feat_df.loc[0, "rolling_avg_3"] == 45
    assert feat_df.loc[0, "crowd_change"] == 0.0
    assert feat_df.loc[0, "crowd_deviation"] == 0.0


def test_split_chronological(sample_feature_df):
    """Verifies that train/test split maintains strict chronological boundary without shuffling."""
    df_feat = prepare_features(sample_feature_df, is_training=True)
    train_df, test_df, X_train, X_test, y_c_train, y_c_test, y_w_train, y_w_test = split_chronological(
        df_feat, test_ratio=0.30
    )

    assert len(train_df) + len(test_df) == len(df_feat)
    max_train_time = train_df["recorded_at"].max()
    min_test_time = test_df["recorded_at"].min()

    # Temporal boundary: all train timestamps must precede or equal earliest test timestamp
    assert max_train_time <= min_test_time
    assert len(X_train) == len(y_c_train)
    assert len(X_test) == len(y_c_test)
