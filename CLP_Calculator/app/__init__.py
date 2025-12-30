from flask import Flask
import os
from .config import Config
from .extensions import db, migrate, csrf

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Hotfix for schema (from original app.py)
    with app.app_context():
        check_and_fix_schema(app)

    # Register blueprints
    from .routes.substances import substances_bp
    from .routes.mixtures import mixtures_bp
    from .routes.data import data_bp

    app.register_blueprint(substances_bp)
    app.register_blueprint(mixtures_bp)
    app.register_blueprint(data_bp)

    return app

def check_and_fix_schema(app):
    import sqlite3
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    # If using absolute path from basedir
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(app.root_path), db_path)
    
    if not os.path.exists(db_path): 
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT classification_log FROM mixture LIMIT 1")
        except sqlite3.OperationalError:
            print("Přidávám chybějící sloupec 'classification_log' do tabulky 'mixture'...")
            cursor.execute("ALTER TABLE mixture ADD COLUMN classification_log JSON")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Chyba při kontrole schématu: {e}")
