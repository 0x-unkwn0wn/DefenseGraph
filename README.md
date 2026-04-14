# DefenseGraph

Minimal MVP for mapping:

`tool -> capability -> ATT&CK -> coverage -> gaps`

## Run locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## MVP flow

1. Create a tool.
2. Open the tool detail page.
3. Toggle capabilities on or off and set `partial` or `full`.
4. Open `ATT&CK Coverage` to see computed coverage.
5. Open `Gaps` to see techniques with `none` or `detect` only coverage.
