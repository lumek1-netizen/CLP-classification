import sqlite3
import os

db_path = os.path.join("instance", "clp_calculator.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(mixture)")
for row in cursor.fetchall():
    print(row)
cursor.execute("PRAGMA table_info(substance)")
print("--- SUBSTANCE ---")
for row in cursor.fetchall():
    print(row)
conn.close()
