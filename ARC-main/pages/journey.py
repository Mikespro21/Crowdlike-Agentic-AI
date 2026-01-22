import streamlit as st

from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit
from crowdlike.layout import render_sidebar
from crowdlike.ui import apply_ui, hero, soft_divider, callout, button_style, nav
from crowdlike.agents import get_agents, create_agent
from crowdlike.version import VERSION


st.set_page_config(page_title="Onboarding • Crowdlike", page_icon="🧭", layout="wide")
apply_ui()

# Navbar + session user
nav(active="journey")
user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "journey")

# Sidebar
render_sidebar(user, active_page="journey")


def _set_step(n: int) -> None:
    st.session_state["onboard_step"] = n


def _complete() -> None:
    st.session_state["onboard_complete"] = True
    user["onboarded"] = True
    save_current_user()
    st.success("Setup complete. Redirecting to Dashboard…")
    st.switch_page("pages/dashboard.py")


# Session defaults
if "onboard_step" not in st.session_state:
    st.session_state["onboard_step"] = 1
if "onboard_complete" not in st.session_state:
    st.session_state["onboard_complete"] = bool(user.get("onboarded"))

# If already onboarded, offer reset instead of forcing
if st.session_state.get("onboard_complete"):
    hero("🧭 Onboarding", "You're already set up", "You can restart the onboarding anytime, or go straight to the app.")
    c1, c2 = st.columns([1, 1])
    with c1:
        button_style("go_dash", "purple")
        if st.button("Go to Dashboard", key="go_dash", use_container_width=True):
            st.switch_page("pages/dashboard.py")
    with c2:
        button_style("restart_onb", "ghost")
        if st.button("Restart onboarding", key="restart_onb", use_container_width=True):
            st.session_state["onboard_complete"] = False
            st.session_state["onboard_step"] = 1
            st.experimental_rerun()
    st.stop()

hero(
    "🫧 Crowdlike v" + VERSION,
    "Welcome — let’s get you ready in 60 seconds",
    "This wizard creates a clean baseline: identity → agent → safety defaults. Everything is cloud-session safe.",
)

# Stepper
steps = [
    (1, "Identity", "Pick a name + avatar"),
    (2, "Create agent", "Create your first agent"),
    (3, "Safety defaults", "Set basic guardrails"),
    (4, "Run your first cycle", "Open Coach and run"),
]
active = int(st.session_state["onboard_step"])

st.markdown('<div class="card card-strong">', unsafe_allow_html=True)
cols = st.columns(len(steps), gap="small")
for i, (n, title, sub) in enumerate(steps):
    done = n < active
    is_active = n == active
    with cols[i]:
        badge = "✓" if done else str(n)
        st.markdown(
            f"""
            <div class="pill {'pill-on' if is_active else ''}" style="width:100%; justify-content:center; margin-bottom:8px;">
              <span style="font-weight:900">{badge}</span>&nbsp;{title}
            </div>
            <div style="font-size:0.85rem; color:var(--muted); line-height:1.2">{sub}</div>
            """,
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

soft_divider()

left, right = st.columns([1.2, 1.0], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if active == 1:
        st.markdown("### 1) Identity")
        st.caption("This is just for the demo session. You can change it later in Profile.")
        c1, c2 = st.columns([2, 1], gap="medium")
        with c1:
            name = st.text_input("Display name", value=user.get("display_name") or user.get("username") or "")
        with c2:
            avatar = st.selectbox("Avatar", ["🫧","🧠","🤖","🧑‍🚀","🦋","⚡","🪙","🛰️","🧿","🌊"], index=0)
        user["display_name"] = name.strip() or user.get("display_name") or "Guest"
        user["avatar"] = avatar
        save_current_user()
        callout("Tip: keep the name short for leaderboard cards.", tone="muted")

    elif active == 2:
        st.markdown("### 2) Create your first agent")
        st.caption("Agents are independent portfolios. Start with one and add more later.")
        agents = get_agents(user)
        if agents:
            st.success(f"You already have {len(agents)} agent(s).")
            st.write("You can proceed, or create another.")
        a_name = st.text_input("Agent name", value="Crowdlike Alpha")
        risk = st.slider("Risk level", 1, 100, 35)
        if st.button("Create agent", key="onb_create_agent", type="primary", use_container_width=True):
            create_agent(user, name=a_name.strip() or "Crowdlike Alpha", risk=risk)
            save_current_user()
            st.success("Agent created.")
            st.session_state["onboard_step"] = 3
            st.experimental_rerun()

    elif active == 3:
        st.markdown("### 3) Safety defaults")
        st.caption("These guardrails make the demo feel predictable and safe.")
        policy = user.get("policy") if isinstance(user.get("policy"), dict) else {}
        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            per_tx = st.number_input("Max per action (USDC)", min_value=1.0, value=float(policy.get("max_per_tx_usdc", 15.0)), step=1.0)
        with c2:
            daily = st.number_input("Daily cap (USDC)", min_value=5.0, value=float(policy.get("daily_cap_usdc", 50.0)), step=5.0)
        with c3:
            cooldown = st.number_input("Cooldown (seconds)", min_value=0, value=int(policy.get("cooldown_s", 30)), step=5)
        policy.update({"max_per_tx_usdc": per_tx, "daily_cap_usdc": daily, "cooldown_s": cooldown, "risk": int(policy.get("risk", 35))})
        user["policy"] = policy
        save_current_user()
        callout("You can tune these later in Profile → Limits and Safety.", tone="muted")

    else:
        st.markdown("### 4) Run your first cycle")
        st.caption("We’ll open Coach. There you can run a cycle (plan → propose → approve/execute).")
        st.info("When you click Continue, you’ll be taken to Coach.")
        button_style("open_coach", "purple")
        if st.button("Open Coach", key="open_coach", use_container_width=True):
            _complete()

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card card-strong">', unsafe_allow_html=True)
    st.markdown("### Why this flow exists")
    st.write(
        "- A single clear path for judges\n"
        "- One primary action per step\n"
        "- Safe defaults so autonomy doesn’t feel scary\n"
        "- Cloud-ready session model (no local files)"
    )
    st.markdown("### What you can do next")
    st.write(
        "- Coach: run agent cycles\n"
        "- Market: practice trades + checkout\n"
        "- Analytics: track profit/drawdown\n"
        "- Leaderboards: compare agents"
    )
    st.markdown("</div>", unsafe_allow_html=True)

soft_divider()

# Footer controls
b1, b2, b3 = st.columns([1, 1, 1], gap="large")
with b1:
    button_style("onb_back", "ghost")
    if st.button("Back", key="onb_back", use_container_width=True, disabled=(active <= 1)):
        st.session_state["onboard_step"] = max(1, active - 1)
        st.experimental_rerun()
with b2:
    button_style("onb_skip", "ghost")
    if st.button("Skip for now", key="onb_skip", use_container_width=True):
        _complete()
with b3:
    button_style("onb_next", "purple")
    if st.button("Continue", key="onb_next", use_container_width=True):
        if active < len(steps):
            st.session_state["onboard_step"] = active + 1
            st.experimental_rerun()
        else:
            _complete()
