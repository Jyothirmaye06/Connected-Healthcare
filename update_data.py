import sqlite3
from datetime import datetime


DB_NAME = "healthcare.db"


# ---------------------------------------------------------
# GET HOSPITALS
# ---------------------------------------------------------

def get_hospitals():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, location
        FROM hospitals
        ORDER BY id
    """)

    hospitals = cursor.fetchall()

    conn.close()

    return hospitals


# ---------------------------------------------------------
# VALIDATE INPUT
# ---------------------------------------------------------

def validate_value(
    value,
    field_name,
    minimum=0
):

    try:

        value = int(value)

    except ValueError:

        raise ValueError(
            f"{field_name} must be a number."
        )

    if value < minimum:

        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return value


# ---------------------------------------------------------
# ADD NEW OBSERVATION
# ---------------------------------------------------------


    hospital_id,
    people_waiting,
    waiting_minutes,
    new_patients,
    discharged_patients,
    emergency_cases,
    holiday,
    special_event
):

    people_waiting = validate_value(
        people_waiting,
        "People waiting"
    )

    waiting_minutes = validate_value(
        waiting_minutes,
        "Waiting minutes"
    )

    ndef add_hospital_observation(ew_patients = validate_value(
        new_patients,
        "New patients"
    )

    discharged_patients = validate_value(
        discharged_patients,
        "Discharged patients"
    )

    emergency_cases = validate_value(
        emergency_cases,
        "Emergency cases"
    )

    holiday = validate_value(
        holiday,
        "Holiday"
    )

    if holiday not in [0, 1]:

        raise ValueError(
            "Holiday must be 0 or 1."
        )

    if not special_event:

        special_event = "None"

    recorded_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
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
        people_waiting,
        waiting_minutes,
        new_patients,
        discharged_patients,
        emergency_cases,
        holiday,
        special_event,
        recorded_at
    ))

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return new_id, recorded_at


# ---------------------------------------------------------
# COMMAND LINE INTERFACE
# ---------------------------------------------------------

def main():

    print("\nCONNECTED HEALTHCARE")
    print("NEW HOSPITAL DATA ENTRY")
    print("=" * 60)

    hospitals = get_hospitals()

    if not hospitals:

        print(
            "No hospitals found in database."
        )

        return

    print("\nAvailable hospitals:")

    for hospital_id, name, location in hospitals:

        print(
            f"{hospital_id}. "
            f"{name} - {location}"
        )

    print()

    try:

        hospital_id = int(
            input("Enter hospital ID: ")
        )

        valid_ids = [
            h[0]
            for h in hospitals
        ]

        if hospital_id not in valid_ids:

            print(
                "Invalid hospital ID."
            )

            return

        people_waiting = input(
            "People currently waiting: "
        )

        waiting_minutes = input(
            "Current waiting time (minutes): "
        )

        new_patients = input(
            "New patients: "
        )

        discharged_patients = input(
            "Discharged patients: "
        )

        emergency_cases = input(
            "Emergency cases: "
        )

        holiday = input(
            "Holiday? (0 = No, 1 = Yes): "
        )

        special_event = input(
            "Special event (press Enter for None): "
        )

        new_id, recorded_at = (
            add_hospital_observation(
                hospital_id,
                people_waiting,
                waiting_minutes,
                new_patients,
                discharged_patients,
                emergency_cases,
                holiday,
                special_event
            )
        )

        print("\n" + "=" * 60)

        print(
            "New hospital observation added successfully!"
        )

        print(
            "Record ID:",
            new_id
        )

        print(
            "Recorded at:",
            recorded_at
        )

        print("=" * 60)

    except ValueError as e:

        print(
            "\nInput error:",
            e
        )

    except Exception as e:

        print(
            "\nDatabase error:",
            e
        )


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    main()