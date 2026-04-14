# DefenseGraph Backend

Run locally:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API starts on `http://127.0.0.1:8000` and seeds the SQLite database on first startup.

## Migrate an existing database

If you already have an older `defensegraph.db`, run:

```bash
python scripts/migrate_db.py
```

Or point to a specific file:

```bash
python scripts/migrate_db.py --db C:\path\to\defensegraph.db
```

The migration runs in place and creates a timestamped backup before rebuilding the schema.
