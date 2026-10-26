import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "healthcare.db"

# Reproducible synthetic data
random.seed(42)


# ============================================================
# HOSPITALS
# ============================================================

hospitals = [
    ("Apollo Hospital", "Chittoor"),
    ("Government General Hospital", "Chittoor"),
    ("Sri Venkateswara Hospital", "Tirupati")
]


# ============================================================
# HEALTH INFORMATION
# ============================================================

health_information = [
    (
        "Fever",
        "High body temperature, chills, weakness or body aches",
        "Stay hydrated, maintain hygiene and avoid close contact when sick",
        "Seek medical help if fever is severe, persistent or accompanied by serious symptoms"
    ),
    (
        "Respiratory Infection",
        "Cough, sore throat, breathing difficulty or congestion",
        "Maintain hand hygiene and avoid close contact with sick people",
        "Seek medical help for breathing difficulty or worsening symptoms"
    ),
    (
        "Dengue",
        "Fever, headache, body pain, weakness or skin rash",
        "Prevent mosquito breeding and use mosquito protection",
        "Seek medical attention for severe symptoms or persistent fever"
    ),
    (
        "Diabetes",
        "Increased thirst, frequent urination, fatigue or unexplained weight changes",
        "Maintain a healthy lifestyle and follow medical advice",
        "Consult a healthcare professional for persistent or concerning symptoms"
    )
]


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def create_tables():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT NOT NULL,
            location TEXT NOT NULL,
            cases INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """)

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
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    """)

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


# ============================================================
# INSERT HOSPITALS
# ============================================================

def insert_hospitals():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for name, location in hospitals:

        cursor.execute("""
            INSERT OR IGNORE INTO hospitals
            (name, location)
            VALUES (?, ?)
        """, (name, location))

    conn.commit()

    cursor.execute("""
        SELECT id, name, location
        FROM hospitals
        ORDER BY id
    """)

    hospital_data = cursor.fetchall()

    conn.close()

    return hospital_data


# ============================================================
# INSERT HEALTH INFORMATION
# ============================================================

def insert_health_information():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for (
        condition,
        symptoms,
        prevention,
        when_to_seek_help
    ) in health_information:

        cursor.execute("""
            INSERT OR REPLACE INTO health_information
            (
                condition,
                symptoms,
                prevention,
                when_to_seek_help
            )
            VALUES (?, ?, ?, ?)
        """, (
            condition,
            symptoms,
            prevention,
            when_to_seek_help
        ))

    conn.commit()
    conn.close()


# ============================================================
# HOSPITAL-SPECIFIC DEMAND PATTERNS
# ============================================================

def get_demand_pattern(hospital_name):

    if hospital_name == "Apollo Hospital":

        return {
            8: 4,
            9: 7,
            10: 8,
            11: 6,
            12: 3,
            13: 2,
            14: 2,
            15: 4,
            16: 7,
            17: 10,
            18: 12,
            19: 8
        }

    elif hospital_name == "Government General Hospital":

        return {
            8: 7,
            9: 10,
            10: 9,
            11: 6,
            12: 3,
            13: 2,
            14: 2,
            15: 3,
            16: 5,
            17: 7,
            18: 8,
            19: 6
        }

    else:

        return {
            8: 3,
            9: 5,
            10: 6,
            11: 5,
            12: 3,
            13: 2,
            14: 2,
            15: 3,
            16: 4,
            17: 6,
            18: 7,
            19: 5
        }


# ============================================================
# GENERATE HOSPITAL CROWD DATA
# ============================================================

