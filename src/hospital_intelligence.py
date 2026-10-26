"""
Unified Hospital Intelligence module for Connected Healthcare.
Fuses Random Forest regression predictions, Isolation Forest anomaly detection,
and rule-based status generation into a single clean decision-support API.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_access import get_hospital_crowd_history
from src.feature_engineering import prepare_features
from src.prediction import predict_hospital
from src.anomaly_detection import evaluate_observation_anomaly, generate_status_explanation


def get_hospital_intelligence(
    hospital_name: str,
    db_path: Optional[Path] = None,
    custom_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Computes unified operational intelligence for a hospital:
    observed metrics, ML predictions, anomaly status, and operational diagnosis.
    """
    if custom_df is not None:
        df = custom_df.copy()
    else:
        df = get_hospital_crowd_history(hospital_name, db_path=db_path)

    if df.empty:
        raise ValueError(f"No observation data found for hospital: '{hospital_name}'")

    # 1. Feature Engineering
    feature_df = prepare_features(df, is_training=False)
    latest_row = feature_df.iloc[-1]

    # 2. ML Prediction
    pred_info = predict_hospital(hospital_name, db_path=db_path, custom_df=df)

    # 3. Anomaly Detection
    anomaly_label, anomaly_score = evaluate_observation_anomaly(hospital_name, latest_row)

    # 4. Operational Status & Natural-Language Reasons
    status, reasons, severity = generate_status_explanation(latest_row, anomaly_label=anomaly_label)

    intelligence = {
        "hospital": hospital_name,
        "location": pred_info["location"],
        "recorded_at": pred_info["recorded_at"],

        # Observed Situational Metrics
        "current_crowd": pred_info["current_crowd"],
        "current_waiting_minutes": pred_info["current_waiting_minutes"],
        "new_patients": pred_info["new_patients"],
        "discharged_patients": pred_info["discharged_patients"],
        "emergency_cases": pred_info["emergency_cases"],
        "holiday": pred_info["holiday"],
        "special_event": pred_info["special_event"],

        # ML Forecasts
        "predicted_crowd": pred_info["predicted_crowd"],
        "predicted_waiting_minutes": pred_info["predicted_waiting_minutes"],
        "crowd_delta": pred_info["crowd_delta"],
        "waiting_delta": pred_info["waiting_delta"],
        "prediction_horizon": pred_info["prediction_horizon"],
        "model_type": pred_info["model_type"],

        # Anomaly Analysis
        "recent_average": pred_info["recent_average"],
        "crowd_deviation": pred_info["crowd_deviation"],
        "anomaly_score": round(anomaly_score, 4),
        "anomaly_label": anomaly_label,
        "is_anomaly": anomaly_label == -1,

        # Rule-Based Operational Status
        "status": status,
        "reasons": reasons,
        "severity": severity,
    }

    return intelligence


def get_all_hospitals_summary(
    hospital_names: List[str],
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Gathers operational intelligence across all hospitals for comparative overview.
    """
    rows = []
    for name in hospital_names:
        try:
            intel = get_hospital_intelligence(name, db_path=db_path)
            rows.append({
                "Hospital": intel["hospital"],
                "Location": intel["location"],
                "Current Crowd": intel["current_crowd"],
                "Waiting Time (min)": intel["current_waiting_minutes"],
                "Predicted Crowd": intel["predicted_crowd"],
                "Predicted Wait (min)": intel["predicted_waiting_minutes"],
                "Crowd Delta": intel["crowd_delta"],
                "Wait Delta": intel["waiting_delta"],
                "Status": intel["status"],
                "Severity": intel["severity"],
                "Anomaly Score": intel["anomaly_score"],
                "Reasons": "; ".join(intel["reasons"]),
            })
        except Exception as e:
            rows.append({
                "Hospital": name,
                "Location": "Unknown",
                "Current Crowd": 0,
                "Waiting Time (min)": 0,
                "Predicted Crowd": 0,
                "Predicted Wait (min)": 0,
                "Crowd Delta": 0,
                "Wait Delta": 0,
                "Status": f"Error: {e}",
                "Severity": "normal",
                "Anomaly Score": 0.0,
                "Reasons": str(e),
            })
    return pd.DataFrame(rows)
