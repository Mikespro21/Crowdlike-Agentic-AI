import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout, metric_card, button_style
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp, log_activity
from crowdlike.agents import (
    get_agents,
    get_active_agent,
    set_active_agent,
    create_agent,
    delete_agent,
    agent_label,
)
from crowdlike.market_data import get_markets
from crowdlike.performance import portfolio_value, ensure_daily_snapshot, returns_windows, since_inception
from crowdlike.autonomy import trust_signals, effective_mode
from crowdlike.strategy import STRATEGY_TEMPLATES, apply_template, copy_strategy
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event



from crowdlike.flow import flow_banner
st.set_page_config(page_title="Agents", page_icon="🤖", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "agents")

render_sidebar(user, active_page="agents")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

flow_banner(user, active="Create an agent")

hero("🤖 Agents", "Create agents, give each one a separate portfolio + chat history, then compare them by profit and return.", badge="Multi‑agent")

agents = get_agents(user)
active = get_active_agent(user)

# --- Live pricing for all agent holdings (best effort) ---
coin_ids = set()
for a in agents:
    port = a.get("portfolio") if isinstance(a.get("portfolio"), dict) else {}
    pos = port.get("positions") if isinstance(port.get("positions"), dict) else {}
    for cid, qty in pos.items():
        try:
            if abs(float(qty or 0.0)) > 1e-12:
                coin_ids.add(str(cid))
        except Exception:
            continue

# Keep API lightweight
ids_list = list(coin_ids)[:45]
price_map = {}
try:
    if ids_list:
        rows = get_markets("usd", ids_list)
        price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    price_map = {}

# Snapshot each agent daily
for a in agents:
    port = a.get("portfolio") if isinstance(a.get("portfolio"), dict) else {}
    v = portfolio_value(port, price_map)
    ensure_daily_snapshot(a, v)

save_current_user()

# --- Create agent ---
with st.expander("➕ Create a new agent", expanded=False):
    c1, c2, c3 = st.columns([1.2, 0.8, 1.0])
    with c1:
        new_name = st.text_input("Agent name", value="", placeholder="e.g., Zen Momentum")
    with c2:
        new_emoji = st.text_input("Emoji", value="🤖")
    with c3:
        tmpl = st.selectbox("Starting strategy", options=[t["name"] for t in STRATEGY_TEMPLATES], index=0)
    if st.button("Create agent", type="primary"):
        a = create_agent(user, new_name or "Agent", emoji=new_emoji or "🤖")
        apply_template(a, tmpl)
        grant_xp(user, 75, "Agents", "Created a new agent")
        log_activity(user, f"Created agent {a.get('name')}", icon="🤖")
        save_current_user()
        st.success("Created ✅")
        st.rerun()


soft_divider()

# --- Configure selected agent ---
with st.expander("⚙️ Configure selected agent", expanded=False):
    sig = trust_signals(user, active)
    eff_mode, eff_reason = effective_mode(active, sig)
    st.markdown(f"**Effective autonomy:** `{eff_mode}` — {eff_reason}")
    st.caption("AUTO+ may downgrade automatically if trust signals are not met.")

    c1, c2, c3 = st.columns([1.0, 1.0, 1.0])
    with c1:
        new_mode = st.select_slider(
            "Autonomy ladder",
            options=["off", "assist", "auto", "auto_plus"],
            value=str(active.get("mode") or "assist"),
            help="assist = propose and approve. auto = small practice trades may auto-execute. auto_plus = higher caps if unlocked.",
        )
        active["mode"] = new_mode

    # Caps (optional tuning)
    with c2:
        cfg = active.get("autonomy") if isinstance(active.get("autonomy"), dict) else {}
        active["autonomy"] = cfg
        cfg.setdefault("auto_max_notional_usdc", 10.0)
        cfg.setdefault("auto_plus_max_notional_usdc", 40.0)
        cap = st.number_input("Auto notional cap (USDC)", min_value=1.0, max_value=500.0, value=float(cfg.get("auto_max_notional_usdc") or 10.0), step=1.0)
        capp = st.number_input("Auto+ notional cap (USDC)", min_value=5.0, max_value=2000.0, value=float(cfg.get("auto_plus_max_notional_usdc") or 40.0), step=5.0)
        cfg["auto_max_notional_usdc"] = float(cap)
        cfg["auto_plus_max_notional_usdc"] = float(capp)

    with c3:
        cfg = active.get("autonomy") if isinstance(active.get("autonomy"), dict) else {}
        cfg.setdefault("auto_max_trades_per_day", 2)
        cfg.setdefault("auto_plus_max_trades_per_day", 6)
        tpd = st.number_input("Auto trades/day", min_value=0, max_value=25, value=int(cfg.get("auto_max_trades_per_day") or 2), step=1)
        tpd2 = st.number_input("Auto+ trades/day", min_value=0, max_value=50, value=int(cfg.get("auto_plus_max_trades_per_day") or 6), step=1)
        cfg["auto_max_trades_per_day"] = int(tpd)
        cfg["auto_plus_max_trades_per_day"] = int(tpd2)
        active["autonomy"] = cfg

    st.write("")
    st.subheader("Strategy")
    strat = active.get("strategy") if isinstance(active.get("strategy"), dict) else {}
    cur_name = str(strat.get("name") or "Balanced")
    opts = [t["name"] for t in STRATEGY_TEMPLATES]
    try:
        i0 = opts.index(cur_name)
    except Exception:
        i0 = 0
    pick = st.selectbox("Template", options=opts, index=i0, help="A lightweight template that influences trade suggestions.")
    about = next((t.get("about") for t in STRATEGY_TEMPLATES if t.get("name") == pick), "")
    st.caption(str(about or ""))

    if st.button("Save agent settings", type="primary"):
        active.setdefault("strategy", {})
        if isinstance(active["strategy"], dict):
            tmpl = next((t for t in STRATEGY_TEMPLATES if t.get("name") == pick), None)
            if tmpl:
                active["strategy"]["name"] = tmpl["name"]
                active["strategy"]["params"] = dict(tmpl.get("params") or {})
        save_current_user()
        st.success("Saved.")
        st.rerun()

