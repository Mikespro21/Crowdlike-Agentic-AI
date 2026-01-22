import streamlit as st

from crowdlike.ui import (
    apply_ui,
    hero,
    soft_divider,
    status_bar,
    callout,
    event_feed,
    metric_card,
    pills,
)
from crowdlike.settings import bool_setting
from crowdlike.tour import maybe_run_tour
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp, log_activity
from crowdlike.agents import get_active_agent, agent_label
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event, recent_events
from crowdlike.orchestrator import propose_next_action
from crowdlike.runs import run_agent_cycle
from crowdlike.autonomy import trust_signals, effective_mode
from crowdlike.crowd_deviation import deviation_pct
from crowdlike.copying import apply_copy
from crowdlike.audit import log_audit
from crowdlike.market_data import get_markets


from crowdlike.flow import flow_banner
st.set_page_config(page_title="Coach • Crowdlike", page_icon="🤖", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "coach")

render_sidebar(user, active_page="coach")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
_crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(_crowd.get("score", 50.0) or 50.0))
flow_banner(user, active="Run a cycle")

active_agent = get_active_agent(user)

hero(
    "🤖 Coach",
    "Run structured agent cycles, review approvals, and understand exactly why actions were allowed or blocked.",
    badge=agent_label(active_agent),
)

maybe_run_tour(user, "coach")

# --- Market snapshot (best-effort) ---
WATCHLIST = ["bitcoin", "ethereum", "solana", "matic-network", "usd-coin", "tether"]
rows = []
price_map = {}
try:
    rows = get_markets("usd", WATCHLIST)
    price_map = {r.id: float(r.current_price) for r in rows}
except Exception:
    rows = []
    price_map = {}

# --- Top-level view switch (keeps the page uncluttered) ---
view = st.radio(
    "Coach view",
    options=["Run", "Approvals", "Activity"],
    horizontal=True,
    label_visibility="collapsed",
)

def _render_signals() -> None:
    sig = trust_signals(user, active_agent)
    eff_mode, eff_reason = effective_mode(active_agent, sig)

    pills([
        ("Effective", eff_mode, "good" if eff_mode in ("assist", "auto", "auto_plus") else "warn"),
        ("Crowd score", f"{sig.crowd_score:.0f}", "info"),
        ("Receipts", str(sig.verified_receipts), "info"),
        ("Deviation", f"{sig.deviation_pct:.1f}%", "warn" if sig.deviation_pct >= 20 else "info"),
        ("Safety", "OK" if sig.safety_ok else "CHECK", "good" if sig.safety_ok else "bad"),
    ])

    callout(
        f"**Why this mode?** {eff_reason}",
        tone="muted" if eff_mode in ("assist", "auto", "auto_plus") else "warning",
    )

def _render_run() -> None:
    st.markdown("### Autonomy")
    c1, c2 = st.columns([1.2, 1.0])

    with c1:
        mode = str(active_agent.get("mode") or "assist")
        mode = st.select_slider(
            "Autonomy ladder",
            options=["off", "assist", "auto", "auto_plus"],
            value=mode if mode in ("off", "assist", "auto", "auto_plus") else "assist",
            help="assist = proposes actions that require approval. auto = executes within caps. auto_plus = higher caps only when trust signals unlock it.",
        )
        active_agent["mode"] = mode

        with st.expander("Policy constraints", expanded=False):
            pol = user.get("policy") if isinstance(user.get("policy"), dict) else {}
            try:
                max_dev = float(pol.get("max_deviation_pct", 20.0) or 20.0)
            except Exception:
                max_dev = 20.0
            max_dev = st.slider(
                "Max crowd deviation (%)",
                min_value=0.0,
                max_value=80.0,
                step=1.0,
                value=float(max_dev),
                help="If an agent drifts too far from the crowd, actions are constrained (queued for approval or blocked by safety).",
            )
            pol["max_deviation_pct"] = float(max_dev)
            user["policy"] = pol

            # Live deviation preview (fast and judge-friendly)
            try:
                dev_now = float(deviation_pct(user, active_agent) or 0.0)
            except Exception:
                dev_now = 0.0
            callout(
                f"Current deviation: **{dev_now:.1f}%** (max {max_dev:.1f}%)",
                tone="warning" if dev_now > max_dev else "muted",
            )

    with c2:
        st.markdown("### Trust signals")
        _render_signals()
        st.caption("These signals determine what agents are allowed to do without approval.")


soft_divider()

st.markdown("### Run cycle")
r1, r2, r3 = st.columns([1.2, 1.0, 1.0])

with r1:
    if st.button("Run agent cycle", type="primary", use_container_width=True):
        report = run_agent_cycle(user, active_agent, markets=rows if isinstance(rows, list) else None, reason="coach")
        prop = report.get("proposal") if isinstance(report.get("proposal"), dict) else {}
        title = str(prop.get("title") or "Action")

        if report.get("executed"):
            st.success(f"Executed: {title}")
        elif report.get("queued"):
            st.success(f"Queued for approval: {title}")
        else:
            dec = report.get("decision") if isinstance(report.get("decision"), dict) else {}
            st.info(str(dec.get("reason") or "No action"))
        save_current_user()
        st.rerun()

