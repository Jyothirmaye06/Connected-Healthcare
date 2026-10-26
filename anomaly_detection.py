"""
Root wrapper for anomaly detection and operational status determination.
Maintains backward compatibility with legacy imports and provides CLI testing.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.data_access import get_all_crowd_data
from src.feature_engineering import prepare_features
from src.anomaly_detection import (
    load_anomaly_models,
    evaluate_observation_anomaly,
    generate_status_explanation,
    analyze_hospital_anomalies,
)


def load_data():
    """Legacy helper returning all raw crowd observations."""
    return get_all_crowd_data()


def create_anomaly_features(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy helper constructing anomaly features."""
    return prepare_features(df, is_training=False)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy helper analyzing anomalies across a dataframe."""
    return analyze_hospital_anomalies(df)


def generate_status(row: pd.Series):
    """
    Legacy helper returning (status, reasons) tuple for a single observation.
    """
    anomaly_label = row.get("anomaly_label", 1)
    status, reasons, _ = generate_status_explanation(row, anomaly_label=anomaly_label)
    return status, reasons


def analyze_latest_activity():
    """CLI test displaying anomaly detection and status for each hospital's latest observation."""
    print("=" * 70)
    print("CONNECTED HEALTHCARE — LATEST ANOMALY & STATUS ANALYSIS")
    print("=" * 70)

    df = load_data()
    feature_df = create_anomaly_features(df)
    results = detect_anomalies(feature_df)

    for hospital in sorted(results["hospital"].unique()):
        hosp_data = results[results["hospital"] == hospital].sort_values("recorded_at")
        latest = hosp_data.iloc[-1]
        status, reasons = generate_status(latest)

        print(f"\nHospital: {hospital} ({latest['location']})")
        print(f"Recorded At: {latest['recorded_at']}")
        print(f"Crowd: {latest['people_waiting']} (Recent Avg: {latest['rolling_avg_3']:.1f}, Deviation: {latest['crowd_deviation']:+.1f})")
        print(f"Waiting Time: {latest['waiting_minutes']} min | New Patients: {latest['new_patients']} | Emergencies: {latest['emergency_cases']}")
        print(f"Isolation Forest Score: {latest['anomaly_score']:.4f} (Anomaly Flag: {latest['anomaly_label'] == -1})")
        print(f"Operational Status: {status}")
        print("Reasons:")
        for r in reasons:
            print(f"  - {r}")


if __name__ == "__main__":
    analyze_latest_activity()