import os
import sqlite3
from app import create_app

app = create_app()
print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {app.config['SQLALCHEMY_DATABASE_URI']}")

db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
print(f"DEBUG: Resolved db_path = {db_path}")
print(f"DEBUG: File exists? {os.path.exists(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    print("✅ Přímo připojeno přes sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✅ Tabulky: {tables}")
    conn.close()
except Exception as e:
    print(f"❌ Chyba při sqlite3 připojení: {e}")

with app.app_context():
    try:
        from app.extensions import db
        from sqlalchemy import text
        result = db.session.execute(text("SELECT 1")).fetchone()
        print(f"✅ SQLAlchemy připojení funguje: {result}")
    except Exception as e:
        print(f"❌ SQLAlchemy selhalo: {e}")
