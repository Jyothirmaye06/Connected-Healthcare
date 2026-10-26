
"""Database-backed staff account operations."""

import hmac
import sqlite3
from typing import Optional

from src.authentication import (
    AuthenticatedUser,
    PBKDF2_ITERATIONS,
    create_password_hash,
)
from src.data_access import get_connection


def create_staff_account(
    username: str,
    password: str,
    hospital_id: int,
    created_by: AuthenticatedUser,
    db_path=None,
) -> None:
    """Create a pending account; only an administrator may create accounts."""
    if created_by is None or created_by.role != "admin":
        raise PermissionError("Only an administrator can create staff accounts.")

    username = username.strip()
    if not username or len(username) > 80:
        raise ValueError("Username must contain 1–80 characters.")
    if isinstance(hospital_id, bool) or not isinstance(hospital_id, int) or hospital_id <= 0:
        raise ValueError("Select a valid hospital ID.")

    salt, password_hash = create_password_hash(password)
    conn = get_connection(db_path)
    try:
        hospital = conn.execute(
            "SELECT 1 FROM hospitals WHERE id = ?", (hospital_id,)
        ).fetchone()
        if hospital is None:
            raise ValueError("The selected hospital does not exist.")

        with conn:
            conn.execute(
                """
                INSERT INTO staff_accounts
                    (username, password_salt, password_hash, hospital_id,
                     status, created_by)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (username, salt, password_hash, hospital_id, created_by.username),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("That username already exists.") from exc
    finally:
        conn.close()


def set_staff_account_status(
    username: str,
    status: str,
    actor: AuthenticatedUser,
    db_path=None,
) -> None:
    """Approve or suspend an account; only an administrator may change status."""
    if actor is None or actor.role != "admin":
        raise PermissionError("Only an administrator can change account status.")
    if status not in {"active", "suspended", "pending"}:
        raise ValueError("Invalid account status.")

    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE staff_accounts
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE username = ? COLLATE NOCASE
                """,
                (status, username.strip()),
            )
            if cursor.rowcount != 1:
                raise ValueError("Staff account not found.")
    finally:
        conn.close()


def authenticate_staff_account(
    username: str,
    password: str,
    db_path=None,
) -> Optional[AuthenticatedUser]:
    """Authenticate only active database-backed staff accounts."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT username, password_salt, password_hash, hospital_id, status
            FROM staff_accounts
            WHERE username = ? COLLATE NOCASE
            """,
            (username.strip(),),
        ).fetchone()
    finally:
        conn.close()

    if row is None or row["status"] != "active":
        return None

    try:
        salt = bytes.fromhex(row["password_salt"])
        expected = bytes.fromhex(row["password_hash"])
        if len(salt) < 16 or len(expected) != 32:
            return None
        actual = __import__("hashlib").pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
    except (TypeError, ValueError, UnicodeError):
        return None

    if not hmac.compare_digest(actual, expected):
        return None

    return AuthenticatedUser(
        username=row["username"],
        role="staff",
        hospital_ids=(row["hospital_id"],),
    )

def get_active_staff_user(
    username: str,
    db_path=None,
) -> Optional[AuthenticatedUser]:
    """Resolve a staff identity only while its database account is active."""
    if not username or not username.strip():
        return None

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT username, hospital_id
            FROM staff_accounts
            WHERE username = ? COLLATE NOCASE
              AND status = 'active'
            """,
            (username.strip(),),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return AuthenticatedUser(
        username=row["username"],
        role="staff",
        hospital_ids=(row["hospital_id"],),
    )