soft_divider()


# --- Active agent quick controls ---
st.markdown('<div class="card card-strong">', unsafe_allow_html=True)
ac1, ac2, ac3, ac4 = st.columns([1.2, 1.0, 1.0, 1.0])
with ac1:
    st.markdown(f"<div style='font-weight:860'>Active</div><div style='font-size:1.15rem;font-weight:900;margin-top:2px'>{agent_label(active)}</div>", unsafe_allow_html=True)
with ac2:
    mode = str(active.get("mode") or "assist")
    sig = trust_signals(user, active)
    eff_mode, _ = effective_mode(active, sig)
    st.caption("Autonomy")
    st.write(f"**{str(mode).upper()}**")
    st.caption(f"Effective: {eff_mode}")
with ac3:
    strat = active.get("strategy") if isinstance(active.get("strategy"), dict) else {}
    st.caption("Strategy")
    st.write(f"**{str(strat.get('name','Balanced'))}**")
with ac4:
    if st.button("Open Chat", key="agents_go_chat", use_container_width=True):
        st.switch_page("pages/chat.py")

st.markdown('</div>', unsafe_allow_html=True)

soft_divider()

# --- Agent grid ---
st.subheader("Your agents")
if not agents:
    callout("warn", "No agents found", "Create an agent above.")