with r2:
    if st.button("Generate proposal only", use_container_width=True):
        p = propose_next_action(user, active_agent, markets=rows if isinstance(rows, list) else None)
        log_event(
            user,
            kind="agent",
            title="New proposal",
            details=str(p.get("title") or "proposal"),
            severity="info",
            agent_id=str(active_agent.get("id")),
        )
        log_audit(
            user,
            kind="proposal",
            msg=f"Proposed: {p.get('title')}",
            agent_id=str(active_agent.get("id")),
            proposal_id=str(p.get("id")),
        )
        grant_xp(user, 10, "Coach", "Generated proposal")
        log_activity(user, "Generated a proposal", icon="🤖")
        save_current_user()
        st.success("Proposal queued ✅")
        st.rerun()

with r3:
    st.caption("Tip: approvals appear in the next tab.")
    st.markdown("")

# Preview last run report (if present)
runs = active_agent.get("runs") if isinstance(active_agent.get("runs"), list) else []
if runs:
    last = runs[-1] if isinstance(runs[-1], dict) else None
    if last:
        with st.expander("Last run report", expanded=False):
            st.markdown(f"**Run ID:** `{last.get('run_id','')}`")
            st.caption(str(last.get("reason") or ""))
            dec = last.get("decision") if isinstance(last.get("decision"), dict) else {}
            st.markdown(f"**Decision:** {dec.get('status','')} — {dec.get('reason','')}")
            prop = last.get("proposal") if isinstance(last.get("proposal"), dict) else {}
            if prop:
                st.markdown(f"**Proposed:** {prop.get('title','')}")
                st.caption(f"Type: {prop.get('type','')} · Mode: {prop.get('mode','')}")
else:
    callout("Run your first cycle to generate a report and see the agent workflow end-to-end.", tone="muted")


def _render_approvals() -> None:
    st.markdown("### Pending approvals")
    approvals = active_agent.get("approvals") if isinstance(active_agent.get("approvals"), list) else []
    if not approvals:
        callout("No pending approvals. Generate a proposal in the Run tab.", tone="muted")
        return

    for i, p in enumerate(list(approvals)[:16]):
        if not isinstance(p, dict):
            continue

        with st.container(border=True):
            st.markdown(f"**{p.get('title','Proposal')}**")
            st.caption(f"Type: {p.get('type')} · ID: {p.get('id')}")

            cons = p.get("constraints") if isinstance(p.get("constraints"), dict) else {}
            if cons:
                try:
                    dev = float(cons.get("deviation_pct", 0.0) or 0.0)
                    mx = float(cons.get("max_deviation_pct", 0.0) or 0.0)
                    st.caption(f"Deviation: {dev:.1f}% (max {mx:.1f}%)")
                except Exception:
                    pass

            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("Approve", key=f"appr_yes_{i}", type="primary", use_container_width=True):
                    applied = False
                    try:
                        if str(p.get("type")) == "copy":
                            applied = apply_copy(user, active_agent, p)
                        else:
                            # For non-copy proposals, we simply mark approved and let the run loop handle execution.
                            applied = True
                    except Exception:
                        applied = False

                    # remove proposal
                    try:
                        active_agent["approvals"].remove(p)
                    except Exception:
                        pass

                    log_event(
                        user,
                        kind="agent",
                        title="Approved proposal",
                        details=str(p.get("title") or ""),
                        severity="success" if applied else "info",
                        agent_id=str(active_agent.get("id")),
                    )
                    log_audit(
                        user,
                        kind="approve",
                        msg=f"Approved: {p.get('title')}",
                        agent_id=str(active_agent.get("id")),
                        proposal_id=str(p.get("id")),
                    )
                    save_current_user()
                    st.rerun()

            with cols[1]:
                if st.button("Reject", key=f"appr_no_{i}", use_container_width=True):
                    try:
                        active_agent["approvals"].remove(p)
                    except Exception:
                        pass
                    log_event(
                        user,
                        kind="agent",
                        title="Rejected proposal",
                        details=str(p.get("title") or ""),
                        severity="info",
                        agent_id=str(active_agent.get("id")),
                    )
                    log_audit(
                        user,
                        kind="reject",
                        msg=f"Rejected: {p.get('title')}",
                        agent_id=str(active_agent.get("id")),
                        proposal_id=str(p.get("id")),
                    )
                    save_current_user()
                    st.rerun()


def _render_activity() -> None:
    st.markdown("### Recent events")
    # Let the user choose whether to view all events or just this agent
    scope = st.radio("Scope", options=["This agent", "All agents"], horizontal=True, label_visibility="collapsed")
    if scope == "This agent":
        ev = recent_events(user, agent_id=str(active_agent.get("id")), limit=18)
    else:
        ev = recent_events(user, limit=18)
    event_feed(ev)


if view == "Run":
    _render_run()
elif view == "Approvals":
    _render_approvals()
else:
    _render_activity()

save_current_user()