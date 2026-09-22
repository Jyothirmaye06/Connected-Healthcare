"""
config.py
---------
Central configuration for the Connected Healthcare platform.

Everything that a reviewer/demonstrator might want to tweak (crowd thresholds,
locations, trend windows, colours) lives here instead of being scattered
through the UI code.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "healthcare.db"

# --------------------------------------------------------------------------
# Application identity
# --------------------------------------------------------------------------
APP_NAME = "Connected Healthcare"
APP_TAGLINE = "Healthcare Intelligence • Awareness • Hospital Crowd"

# Locations available in the public location selector.
# Adding a new location here + seeding data for it is all that is required.
LOCATIONS = ["Chittoor", "Tirupati"]

# --------------------------------------------------------------------------
# Hospital crowd status thresholds (patients waiting)
# Configurable, as required by the project brief.
#   patients_waiting <= LOW_MAX                  -> Low
#   LOW_MAX < patients_waiting <= MODERATE_MAX   -> Moderate
#   patients_waiting > MODERATE_MAX              -> High
# --------------------------------------------------------------------------
CROWD_THRESHOLDS = {
    "low_max": 15,
    "moderate_max": 35,
}

CROWD_STATUS_STYLE = {
    "Low": {"emoji": "🟢", "color": "#16a34a"},
    "Moderate": {"emoji": "🟡", "color": "#d97706"},
    "High": {"emoji": "🔴", "color": "#dc2626"},
    "Unknown": {"emoji": "⚪", "color": "#6b7280"},
}

# --------------------------------------------------------------------------
# Analysis settings
# --------------------------------------------------------------------------
# "Recent Health Trends" compares the last TREND_WINDOW_DAYS against the
# TREND_WINDOW_DAYS immediately before it.
TREND_WINDOW_DAYS = 14

# A condition needs at least this many cases in the comparison window before
# the platform is willing to call it "rising" / "falling".
MIN_CASES_FOR_TREND = 5

# Age bands used across every age-group analysis.
AGE_BANDS = [
    ("0-17", 0, 17),
    ("18-30", 18, 30),
    ("31-45", 31, 45),
    ("46-60", 46, 60),
    ("61+", 61, 200),
]
AGE_BAND_LABELS = [band[0] for band in AGE_BANDS]

SEVERITY_LEVELS = ["Mild", "Moderate", "Severe"]
GENDERS = ["Male", "Female", "Other"]

# --------------------------------------------------------------------------
# Machine learning settings
# --------------------------------------------------------------------------
# Minimum number of historical queue rows for a hospital before the crowd
# model is allowed to produce a prediction for it.
MIN_ROWS_FOR_PREDICTION = 40

# Hours of the day the hospitals record queue data for (used by seeding and
# by the prediction time picker).
OPERATING_HOURS = list(range(8, 22))  # 08:00 - 21:00

# --------------------------------------------------------------------------
# Demo admin credentials (prototype only — NOT production authentication)
# --------------------------------------------------------------------------
DEMO_ADMIN_USERNAME = "admin"
DEMO_ADMIN_PASSWORD = "admin123"

# --------------------------------------------------------------------------
# Standard notices shown in the UI
# --------------------------------------------------------------------------
DEMO_DATA_NOTICE = (
    "Demo/Synthetic Data — Not real patient data. "
    "All records are generated for academic demonstration only."
)

MEDICAL_DISCLAIMER = (
    "This platform provides general health information and reported trends. "
    "It does not diagnose medical conditions and is not a substitute for "
    "professional medical care. Consider consulting a qualified healthcare "
    "professional about any personal health concern. For emergencies, seek "
    "appropriate emergency medical care."
)

PREDICTION_DISCLAIMER = (
    "Prediction based on historical/demo data. This is a statistical estimate, "
    "not live hospital information, and has not been validated against real "
    "hospital operations."
)
