"""
Unit tests for Isolation Forest anomaly detection and rule-based status diagnosis.
"""

import pytest
import pandas as pd
from src.anomaly_detection import (
    load_anomaly_models,
    evaluate_observation_anomaly,
    generate_status_explanation,
    analyze_hospital_anomalies,
)


def test_load_anomaly_models():
    models = load_anomaly_models()
    assert isinstance(models, dict)
    assert "Apollo Hospital" in models
    assert "Government General Hospital" in models
    assert "Sri Venkateswara Hospital" in models


def test_evaluate_observation_anomaly():
    test_row = pd.Series({
        "people_waiting": 35,
        "waiting_minutes": 45,
        "new_patients": 8,
        "discharged_patients": 6,
        "emergency_cases": 0,
        "crowd_change": 2.0,
        "crowd_deviation": 1.5,
    })
    label, score = evaluate_observation_anomaly("Apollo Hospital", test_row)
    assert label in [-1, 1]
    assert isinstance(score, float)


def test_unknown_hospital_anomaly_fallback():
    test_row = pd.Series({
        "people_waiting": 35,
        "waiting_minutes": 45,
        "new_patients": 8,
        "discharged_patients": 6,
        "emergency_cases": 0,
        "crowd_change": 0.0,
        "crowd_deviation": 0.0,
    })
    label, score = evaluate_observation_anomaly("Unregistered Hospital", test_row)
    assert label == 1  # Default to normal for unknown facilities
    assert score == 0.0


def test_status_generation_normal():
    normal_row = pd.Series({
        "crowd_deviation": 2.0,
        "waiting_minutes": 45,
        "new_patients": 10,
        "emergency_cases": 0,
        "rolling_avg_3": 35.0,
    })
    status, reasons, severity = generate_status_explanation(normal_row, anomaly_label=1)
    assert status == "Normal"
    assert severity == "normal"
    assert len(reasons) >= 1


def test_status_generation_unusual():
    # Exactly one indicator breached (e.g. high waiting time)
    unusual_row = pd.Series({
        "crowd_deviation": 3.0,
        "waiting_minutes": 85,  # Exceeds 80 min
        "new_patients": 10,
        "emergency_cases": 0,
        "rolling_avg_3": 35.0,
    })
    status, reasons, severity = generate_status_explanation(unusual_row, anomaly_label=1)
    assert status == "Unusual Activity"
    assert severity == "unusual"
    assert any("waiting time" in r.lower() for r in reasons)


def test_status_generation_significant_spike():
    # Multiple indicators breached + anomaly flag
    spike_row = pd.Series({
        "crowd_deviation": 37.7,  # Exceeds 10
        "waiting_minutes": 96,    # Exceeds 80
        "new_patients": 20,
        "emergency_cases": 2,
        "rolling_avg_3": 47.3,
    })
    status, reasons, severity = generate_status_explanation(spike_row, anomaly_label=-1)
    assert status == "Significant Spike"
    assert severity == "spike"
    assert len(reasons) >= 2
    assert any("isolation forest" in r.lower() for r in reasons)
