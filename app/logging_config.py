"""
Konfigurace centralizovaného loggingu pro CLP Calculator.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask


def setup_logging(app: Flask) -> None:
    """
    Nastaví logging pro aplikaci.
    
    Development: Loguje do konzole (DEBUG level)
    Production: Loguje do souborů s rotací (INFO level)
    """
    
    # Vytvoř logs adresář, pokud neexistuje
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Formát log zpráv
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (%(pathname)s:%(lineno)d): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === FILE HANDLER (vždy) ===
    # Rotující soubor: max 10MB, 10 backup souborů
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'clp_calculator.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # V produkci pouze INFO a výše, v dev i DEBUG
    if app.debug:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    
    # === CONSOLE HANDLER (pouze development) ===
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
    
    # === ERROR FILE HANDLER (pouze chyby) ===
    error_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'errors.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_file_handler)
    
    # Nastav úroveň root loggeru
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
    
    # Úvodní log zpráva
    app.logger.info('=' * 80)
    app.logger.info('CLP Calculator Application Starting')
    app.logger.info(f'Environment: {"Development" if app.debug else "Production"}')
    app.logger.info(f'Database: {app.config.get("SQLALCHEMY_DATABASE_URI", "Not set")}')
    app.logger.info('=' * 80)
