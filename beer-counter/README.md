# 🍺 Beer Counter

Jednoduchá webová aplikace pro počítání piv (nebo jakýchkoliv jiných jednotek).

## Funkce

- ✅ Registrace a přihlašování uživatelů
- ✅ Počítání jednotek (piv) pro každého uživatele
- ✅ QR kódy pro snadné sdílení registrace
- ✅ Admin panel pro správu uživatelů
- ✅ Responsivní design (funguje na mobilu)
- ✅ Jednoduché a přehledné rozhraní

## Technologie

- **Backend**: FastAPI (Python)
- **Frontend**: HTML + TailwindCSS + JavaScript
- **Databáze**: PostgreSQL
- **Kontejnerizace**: Docker Compose

## Rychlé spuštění

1. **Klonování projektu**
   ```bash
   git clone <repository-url>
   cd beer-counter
   ```

2. **Spuštění aplikace**
   ```bash
   docker compose up -d
   ```

3. **Otevření v prohlížeči**
   ```
   http://localhost:8000
   ```

## Testovací účty

- **Admin**: `admin` / `admin`

## Struktura projektu

```
beer-counter/
├── backend/           # FastAPI backend
├── frontend/          # HTML templates a static soubory
├── docker-compose.yml # Docker Compose konfigurace
└── README.md         # Tento soubor
```

## Použití

1. **Registrace**: Vytvořte si účet na `/register`
2. **Přihlášení**: Přihlaste se na `/login`
3. **Dashboard**: Přidávejte piva a sledujte svůj počet
4. **QR kód**: Sdílejte svůj QR kód s přáteli pro rychlou registraci
5. **Admin panel**: Admin může spravovat uživatele na `/admin`

## Přizpůsobení

Chcete počítat něco jiného než piva? Jednoduše změňte:

1. **Texty v templates**: Změňte "piva" na "kávy", "kilometry" atd.
2. **Emoji**: Změňte 🍺 na ☕, 🏃‍♂️ nebo jiné
3. **Název aplikace**: Upravte v `main.py` a HTML templates

## Vývoj

Pro vývoj můžete spustit služby jednotlivě:

```bash
# Pouze databáze
docker compose up db -d

# Backend s live reload
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Produkce

Pro produkční nasazení:

1. Změňte `SECRET_KEY` v `.env`
2. Použijte silnější hesla pro databázi
3. Zvažte použití reverse proxy (nginx)
4. Nastavte HTTPS

## Licence

MIT License - použijte jak chcete! 🍺