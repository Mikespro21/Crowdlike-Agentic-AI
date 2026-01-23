# Crowdlike — Option B (React UI inside Streamlit)

**Entry point:** run `streamlit run app.py` from the repo root.


This is the **Option B** integration: keep the existing **React (Vite) UI** intact for maximum design fidelity, and run it **inside Streamlit** via an iframe. Streamlit becomes the shell/orchestrator, and a small **Python backend (FastAPI)** is included for future Python-first functionality.

## What you get

- **1:1 UI** (you keep the React app)
- A **Streamlit wrapper** (`app.py`) that:
  - starts a static server for `dist/`
  - starts an optional FastAPI backend
  - embeds the UI via iframe
- A **FastAPI backend** (`backend_api.py`) that can proxy CoinGecko endpoints (optional, but useful)

## Setup


> Note: If `./dist` is missing, `app.py` will attempt to run `npm install` and `npm run build` automatically.

### 1) Install JS deps and build the React UI
From this repo root:

```bash
npm install

# Optional: point the React app to the local backend instead of hitting CoinGecko directly
echo VITE_COINGECKO_API_URL=http://127.0.0.1:8001 > .env.local

npm run build
```

This creates `./dist`.

### 2) Install Python deps and run Streamlit
```bash
pip install -r requirements.txt
streamlit run app.py
```

- Streamlit: http://localhost:8501  
- React (served): http://localhost:8502 (or next free port)  
- Backend: http://localhost:8001 (or next free port)

## Configuration knobs

Environment variables (optional):

- `CROWDLIKE_START_BACKEND=true|false` (default true)
- `CROWDLIKE_BACKEND_PORT=8001`
- `CROWDLIKE_FRONTEND_PORT=8502`
- `CROWDLIKE_COINGECKO_BASE=https://api.coingecko.com/api/v3`
- `CROWDLIKE_CACHE_TTL=30` (seconds)

## Notes on “conversion”

This approach is not a pixel-by-pixel rewrite into Streamlit widgets. It is an **integration** that preserves the original React UI, which is the most reliable way to keep premium design + interactions.

If you later decide you want a **pure Streamlit** implementation (Option A), we can do that as a second phase—typically after the demo/submission is stable.