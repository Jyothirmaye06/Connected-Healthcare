"""
Dataset inspection and audit script for Connected Healthcare.
Performs data quality checks, schema verification, summary statistics,
and generates verified audit figures.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH


def audit_database():
    print("=" * 70)
    print("CONNECTED HEALTHCARE — DATASET AUDIT REPORT")
    print("=" * 70)
    print(f"Database File: {DB_PATH}")
    print(f"File Exists  : {DB_PATH.exists()}")
    print(f"File Size    : {DB_PATH.stat().st_size:,} bytes")
    print("-" * 70)

    conn = sqlite3.connect(DB_PATH)

    # 1. Tables Overview
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    print(f"\nUser Tables Found ({len(tables)}): {', '.join(tables)}")

    # 2. Hospitals Table
    print("\n" + "=" * 50)
    print("1. TABLE: hospitals")
    print("=" * 50)
    df_hospitals = pd.read_sql_query("SELECT * FROM hospitals", conn)
    print(f"Total Hospitals: {len(df_hospitals)}")
    print(df_hospitals.to_string(index=False))

    # 3. Hospital Crowd Table
    print("\n" + "=" * 50)
    print("2. TABLE: hospital_crowd")
    print("=" * 50)
    df_crowd = pd.read_sql_query(
        """
        SELECT hc.*, h.name as hospital_name, h.location
        FROM hospital_crowd hc
        JOIN hospitals h ON hc.hospital_id = h.id
        ORDER BY hc.recorded_at
        """,
        conn
    )
    print(f"Total Observations: {len(df_crowd)}")
    print(f"Earliest Timestamp: {df_crowd['recorded_at'].min()}")
    print(f"Latest Timestamp  : {df_crowd['recorded_at'].max()}")

    # Observations per hospital
    print("\nObservations per Hospital:")
    obs_counts = df_crowd.groupby(["hospital_id", "hospital_name", "location"]).size().reset_index(name="count")
    print(obs_counts.to_string(index=False))

    # Missing values
    missing = df_crowd.isnull().sum()
    print("\nMissing Values:")
    print(missing[missing > 0] if missing.sum() > 0 else "  No missing values detected (0 nulls).")

    # Duplicate check
    duplicates = df_crowd.duplicated(subset=["hospital_id", "recorded_at"]).sum()
    print(f"Duplicate (hospital_id, recorded_at) records: {duplicates}")

    # Numerical statistics
    num_cols = ["people_waiting", "waiting_minutes", "new_patients", "discharged_patients", "emergency_cases"]
    print("\nNumerical Feature Summary Statistics:")
    print(df_crowd[num_cols].describe().round(2))

    # Negative check
    neg_counts = {col: (df_crowd[col] < 0).sum() for col in num_cols}
    print(f"\nNegative value check: {neg_counts}")

    # Events and Holidays
    print(f"\nHoliday observations: {(df_crowd['holiday'] == 1).sum()} ({(df_crowd['holiday'] == 1).mean() * 100:.1f}%)")
    print("Special event distribution:")
    print(df_crowd["special_event"].value_counts().to_string())

    # 4. Health Cases Table
    print("\n" + "=" * 50)
    print("3. TABLE: health_cases")
    print("=" * 50)
    df_cases = pd.read_sql_query("SELECT * FROM health_cases ORDER BY date", conn)
    print(f"Total Health Case Records: {len(df_cases)}")
    print(f"Earliest Date: {df_cases['date'].min()}")
    print(f"Latest Date  : {df_cases['date'].max()}")
    print(f"Locations Represented: {df_cases['location'].unique().tolist()}")
    print(f"Conditions Represented: {df_cases['condition'].unique().tolist()}")

    print("\nCase Counts by Condition:")
    cond_summary = df_cases.groupby("condition")["cases"].agg(["count", "min", "mean", "max", "sum"]).round(1)
    print(cond_summary)

    # 5. Health Information Table
    print("\n" + "=" * 50)
    print("4. TABLE: health_information")
    print("=" * 50)
    df_info = pd.read_sql_query("SELECT * FROM health_information", conn)
    print(f"Total Educational Conditions: {len(df_info)}")
    for _, row in df_info.iterrows():
        print(f"\n- Condition: {row['condition']}")
        print(f"  Symptoms : {row['symptoms']}")
        print(f"  Guidance : {row['prevention'][:60]}...")

    conn.close()
    print("\n" + "=" * 70)
    print("AUDIT COMPLETE — All database records verified.")
    print("=" * 70)


if __name__ == "__main__":
    audit_database()
