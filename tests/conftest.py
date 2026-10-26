"""
Pytest configuration and shared fixtures for Connected Healthcare tests.
Ensures automated tests run against isolated temporary databases and never modify healthcare.db.
"""

import sys
import sqlite3
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from datetime import datetime, timedelta

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture
def temp_db_path(tmp_path):
    """
    Creates an isolated temporary SQLite database populated with minimal test records.
    Never interacts with the live healthcare.db.
    """
    db_file = tmp_path / "test_healthcare.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE hospital_crowd (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            people_waiting INTEGER NOT NULL,
            waiting_minutes INTEGER NOT NULL,
            new_patients INTEGER DEFAULT 0,
            discharged_patients INTEGER DEFAULT 0,
            emergency_cases INTEGER DEFAULT 0,
            holiday INTEGER DEFAULT 0,
            special_event TEXT DEFAULT 'None',
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    """)

    cur.execute("""
        CREATE TABLE health_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL,
            location TEXT NOT NULL,
            cases INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE health_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL UNIQUE,
            symptoms TEXT,
            prevention TEXT,
            when_to_seek_help TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE staff_accounts (
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
    # Populate minimal hospitals
    cur.execute("INSERT INTO hospitals (id, name, location) VALUES (1, 'Test City Hospital', 'TestCity')")
    cur.execute("INSERT INTO hospitals (id, name, location) VALUES (2, 'Test General Clinic', 'TestCity')")

    # Populate 15 chronological crowd observations for Hospital 1
    base_time = datetime(2026, 8, 1, 8, 0, 0)
    for i in range(15):
        t = base_time + timedelta(hours=i)
        cur.execute("""
            INSERT INTO hospital_crowd (
                hospital_id, people_waiting, waiting_minutes, new_patients,
                discharged_patients, emergency_cases, holiday, special_event, recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            20 + i * 2,
            30 + i * 3,
            5 + (i % 3),
            4 + (i % 2),
            1 if i == 10 else 0,
            0,
            'None',
            t.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # Populate 5 days of health cases
    for d in range(10):
        dt = (base_time + timedelta(days=d)).strftime("%Y-%m-%d")
        cur.execute("INSERT INTO health_cases (condition, location, cases, date) VALUES (?, ?, ?, ?)",
                    ("Fever", "TestCity", 20 + d * 2, dt))
        cur.execute("INSERT INTO health_cases (condition, location, cases, date) VALUES (?, ?, ?, ?)",
                    ("Dengue", "TestCity", 10 + d, dt))

    # Populate health info
    cur.execute("""
        INSERT INTO health_information (condition, symptoms, prevention, when_to_seek_help)
        VALUES ('Fever', 'High temperature', 'Rest and hydration', 'If persistent over 3 days')
    """)

    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def sample_feature_df():
    """Generates an in-memory sample DataFrame for feature engineering tests."""
    records = []
    base_time = datetime(2026, 8, 1, 8, 0, 0)
    for h in ["Hospital A", "Hospital B"]:
        for i in range(10):
            t = base_time + timedelta(hours=i)
            records.append({
                "hospital": h,
                "location": "LocA",
                "people_waiting": 30 + i * 2,
                "waiting_minutes": 40 + i * 3,
                "new_patients": 8,
                "discharged_patients": 5,
                "emergency_cases": 0,
                "holiday": 0,
                "special_event": "None",
                "recorded_at": t.strftime("%Y-%m-%d %H:%M:%S")
            })
    return pd.DataFrame(records)


