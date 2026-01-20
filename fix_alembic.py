"""Fix alembic version."""
import sqlite3

conn = sqlite3.connect('instance/clp_calculator.db')
cursor = conn.cursor()
cursor.execute("UPDATE alembic_version SET version_num = '82600b03d50a'")
conn.commit()
conn.close()
print("✓ Alembic version updated to 82600b03d50a")
