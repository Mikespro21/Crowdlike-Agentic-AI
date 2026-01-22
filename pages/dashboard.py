import streamlit as st

from crowdlike.ui import apply_ui, callout, hero, metric_card, soft_divider
from crowdlike.layout import render_sidebar
from crowdlike.auth import require_login, save_current_user
from crowdlike.agents import get_active_agent, get_agents
from crowdlike.events import recent_events
from crowdlike.ui import event_feed
from crowdlike.game import ensure_user_schema
from crowdlike.version import VERSION

st.set_page_config(page_title="Crowdlike — Dashboard", page_icon="🚀", layout="wide")
apply_ui()

user = require_login("Crowdlike")
ensure_user_schema(user)

# v{VERSION}: onboarding gate
if not st.session_state.get("onboard_complete") and not user.get("onboarded"):
    callout("You are in a fresh cloud session. Complete onboarding once for the smoothest flow.", tone="warning")
    st.page_link("pages/journey.py", label="Start onboarding →", width="stretch")
    soft_divider()

render_sidebar(user, active_page="dashboard")


hero('Dashboard', subtitle='Your live control panel: agent status, risk posture, recent activity, and next actions.')
st.markdown("## Dashboard")

agents = get_agents(user)
active = get_active_agent(user)

c1, c2, c3 = st.columns([1.2, 1.0, 1.0], gap="large")
with c1:
    callout(
        "Your active agent",
        f"**{active.get('name','Agent')}** is selected. Use Agents to add more, or Coach to run a cycle.",
        tone="muted",
    )
with c2:
    metric_card("Agents", str(len(agents)), "Total agents")
with c3:
    metric_card("Activity", str(len(user.get("events", []))), "Recorded events")

soft_divider()

a, b, c = st.columns([1.0, 1.0, 1.0], gap="large")
with a:
    st.page_link("pages/agents.py", label="🧠 Manage agents", width="stretch")
with b:
    st.page_link("pages/coach.py", label="🤖 Run in Coach", width="stretch")
with c:
    st.page_link("pages/market.py", label="📈 Market / Checkout", width="stretch")

soft_divider()

event_feed(recent_events(user, agent_id=active), title="Recent activity", compact=True)

save_current_user()
