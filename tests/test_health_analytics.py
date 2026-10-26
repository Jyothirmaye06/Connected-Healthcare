"""
Unit tests for public health surveillance and analytics module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.health_analytics import (
    analyze_health_activity,
    get_health_trend_pivot,
    generate_community_insight,
)


def test_analyze_health_activity_distinguishes_abs_and_pct():
    """
    Explicitly tests that absolute case difference (+X cases)
    is cleanly distinguished from relative percentage change (+Y%).
    """
    records = []
    base_date = datetime(2026, 8, 1)

    # 7 baseline days with exactly 20 cases daily
    for d in range(7):
        records.append({
            "condition": "Fever",
            "cases": 20,
            "date": pd.Timestamp(base_date + timedelta(days=d))
        })
    # 8th day (latest) with 30 cases (+10 cases, +50%)
    records.append({
        "condition": "Fever",
        "cases": 30,
        "date": pd.Timestamp(base_date + timedelta(days=7))
    })

    df = pd.DataFrame(records)
    res = analyze_health_activity(df)

    assert len(res) == 1
    row = res.iloc[0]
    assert row["condition"] == "Fever"
    assert row["latest_cases"] == 30
    assert row["recent_average"] == 20.0
    # Absolute difference is 10 cases, NOT 50
    assert row["absolute_difference"] == 10.0
    # Percentage change is 50.0%
    assert row["percentage_change"] == 50.0
    assert row["status"] == "Significant Increase"


def test_get_health_trend_pivot():
    records = [
        {"date": pd.Timestamp("2026-08-01"), "condition": "Fever", "cases": 15},
        {"date": pd.Timestamp("2026-08-01"), "condition": "Dengue", "cases": 5},
        {"date": pd.Timestamp("2026-08-02"), "condition": "Fever", "cases": 18},
        {"date": pd.Timestamp("2026-08-02"), "condition": "Dengue", "cases": 7},
    ]
    df = pd.DataFrame(records)
    pivot = get_health_trend_pivot(df)

    assert pivot.shape == (2, 2)
    assert "Fever" in pivot.columns
    assert "Dengue" in pivot.columns
    assert pivot.loc[pd.Timestamp("2026-08-01"), "Fever"] == 15


def test_community_insight_generation():
    activity_elevated = pd.DataFrame([
        {"condition": "Dengue", "status": "Significant Increase"}
    ])
    # Case A: Hospital surge + Disease surge
    insight1 = generate_community_insight("Significant Spike", activity_elevated)
    assert insight1["type"] == "warning"
    assert "Dengue" in insight1["message"]
    assert "does not determine clinical causation" in insight1["message"]

    # Case B: Hospital normal + Normal disease
    activity_normal = pd.DataFrame([
        {"condition": "Fever", "status": "Normal"}
    ])
    insight2 = generate_community_insight("Normal", activity_normal)
    assert insight2["type"] == "success"
