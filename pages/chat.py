import datetime as dt

import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout, button_style
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp
from crowdlike.agents import get_agents, get_active_agent, set_active_agent, agent_label
from crowdlike.market_data import get_markets
from crowdlike.performance import portfolio_value, returns_windows, since_inception, ensure_daily_snapshot
from crowdlike.strategy import STRATEGY_TEMPLATES, apply_template
from crowdlike.safety import trigger_panic
from crowdlike.layout import render_sidebar


st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "chat")

render_sidebar(user, active_page="chat")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

agents = get_agents(user)
active = get_active_agent(user)

hero("💬 Chat", "Chat with one agent at a time. Each agent has its own chat history.", badge=agent_label(active))

st.caption("Tip: switch your active agent from the sidebar to change portfolios + chat history.")

# --- Pricing for holdings ---
coin_ids = []
port = active.get("portfolio") if isinstance(active.get("portfolio"), dict) else {}
pos = port.get("positions") if isinstance(port.get("positions"), dict) else {}
for cid, qty in pos.items():
    try:
        if abs(float(qty or 0.0)) > 1e-12:
            coin_ids.append(str(cid))
    except Exception:
        continue

price_map = {}
try:
    if coin_ids:
        rows = get_markets("usd", coin_ids[:45])
        price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    price_map = {}

value_now = portfolio_value(port, price_map)
ensure_daily_snapshot(active, value_now)
inc = since_inception(active, value_now)
win = returns_windows(active, value_now)

# --- Sidebar-like status cards ---
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    st.markdown(f"**Value:** ${value_now:,.2f}")
with sc2:
    st.markdown(f"**P&L:** ${inc['profit']:,.2f} ({inc['return_pct']:+.2f}%)")
with sc3:
    st.markdown(f"**Today:** {win['daily']['return_pct']:+.2f}%")
with sc4:
    if st.button("Open Market", width="stretch"):
        st.switch_page("pages/market.py")

soft_divider()

# --- Chat history ---
chat = active.setdefault("chat", [])
if not isinstance(chat, list):
    chat = []
    active["chat"] = chat

for msg in chat[-30:]:
    if not isinstance(msg, dict):
        continue
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    ts = msg.get("ts", "")
    with st.chat_message(role):
        st.markdown(content)
        if ts:
            st.caption(ts)


def _agent_reply(user_text: str) -> str:
    t = (user_text or "").strip()
    low = t.lower()

    strat = active.get("strategy") if isinstance(active.get("strategy"), dict) else {}
    strat_name = str(strat.get("name", "Balanced"))

    # Quick commands (demo)
    if low in ("panic", "panic sell", "exit"):
        trigger_panic(active)
        return "✅ Panic flag set. Go to **Safety** to confirm/execute the exit."

    if "performance" in low or "how am i" in low or "returns" in low:
        return (
            f"Here’s **{agent_label(active)}** right now:\n\n"
            f"- Value: **${value_now:,.2f}**\n"
            f"- Since inception: **{inc['return_pct']:+.2f}%** (${inc['profit']:,.2f})\n"
            f"- Daily: **{win['daily']['return_pct']:+.2f}%** · Weekly: **{win['weekly']['return_pct']:+.2f}%** · Monthly: **{win['monthly']['return_pct']:+.2f}%** · Yearly: **{win['yearly']['return_pct']:+.2f}%**\n\n"
            "If you want, I can explain what changed and suggest a safer risk setting."
        )

    if low.startswith("set strategy"):
        # Example: set strategy Momentum
        parts = t.split(" ")
        if len(parts) >= 3:
            name = " ".join(parts[2:])
            choices = [x["name"] for x in STRATEGY_TEMPLATES]
            match = next((c for c in choices if c.lower() == name.lower()), None)
            if match:
                apply_template(active, match)
                return f"✅ Strategy updated to **{match}**."
        return "Try: `set strategy Momentum` (choices: Balanced, Momentum, Mean Reversion, Index)."

    # Default helper
    return (
        "I’m your demo agent. Things you can ask:\n"
        "- `performance` (shows daily/weekly/monthly/yearly returns)\n"
        "- `set strategy Momentum`\n"
        "- `panic` (sets a panic sell flag)\n\n"
        f"Current strategy: **{strat_name}**"
    )


prompt = st.chat_input("Message your agent…")
if prompt:
    now = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    chat.append({"role": "user", "content": prompt, "ts": now})

    reply = _agent_reply(prompt)
    chat.append({"role": "assistant", "content": reply, "ts": now})

    grant_xp(user, 5, "Chat", "Chatted with an agent")
    save_current_user()
    st.rerun()

soft_divider()

callout(
    "info",
    "Next",
    "In production, each agent would have its own embedded USDC wallet, act within your risk/limit policy, and log actions for auditability.",
)

save_current_user()
