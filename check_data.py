import sqlite3

conn = sqlite3.connect("healthcare.db")

cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM hospital_crowd")
hospital_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM health_cases")
health_count = cursor.fetchone()[0]

print("Hospital observations:", hospital_count)
print("Health observations:", health_count)

cursor.execute("""
    SELECT
        h.name,
        hc.people_waiting,
        hc.waiting_minutes,
        hc.new_patients,
        hc.discharged_patients,
        hc.emergency_cases,
        hc.recorded_at
    FROM hospital_crowd hc
    JOIN hospitals h
    ON hc.hospital_id = h.id
    ORDER BY hc.recorded_at
    LIMIT 10
""")

print("\nSample hospital observations:\n")

for row in cursor.fetchall():
    print(row)

conn.close()