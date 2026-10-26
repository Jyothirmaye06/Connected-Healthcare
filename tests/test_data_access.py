"""
Unit tests for data access layer.
Uses isolated temporary SQLite database fixture.
"""

import pytest
import pandas as pd
from src.data_access import (
    get_connection,
    get_hospitals_df,
    get_hospital_crowd_history,
    get_all_crowd_data,
    get_health_cases_df,
    get_health_information_df,
    insert_crowd_observation,
)


def test_get_hospitals_df(temp_db_path):
    df = get_hospitals_df(db_path=temp_db_path)
    assert len(df) == 2
    assert "Test City Hospital" in df["name"].values
    assert "Test General Clinic" in df["name"].values


def test_empty_database_returns_empty_dataframes(tmp_path):
    empty_db = tmp_path / "empty_healthcare.db"
    empty_db.touch()

    assert get_hospitals_df(db_path=empty_db).empty
    assert get_hospital_crowd_history("Any Hospital", db_path=empty_db).empty
    assert get_all_crowd_data(db_path=empty_db).empty
    assert get_health_cases_df(db_path=empty_db).empty
    assert get_health_information_df(db_path=empty_db).empty


def test_get_hospital_crowd_history(temp_db_path):
    df = get_hospital_crowd_history("Test City Hospital", db_path=temp_db_path)
    assert len(df) == 15
    assert df["people_waiting"].iloc[0] == 20
    assert df["people_waiting"].iloc[-1] == 48
    # Chronological sort check
    assert df["recorded_at"].is_monotonic_increasing


def test_get_hospital_crowd_history_unknown(temp_db_path):
    df = get_hospital_crowd_history("Nonexistent Hospital", db_path=temp_db_path)
    assert df.empty


def test_insert_crowd_observation_transaction(temp_db_path):
    initial_df = get_hospital_crowd_history("Test City Hospital", db_path=temp_db_path)
    initial_count = len(initial_df)

    new_id, ts = insert_crowd_observation(
        hospital_id=1,
        people_waiting=55,
        waiting_minutes=70,
        new_patients=12,
        discharged_patients=8,
        emergency_cases=2,
        holiday=0,
        special_event="None",
        recorded_at="2026-08-01 23:00:00",
        db_path=temp_db_path
    )

    assert new_id > 0
    updated_df = get_hospital_crowd_history("Test City Hospital", db_path=temp_db_path)
    assert len(updated_df) == initial_count + 1
    latest = updated_df.iloc[-1]
    assert latest["people_waiting"] == 55
    assert latest["waiting_minutes"] == 70
    assert latest["emergency_cases"] == 2


def test_get_health_cases_filtered(temp_db_path):
    df_all = get_health_cases_df(db_path=temp_db_path)
    assert len(df_all) == 20

    df_filtered = get_health_cases_df(location="TestCity", db_path=temp_db_path)
    assert len(df_filtered) == 20

    df_empty = get_health_cases_df(location="UnknownLocation", db_path=temp_db_path)
    assert df_empty.empty


def test_get_health_information_df(temp_db_path):
    df_info = get_health_information_df(db_path=temp_db_path)
    assert len(df_info) == 1
    assert df_info["condition"].iloc[0] == "Fever"
