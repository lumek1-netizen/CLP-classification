import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-clp-12345')
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and db_url.startswith('sqlite:///'):
        # Check if it's already an absolute path (sqlite://// on Linux or sqlite:///C: on Windows)
        path = db_url.replace('sqlite:///', '')
        if not os.path.isabs(path):
            db_url = 'sqlite:///' + os.path.join(basedir, path)
    
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///' + os.path.join(basedir, 'instance', 'clp_calculator.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