else:
    # --- Browse controls (v1) ---
    f1, f2, f3 = st.columns([1.6, 1.0, 1.0])
    with f1:
        q = st.text_input("Search agents", key="agents_search", placeholder="Search by name, emoji, or strategy…")
    with f2:
        sort_by = st.selectbox("Sort by", options=["Active first", "Value", "P&L", "Return"], index=0)
    with f3:
        view_cols = st.selectbox("Layout", options=["3 columns", "2 columns"], index=0)

    # Precompute lightweight metrics for sorting/filtering (display-only)
    cards = []
    ql = (q or "").strip().lower()
    for a in agents:
        port = a.get("portfolio") if isinstance(a.get("portfolio"), dict) else {}
        v = portfolio_value(port, price_map)
        inc = since_inception(a, v)
        win = returns_windows(a, v)
        label = agent_label(a)
        strategy_name = str(((a.get("strategy") or {}) if isinstance(a.get("strategy"), dict) else {}).get("name") or "")
        searchable = f"{label} {strategy_name}".lower()
        if ql and ql not in searchable:
            continue
        cards.append((a, v, inc, win, label, strategy_name))

    def _is_active(a):
        return str(a.get("id")) == str(user.get("active_agent_id"))

    if sort_by == "Value":
        cards.sort(key=lambda t: float(t[1] or 0.0), reverse=True)
    elif sort_by == "P&L":
        cards.sort(key=lambda t: float((t[2] or {}).get("profit", 0.0) or 0.0), reverse=True)
    elif sort_by == "Return":
        cards.sort(key=lambda t: float((t[2] or {}).get("return_pct", 0.0) or 0.0), reverse=True)
    else:
        cards.sort(key=lambda t: (not _is_active(t[0]), -float(t[1] or 0.0)))

    cols_n = 3 if view_cols == "3 columns" else 2
    cols = st.columns(cols_n)
    for i, (a, v, inc, win, label, strategy_name) in enumerate(cards):
        port = a.get("portfolio") if isinstance(a.get("portfolio"), dict) else {}
        v = portfolio_value(port, price_map)
        inc = since_inception(a, v)
        win = returns_windows(a, v)

        pl_kind = "good" if float(inc.get("profit", 0.0) or 0.0) >= 0 else "bad"

        is_active = str(a.get("id")) == str(user.get("active_agent_id"))
        badge = "Active" if is_active else (a.get("strategy") or {}).get("name", "Strategy")

        with cols[i % 3]:
            st.markdown(
                '<div class="card" style="margin-bottom:0.75rem">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">'
                f'<div style="font-weight:900;font-size:1.05rem">{agent_label(a)}</div>'
                f'<div class="badge"><span class="badge-dot"></span><span>{badge}</span></div>'
                f'</div>'
                f'<div style="margin-top:0.5rem;display:flex;gap:0.55rem;flex-wrap:wrap">'
                f'<span class="pill info"><span class="k">Value</span><span>${v:,.2f}</span></span>'
                f'<span class="pill {pl_kind}"><span class="k">P&amp;L</span><span>${inc["profit"]:,.2f}</span></span>'
                f'<span class="pill"><span class="k">Return</span><span>{inc["return_pct"]:+.2f}%</span></span>'
                f'</div>'
                f'<div style="color:var(--muted);font-size:0.84rem;margin-top:0.55rem">'
                f'Daily {win["daily"]["return_pct"]:+.2f}% · Weekly {win["weekly"]["return_pct"]:+.2f}% · Monthly {win["monthly"]["return_pct"]:+.2f}% · Yearly {win["yearly"]["return_pct"]:+.2f}%'
                f'</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Select", key=f"sel_{a.get('id')}", use_container_width=True, disabled=is_active):
                    set_active_agent(user, str(a.get("id")))
                    save_current_user()
                    st.rerun()
            with b2:
                if st.button("Copy", key=f"cpy_{a.get('id')}", use_container_width=True, disabled=is_active):
                    st.session_state["copy_target_id"] = str(a.get("id"))
                    st.session_state["copy_source_id"] = str(active.get("id"))
                    st.session_state["copy_mode"] = "params"
                    st.session_state["open_copy_modal"] = True
            with b3:
                if st.button(
                    "Delete",
                    key=f"del_{a.get('id')}",
                    use_container_width=True,
                    disabled=is_active and len(agents) == 1,
                ):
                    st.session_state["confirm_delete_agent_id"] = str(a.get("id"))


# --- Confirm delete (prevents accidental clicks during demos) ---
confirm_id = str(st.session_state.get("confirm_delete_agent_id") or "")
if confirm_id:
    tgt = next((a for a in agents if str(a.get("id")) == confirm_id), None)
    if tgt:
        soft_divider()
        callout(
            "warn",
            "Confirm delete",
            f"Delete <b>{agent_label(tgt)}</b>? This removes its portfolio + chat history (local demo only).",
        )
        c1, c2 = st.columns(2)
        with c1:
            button_style("confirm_del_yes", "bad")
            if st.button("Yes, delete", key="confirm_del_yes", use_container_width=True):
                delete_agent(user, confirm_id)
                st.session_state["confirm_delete_agent_id"] = ""
                save_current_user()
                st.warning("Deleted")
                st.rerun()
        with c2:
            if st.button("Cancel", key="confirm_del_no", use_container_width=True):
                st.session_state["confirm_delete_agent_id"] = ""
                st.rerun()

# --- Copy strategy panel ---
if st.session_state.get("open_copy_modal"):
    st.markdown('<div class="card card-strong">', unsafe_allow_html=True)
    st.markdown("<div style='font-weight:900'>Copy strategy</div><div style='color:var(--muted);margin-top:4px'>Copy a strategy from one agent to another (demo).</div>", unsafe_allow_html=True)

    ids = [str(a.get("id")) for a in agents]
    id_to_label = {str(a.get("id")): agent_label(a) for a in agents}

    c1, c2, c3, c4 = st.columns([1.3, 1.3, 0.9, 0.8])
    with c1:
        src = st.selectbox("Source", options=ids, format_func=lambda x: id_to_label.get(x, x), key="copy_source_id")
    with c2:
        tgt = st.selectbox("Target", options=ids, format_func=lambda x: id_to_label.get(x, x), key="copy_target_id")
    with c3:
        mode = st.selectbox("Mode", options=["full", "params"], key="copy_mode")
    with c4:
        st.write("")
        if st.button("Close", key="copy_close", use_container_width=True):
            st.session_state["open_copy_modal"] = False
            st.rerun()

    if st.button("Apply copy", type="primary"):
        src_a = next((a for a in agents if str(a.get("id")) == str(src)), None)
        tgt_a = next((a for a in agents if str(a.get("id")) == str(tgt)), None)
        if not src_a or not tgt_a:
            st.error("Pick valid source/target.")
        elif str(src_a.get("id")) == str(tgt_a.get("id")):
            st.error("Source and target must be different.")
        else:
            copy_strategy(src_a, tgt_a, mode=mode)
            grant_xp(user, 40, "Agents", "Copied a strategy")
            log_activity(user, f"Copied strategy {src_a.get('name')} → {tgt_a.get('name')}", icon="🧬")
            save_current_user()
            st.success("Copied ✅")
            st.session_state["open_copy_modal"] = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

save_current_user()