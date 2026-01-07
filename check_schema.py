import sqlite3
import os

db_path = os.path.join('instance', 'clp_calculator.db')
if not os.path.exists(db_path):
    print("DB not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mixture)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"Columns in mixture table: {columns}")
    conn.close()
