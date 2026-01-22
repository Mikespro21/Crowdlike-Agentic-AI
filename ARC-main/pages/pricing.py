import streamlit as st

from crowdlike.ui import apply_ui, soft_divider, callout, metric_card
from crowdlike.site import site_footer, site_header, site_hero
from crowdlike.pricing import quote_daily
from crowdlike.auth import current_user
from crowdlike.agents import get_agents
from crowdlike.version import VERSION


st.set_page_config(page_title="Crowdlike — Pricing", page_icon="💳", layout="wide")
apply_ui()

site_header(active="pricing")


site_hero(kicker=f"Crowdlike v{VERSION}", title="Pricing", subtitle="Transparent demo tiers for autonomy, limits, approvals, and enterprise-style guardrails—no surprises, just control.")

soft_divider()

u = current_user() or None
default_agents = 3
if u:
    try:
        default_agents = max(1, len(get_agents(u)))
    except Exception:
        default_agents = 3

c1, c2 = st.columns([1.2, 1.0], gap="large")
with c1:
    callout(
        "Formula",
        "**price_per_day = (agentCount²) × (risk / 100)**",
        tone="muted",
    )
    st.markdown("### Estimate")
    agent_count = st.slider("Number of agents", 1, 20, int(default_agents))
    risk = st.slider("Risk (0–100)", 0, 100, 35)
with c2:
    q = quote_daily(agent_count=agent_count, risk=risk)
    metric_card("Estimated price / day", f"{q['price']:.4f}", "Demo units")
    metric_card("Agents", str(agent_count), "Count")
    metric_card("Risk", f"{risk}/100", "User setting")
    st.markdown("### Notes")
    st.write("- AUTO/AUTO+ does not change the base price in this demo build.")
    st.write("- Higher risk increases price because it increases potential impact and monitoring needs.")

soft_divider()

callout(
    "Next step",
    "If you want personalized pricing using your actual agents, launch the app and create agents first.",
    tone="muted",
)

c1, c2 = st.columns([1.0, 1.0], gap="large")
with c1:
    st.page_link("pages/dashboard.py", label="🚀 Dashboard", use_container_width=True)
with c2:
    st.page_link("pages/journey.py", label="🧭 Guided Journey", use_container_width=True)

site_footer()
