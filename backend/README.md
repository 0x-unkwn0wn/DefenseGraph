# DefenseGraph Backend

Run locally:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API starts on `http://127.0.0.1:8000` and seeds the SQLite database on first startup.
