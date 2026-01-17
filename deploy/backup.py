import os
import shutil
import datetime
import tarfile
import logging

# Konfigurace
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = os.path.join(PROJECT_DIR, "backups")
DB_FILE = os.path.join(PROJECT_DIR, "instance", "clp_calculator.db")
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")
RETENTION_DAYS = 30

# Nastavení loggingu pro zálohování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_backup():
    """Vytvoří komprimovanou zálohu databáze a logů."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logging.info(f"Vytvořen adresář pro zálohy: {BACKUP_DIR}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"clp_backup_{timestamp}.tar.gz"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    logging.info(f"Zahajuji zálohování do: {backup_filename}")

    try:
        with tarfile.open(backup_path, "w:gz") as tar:
            # Záloha databáze
            if os.path.exists(DB_FILE):
                tar.add(DB_FILE, arcname="clp_calculator.db")
                logging.info("Databáze přidána do zálohy.")
            else:
                logging.warning(f"Databázový soubor nenalezen: {DB_FILE}")

            # Záloha logů
            if os.path.exists(LOGS_DIR):
                tar.add(LOGS_DIR, arcname="logs")
                logging.info("Adresář s logy přidán do zálohy.")
            
            # Záloha .env (pro konfiguraci)
            env_file = os.path.join(PROJECT_DIR, ".env")
            if os.path.exists(env_file):
                tar.add(env_file, arcname=".env.backup")
                logging.info(".env soubor přidán do zálohy.")

        logging.info(f"Záloha úspěšně vytvořena: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Chyba při vytváření zálohy: {e}")
        return False

def rotate_backups():
    """Smaže zálohy starší než RETENTION_DAYS."""
    logging.info(f"Provádím rotaci záloh (retence: {RETENTION_DAYS} dní)...")
    
    now = datetime.datetime.now()
    count = 0
    
    for filename in os.listdir(BACKUP_DIR):
        if not filename.startswith("clp_backup_"):
            continue
            
        file_path = os.path.join(BACKUP_DIR, filename)
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if (now - file_time).days > RETENTION_DAYS:
            os.remove(file_path)
            logging.info(f"Smazána stará záloha: {filename}")
            count += 1
            
    logging.info(f"Rotace dokončena. Smazáno {count} souborů.")

if __name__ == "__main__":
    if create_backup():
        rotate_backups()
