import sqlite3

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_PATH

DB_NAME = str(DB_PATH)


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --------------------------------------------------
    # 1. HOSPITALS TABLE
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL
        )
    """)

    # --------------------------------------------------
    # 2. HEALTH CASES TABLE
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL,
            location TEXT NOT NULL,
            cases INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # --------------------------------------------------
    # 3. HOSPITAL CROWD TABLE
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospital_crowd (
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

            FOREIGN KEY (hospital_id)
            REFERENCES hospitals(id)
        )
    """)

    # --------------------------------------------------
    # 4. HEALTH INFORMATION TABLE
    # --------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            condition TEXT NOT NULL UNIQUE,

            symptoms TEXT,
            prevention TEXT,
            when_to_seek_help TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("Database created successfully!")


if __name__ == "__main__":
    create_database()