"""
Anomaly detection and operational status determination module.
Uses pre-trained Isolation Forest models to flag multi-variable operational anomalies
and applies a transparent rule-based layer to generate human-readable status explanations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    ANOMALY_MODELS_PATH,
    ANOMALY_FEATURE_COLUMNS,
    ISOLATION_FOREST_PARAMS,
    STATUS_THRESHOLDS,
)
from src.feature_engineering import prepare_features

_ANOMALY_MODELS_CACHE = {}


def load_anomaly_models(force_reload: bool = False) -> Dict[str, IsolationForest]:
    """
    Loads pre-trained hospital-specific Isolation Forest models.
    Caches models in memory to avoid repeated disk reads.
    """
    global _ANOMALY_MODELS_CACHE

    if not force_reload and _ANOMALY_MODELS_CACHE:
        return _ANOMALY_MODELS_CACHE

    if not ANOMALY_MODELS_PATH.exists():
        return {}

    models_dict = joblib.load(ANOMALY_MODELS_PATH)
    _ANOMALY_MODELS_CACHE = models_dict
    return _ANOMALY_MODELS_CACHE


def evaluate_observation_anomaly(
    hospital_name: str,
    row: pd.Series
) -> Tuple[int, float]:
    """
    Scores a single observation with the hospital-specific Isolation Forest.
    
    Returns:
    --------
    Tuple[int, float]: (anomaly_label, anomaly_score)
        label is -1 for anomaly, 1 for normal.
        score is raw decision function value (lower means more abnormal).
    """
    models = load_anomaly_models()
    model = models.get(hospital_name)

    # Fallback if no pre-trained model exists for an unknown hospital
    if model is None:
        return 1, 0.0

    feat_vals = [row[col] for col in ANOMALY_FEATURE_COLUMNS]
    X_single = pd.DataFrame([feat_vals], columns=ANOMALY_FEATURE_COLUMNS)

    label = int(model.predict(X_single)[0])
    score = float(model.decision_function(X_single)[0])

    return label, score


def generate_status_explanation(
    row: pd.Series,
    anomaly_label: Optional[int] = None
) -> Tuple[str, List[str], str]:
    """
    Rule-based operational classification separate from machine learning.
    Translates operational metrics and anomaly flag into a human-readable diagnosis.

    Parameters:
    -----------
    row : pd.Series
        Observation containing people_waiting, waiting_minutes, new_patients,
        emergency_cases, crowd_deviation.
    anomaly_label : Optional[int]
        If provided, -1 indicates Isolation Forest detected an operational outlier.

    Returns:
    --------
    Tuple[str, List[str], str]: (status_title, reasons_list, severity_class)
    """
    indicators = []

    # 1. Crowd Deviation check
    dev = row.get("crowd_deviation", 0.0)
    if pd.notna(dev) and dev >= STATUS_THRESHOLDS["crowd_deviation"]:
        indicators.append(
            f"Crowd is {dev:+.1f} people above its recent 3-period average ({row.get('rolling_avg_3', 0.0):.1f})"
        )

    # 2. Waiting Time check
    wait = row.get("waiting_minutes", 0)
    if wait >= STATUS_THRESHOLDS["waiting_minutes"]:
        indicators.append(
            f"Waiting time ({wait} min) exceeds operational target ({STATUS_THRESHOLDS['waiting_minutes']} min)"
        )

    # 3. Patient Inflow check
    new_pts = row.get("new_patients", 0)
    if new_pts >= STATUS_THRESHOLDS["new_patients"]:
        indicators.append(
            f"High patient arrivals ({new_pts} new patients in past hour)"
        )

    # 4. Emergency Influx check
    emerg = row.get("emergency_cases", 0)
    if emerg >= STATUS_THRESHOLDS["emergency_cases"]:
        indicators.append(
            f"Increased emergency surge ({emerg} acute cases requiring immediate triage)"
        )

    # 5. ML Anomaly Detection check
    is_anomaly = anomaly_label == -1
    if is_anomaly:
        indicators.append(
            "Isolation Forest flagged an unusual multi-variable activity pattern"
        )

    # Hierarchical rule evaluation
    if (is_anomaly and len(indicators) >= 2) or len(indicators) >= 2:
        return "Significant Spike", indicators, "spike"

    if is_anomaly or len(indicators) == 1:
        return "Unusual Activity", indicators, "unusual"

    return "Normal", ["All operational indicators are within normal historical ranges."], "normal"


def analyze_hospital_anomalies(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Enriches a dataframe of observations with anomaly scores and status reasons.
    """
    df_feat = prepare_features(df, is_training=False)
    models = load_anomaly_models()

    df_feat["anomaly_label"] = 1
    df_feat["anomaly_score"] = 0.0
    df_feat["status"] = "Normal"
    df_feat["reasons"] = [[] for _ in range(len(df_feat))]

    for hospital_name in df_feat["hospital"].unique():
        hosp_mask = df_feat["hospital"] == hospital_name
        model = models.get(hospital_name)
        if model is None:
            continue

        hosp_df = df_feat.loc[hosp_mask, ANOMALY_FEATURE_COLUMNS]
        labels = model.predict(hosp_df)
        scores = model.decision_function(hosp_df)

        df_feat.loc[hosp_mask, "anomaly_label"] = labels
        df_feat.loc[hosp_mask, "anomaly_score"] = scores

    # Generate status for each row
    for idx, row in df_feat.iterrows():
        status, reasons, _ = generate_status_explanation(row, row["anomaly_label"])
        df_feat.at[idx, "status"] = status
        df_feat.at[idx, "reasons"] = reasons

    return df_feat
