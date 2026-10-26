import sqlite3
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))

print("Database:", DB_PATH)

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print("Tables:", [row[0] for row in tables])

for table in ("hospitals", "health_cases", "staff_accounts"):
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} records")

conn.close()
