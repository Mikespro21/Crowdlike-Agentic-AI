# Crowdlike (ARC Main UI + ARC Functionality)

This repository keeps **ARC-main UI/UX** as the default landing experience, while integrating the **full Crowdlike ARC Streamlit app functionality** (wallet + env settings, agents, coach runs, market practice/checkout hooks, analytics, leaderboards, safety guardrails, quests/shop/social, and admin audit).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Navigation model

- The **Home** page (`app.py`) is the ARC-main Tailwind-based UI.
- Clicking a nav item (Dashboard, Agents, Market, etc.) routes into the corresponding Streamlit page under `./pages/`.
- On app pages, Streamlit’s default sidebar is hidden and replaced with a fixed ARC-main-style sidebar shell.

## Environment variables

Copy `.env.example` to `.env` and set values as needed. The app also supports Streamlit secrets (`.streamlit/secrets.toml`).

