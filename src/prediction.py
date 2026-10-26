"""
Machine learning prediction engine for Connected Healthcare.
Loads saved Random Forest regression pipelines and generates future crowd
and waiting-time forecasts for hospital decision support.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    CROWD_MODEL_PATH,
    WAITING_MODEL_PATH,
    FEATURE_COLUMNS,
    PREDICTION_HORIZON_LABEL,
)
from src.data_access import get_hospital_crowd_history
from src.feature_engineering import prepare_features

# Module-level model cache to avoid repeated disk I/O
_MODELS_CACHE = {}


def load_models(force_reload: bool = False) -> Tuple[Any, Any]:
    """
    Loads saved crowd and waiting-time Random Forest pipelines.
    Caches models in memory for high-performance Streamlit inference.
    """
    global _MODELS_CACHE

    if not force_reload and "crowd" in _MODELS_CACHE and "waiting" in _MODELS_CACHE:
        return _MODELS_CACHE["crowd"], _MODELS_CACHE["waiting"]

    if not CROWD_MODEL_PATH.exists():
        raise FileNotFoundError(f"Crowd model file not found at: {CROWD_MODEL_PATH}")
    if not WAITING_MODEL_PATH.exists():
        raise FileNotFoundError(f"Waiting-time model file not found at: {WAITING_MODEL_PATH}")

    crowd_model = joblib.load(CROWD_MODEL_PATH)
    waiting_model = joblib.load(WAITING_MODEL_PATH)

    _MODELS_CACHE["crowd"] = crowd_model
    _MODELS_CACHE["waiting"] = waiting_model

    return crowd_model, waiting_model


def predict_hospital(
    hospital_name: str,
    db_path: Optional[Path] = None,
    custom_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Generates future crowd and waiting-time forecasts for the specified hospital
    based on its latest recorded observation.

    Parameters:
    -----------
    hospital_name : str
        Name of the hospital to forecast.
    db_path : Optional[Path]
        Custom database path (for test isolation).
    custom_df : Optional[pd.DataFrame]
        Pre-loaded dataframe (used for testing or simulations).

    Returns:
    --------
    dict containing observed situation, forecasts, deltas, and metadata.
    """
    if custom_df is not None:
        df = custom_df.copy()
    else:
        df = get_hospital_crowd_history(hospital_name, db_path=db_path)

    if df.empty:
        raise ValueError(f"No historical observation data found for hospital: '{hospital_name}'")

    # Feature engineering for inference (no lookahead targets required)
    feature_df = prepare_features(df, is_training=False)

    if feature_df.empty:
        raise ValueError(f"Unable to construct features for hospital: '{hospital_name}'")

    # Latest observation
    latest = feature_df.iloc[-1]

    # Prepare input DataFrame with exact feature ordering
    input_row = {col: [latest[col]] for col in FEATURE_COLUMNS}
    input_df = pd.DataFrame(input_row)

    crowd_model, waiting_model = load_models()

    raw_crowd_pred = crowd_model.predict(input_df)[0]
    raw_waiting_pred = waiting_model.predict(input_df)[0]

    # Non-negative, rounded integers
    predicted_crowd = max(0, int(round(raw_crowd_pred)))
    predicted_waiting_minutes = max(0, int(round(raw_waiting_pred)))

    current_crowd = int(latest["people_waiting"])
    current_waiting_minutes = int(latest["waiting_minutes"])

    return {
        "hospital": hospital_name,
        "location": latest["location"],
        "recorded_at": latest["recorded_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(latest["recorded_at"], "strftime") else str(latest["recorded_at"]),
        "current_crowd": current_crowd,
        "current_waiting_minutes": current_waiting_minutes,
        "new_patients": int(latest["new_patients"]),
        "discharged_patients": int(latest["discharged_patients"]),
        "emergency_cases": int(latest["emergency_cases"]),
        "holiday": int(latest["holiday"]),
        "special_event": str(latest["special_event"]),
        "predicted_crowd": predicted_crowd,
        "predicted_waiting_minutes": predicted_waiting_minutes,
        "crowd_delta": predicted_crowd - current_crowd,
        "waiting_delta": predicted_waiting_minutes - current_waiting_minutes,
        "recent_average": round(float(latest["rolling_avg_3"]), 1),
        "crowd_deviation": round(float(latest["crowd_deviation"]), 1),
        "prediction_horizon": PREDICTION_HORIZON_LABEL,
        "model_type": "Random Forest Regressor (Holdout Validated)",
    }
