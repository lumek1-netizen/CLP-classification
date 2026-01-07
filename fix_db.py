import sqlite3
import os
import sys

# Redirect stdout to file
sys.stdout = open('db_fix_log.txt', 'w', encoding='utf-8')

db_path = os.path.join('instance', 'clp_calculator.db')

if not os.path.exists(db_path):
    print(f"Chyba: Databáze nenalezena na cestě: {db_path}")
    exit(1)

print(f"Otevírám databázi: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column_if_not_exists(table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"Přidán sloupec: {table}.{column}")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Sloupec již existuje: {table}.{column}")
            return False
        else:
            print(f"Chyba při přidávání {column}: {e}")
            return False

# 1. Oprava tabulky Mixture
print("\n--- Kontrola tabulky 'mixture' ---")
mixture_cols = [
    ('updated_at', 'DATETIME'),
    ('final_atemix_oral', 'FLOAT'),
    ('final_atemix_dermal', 'FLOAT'),
    ('final_atemix_inhalation', 'FLOAT'),
    ('final_signal_word', 'VARCHAR(50)'),
    ('classification_log', 'JSON')
]

for col_name, col_type in mixture_cols:
    add_column_if_not_exists('mixture', col_name, col_type)

# 2. Oprava tabulky Substance
print("\n--- Kontrola tabulky 'substance' ---")
substance_cols = [
    ('updated_at', 'DATETIME'),
    ('created_at', 'DATETIME'),
    ('ate_oral', 'FLOAT'),
    ('ate_dermal', 'FLOAT'),
    ('ate_inhalation_vapours', 'FLOAT'),
    ('ate_inhalation_dusts_mists', 'FLOAT'),
    ('ate_inhalation_gases', 'FLOAT'),
    ('m_factor_acute', 'INTEGER DEFAULT 1'),
    ('m_factor_chronic', 'INTEGER DEFAULT 1'),
    ('scl_limits', 'TEXT')
]

for col_name, col_type in substance_cols:
    add_column_if_not_exists('substance', col_name, col_type)

conn.commit()
conn.close()
print("\nHotovo. Databáze byla aktualizována.")
