import streamlit as st

from crowdlike.settings import bool_setting
from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout, button_style, metric_card
from crowdlike.tour import maybe_run_tour
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp, add_notification, log_activity
from crowdlike.layout import render_sidebar

st.set_page_config(page_title="Shop", page_icon="🛍️", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
maybe_run_tour(user, current_page="shop")
ensure_user_schema(user)
record_visit(user, "shop")

render_sidebar(user, active_page="shop")
save_current_user()

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
score = float(crowd.get("score", 50.0) or 50.0)

hero("🛍️ Shop", "Upgrades, perks, and judge-friendly checkouts.", badge="Store")

status_bar(wallet_set=wallet_set, demo_mode=_demo, crowd_score=score)

coins = int(user.get("coins", 0) or 0)
owned = set(user.get("inventory") or [])

m1, m2, m3 = st.columns(3)
with m1:
    metric_card("Your coins", f"{coins:,}", "Earned by quests", accent="purple")
with m2:
    metric_card("Crowd Score", f"{score:.0f}", "Gently boosts limits", accent="blue")
with m3:
    metric_card("Owned", f"{len(owned)} items", "Local-only inventory", accent="none")

soft_divider()

st.subheader("Coin items (instant)")
items = [
    {"id": "glass_theme", "name": "Glassy Theme Pack", "desc": "Smoother cards + subtle motion polish.", "cost": 150},
    {"id": "agent_boost", "name": "Agent Readiness Boost", "desc": "Unlocks a guided Agent checklist + extra prompts.", "cost": 250},
    {"id": "social_badge", "name": "Community Badge", "desc": "Adds a badge to your profile + a small crowd bump.", "cost": 200},
]

cols = st.columns(3)
for i, it in enumerate(items):
    with cols[i % 3]:
        st.markdown(
            '<div class="card">'
            f'<div style="font-weight:880">{it["name"]}</div>'
            f'<div style="color:var(--muted);margin-top:6px">{it["desc"]}</div>'
            f'<div style="margin-top:0.65rem;font-weight:900">{it["cost"]} coins</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if it["id"] in owned:
            st.button("Owned", key=f"owned_{it['id']}", disabled=True, use_container_width=True)
        else:
            can = coins >= it["cost"]
            button_style(f"buy_{it['id']}", "purple" if can else "white")
            if st.button("Buy", key=f"buy_{it['id']}", disabled=not can, use_container_width=True, type="primary" if can else "secondary"):
                user["coins"] = int(user.get("coins", 0) or 0) - int(it["cost"])
                user.setdefault("inventory", []).append(it["id"])
                grant_xp(user, 10, "Shop", f"Bought {it['name']}")
                add_notification(user, "Purchased", it["name"])
                log_activity(user, f"Bought {it['name']} for {it['cost']} coins", icon="🛒")
                if it["id"] == "social_badge":
                    crowd = user.setdefault("crowd", {"score": 50.0, "likes_received": 0, "likes_given": 0})
                    crowd["score"] = float(crowd.get("score", 50.0)) + 2.0
                save_current_user()
                st.rerun()

soft_divider()
st.subheader("Premium perks (testnet USDC)")

callout(
    "info",
    "Proof-of-receipt flow",
    "Pick a perk → generate a command → run it locally → paste the tx hash. The app verifies and unlocks the perk.",
)

p1, p2 = st.columns(2)
with p1:
    st.markdown(
        '<div class="card card-strong">'
        '<div style="font-weight:880">VIP Pass</div>'
        '<div style="color:var(--muted);margin-top:6px">Unlock VIP drops + a flex badge (demo).</div>'
        '<div style="margin-top:0.65rem;font-weight:950;font-size:1.15rem">$1.00 USDC</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    button_style("shop_buy_vip", "purple" if wallet_set else "white")
    if st.button("Buy with USDC →", key="shop_buy_vip", use_container_width=True, type="primary", disabled=not wallet_set):
        st.session_state["checkout_offer_id"] = "vip_pass"
        st.session_state["checkout_step"] = 1
        st.switch_page("pages/market.py")
    if not wallet_set:
        st.caption("Add a wallet first (Profile).")

with p2:
    st.markdown(
        '<div class="card card-strong">'
        '<div style="font-weight:880">Creator Tip</div>'
        '<div style="color:var(--muted);margin-top:6px">Tip the community treasury (demo).</div>'
        '<div style="margin-top:0.65rem;font-weight:950;font-size:1.15rem">$0.10 USDC</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    button_style("shop_buy_tip", "blue" if wallet_set else "white")
    if st.button("Tip with USDC →", key="shop_buy_tip", use_container_width=True, disabled=not wallet_set):
        st.session_state["checkout_offer_id"] = "creator_tip"
        st.session_state["checkout_step"] = 1
        st.switch_page("pages/market.py")
    if not wallet_set:
        st.caption("Add a wallet first (Profile).")

save_current_user()
