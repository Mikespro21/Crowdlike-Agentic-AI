import uuid
import streamlit as st

from crowdlike.settings import bool_setting
from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, metric_card, callout, button_style, xp_bar
from crowdlike.tour import maybe_run_tour
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, add_notification, log_activity
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event


st.set_page_config(page_title="Social", page_icon="🫶", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
maybe_run_tour(user, current_page="social")
ensure_user_schema(user)
record_visit(user, "social")

render_sidebar(user, active_page="social")
save_current_user()

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
wallet_set = bool((wallet.get("address") or "").strip())

hero("🫶 Social", "Likes are the crowd feedback loop — they gently influence what your agent can do.", badge="Crowd")

crowd = user.setdefault("crowd", {"score": 50.0, "likes_received": 0, "likes_given": 0})
feed = user.setdefault("social_feed", [])

# Seed demo posts once
if not feed:
    feed.extend([
        {"id": "p1", "author": "Arc Builder", "text": "Tip: Start with low limits, then raise after your first verified receipt.", "likes": 3},
        {"id": "p2", "author": "Crowdlike", "text": "Crowd Score gently boosts limits (±20%) but never breaks your safety rails.", "likes": 5},
        {"id": "p3", "author": "Demo User", "text": "I verified my first checkout — smooth!", "likes": 2},
    ])
    save_current_user()

score = float(crowd.get("score", 50.0) or 50.0)
status_bar(wallet_set=wallet_set, demo_mode=_demo, crowd_score=score)

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Crowd Score", f"{score:.0f}", "Target 70+ for smoother autonomy", accent="purple")
with c2:
    metric_card("Likes given", f"{int(crowd.get('likes_given',0) or 0)}", "Participation boosts score", accent="blue")
with c3:
    metric_card("Likes received", f"{int(crowd.get('likes_received',0) or 0)}", "Social proof signal", accent="none")

xp_bar(min(1.0, max(0.0, score / 100.0)), left="0", right="100")

soft_divider()
st.subheader("Post an update")

callout(
    "info",
    "Good posts for judges",
    "Try: “I verified a checkout” or “I set my limits to $0.10/tx” — it shows the feedback loop clearly.",
)

suggest = st.columns(3)
with suggest[0]:
    if st.button("Verified my first receipt ✅", key="sugg_1", use_container_width=True):
        st.session_state["draft_post"] = "Just verified my first checkout ✅ Raised my daily cap to $0.50."
with suggest[1]:
    if st.button("Set limits 🛡️", key="sugg_2", use_container_width=True):
        st.session_state["draft_post"] = "Set my safety limits: $0.10/tx with a 15s cooldown. Feeling safe."
with suggest[2]:
    if st.button("Agent plan 🤖", key="sugg_3", use_container_width=True):
        st.session_state["draft_post"] = "My agent plan: small tips + strict limits + verify receipts before scaling."

draft = st.session_state.get("draft_post", "")

with st.form("post_form", clear_on_submit=True):
    txt = st.text_area(
        "What are you building?",
        value=draft,
        placeholder="e.g., I verified a checkout and adjusted my limits…",
        height=100,
        max_chars=280,
    )
    submitted = st.form_submit_button("Post")
    if submitted:
        msg = (txt or "").strip()
        st.session_state["draft_post"] = ""
        if not msg:
            st.warning("Write something first.")
        else:
            feed.insert(0, {"id": str(uuid.uuid4()), "author": user.get("username", "Member"), "text": msg[:280], "likes": 0})
            log_activity(user, "Posted an update", icon="🫶")
            log_event(user, kind="social", title="New post", details=msg[:80], severity="info", agent_id=str(user.get("active_agent_id") or ""))
            save_current_user()
            st.success("Posted.")
            st.rerun()

soft_divider()
st.subheader("Feed")

for p in feed[:25]:
    with st.container():
        st.markdown(
            '<div class="card">'
            f'<div style="display:flex; align-items:center; justify-content:space-between; gap:10px">'
            f'<div style="font-weight:880">{p.get("author","")}</div>'
            f'<div class="badge"><span class="badge-dot"></span><span>{int(p.get("likes",0) or 0)} likes</span></div>'
            f'</div>'
            f'<div style="color:var(--muted);margin-top:6px">{p.get("text","")}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 3])
        with cols[0]:
            button_style(f"like_{p.get('id')}", "blue")
            if st.button("Like", key=f"like_{p.get('id')}", use_container_width=True):
                p["likes"] = int(p.get("likes", 0) or 0) + 1
                crowd["likes_given"] = int(crowd.get("likes_given", 0) or 0) + 1
                crowd["score"] = float(crowd.get("score", 50.0) or 50.0) + 0.3
                add_notification(user, "Liked", f"You liked {p.get('author','a post')}.")
                save_current_user()
                st.rerun()
        with cols[1]:
            st.caption("Tip: Liking posts is the quickest way to demonstrate the crowd-feedback loop.")

soft_divider()
st.subheader("How this changes autonomy")

callout(
    "good",
    "Crowd Score → limits (bounded)",
    "Crowd Score can nudge your max-per-tx and daily cap by up to ±20%, but it never overrides your safety settings.",
)

save_current_user()
