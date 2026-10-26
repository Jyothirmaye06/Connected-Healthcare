"""
Dynamic synthetic dataset generator and live operational simulation engine.
Handles automated database initialization when empty, and provides a controlled
generator to simulate the next operating hour for any hospital facility.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH
from src.data_access import get_connection

# Reproducible initial generation
DEFAULT_SEED = 42

HOSPITAL_DEFINITIONS = [
    ("Apollo Hospital", "Chittoor"),
    ("Government General Hospital", "Chittoor"),
    ("Sri Venkateswara Hospital", "Tirupati"),
]

HEALTH_INFORMATION_DEFINITIONS = [
    (
        "Fever",
        "High body temperature, chills, weakness or body aches",
        "Stay hydrated, maintain hygiene and avoid close contact when sick",
        "Seek medical help if fever is severe, persistent or accompanied by serious symptoms",
    ),
    (
        "Respiratory Infection",
        "Cough, sore throat, breathing difficulty or congestion",
        "Maintain hand hygiene and avoid close contact with sick people",
        "Seek medical help for breathing difficulty or worsening symptoms",
    ),
    (
        "Dengue",
        "Fever, headache, body pain, weakness or skin rash",
        "Prevent mosquito breeding and use mosquito protection",
        "Seek medical attention for severe symptoms or persistent fever",
    ),
    (
        "Diabetes",
        "Increased thirst, frequent urination, fatigue or unexplained weight changes",
        "Maintain a healthy lifestyle and follow medical advice",
        "Consult a healthcare professional for persistent or concerning symptoms",
    ),
]


def ensure_database_populated(db_path: Optional[Path] = None, seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """
    Checks if the database has usable hospital, crowd, and health data.
    If tables or records are missing or empty, generates a realistic 60-day synthetic dataset.
    If valid records already exist, reuses all existing data untouched.

    Returns:
    --------
    dict summarizing database state and actions taken.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Create tables if not present
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL
        )
    """)
    cur.execute("""
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
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL,
            location TEXT NOT NULL,
            cases INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL UNIQUE,
            symptoms TEXT,
            prevention TEXT,
            when_to_seek_help TEXT
        )
    """)
    conn.commit()

    # Inspect current counts
    cur.execute("SELECT COUNT(*) FROM hospitals")
    hosp_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM hospital_crowd")
    crowd_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM health_cases")
    cases_count = cur.fetchone()[0]

    if hosp_count > 0 and crowd_count > 100 and cases_count > 50:
        conn.close()
        return {
            "status": "existing_data_reused",
            "message": f"Valid dataset found ({hosp_count} hospitals, {crowd_count} crowd records, {cases_count} cases). Existing data preserved.",
            "hospitals": hosp_count,
            "crowd_records": crowd_count,
            "health_cases": cases_count,
        }

    # Generate complete synthetic dataset
    random.seed(seed)

    # 1. Insert Hospitals
    for name, location in HOSPITAL_DEFINITIONS:
        cur.execute("INSERT OR IGNORE INTO hospitals (name, location) VALUES (?, ?)", (name, location))
    conn.commit()

    cur.execute("SELECT id, name, location FROM hospitals ORDER BY id")
    hospitals = cur.fetchall()

    # 2. Insert Health Information
    for cond, sym, prev, seek in HEALTH_INFORMATION_DEFINITIONS:
        cur.execute("""
            INSERT OR REPLACE INTO health_information (condition, symptoms, prevention, when_to_seek_help)
            VALUES (?, ?, ?, ?)
        """, (cond, sym, prev, seek))
    conn.commit()

    # 3. Generate 60 Days of Hospital Crowd Observations (08:00 - 19:00, 12 hrs/day)
    start_date = datetime(2026, 8, 1, 8, 0, 0)
    total_crowd_records = 0

    demand_patterns = {
        "Apollo Hospital": {8: 4, 9: 7, 10: 8, 11: 6, 12: 3, 13: 2, 14: 2, 15: 4, 16: 7, 17: 10, 18: 12, 19: 8},
        "Government General Hospital": {8: 7, 9: 10, 10: 9, 11: 6, 12: 3, 13: 2, 14: 2, 15: 3, 16: 5, 17: 7, 18: 8, 19: 6},
        "Sri Venkateswara Hospital": {8: 3, 9: 5, 10: 6, 11: 5, 12: 3, 13: 2, 14: 2, 15: 3, 16: 4, 17: 6, 18: 7, 19: 5},
    }

    initial_crowds = {
        "Apollo Hospital": 42,
        "Government General Hospital": 48,
        "Sri Venkateswara Hospital": 35,
    }

    arrival_factors = {
        "Apollo Hospital": 1.15,
        "Government General Hospital": 1.00,
        "Sri Venkateswara Hospital": 0.85,
    }

    for hosp_id, hosp_name, hosp_loc in hospitals:
        pattern = demand_patterns.get(hosp_name, demand_patterns["Government General Hospital"])
        prev_crowd = initial_crowds.get(hosp_name, 40)
        h_arr_factor = arrival_factors.get(hosp_name, 1.00)

        for day in range(60):
            current_date = start_date + timedelta(days=day)
            weekday = current_date.weekday()
            weekend_effect = 1.12 if weekday >= 5 else 1.00
            holiday = 1 if day in [10, 25, 40, 55] else 0
            holiday_effect = 1.18 if holiday else 1.00

            for hour in range(8, 20):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)

                # Diurnal rush
                arrival_factor = 1.25 if hour in [9, 10, 11] else (1.30 if hour in [17, 18, 19] else 1.00)
                base_arrivals = 9.0 * h_arr_factor
                new_patients = max(1, int(random.gauss(base_arrivals * arrival_factor * weekend_effect * holiday_effect, 3)))
                discharges = max(1, int(random.gauss(6.5 * h_arr_factor, 2)))

                emergency_cases = 0
                special_event = "None"
                if random.random() < 0.035:
                    emergency_cases = random.randint(2, 7)
                    special_event = "Emergency"
                elif random.random() < 0.015:
                    special_event = "Local Event"
                    new_patients += random.randint(5, 12)
                elif random.random() < 0.020:
                    special_event = "Disease Outbreak"
                    new_patients += random.randint(5, 10)

                hidden_demand = random.gauss(pattern.get(hour, 4), 4)
                flow_effect = (new_patients - discharges) * 0.45
                emerg_effect = emergency_cases * random.uniform(0.8, 1.8)
                event_effect = 6.0 if special_event != "None" else 0.0
                memory_effect = prev_crowd * random.uniform(0.70, 0.90)

                current_crowd = int(max(10, min(150, memory_effect + hidden_demand + flow_effect + emerg_effect + event_effect + random.gauss(0, 4))))
                waiting_minutes = int(max(10, min(180, 20 + current_crowd * 0.75 + emergency_cases * 4 + random.gauss(0, 5))))

                cur.execute("""
                    INSERT INTO hospital_crowd (
                        hospital_id, people_waiting, waiting_minutes, new_patients,
                        discharged_patients, emergency_cases, holiday, special_event, recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hosp_id,
                    current_crowd,
                    waiting_minutes,
                    new_patients,
                    discharges,
                    emergency_cases,
                    holiday,
                    special_event,
                    timestamp.strftime("%Y-%m-%d %H:%M:%S")
                ))
                prev_crowd = current_crowd
                total_crowd_records += 1

    conn.commit()

    # 4. Generate Health Cases (60 days x 2 locations x 4 conditions = 480)
    conditions = ["Fever", "Respiratory Infection", "Dengue", "Diabetes"]
    locations = ["Chittoor", "Tirupati"]
    base_cases_map = {"Fever": 45, "Respiratory Infection": 35, "Dengue": 18, "Diabetes": 12}
    total_cases = 0

    for day in range(60):
        curr_dt = start_date + timedelta(days=day)
        date_str = curr_dt.strftime("%Y-%m-%d")
        for loc in locations:
            for cond in conditions:
                base = base_cases_map[cond]
                trend = day * 0.15
                variation = random.gauss(0, 5)
                outbreak = 0
                if cond == "Dengue" and 30 <= day <= 38:
                    outbreak = random.randint(15, 30)
                elif cond == "Respiratory Infection" and 42 <= day <= 50:
                    outbreak = random.randint(8, 18)

                loc_effect = random.randint(-3, 5) if loc == "Tirupati" else random.randint(-2, 3)
                daily_cases = max(2, int(base + trend + variation + outbreak + loc_effect))

                cur.execute("""
                    INSERT INTO health_cases (condition, location, cases, date)
                    VALUES (?, ?, ?, ?)
                """, (cond, loc, daily_cases, date_str))
                total_cases += 1

    conn.commit()
    conn.close()

    return {
        "status": "generated_synthetic_dataset",
        "message": f"Generated fresh synthetic dataset with {len(hospitals)} hospitals, {total_crowd_records} observations, and {total_cases} health case records.",
        "hospitals": len(hospitals),
        "crowd_records": total_crowd_records,
        "health_cases": total_cases,
    }