def generate_hospital_data(hospital_data):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    start_date = datetime(2026, 8, 1)

    total_records = 0

    for hospital_id, hospital_name, location in hospital_data:

        # Each hospital starts with a different typical crowd.
        hospital_initial_crowd = {
            "Apollo Hospital": 42,
            "Government General Hospital": 48,
            "Sri Venkateswara Hospital": 35
        }.get(hospital_name, 40)

        previous_crowd = hospital_initial_crowd

        demand_pattern = get_demand_pattern(
            hospital_name
        )

        for day in range(60):

            current_date = (
                start_date
                + timedelta(days=day)
            )

            weekday = current_date.weekday()

            # ----------------------------------------------------
            # WEEKEND EFFECT
            # ----------------------------------------------------

            if weekday >= 5:
                weekend_effect = 1.12
            else:
                weekend_effect = 1.00

            # ----------------------------------------------------
            # HOLIDAY EFFECT
            # ----------------------------------------------------

            holiday = 1 if day in [10, 25, 40, 55] else 0

            if holiday:
                holiday_effect = 1.18
            else:
                holiday_effect = 1.00

            for hour in range(8, 20):

                timestamp = current_date.replace(
                    hour=hour,
                    minute=0,
                    second=0
                )

                # ==================================================
                # PATIENT ARRIVALS
                # ==================================================

                if hour in [9, 10, 11]:

                    arrival_factor = 1.25

                elif hour in [17, 18, 19]:

                    arrival_factor = 1.30

                else:

                    arrival_factor = 1.00

                # Hospital-specific arrival capacity
                hospital_arrival_factor = {
                    "Apollo Hospital": 1.15,
                    "Government General Hospital": 1.00,
                    "Sri Venkateswara Hospital": 0.85
                }.get(hospital_name, 1.00)

                base_arrivals = (
                    9
                    * hospital_arrival_factor
                )

                new_patients = max(
                    1,
                    int(
                        random.gauss(
                            base_arrivals
                            * arrival_factor
                            * weekend_effect
                            * holiday_effect,
                            3
                        )
                    )
                )

                # ==================================================
                # DISCHARGES
                # ==================================================

                discharged_patients = max(
                    1,
                    int(
                        random.gauss(
                            6.5
                            * hospital_arrival_factor,
                            2
                        )
                    )
                )

                # ==================================================
                # SPECIAL EVENTS
                # ==================================================

                emergency_cases = 0
                special_event = "None"

                # Emergency event
                if random.random() < 0.035:

                    emergency_cases = random.randint(
                        2,
                        7
                    )

                    special_event = "Emergency"

                # Local event
                if random.random() < 0.015:

                    special_event = "Local Event"

                    new_patients += random.randint(
                        5,
                        12
                    )

                # Disease outbreak
                if random.random() < 0.020:

                    special_event = "Disease Outbreak"

                    new_patients += random.randint(
                        5,
                        10
                    )

                # ==================================================
                # HIDDEN DEMAND
                # ==================================================

                # Some hospital demand is not directly observable.
                # This represents unknown real-world factors.

                hidden_demand = random.gauss(
                    demand_pattern[hour],
                    4
                )

                # ==================================================
                # PATIENT FLOW EFFECT
                # ==================================================

                flow_effect = (
                    (
                        new_patients
                        - discharged_patients
                    )
                    * 0.45
                )

                # ==================================================
                # EMERGENCY EFFECT
                # ==================================================

                emergency_effect = (
                    emergency_cases
                    * random.uniform(
                        0.8,
                        1.8
                    )
                )

                # ==================================================
                # SPECIAL EVENT EFFECT
                # ==================================================

                event_effect = 0

                if special_event == "Local Event":

                    event_effect = random.uniform(
                        3,
                        10
                    )

                elif special_event == "Disease Outbreak":

                    event_effect = random.uniform(
                        5,
                        15
                    )

                elif special_event == "Emergency":

                    event_effect = random.uniform(
                        1,
                        5
                    )

                # ==================================================
                # PREVIOUS CROWD MEMORY
                # ==================================================

                # Previous crowd matters, but does not completely
                # determine future crowd.

                memory_effect = (
                    previous_crowd
                    * random.uniform(
                        0.70,
                        0.90
                    )
                )

                # ==================================================
                # COMBINE DEMAND SIGNALS
                # ==================================================

                demand_change = (
                    hidden_demand
                    + flow_effect
                    + emergency_effect
                    + event_effect
                )

                current_crowd = (
                    memory_effect
                    + demand_change
                )

                # ==================================================
                # UNEXPECTED VARIATION
                # ==================================================

                current_crowd += random.gauss(
                    0,
                    4
                )

                # ==================================================
                # KEEP CROWD REALISTIC
                # ==================================================

                current_crowd = int(
                    max(
                        10,
                        min(
                            current_crowd,
                            150
                        )
                    )
                )

                # ==================================================
                # WAITING TIME
                # ==================================================

                waiting_minutes = int(
                    20
                    + (
                        current_crowd
                        * 0.75
                    )
                    + (
                        emergency_cases
                        * 4
                    )
                    + random.gauss(
                        0,
                        5
                    )
                )

                waiting_minutes = max(
                    10,
                    min(
                        waiting_minutes,
                        180
                    )
                )

                # ==================================================
                # SAVE RECORD
                # ==================================================

                cursor.execute("""
                    INSERT INTO hospital_crowd
                    (
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
                    current_crowd,
                    waiting_minutes,
                    new_patients,
                    discharged_patients,
                    emergency_cases,
                    holiday,
                    special_event,
                    timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))

                total_records += 1

                # Current observation becomes the previous state.
                previous_crowd = current_crowd

    conn.commit()
    conn.close()

    print(
        "Realistic hospital data inserted successfully!"
    )

    print(
        "Total hospital observations:",
        total_records
    )


# ============================================================
# GENERATE HEALTH CASE DATA
# ============================================================

def generate_health_cases():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    start_date = datetime(2026, 8, 1)

    conditions = [
        "Fever",
        "Respiratory Infection",
        "Dengue",
        "Diabetes"
    ]

    locations = [
        "Chittoor",
        "Tirupati"
    ]

    total_records = 0

    for day in range(60):

        current_date = (
            start_date
            + timedelta(days=day)
        )

        for location in locations:

            for condition in conditions:

                # ------------------------------------------------
                # BASE CASE LEVEL
                # ------------------------------------------------

                base_cases = {
                    "Fever": 45,
                    "Respiratory Infection": 35,
                    "Dengue": 18,
                    "Diabetes": 12
                }[condition]

                # Gradual background trend
                trend = day * 0.15

                # Normal random variation
                variation = random.gauss(
                    0,
                    5
                )

                # ------------------------------------------------
                # DISEASE-SPECIFIC SPIKE
                # ------------------------------------------------

                outbreak_effect = 0

                if (
                    condition == "Dengue"
                    and 30 <= day <= 38
                ):

                    outbreak_effect = random.randint(
                        15,
                        30
                    )

                # Respiratory infection seasonal increase
                if (
                    condition == "Respiratory Infection"
                    and 42 <= day <= 50
                ):

                    outbreak_effect += random.randint(
                        8,
                        18
                    )

                # ------------------------------------------------
                # LOCATION DIFFERENCE
                # ------------------------------------------------

                location_effect = 0

                if location == "Tirupati":

                    location_effect = random.randint(
                        -3,
                        5
                    )

                else:

                    location_effect = random.randint(
                        -2,
                        3
                    )

                # ------------------------------------------------
                # FINAL CASE COUNT
                # ------------------------------------------------

                cases = int(
                    max(
                        2,
                        base_cases
                        + trend
                        + variation
                        + outbreak_effect
                        + location_effect
                    )
                )

                cursor.execute("""
                    INSERT INTO health_cases
                    (
                        condition,
                        location,
                        cases,
                        date
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    condition,
                    location,
                    cases,
                    current_date.strftime(
                        "%Y-%m-%d"
                    )
                ))

                total_records += 1

    conn.commit()
    conn.close()

    print(
        "Health case data inserted successfully!"
    )

    print(
        "Total health case records:",
        total_records
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Creating database tables...")

    create_tables()

    print("Adding hospitals...")

    hospital_data = insert_hospitals()

    print("Adding health information...")

    insert_health_information()

    print("Generating hospital data...")

    generate_hospital_data(
        hospital_data
    )

    print("Generating health case data...")

    generate_health_cases()

    print("\nData generation completed successfully!")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()

