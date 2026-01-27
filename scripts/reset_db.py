"""
Skript pro kompletní reset a inicializaci databáze.

POZOR: Tento skript smaže všechna data v databázi!
Slouží k:
1. Smazání všech tabulek (Drop All).
2. Spuštění migrací (Upgrade).
3. Vytvoření výchozích rolí a administrátorského účtu.
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text
import os

app = create_app()
with app.app_context():
    print("Mažu všechny tabulky...")
    # SQLite nepodporuje CASCADE, drop_all() řeší závislosti v rámci SQLAlchemy metadat
    try:
        db.drop_all()
        print("Tabulky smazány.")
        
        # Musíme smazat i tabulku verzí migrací, aby upgrade proběhl od začátku
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version;"))
        db.session.commit()
        print("Tabulka alembic_version smazána.")
    except Exception as e:
        print(f"Chyba při mazání tabulek: {e}")

    # Spuštění migrací pro vytvoření nového schématu
    from flask_migrate import upgrade
    try:
        print("Spouštím migrace (upgrade)...")
        upgrade()
        print("Migrace dokončeny.")
        
        # Vytvoření rolí a admin uživatele
        from app.models.user import User
        from app.models.role import Role
        
        # Zajištění existence rolí
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Administrátor systému')
            db.session.add(admin_role)
            
        editor_role = Role.query.filter_by(name='editor').first()
        if not editor_role:
            editor_role = Role(name='editor', description='Editor látek a směsí')
            db.session.add(editor_role)
            
        db.session.commit()
        print("Role vytvořeny/ověřeny.")
        
        # Vytvoření admin uživatele
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', role=admin_role)
            admin_user.set_password('admin123') # Výchozí heslo, uživatel by si ho měl změnit
            db.session.add(admin_user)
            db.session.commit()
            print("Admin uživatel 'admin' vytvořen s heslem 'admin123'.")
        else:
            print("Admin uživatel již existuje.")
            
    except Exception as e:
        print(f"Chyba při obnově databáze: {e}")
        import traceback
        traceback.print_exc()
