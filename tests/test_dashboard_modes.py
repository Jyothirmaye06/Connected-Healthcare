"""
Unit tests for dual dashboard experiences (Public vs Developer/Admin).
"""

import pytest
import pandas as pd
from src.i18n import t
from src.hospital_intelligence import get_hospital_intelligence, get_all_hospitals_summary
from src.data_access import get_hospitals_df, get_all_crowd_data, get_connection
from src.data_validation import check_dataframe_health


def test_public_dashboard_summary_generation_all_languages():
    intel = get_hospital_intelligence("Apollo Hospital")

    for lang_code in ["en", "te", "hi"]:
        if intel["status"] == "Normal":
            summary = t(
                "summary_normal",
                lang=lang_code,
                hospital=intel["hospital"],
                location=intel["location"],
                crowd=intel["current_crowd"],
                wait=intel["current_waiting_minutes"],
            )
        elif intel["status"] == "Unusual Activity":
            summary = t(
                "summary_unusual",
                lang=lang_code,
                hospital=intel["hospital"],
                location=intel["location"],
                crowd=intel["current_crowd"],
                baseline=intel["recent_average"],
                wait=intel["current_waiting_minutes"],
            )
        else:
            summary = t(
                "summary_spike",
                lang=lang_code,
                hospital=intel["hospital"],
                location=intel["location"],
                crowd=intel["current_crowd"],
                wait=intel["current_waiting_minutes"],
            )

        assert len(summary.strip()) > 10
        assert intel["hospital"] in summary


def test_developer_mode_telemetry_and_schema_inspection():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()

    assert "hospitals" in tables
    assert "hospital_crowd" in tables
    assert "health_cases" in tables
    assert "health_information" in tables


def test_developer_mode_data_quality_probe():
    all_crowd = get_all_crowd_data()
    health = check_dataframe_health(all_crowd)
    assert not health["has_missing"]
    assert health["duplicate_timestamps"] == 0
    for col, neg_cnt in health["negative_values"].items():
        assert neg_cnt == 0, f"Negative value found in column {col}"
