"""
utils/database_utils.py
-----------------------
All SQL lives here. These functions return plain pandas DataFrames / dicts and
never import Streamlit, so they can be unit-tested or reused from a notebook.

Every public reader accepts a `location` argument where relevant — location
filtering is applied inside SQL, not in the UI, so the dashboard can never
accidentally mix two cities together.
"""

from datetime import datetime

import pandas as pd

from database import DatabaseError, connection_scope, get_connection


# --------------------------------------------------------------------------
# Low-level helper
# --------------------------------------------------------------------------
def run_query(sql, params=()):
    """Run a SELECT and return a DataFrame. Never raises on empty results."""
    conn = None
    try:
        conn = get_connection()
        return pd.read_sql_query(sql, conn, params=params)
    except Exception as exc:
        raise DatabaseError(f"Query failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


# --------------------------------------------------------------------------
# Locations & hospitals
# --------------------------------------------------------------------------
def get_locations():
    """Distinct locations that actually have hospitals in the database."""
    df = run_query("SELECT DISTINCT location FROM hospitals ORDER BY location;")
    return df["location"].tolist()


def get_hospitals(location=None):
    """Hospitals, optionally restricted to one location."""
    if location:
        return run_query(
            """
            SELECT hospital_id, hospital_name, location
            FROM hospitals
            WHERE location = ?
            ORDER BY hospital_name;
            """,
            (location,),
        )
    return run_query(
        "SELECT hospital_id, hospital_name, location FROM hospitals ORDER BY location, hospital_name;"
    )


# --------------------------------------------------------------------------
# Healthcare cases
# --------------------------------------------------------------------------
def get_cases(location, condition=None, days=None):
    """
    Reported cases for a location, joined to the hospital name.

    condition : optional exact condition filter
    days      : optional look-back window in days
    """
    sql = """
        SELECT c.case_id, c.condition, c.age, c.gender, c.severity, c.case_date,
               h.hospital_id, h.hospital_name, h.location
        FROM healthcare_cases AS c
        JOIN hospitals AS h ON h.hospital_id = c.hospital_id
        WHERE h.location = ?
    """
    params = [location]

    if condition:
        sql += " AND c.condition = ?"
        params.append(condition)
    if days:
        sql += " AND date(c.case_date) >= date('now', ?)"
        params.append(f"-{int(days)} day")

    sql += " ORDER BY c.case_date DESC;"
    df = run_query(sql, tuple(params))
    if not df.empty:
        df["case_date"] = pd.to_datetime(df["case_date"], errors="coerce")
    return df


def get_conditions(location=None):
    """Conditions that have at least one reported case (optionally by location)."""
    if location:
        df = run_query(
            """
            SELECT DISTINCT c.condition
            FROM healthcare_cases AS c
            JOIN hospitals AS h ON h.hospital_id = c.hospital_id
            WHERE h.location = ?
            ORDER BY c.condition;
            """,
            (location,),
        )
    else:
        df = run_query(
            "SELECT DISTINCT condition FROM healthcare_cases ORDER BY condition;"
        )
    return df["condition"].tolist()


def get_all_known_conditions():
    """Union of conditions in cases and in the health-information table."""
    df = run_query(
        """
        SELECT condition FROM healthcare_cases
        UNION
        SELECT condition FROM health_information
        ORDER BY condition;
        """
    )
    return df["condition"].tolist()


# --------------------------------------------------------------------------
# Health information
# --------------------------------------------------------------------------
def get_health_information(condition):
    """Educational information for a condition, or None when not available."""
    df = run_query(
        """
        SELECT condition, symptoms, prevention, when_to_seek_help
        FROM health_information
        WHERE condition = ?;
        """,
        (condition,),
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


# --------------------------------------------------------------------------
# Hospital queue (crowd)
# --------------------------------------------------------------------------
def get_latest_queue(location):
    """
    The most recent reported queue record for every hospital in a location.

    Hospitals with no queue history at all are still returned (with NULLs) so
    the UI can show an honest "no reported data yet" card.
    """
    df = run_query(
        """
        SELECT h.hospital_id, h.hospital_name, h.location,
               q.patients_waiting, q.estimated_waiting_minutes, q.recorded_at
        FROM hospitals AS h
        LEFT JOIN hospital_queue AS q
               ON q.queue_id = (
                    SELECT queue_id
                    FROM hospital_queue
                    WHERE hospital_id = h.hospital_id
                    ORDER BY datetime(recorded_at) DESC, queue_id DESC
                    LIMIT 1
               )
        WHERE h.location = ?
        ORDER BY h.hospital_name;
        """,
        (location,),
    )
    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
    return df


def get_queue_history(hospital_id=None, location=None, days=None):
    """Historical queue observations for one hospital or a whole location."""
    sql = """
        SELECT q.queue_id, q.hospital_id, h.hospital_name, h.location,
               q.recorded_at, q.patients_waiting, q.estimated_waiting_minutes
        FROM hospital_queue AS q
        JOIN hospitals AS h ON h.hospital_id = q.hospital_id
        WHERE 1 = 1
    """
    params = []
    if hospital_id is not None:
        sql += " AND q.hospital_id = ?"
        params.append(int(hospital_id))
    if location:
        sql += " AND h.location = ?"
        params.append(location)
    if days:
        sql += " AND datetime(q.recorded_at) >= datetime('now', ?)"
        params.append(f"-{int(days)} day")

    sql += " ORDER BY datetime(q.recorded_at);"
    df = run_query(sql, tuple(params))
    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
        df = df.dropna(subset=["recorded_at"])
    return df


# --------------------------------------------------------------------------
# Writes (used by the Admin page)
# --------------------------------------------------------------------------
def insert_queue_record(hospital_id, patients_waiting, estimated_waiting_minutes,
                        recorded_at=None):
    """
    Append a NEW timestamped queue record.

    Historical rows are never overwritten — this is what allows the platform to
    demonstrate historical data collection and to train the ML model.
    """
    if patients_waiting < 0 or estimated_waiting_minutes < 0:
        raise ValueError("Queue values cannot be negative.")

    recorded_at = recorded_at or datetime.now()
    if isinstance(recorded_at, datetime):
        recorded_at = recorded_at.strftime("%Y-%m-%d %H:%M:%S")

    with connection_scope() as conn:
        cursor = conn.execute(
            """
            INSERT INTO hospital_queue
                (hospital_id, recorded_at, patients_waiting, estimated_waiting_minutes)
            VALUES (?, ?, ?, ?);
            """,
            (int(hospital_id), recorded_at, int(patients_waiting),
             int(estimated_waiting_minutes)),
        )
        return cursor.lastrowid


def insert_case_records(hospital_id, condition, severity, count=1, age=None,
                        gender="Other", case_date=None):
    """
    Add `count` anonymous case records. Only non-identifying attributes are
    stored (condition, age, gender, severity, date).
    """
    if count < 1:
        raise ValueError("Case count must be at least 1.")

    case_date = case_date or datetime.now().date()
    if hasattr(case_date, "isoformat"):
        case_date = case_date.isoformat()

    rows = [
        (int(hospital_id), condition, int(age if age is not None else 30),
         gender, severity, case_date)
        for _ in range(int(count))
    ]
    with connection_scope() as conn:
        conn.executemany(
            """
            INSERT INTO healthcare_cases
                (hospital_id, condition, age, gender, severity, case_date)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
    return len(rows)


def upsert_health_information(condition, symptoms, prevention, when_to_seek_help):
    """Insert or update the educational information for a condition."""
    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO health_information
                (condition, symptoms, prevention, when_to_seek_help)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(condition) DO UPDATE SET
                symptoms = excluded.symptoms,
                prevention = excluded.prevention,
                when_to_seek_help = excluded.when_to_seek_help;
            """,
            (condition, symptoms, prevention, when_to_seek_help),
        )
    return True


def add_hospital(hospital_name, location):
    """Register a new hospital (ignored if the same name/location exists)."""
    with connection_scope() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO hospitals (hospital_name, location) VALUES (?, ?);",
            (hospital_name.strip(), location.strip()),
        )
    return True


def save_prediction(hospital_id, predicted_for, patients_waiting, waiting_minutes):
    """Store a generated prediction so predicted vs actual can be compared later."""
    if isinstance(predicted_for, datetime):
        predicted_for = predicted_for.strftime("%Y-%m-%d %H:%M:%S")

    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO crowd_predictions
                (hospital_id, predicted_for, predicted_patients_waiting,
                 predicted_waiting_minutes, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (int(hospital_id), predicted_for, int(patients_waiting),
             int(waiting_minutes), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    return True


def get_saved_predictions(hospital_id=None, location=None):
    """Previously saved predictions, joined to actual values where available."""
    sql = """
        SELECT p.prediction_id, p.hospital_id, h.hospital_name, h.location,
               p.predicted_for, p.predicted_patients_waiting,
               p.predicted_waiting_minutes, p.created_at
        FROM crowd_predictions AS p
        JOIN hospitals AS h ON h.hospital_id = p.hospital_id
        WHERE 1 = 1
    """
    params = []
    if hospital_id is not None:
        sql += " AND p.hospital_id = ?"
        params.append(int(hospital_id))
    if location:
        sql += " AND h.location = ?"
        params.append(location)
    sql += " ORDER BY datetime(p.predicted_for) DESC;"

    df = run_query(sql, tuple(params))
    if not df.empty:
        df["predicted_for"] = pd.to_datetime(df["predicted_for"], errors="coerce")
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df


# --------------------------------------------------------------------------
# Summary counts
# --------------------------------------------------------------------------
def get_database_summary():
    """Row counts per table — shown on the Admin page."""
    tables = ["hospitals", "healthcare_cases", "hospital_queue",
              "health_information", "crowd_predictions"]
    summary = {}
    for table in tables:
        df = run_query(f"SELECT COUNT(*) AS n FROM {table};")
        summary[table] = int(df["n"].iloc[0]) if not df.empty else 0
    return summary
