from __future__ import annotations

"""User-flow helpers (v1.1).

Goal: make the app feel like a coherent product, not a set of pages.

We expose:
- a canonical step model (completion checks)
- a "next best action" resolver
- lightweight UI helpers (banner + sidebar summary)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from crowdlike.agents import get_agents, get_active_agent
from crowdlike.ui import callout, soft_divider, button_style


@dataclass(frozen=True)
class FlowStep:
    id: str
    label: str
    page: str
    desc: str
    # When True, the step is optional (won't block "complete")
    optional: bool = False


# Canonical v1.1 user journey (fast, product-like).
FLOW_STEPS: List[FlowStep] = [
    FlowStep("agents", "Create an agent", "pages/agents.py", "Create or select an agent with its own portfolio."),
    FlowStep("wallet", "Add your wallet", "pages/profile.py", "Paste a public 0x address (never a private key)."),
    FlowStep("limits", "Set limits", "pages/profile.py", "Pick a preset (Conservative/Balanced/Aggressive)."),
    FlowStep("run", "Run a cycle", "pages/coach.py", "Generate a run report and (optionally) a proposal."),
    FlowStep("analytics", "Review performance", "pages/analytics.py", "See profit/return, risk, drawdown, and runs."),
    FlowStep("verify", "Verify a receipt", "pages/market.py", "Testnet checkout → paste tx hash → verify."),
]


def _readiness(user: Dict[str, Any]) -> Dict[str, bool]:
    wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
    wallet_addr = (wallet.get("address") or "").strip()
    wallet_set = bool(wallet_addr)

    policy = user.get("policy") if isinstance(user.get("policy"), dict) else {}
    limits_set = any(k in policy for k in ("max_per_tx_usdc", "daily_cap_usdc", "cooldown_s", "risk"))

    has_verified = any((p or {}).get("status") == "verified" for p in (user.get("purchases") or []))

    agents = get_agents(user)
    has_agents = bool(agents)

    active = get_active_agent(user) if has_agents else {}
    runs = active.get("runs") if isinstance(active.get("runs"), list) else []
    has_run = bool(runs)

    # Analytics step is considered complete if you have at least one run or trade.
    port = active.get("portfolio") if isinstance(active.get("portfolio"), dict) else {}
    trades = port.get("trades") if isinstance(port.get("trades"), list) else []
    analytics_ready = has_run or bool(trades)

    return {
        "agents": has_agents,
        "wallet": wallet_set,
        "limits": limits_set,
        "run": has_run,
        "analytics": analytics_ready,
        "verify": has_verified,
    }


def next_step(user: Dict[str, Any]) -> Optional[FlowStep]:
    r = _readiness(user)
    for step in FLOW_STEPS:
        if step.optional:
            continue
        if not r.get(step.id, False):
            return step
    return None


def progress(user: Dict[str, Any]) -> Tuple[int, int, List[Tuple[FlowStep, bool]]]:
    r = _readiness(user)
    rows: List[Tuple[FlowStep, bool]] = [(s, bool(r.get(s.id, False))) for s in FLOW_STEPS]
    done = sum(1 for _, ok in rows if ok)
    total = len(rows)
    return done, total, rows


def flow_banner(user: Dict[str, Any], *, active: str = "") -> None:
    """Small, consistent banner at top of key pages: progress + next action."""
    done, total, rows = progress(user)
    ns = next_step(user)

    # Compact summary row
    st.markdown(
        f'<div class="card card-strong" style="padding:12px 14px;">'
        f'<div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">'
        f'<div style="font-weight:850;">🧭 Journey</div>'
        f'<div style="color:var(--muted); font-size:0.95rem;">{done}/{total} steps complete</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Stepper pills (scrollable)
    st.markdown('<div style="overflow-x:auto; white-space:nowrap; padding:6px 2px 2px 2px;">', unsafe_allow_html=True)
    for step, ok in rows:
        label = ("✅ " if ok else "⬜ ") + step.label
        active_style = "border:1px solid rgba(99,102,241,0.35);" if (active and step.label == active) else ""
        st.markdown(
            f'<span style="display:inline-block; margin-right:8px; padding:6px 10px; border-radius:999px; '
            f'background:rgba(255,255,255,0.65); {active_style} '
            f'box-shadow:0 1px 10px rgba(15,23,42,0.06); font-size:0.9rem;">{label}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if ns:
        soft_divider()
        callout(
            f"**Next:** {ns.label}\n\n{ns.desc}",
            tone="muted",
        )
        button_style("flow_continue", "purple")
        if st.button(f"Continue → {ns.label}", key="flow_continue", use_container_width=True):
            st.switch_page(ns.page)


def sidebar_flow_card(user: Dict[str, Any], *, active_page: str = "") -> None:
    """Sidebar version: always visible 'what next' + quick continue button."""
    done, total, rows = progress(user)
    ns = next_step(user)

    st.markdown("**Journey**")
    st.caption(f"{done}/{total} steps complete")

    st.markdown('<div style="max-height:180px; overflow-y:auto; padding-right:6px;">', unsafe_allow_html=True)
    for step, ok in rows:
        st.write(("✅ " if ok else "⬜ ") + step.label)
        st.caption(step.desc)
    st.markdown("</div>", unsafe_allow_html=True)

    if ns:
        button_style("sb_continue", "purple")
        if st.button(f"Continue → {ns.label}", key=f"sb_continue_{active_page}", use_container_width=True):
            st.switch_page(ns.page)
        st.caption("Or open the full wizard.")
        if st.button("Open Journey wizard", key=f"sb_open_journey_{active_page}", use_container_width=True):
            st.switch_page("pages/journey.py")
    else:
        callout("You’re fully set up. Run cycles and explore leaderboards.", tone="success")
