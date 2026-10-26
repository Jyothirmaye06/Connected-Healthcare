"""
Smoke tests for dashboard components and application imports.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from src.hospital_intelligence import get_all_hospitals_summary


def test_config_paths_exist():
    assert config.BASE_DIR.exists()
    assert config.DB_PATH.exists()
    assert config.CROWD_MODEL_PATH.exists()
    assert config.WAITING_MODEL_PATH.exists()
    assert config.ANOMALY_MODELS_PATH.exists()


def test_status_thresholds_configured():
    thresholds = config.STATUS_THRESHOLDS
    assert "crowd_deviation" in thresholds
    assert "waiting_minutes" in thresholds
    assert "new_patients" in thresholds
    assert "emergency_cases" in thresholds


def test_hospitals_summary_for_comparison():
    summary_df = get_all_hospitals_summary(["Apollo Hospital", "Government General Hospital"])
    assert len(summary_df) == 2
    assert "Current Crowd" in summary_df.columns
    assert "Predicted Crowd" in summary_df.columns
    assert "Status" in summary_df.columns
