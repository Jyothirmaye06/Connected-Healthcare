"""
Unit tests for machine learning predictions using trained models.
"""

import pytest
import pandas as pd
from src.prediction import predict_hospital, load_models
from config import CROWD_MODEL_PATH, WAITING_MODEL_PATH


def test_load_models_cached():
    m1, m2 = load_models()
    assert m1 is not None
    assert m2 is not None
    # Check pipeline step
    assert hasattr(m1, "predict")
    assert hasattr(m2, "predict")


def test_predict_hospital_live():
    """Tests forecast generation for Apollo Hospital using live models."""
    res = predict_hospital("Apollo Hospital")

    assert res["hospital"] == "Apollo Hospital"
    assert "current_crowd" in res
    assert "predicted_crowd" in res
    assert "predicted_waiting_minutes" in res

    # Predictions must be non-negative integers
    assert isinstance(res["predicted_crowd"], int)
    assert res["predicted_crowd"] >= 0
    assert isinstance(res["predicted_waiting_minutes"], int)
    assert res["predicted_waiting_minutes"] >= 0
    assert "prediction_horizon" in res


def test_predict_hospital_with_custom_dataframe():
    """Tests prediction with an isolated custom DataFrame."""
    custom_df = pd.DataFrame([
        {
            "hospital": "Mock Hospital",
            "location": "Mock City",
            "people_waiting": 40,
            "waiting_minutes": 50,
            "new_patients": 10,
            "discharged_patients": 5,
            "emergency_cases": 1,
            "holiday": 0,
            "special_event": "None",
            "recorded_at": "2026-08-01 10:00:00"
        },
        {
            "hospital": "Mock Hospital",
            "location": "Mock City",
            "people_waiting": 44,
            "waiting_minutes": 55,
            "new_patients": 8,
            "discharged_patients": 4,
            "emergency_cases": 0,
            "holiday": 0,
            "special_event": "None",
            "recorded_at": "2026-08-01 11:00:00"
        }
    ])

    res = predict_hospital("Mock Hospital", custom_df=custom_df)
    assert res["hospital"] == "Mock Hospital"
    assert res["current_crowd"] == 44
    assert res["current_waiting_minutes"] == 55
    assert res["predicted_crowd"] >= 0
    assert res["predicted_waiting_minutes"] >= 0


def test_predict_hospital_empty_raises():
    with pytest.raises(ValueError, match="No historical observation data found"):
        predict_hospital("Completely Unknown Hospital Name")
