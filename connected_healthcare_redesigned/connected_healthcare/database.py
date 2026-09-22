"""
database.py
-----------
Connection management and schema definition for the SQLite database.

This module knows nothing about Streamlit or about analysis — it only creates
connections and tables. All read/write helpers live in utils/database_utils.py.
"""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH


class DatabaseError(Exception):
    """Raised when the database cannot be reached or a statement fails."""


# --------------------------------------------------------------------------
# Connections
# --------------------------------------------------------------------------
def get_connection():
    """
    Open a connection to the SQLite database.

    check_same_thread=False is required because Streamlit runs script reruns
    on worker threads. Foreign keys are enabled explicitly (SQLite disables
    them by default).
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as exc:  # pragma: no cover - defensive
        raise DatabaseError(f"Could not connect to the database: {exc}") from exc


@contextmanager
def connection_scope():
    """Context manager that commits on success and always closes."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise DatabaseError(f"Database operation failed: {exc}") from exc
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------
SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS hospitals (
        hospital_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_name TEXT NOT NULL,
        location      TEXT NOT NULL,
        UNIQUE (hospital_name, location)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS healthcare_cases (
        case_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id INTEGER NOT NULL,
        condition   TEXT    NOT NULL,
        age         INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
        gender      TEXT    NOT NULL,
        severity    TEXT    NOT NULL,
        case_date   TEXT    NOT NULL,
        FOREIGN KEY (hospital_id) REFERENCES hospitals (hospital_id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS hospital_queue (
        queue_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id               INTEGER NOT NULL,
        recorded_at               TEXT    NOT NULL,
        patients_waiting          INTEGER NOT NULL CHECK (patients_waiting >= 0),
        estimated_waiting_minutes INTEGER NOT NULL CHECK (estimated_waiting_minutes >= 0),
        FOREIGN KEY (hospital_id) REFERENCES hospitals (hospital_id)
            ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS health_information (
        information_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        condition         TEXT NOT NULL UNIQUE,
        symptoms          TEXT NOT NULL,
        prevention        TEXT NOT NULL,
        when_to_seek_help TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS crowd_predictions (
        prediction_id               INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id                 INTEGER NOT NULL,
        predicted_for               TEXT    NOT NULL,
        predicted_patients_waiting  INTEGER NOT NULL,
        predicted_waiting_minutes   INTEGER NOT NULL,
        created_at                  TEXT    NOT NULL,
        FOREIGN KEY (hospital_id) REFERENCES hospitals (hospital_id)
            ON DELETE CASCADE
    );
    """,
    # Indexes that matter for the dashboard queries
    "CREATE INDEX IF NOT EXISTS idx_cases_condition ON healthcare_cases (condition);",
    "CREATE INDEX IF NOT EXISTS idx_cases_date ON healthcare_cases (case_date);",
    "CREATE INDEX IF NOT EXISTS idx_queue_hospital_time ON hospital_queue (hospital_id, recorded_at);",
]


def init_db():
    """Create every table/index if it does not already exist (idempotent)."""
    with connection_scope() as conn:
        cursor = conn.cursor()
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
    return True


def database_is_empty():
    """True when there are no hospitals yet — i.e. seeding is required."""
    with connection_scope() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM hospitals;").fetchone()
        return row["n"] == 0


def ensure_database():
    """
    Called once at application start-up.

    Creates the schema and, if the database has never been populated, loads
    the synthetic demo dataset so the app is never shown empty.
    """
    init_db()
    if database_is_empty():
        # Imported lazily to avoid a circular import at module load time.
        from seed_data import seed_all

        seed_all()
    return True


if __name__ == "__main__":
    ensure_database()
    print(f"Database ready at: {DB_PATH}")
