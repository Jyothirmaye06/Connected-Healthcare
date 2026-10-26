import sqlite3

conn = sqlite3.connect("healthcare.db")

for table in ["hospitals", "health_cases", "health_information", "hospital_crowd"]:
    print(f"\n--- {table} ---")
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    for column in columns:
        print(f"{column[1]}: {column[2]}")

conn.close()
