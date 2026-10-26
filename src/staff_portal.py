"""Server-side authorized hospital observation entry and audit recording."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.authentication import AuthenticatedUser, user_can_access_hospital, user_has_role
from src.data_access import get_connection
from src.data_validation import validate_observation_payload


class AuthorizationError(PermissionError):
    """Raised when a user attempts an operation outside their configured role."""


class ObservationTimestampError(ValueError):
    """Raised when a submitted observation timestamp is invalid."""


def _normalize_timestamp(value: Any) -> str:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError) as ex:
        raise ObservationTimestampError("Enter a valid observation date and time.") from ex
    if pd.isna(timestamp):
        raise ObservationTimestampError("Enter a valid observation date and time.")
    submitted = timestamp.to_pydatetime()
    if submitted.tzinfo is not None:
        submitted = submitted.astimezone().replace(tzinfo=None)
    if submitted > datetime.now() + timedelta(minutes=5):
        raise ObservationTimestampError("Observation time cannot be in the future.")
    return submitted.strftime("%Y-%m-%d %H:%M:%S")


def submit_staff_observation(
    user: Optional[AuthenticatedUser],
    payload: Dict[str, Any],
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Validates authorization, inserts an observation, and writes its audit event."""
    if not user_has_role(user, "staff"):
        raise AuthorizationError("An authenticated staff or administrator account is required.")
    if user is None:
        raise AuthorizationError("An authenticated staff or administrator account is required.")

    recorded_at = _normalize_timestamp(payload.get("recorded_at"))
    conn = get_connection(db_path)
    try:
        hospital_rows = conn.execute("SELECT id FROM hospitals").fetchall()
        valid_hospital_ids = [int(row["id"]) for row in hospital_rows]
        validated = validate_observation_payload(payload, valid_hospital_ids)
        hospital_id = validated["hospital_id"]
        if not user_can_access_hospital(user, hospital_id):
            raise AuthorizationError("Your account is not authorized for this hospital.")

        with conn:
            cursor = conn.execute(
                """
                INSERT INTO hospital_crowd (
                    hospital_id, people_waiting, waiting_minutes, new_patients,
                    discharged_patients, emergency_cases, holiday, special_event,
                    recorded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hospital_id,
                    validated["people_waiting"],
                    validated["waiting_minutes"],
                    validated["new_patients"],
                    validated["discharged_patients"],
                    validated["emergency_cases"],
                    validated["holiday"],
                    validated["special_event"],
                    recorded_at,
                ),
            )
            observation_id = cursor.lastrowid
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS observation_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    hospital_id INTEGER NOT NULL,
                    observation_id INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    submitted_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO observation_audit (
                    actor_username, action, hospital_id, observation_id,
                    recorded_at, submitted_at
                )
                VALUES (?, 'insert', ?, ?, ?, ?)
                """,
                (
                    user.username,
                    hospital_id,
                    observation_id,
                    recorded_at,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
        return {
            "observation_id": observation_id,
            "hospital_id": hospital_id,
            "recorded_at": recorded_at,
            "actor_username": user.username,
        }
    finally:
        conn.close()


def get_observation_audit(
    user: Optional[AuthenticatedUser],
    db_path: Optional[Path] = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Returns audit metadata for authorized staff scope or administrator review."""
    if not user_has_role(user, "staff"):
        raise AuthorizationError("An authenticated staff or administrator account is required.")
    if user is None:
        raise AuthorizationError("An authenticated staff or administrator account is required.")
    conn = get_connection(db_path)
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='observation_audit'"
        ).fetchone()
        if exists is None:
            return pd.DataFrame(columns=[
                "actor_username", "action", "hospital_id", "observation_id",
                "recorded_at", "submitted_at",
            ])
        query = """
            SELECT actor_username, action, hospital_id, observation_id,
                   recorded_at, submitted_at
            FROM observation_audit
        """
        params = []
        if user.role != "admin":
            if not user.hospital_ids:
                return pd.DataFrame(columns=[
                    "actor_username", "action", "hospital_id", "observation_id",
                    "recorded_at", "submitted_at",
                ])
            placeholders = ",".join("?" for _ in user.hospital_ids)
            query += f" WHERE hospital_id IN ({placeholders})"
            params.extend(user.hospital_ids)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
