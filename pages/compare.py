import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit
from crowdlike.agents import get_agents
from crowdlike.market_data import get_markets
from crowdlike.leaderboards import leaderboard_rows
from crowdlike.layout import render_sidebar


st.set_page_config(page_title="Leaderboards", page_icon="🏁", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "compare")

render_sidebar(user, active_page="compare")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

hero("🏁 Leaderboards", "Daily / weekly / monthly / yearly leaderboards using Bot IDs (spec).", badge="Scoring")

agents = get_agents(user)
if not agents:
    callout("warn", "No agents", "Create at least one agent in the Agents page.")
    st.stop()

# Best-effort price map for portfolio valuation (CoinGecko)
WATCHLIST = ["bitcoin","ethereum","solana","matic-network","usd-coin","tether"]
try:
    rows = get_markets("usd", WATCHLIST)
    price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    price_map = {}

role = str(user.get("role") or "human").lower()

tabs = st.tabs(["Daily", "Weekly", "Monthly", "Yearly"])
windows = ["daily","weekly","monthly","yearly"]

for tab, w in zip(tabs, windows):
    with tab:
        lb = leaderboard_rows(user, agents, price_map=price_map, window=w, role=role)
        if not lb:
            st.info("No data yet.")
            continue

        callout(
            "info",
            "Score definition",
            "Profit is rounded to two decimals before scoring. Score = (profit * 100) + streaks. "
            "Streaks = consecutive periods with profit above 0.",
        )

        # Minimal human view
        if role not in ("bot","admin"):
            st.dataframe(
                [{ "Bot ID": r["bot_id"], "Score": round(r["score"],2), "Profit": r["profit"], "Streaks": r["streaks"] } for r in lb],
                width="stretch",
                hide_index=True,
            )
        else:
            st.dataframe(lb, width="stretch", hide_index=True)

save_current_user()
