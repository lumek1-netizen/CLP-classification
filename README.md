# CLP_Calculator

CLP_Calculator je webová aplikace vyvinutá v rámci Flasku, která slouží ke klasifikaci chemických látek a směsí podle nařízení EP a Rady (ES) č. 1272/2008 o klasifikaci, označování a balení látek a směsí (CLP).

## 🚀 Funkce

- **Správa látek**: Evidence chemických látek, jejich CAS čísel, H-vět, GHS piktogramů a M-faktorů.
- **Ekotoxické parametry**: 
  - Zadávání standardních testů (LC50, EC50, NOEC) podle CLP Přílohy I, část 4.1.
  - Automatická klasifikace Aquatic Acute (H400) a Aquatic Chronic (H410-H413).
  - Podpora pro LC50 ryby (96h), EC50 daphnie (48h), EC50 řasy (72h).
- **Klasifikace směsí**: 
  - Výpočet akutní toxicity směsi (ATEmix).
  - Klasifikace environmentálních nebezpečností na základě LC50/EC50 s M-faktory.
  - Klasifikace na základě aditivity (poleptání/podráždění kůže a očí).
  - Klasifikace na základě limitů (CMR, STOT, senzibilizace).
  - Podpora pro specifické koncentrační limity (SCL).
- **Export a logování**: Detailní logování výpočetních kroků pro každou směs včetně ekotoxických klasifikací.
- **Bezpečnost**: Autentizace uživatelů, CSRF ochrana, validace vstupů.

## 🛠️ Instalace

1. **Klonování repozitáře**:
   ```bash
   git clone <url-repozitare>
   cd CLP_Calculator
   ```

2. **Vytvoření virtuálního prostředí**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instalace závislostí**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurace**:
   Vytvořte `.env` soubor podle `.env.example`:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=vas-tajny-klic
   DATABASE_URL=sqlite:///instance/clp_database.db
   ```

5. **Inicializace databáze**:
   ```bash
   flask db upgrade
   ```

6. **Vytvoření administrátora**:
   ```bash
   python create_admin.py
   ```

## 💻 Spuštění

```bash
python run.py
```
Aplikace bude dostupná na `http://127.0.0.1:5000`.

## 🧪 Testování

Aplikace používá `pytest` pro testování.

```bash
# Spuštění všech testů
pytest

# Spuštění s reportem pokrytí
pytest --cov=app tests/
```

## 🏗️ Architektura

Aplikace využívá **Factory Pattern** pro inicializaci Flasku a je rozdělena do logických modulů:

- `app/models/`: SQLAlchemy modely (Substance, Mixture, User).
- `app/routes/`: Blueprinty pro webové rozhraní.
- `app/services/clp/`: Jádro klasifikační logiky.
  - `ate.py`: Výpočty akutní toxicity.
  - `health.py`: Klasifikace zdravotních nebezpečností.
  - `env.py`: Klasifikace nebezpečnosti pro životní prostředí.
  - `ecotoxicity.py`: Klasifikace na základě LC50/EC50/NOEC hodnot.
  - `scl.py`: Parsování a vyhodnocování SCL.
- `app/constants/`: Definice CLP limitů, H-vět a převodních tabulek.

## 📄 Licence

Tento projekt je určen pro interní použití v rámci klasifikace chemických směsí.
