import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout, metric_card
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp
from crowdlike.agents import get_active_agent, agent_label
from crowdlike.market_data import get_markets
from crowdlike.performance import portfolio_value
from crowdlike.safety import trigger_panic, set_fraud_alert, check_safety_triggers, safety_exit
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event
from crowdlike.audit import log_audit


st.set_page_config(page_title="Safety", page_icon="🛡️", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "safety")

render_sidebar(user, active_page="safety")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

active = get_active_agent(user)

hero("🛡️ Safety", "Configurable exits: max daily loss, max drawdown, fraud/anomaly, and panic.", badge=agent_label(active))

# Prices for current holdings (best-effort)
WATCHLIST = ["bitcoin","ethereum","solana","matic-network","usd-coin","tether"]
try:
    rows = get_markets("usd", WATCHLIST)
    price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    price_map = {}

port = active.get("portfolio") if isinstance(active.get("portfolio"), dict) else {}
cur_v = portfolio_value(port, price_map)

s = active.setdefault("safety", {})
if not isinstance(s, dict):
    s = {"enabled": True}
    active["safety"] = s

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Portfolio value", f"${cur_v:,.2f}", "Demo valuation using spot prices when available")
with c2:
    metric_card("Safety enabled", "Yes" if bool(s.get("enabled", True)) else "No", "Turn exits on/off")
with c3:
    last = s.get("last_exit") if isinstance(s.get("last_exit"), dict) else {}
    metric_card("Last exit", str(last.get("reason") or "—"), str(last.get("ts") or ""))

soft_divider()

st.markdown("### Exit configuration")
colA, colB, colC = st.columns([1.0, 1.0, 1.0])

with colA:
    enabled = st.toggle("Enable safety exits", value=bool(s.get("enabled", True)))
    s["enabled"] = bool(enabled)

with colB:
    max_daily = st.number_input("Max daily loss (USDC)", min_value=0.0, value=float(s.get("max_daily_loss_usdc", 50.0) or 0.0), step=5.0, help="If today's value falls by this amount vs yesterday, trigger exit.")
    s["max_daily_loss_usdc"] = float(max_daily)

with colC:
    max_dd = st.number_input("Max drawdown (%)", min_value=0.0, value=float(s.get("max_drawdown_pct", 25.0) or 0.0), step=1.0, help="If drawdown from peak exceeds this %, trigger exit.")
    s["max_drawdown_pct"] = float(max_dd)

colD, colE = st.columns([1.0, 1.0])
with colD:
    fraud = st.toggle("Fraud/anomaly alert", value=bool(s.get("fraud_alert", False)))
    set_fraud_alert(active, fraud)
with colE:
    if st.button("Panic sell (demo)", type="primary", width="stretch", disabled=not enabled):
        trigger_panic(active)
        log_event(user, kind="safety", title="Panic armed", details="Panic exit will execute on next trigger check.", severity="warn", agent_id=str(active.get("id")))
        log_audit(user, kind="safety", msg="Panic armed", agent_id=str(active.get("id")), severity="warn")
        grant_xp(user, 10, "Safety", "Panic armed")
        save_current_user()
        st.rerun()

soft_divider()

st.markdown("### Run trigger check")
if st.button("Check triggers now", width="stretch"):
    fired, msg = check_safety_triggers(active, price_map)
    if fired:
        st.success(msg)
        log_event(user, kind="safety", title="Safety exit executed", details=msg, severity="success", agent_id=str(active.get("id")))
        log_audit(user, kind="safety_exit", msg=msg, agent_id=str(active.get("id")), severity="success")
        grant_xp(user, 25, "Safety", "Exit executed")
    else:
        st.info(msg)
    save_current_user()
    st.rerun()

st.markdown("### Manual exit")
if st.button("Exit to USDC now (demo)", width="stretch", disabled=not enabled):
    ok, msg = safety_exit(active, price_map, "Manual exit")
    if ok:
        st.success(msg)
        log_event(user, kind="safety", title="Manual exit", details=msg, severity="success", agent_id=str(active.get("id")))
        log_audit(user, kind="safety_exit", msg=msg, agent_id=str(active.get("id")), severity="success")
        grant_xp(user, 25, "Safety", "Manual exit")
    else:
        st.warning(msg)
    save_current_user()
    st.rerun()

save_current_user()
