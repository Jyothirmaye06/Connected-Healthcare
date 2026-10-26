"""Safely add staff-account storage to the existing SQLite database."""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH


def main():
    print(f"Database: {DB_PATH}")

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. No database was created."
        )

    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS staff_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    hospital_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'active', 'suspended')),
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
                )
            """)

        print("SUCCESS: staff_accounts table is ready.")
        print("Existing tables and records were not intentionally changed.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
