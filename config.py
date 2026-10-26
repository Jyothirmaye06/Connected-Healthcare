"""
Central configuration for Connected Healthcare project.
Provides absolute path resolution, model paths, feature lists, and operational thresholds.
"""

from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_BACKUP_DIR = MODELS_DIR / "backup"
DOCS_DIR = BASE_DIR / "docs"

# Database path (always absolute)
DB_PATH = BASE_DIR / "healthcare.db"

# Model artifact paths
CROWD_MODEL_PATH = MODELS_DIR / "crowd_model.pkl"
WAITING_MODEL_PATH = MODELS_DIR / "waiting_time_model.pkl"
ANOMALY_MODELS_PATH = MODELS_DIR / "anomaly_models.pkl"

# Feature definitions for ML prediction
FEATURE_COLUMNS = [
    "hospital",
    "location",
    "hour",
    "day_of_week",
    "is_weekend",
    "people_waiting",
    "previous_crowd",
    "rolling_avg_3",
    "crowd_change",
    "new_patients",
    "discharged_patients",
    "emergency_cases",
    "holiday",
    "special_event",
    "waiting_minutes",
]

CATEGORICAL_FEATURES = [
    "hospital",
    "location",
    "special_event",
]

NUMERICAL_FEATURES = [
    col for col in FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES
]

# Features used for Isolation Forest anomaly detection
ANOMALY_FEATURE_COLUMNS = [
    "people_waiting",
    "waiting_minutes",
    "new_patients",
    "discharged_patients",
    "emergency_cases",
    "crowd_change",
    "crowd_deviation",
]

# Isolation Forest settings
ISOLATION_FOREST_PARAMS = {
    "n_estimators": 200,
    "contamination": 0.05,
    "random_state": 42,
}

# Configurable demo operational thresholds
# These are heuristic decision-support thresholds for viva demonstration,
# not clinically validated diagnostic cutoff values.
STATUS_THRESHOLDS = {
    "crowd_deviation": 10.0,      # people above recent average
    "waiting_minutes": 80,         # minutes
    "new_patients": 22,            # arrivals in hour
    "emergency_cases": 3,          # acute emergencies
}

# Prediction horizon metadata
PREDICTION_HORIZON_LABEL = "Next observation (~1 hour during 08:00 - 19:00 clinic hours)"

# Project notice
SYNTHETIC_DATA_NOTICE = (
    "Demo Project: Hospital observations and health-condition records are synthetic "
    "demonstration data and do not represent a verified live hospital integration."
)
