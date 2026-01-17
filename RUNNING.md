# 🚀 Spuštění CLP Calculator

## Development (Flask dev server)

**Použití:** Pro vývoj a testování

```bash
# Aktivuj virtual environment
venv\Scripts\activate

# Spusť development server
python run.py
```

- **URL:** http://localhost:5000
- **Auto-reload:** Ano (při změně kódu)
- **Debug mode:** Ano
- **Vhodné pro:** Vývoj, testování

---

## Production-like (Waitress WSGI server)

**Použití:** Pro testování produkčního běhu na Windows

```bash
# Jednoduchý způsob:
start_waitress.bat

# Nebo manuálně:
venv\Scripts\activate
waitress-serve --host=127.0.0.1 --port=8000 --threads=4 wsgi:app
```

- **URL:** http://localhost:8000
- **Auto-reload:** Ne
- **Debug mode:** Ne
- **Vhodné pro:** Produkční testování na Windows

### Waitress parametry

- `--host=127.0.0.1` - Pouze localhost (bezpečnější)
- `--port=8000` - Port serveru
- `--threads=4` - Počet worker threads (upravit podle CPU)
- `--channel-timeout=30` - Timeout pro idle connections

---

## Production (Linux - Gunicorn)

**Použití:** Skutečné produkční nasazení na Linux serveru

```bash
# Instalace
pip install gunicorn==21.2.0

# Spuštění
gunicorn -c gunicorn_config.py wsgi:app

# Nebo s parametry:
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 30 wsgi:app
```

- **URL:** http://server-ip:8000
- **Workers:** 2-4 × CPU cores
- **Vhodné pro:** Linux produkční servery

---

## Doporučení

| Prostředí | Server | Kdy použít |
|-----------|--------|------------|
| **Development** | Flask dev server | Vývoj, debugging |
| **Windows Testing** | Waitress | Testování před nasazením |
| **Linux Production** | Gunicorn + Nginx | Produkční nasazení |

---

## Troubleshooting

### Port už je používán

```bash
# Zjisti, co běží na portu 5000/8000
netstat -ano | findstr :5000

# Zastavit proces (nahraď PID)
taskkill /PID <PID> /F
```

### Aplikace se nespustí

1. Zkontroluj, že je aktivní virtual environment
2. Zkontroluj `.env` soubor (SECRET_KEY musí být nastaven)
3. Zkontroluj logy v `logs/clp_calculator.log`
