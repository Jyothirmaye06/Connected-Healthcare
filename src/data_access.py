"""
Data access layer for Connected Healthcare.
Provides thread-safe SQLite connection handling, parameterized queries,
and transaction management.
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH


def _ensure_parent_dir(path: Optional[Path]) -> None:
    """Ensures the configured SQLite parent directory exists."""
    if path is None:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Checks whether a SQLite table exists in the current database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Creates a connection to the SQLite database."""
    target_path = Path(db_path or DB_PATH)
    _ensure_parent_dir(target_path)
    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def get_hospitals_df(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Returns a DataFrame of all hospitals and their locations."""
    conn = get_connection(db_path)
    try:
        if not _table_exists(conn, "hospitals"):
            return pd.DataFrame(columns=["id", "name", "location"])
        query = "SELECT id, name, location FROM hospitals ORDER BY id"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def get_hospital_crowd_history(
    hospital_name: str,
    limit: Optional[int] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Returns historical observations for a specific hospital, sorted chronologically.
    """
    conn = get_connection(db_path)
    try:
        if not _table_exists(conn, "hospitals") or not _table_exists(conn, "hospital_crowd"):
            return pd.DataFrame(columns=[
                "id",
                "hospital",
                "location",
                "people_waiting",
                "waiting_minutes",
                "new_patients",
                "discharged_patients",
                "emergency_cases",
                "holiday",
                "special_event",
                "recorded_at",
            ])
        query = """
            SELECT
                hc.id,
                h.name AS hospital,
                h.location,
                hc.people_waiting,
                hc.waiting_minutes,
                hc.new_patients,
                hc.discharged_patients,
                hc.emergency_cases,
                hc.holiday,
                hc.special_event,
                hc.recorded_at
            FROM hospital_crowd hc
            JOIN hospitals h ON hc.hospital_id = h.id
            WHERE h.name = ?
            ORDER BY hc.recorded_at ASC
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        df = pd.read_sql_query(query, conn, params=(hospital_name,))
        if not df.empty:
            df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        return df
    finally:
        conn.close()


def get_all_crowd_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Returns all crowd observations for all hospitals."""
    conn = get_connection(db_path)
    try:
        if not _table_exists(conn, "hospitals") or not _table_exists(conn, "hospital_crowd"):
            return pd.DataFrame(columns=[
                "id",
                "hospital",
                "location",
                "people_waiting",
                "waiting_minutes",
                "new_patients",
                "discharged_patients",
                "emergency_cases",
                "holiday",
                "special_event",
                "recorded_at",
            ])
        query = """
            SELECT
                hc.id,
                h.name AS hospital,
                h.location,
                hc.people_waiting,
                hc.waiting_minutes,
                hc.new_patients,
                hc.discharged_patients,
                hc.emergency_cases,
                hc.holiday,
                hc.special_event,
                hc.recorded_at
            FROM hospital_crowd hc
            JOIN hospitals h ON hc.hospital_id = h.id
            ORDER BY h.name, hc.recorded_at ASC
        """
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        return df
    finally:
        conn.close()


def get_health_cases_df(
    location: Optional[str] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """Returns health cases, optionally filtered by location."""
    conn = get_connection(db_path)
    try:
        if not _table_exists(conn, "health_cases"):
            return pd.DataFrame(columns=["id", "condition", "location", "cases", "date"])
        if location:
            query = """
                SELECT id, condition, location, cases, date
                FROM health_cases
                WHERE location = ?
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn, params=(location,))
        else:
            query = """
                SELECT id, condition, location, cases, date
                FROM health_cases
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
    finally:
        conn.close()


def get_health_information_df(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Returns guidance metadata for tracked health conditions."""
    conn = get_connection(db_path)
    try:
        if not _table_exists(conn, "health_information"):
            return pd.DataFrame(columns=["id", "condition", "symptoms", "prevention", "when_to_seek_help"])
        query = "SELECT id, condition, symptoms, prevention, when_to_seek_help FROM health_information ORDER BY condition"
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def insert_crowd_observation(
    hospital_id: int,
    people_waiting: int,
    waiting_minutes: int,
    new_patients: int,
    discharged_patients: int,
    emergency_cases: int,
    holiday: int,
    special_event: str,
    recorded_at: str,
    db_path: Optional[Path] = None
) -> Tuple[int, str]:
    """
    Inserts a validated hospital crowd observation using parameterized SQL.
    Returns (new_record_id, recorded_at).
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO hospital_crowd (
                hospital_id,
                people_waiting,
                waiting_minutes,
                new_patients,
                discharged_patients,
                emergency_cases,
                holiday,
                special_event,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(hospital_id),
                int(people_waiting),
                int(waiting_minutes),
                int(new_patients),
                int(discharged_patients),
                int(emergency_cases),
                int(holiday),
                str(special_event),
                str(recorded_at),
            )
        )
        conn.commit()
        new_id = cursor.lastrowid
        return new_id, recorded_at
    finally:
        conn.close()
