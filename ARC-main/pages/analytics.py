import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, metric_card, callout
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit
from crowdlike.layout import render_sidebar
from crowdlike.agents import get_agents, get_active_agent, set_active_agent, agent_label
from crowdlike.market_data import get_markets
from crowdlike.analytics import agents_table, compute_agent_metrics


from crowdlike.flow import flow_banner
st.set_page_config(page_title="Analytics • Crowdlike", page_icon="📊", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "analytics")

render_sidebar(user, active_page="analytics")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
_crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(_crowd.get("score", 50.0) or 50.0))

flow_banner(user, active="Review performance")

hero("📊 Analytics", "Make the demo feel real: see performance, risk, autonomy behavior, and run reports in one place.")

agents = get_agents(user)
active_agent = get_active_agent(user)

# --- Price map (best-effort) ---
WATCHLIST = ["bitcoin", "ethereum", "solana", "matic-network", "usd-coin", "tether"]
rows = []
price_map = {}
try:
    rows = get_markets("usd", WATCHLIST)
    price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    rows = []
    price_map = {}

# Agent picker (optional; sidebar also sets active agent)
if agents:
    labels = [agent_label(a) for a in agents]
    ids = [str(a.get("id")) for a in agents]
    cur = str(active_agent.get("id"))
    try:
        idx = ids.index(cur)
    except Exception:
        idx = 0

    pick = st.selectbox(
        "Agent",
        options=list(range(len(ids))),
        format_func=lambda i: labels[i],
        index=idx,
        label_visibility="collapsed",
    )
    if ids[pick] != cur:
        set_active_agent(user, ids[pick])
        save_current_user()
        st.rerun()

if not agents:
    callout("Create an agent first (Agents page).", tone="warning")
    save_current_user()
    st.stop()

m = compute_agent_metrics(user, active_agent, price_map)
since = m.get("since") if isinstance(m.get("since"), dict) else {}
windows = m.get("windows") if isinstance(m.get("windows"), dict) else {}

# --- KPI row ---
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Portfolio value", f"${float(m.get('value_usdc',0.0) or 0.0):,.2f}", "All positions + cash", accent="purple")
with k2:
    metric_card("P&L (since)", f"${float(since.get('profit',0.0) or 0.0):,.2f}", f"Return {float(since.get('return_pct',0.0) or 0.0):+.2f}%", accent="blue")
with k3:
    metric_card("Crowd deviation", f"{float(m.get('deviation_pct',0.0) or 0.0):.1f}%", "Constraint signal", accent="none")
with k4:
    metric_card("Autonomy", str(m.get("mode") or "assist"), f"Runs {int(m.get('runs_total',0) or 0)}", accent="none")


soft_divider()

tabs = st.tabs(["Overview", "Risk", "Runs & Approvals"])

# ---------------- Overview ----------------
with tabs[0]:
    st.markdown("### Returns windows")
    r1, r2, r3, r4 = st.columns(4)
    def _win(key: str) -> str:
        w = windows.get(key) if isinstance(windows.get(key), dict) else {}
        return f"{float(w.get('return_pct',0.0) or 0.0):+.2f}%"
    with r1: metric_card("Daily", _win("daily"), "Last day", accent="none")
    with r2: metric_card("Weekly", _win("weekly"), "Last 7d", accent="none")
    with r3: metric_card("Monthly", _win("monthly"), "Last 30d", accent="none")
    with r4: metric_card("Yearly", _win("yearly"), "Last 365d", accent="none")

    soft_divider()

    st.markdown("### All agents (compare)")
    table = agents_table(user, agents, price_map)
    if table:
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        callout("No agent metrics yet. Run a cycle in Coach to start populating reports.", tone="muted")

# ---------------- Risk ----------------
with tabs[1]:
    st.markdown("### Risk & stability")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Max drawdown", f"{float(m.get('max_drawdown_pct',0.0) or 0.0):.2f}%", "Peak-to-trough loss", accent="none")
    with c2:
        metric_card("Volatility proxy (30d)", f"{float(m.get('volatility_proxy_pct',0.0) or 0.0):.2f}%", "Stability estimate", accent="none")
    with c3:
        metric_card("Trades", str(int(m.get("trades_total",0) or 0)), f"Buys {int(m.get('buys',0) or 0)} · Sells {int(m.get('sells',0) or 0)}", accent="none")

    soft_divider()

    # Simple value trend (from history/snapshots if present)
    hist = active_agent.get("history") if isinstance(active_agent.get("history"), list) else []
    series = []
    for row in hist:
        if not isinstance(row, dict):
            continue
        d = row.get("d") or row.get("date")
        v = row.get("v") or row.get("value_usdc")
        try:
            series.append((str(d), float(v)))
        except Exception:
            continue
    if len(series) >= 3:
        series = series[-60:]
        st.line_chart({ "value_usdc": [v for _, v in series] }, use_container_width=True)
        st.caption("Value trend (recent snapshots).")
    else:
        callout("Value trend appears after a few daily snapshots. Run a cycle or simulate trades to generate history.", tone="muted")

# ---------------- Runs ----------------
with tabs[2]:
    st.markdown("### Run reports (recent)")
    runs = active_agent.get("runs") if isinstance(active_agent.get("runs"), list) else []
    if not runs:
        callout("No runs yet. Go to Coach → Run agent cycle.", tone="muted")
    else:
        filt = st.selectbox("Filter", options=["All", "Executed", "Queued"], index=0)
        show = []
        for r in list(reversed(runs)):
            if not isinstance(r, dict):
                continue
            if filt == "Executed" and not r.get("executed"):
                continue
            if filt == "Queued" and not r.get("queued"):
                continue
            prop = r.get("proposal") if isinstance(r.get("proposal"), dict) else {}
            dec = r.get("decision") if isinstance(r.get("decision"), dict) else {}
            show.append({
                "ts": r.get("ts"),
                "autonomy": ((r.get("autonomy") or {}) if isinstance(r.get("autonomy"), dict) else {}).get("effective"),
                "proposal": prop.get("title") or "",
                "decision": dec.get("reason") or "",
                "status": "executed" if r.get("executed") else ("queued" if r.get("queued") else "no-op"),
            })
            if len(show) >= 25:
                break
        st.dataframe(show, use_container_width=True, hide_index=True)

    soft_divider()
    st.markdown("### Pending approvals")
    approvals = active_agent.get("approvals") if isinstance(active_agent.get("approvals"), list) else []
    pending = [a for a in approvals if isinstance(a, dict) and str(a.get("status") or "pending") == "pending"]
    metric_card("Pending", str(len(pending)), "Approve/reject in Coach", accent="none")

save_current_user()