def simulate_next_observation(
    hospital_id: int,
    db_path: Optional[Path] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Simulates the next chronological operating hour for the specified hospital.
    Advances timestamp, computes realistic arrivals, discharges, emergency cases,
    and updates the database in a transaction.
    Guarantees no duplicate timestamps are inserted.
    """
    if seed is not None:
        random.seed(seed)

    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Fetch Hospital Info
    cur.execute("SELECT id, name, location FROM hospitals WHERE id = ?", (hospital_id,))
    hosp_row = cur.fetchone()
    if not hosp_row:
        conn.close()
        raise ValueError(f"Hospital with ID {hospital_id} does not exist.")

    hosp_name = hosp_row["name"]

    # 2. Fetch Latest Observation for this hospital
    cur.execute("""
        SELECT * FROM hospital_crowd
        WHERE hospital_id = ?
        ORDER BY recorded_at DESC, id DESC
        LIMIT 1
    """, (hospital_id,))
    latest = cur.fetchone()

    if latest:
        last_time = datetime.strptime(latest["recorded_at"], "%Y-%m-%d %H:%M:%S")
        prev_crowd = latest["people_waiting"]

        # Advance timeline by 1 operating hour
        # If hour is between 8 and 18, next hour is hour + 1
        # If hour >= 19, roll over to 08:00 next day
        if 8 <= last_time.hour < 19:
            next_time = last_time + timedelta(hours=1)
        else:
            next_time = (last_time + timedelta(days=1)).replace(hour=8, minute=0, second=0)
    else:
        # Initial cold start
        next_time = datetime.now().replace(minute=0, second=0)
        prev_crowd = 40

    # Guard against duplicate timestamp collision
    cur.execute("""
        SELECT id FROM hospital_crowd
        WHERE hospital_id = ? AND recorded_at = ?
    """, (hospital_id, next_time.strftime("%Y-%m-%d %H:%M:%S")))
    if cur.fetchone():
        # If timestamp already exists, advance to next minute or second to prevent duplicate key
        next_time = next_time + timedelta(minutes=1)

    hour = next_time.hour
    weekday = next_time.weekday()
    weekend_effect = 1.12 if weekday >= 5 else 1.00
    holiday = 0  # Default normal

    # Inflow and Capacity Factors
    h_arr_factor = 1.15 if "Apollo" in hosp_name else (0.85 if "Venkateswara" in hosp_name else 1.00)
    arrival_factor = 1.25 if hour in [9, 10, 11] else (1.30 if hour in [17, 18, 19] else 1.00)
    base_arrivals = 9.0 * h_arr_factor

    new_patients = max(1, int(random.gauss(base_arrivals * arrival_factor * weekend_effect, 3)))
    discharges = max(1, int(random.gauss(6.5 * h_arr_factor, 2)))

    emergency_cases = 0
    special_event = "None"
    rand_val = random.random()
    if rand_val < 0.04:
        emergency_cases = random.randint(2, 6)
        special_event = "Emergency"
    elif rand_val < 0.06:
        special_event = "Local Event"
        new_patients += random.randint(5, 10)

    flow_delta = (new_patients - discharges) * 0.45
    emerg_effect = emergency_cases * 1.5
    memory_effect = prev_crowd * random.uniform(0.72, 0.88)
    simulated_crowd = int(max(10, min(150, memory_effect + flow_delta + emerg_effect + random.gauss(0, 3))))
    simulated_wait = int(max(10, min(180, 20 + simulated_crowd * 0.75 + emergency_cases * 4 + random.gauss(0, 4))))

    recorded_at_str = next_time.strftime("%Y-%m-%d %H:%M:%S")

    # Parameterized SQL Insertion inside transaction
    cur.execute("""
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
    """, (
        hospital_id,
        simulated_crowd,
        simulated_wait,
        new_patients,
        discharges,
        emergency_cases,
        holiday,
        special_event,
        recorded_at_str,
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return {
        "record_id": new_id,
        "hospital_id": hospital_id,
        "hospital_name": hosp_name,
        "recorded_at": recorded_at_str,
        "people_waiting": simulated_crowd,
        "waiting_minutes": simulated_wait,
        "new_patients": new_patients,
        "discharged_patients": discharges,
        "emergency_cases": emergency_cases,
        "holiday": holiday,
        "special_event": special_event,
    }
