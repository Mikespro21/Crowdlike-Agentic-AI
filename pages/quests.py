import time
import streamlit as st

from crowdlike.settings import bool_setting
from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout, button_style, metric_card
from crowdlike.tour import maybe_run_tour
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit, grant_xp, add_notification, log_activity
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event


st.set_page_config(page_title="Quests", page_icon="🧭", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
maybe_run_tour(user, current_page="quests")
ensure_user_schema(user)
record_visit(user, "quests")

render_sidebar(user, active_page="quests")
save_current_user()

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}

hero("🧭 Quests", "Small, safe steps that build trust — and unlock smoother autonomy.", badge="Daily")

status_bar(wallet_set=wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

today = time.strftime("%Y-%m-%d")
claimed = user.setdefault("quests_claimed", {}).setdefault(today, [])

quests = [
    {"id": "q_wallet", "title": "Set your wallet address", "desc": "Add your wallet address in Profile.", "xp": 20, "coins": 50, "link": "pages/profile.py"},
    {"id": "q_limits", "title": "Set safety limits", "desc": "Pick a risk level and limits in Profile → Limits.", "xp": 20, "coins": 50, "link": "pages/profile.py"},
    {"id": "q_market", "title": "Run a practice trade", "desc": "Use Practice to place a buy/sell.", "xp": 15, "coins": 30, "link": "pages/market.py"},
    {"id": "q_social", "title": "Give 3 likes", "desc": "Like 3 posts in Social.", "xp": 15, "coins": 30, "link": "pages/social.py"},
    {"id": "q_receipt", "title": "Verify a receipt", "desc": "Complete a testnet checkout and verify the tx hash.", "xp": 35, "coins": 70, "link": "pages/market.py"},
]

# Auto-check completion hints (best-effort)
wallet_ok = bool((user.get("wallet") or {}).get("address"))
limits_ok = isinstance(user.get("policy"), dict) and any(k in user["policy"] for k in ("max_per_tx_usdc", "daily_cap_usdc", "cooldown_s"))
has_trade = bool((user.get("portfolio") or {}).get("trades"))
likes_given = int((user.get("crowd") or {}).get("likes_given", 0) or 0)
has_verified = any((p or {}).get("status") == "verified" for p in (user.get("purchases") or []))

completion = {
    "q_wallet": wallet_ok,
    "q_limits": limits_ok,
    "q_market": has_trade,
    "q_social": likes_given >= 3,
    "q_receipt": has_verified,
}

done_count = sum(1 for q in quests if q["id"] in claimed)
total = len(quests)

m1, m2, m3 = st.columns(3)
with m1:
    metric_card("Claimed today", f"{done_count}/{total}", "Resets daily", accent="purple")
with m2:
    metric_card("Coins", f"{int(user.get('coins',0) or 0):,}", "Spend in Shop", accent="blue")
with m3:
    metric_card("XP", f"{int(user.get('xp',0) or 0):,}", "Levels unlock vibes", accent="none")

soft_divider()
st.subheader("Today’s quests")

# Display as 2-column grid for better scan-ability
left, right = st.columns(2)
cols = [left, right]

for idx, q in enumerate(quests):
    done = bool(completion.get(q["id"], False))
    already = q["id"] in claimed
    target = cols[idx % 2]

    with target:
        status = "✅ Claimed" if already else ("✅ Ready" if done else "⬜ Not yet")
        st.markdown(
            '<div class="card">'
            f'<div style="display:flex; align-items:center; justify-content:space-between; gap:12px">'
            f'<div style="font-weight:860">{q["title"]}</div>'
            f'<div class="badge"><span class="badge-dot"></span><span>{status}</span></div>'
            f'</div>'
            f'<div style="color:var(--muted);margin-top:6px">{q["desc"]}</div>'
            f'<div style="margin-top:0.65rem;font-weight:860">Reward: +{q["xp"]} XP · +{q["coins"]} coins</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        b1, b2 = st.columns([1, 1])
        with b1:
            if already:
                st.button("Claimed", key=f"claimed_{q['id']}", disabled=True, width="stretch")
            else:
                can_claim = bool(done)
                button_style(f"claim_{q['id']}", "purple" if can_claim else "white")
                if st.button("Claim", key=f"claim_{q['id']}", disabled=not can_claim, width="stretch", type="primary" if can_claim else "secondary"):
                    claimed.append(q["id"])
                    user["coins"] = int(user.get("coins", 0) or 0) + int(q["coins"])
                    grant_xp(user, int(q["xp"]), "Quest", q["title"])
                    log_event(user, kind="quest", title="Quest claimed", details=str(q.get("title","")), severity="success", agent_id=str(user.get("active_agent_id") or ""))
                    # Small crowd score bump for completing quests
                    crowd = user.setdefault("crowd", {"score": 50.0, "likes_received": 0, "likes_given": 0})
                    crowd["score"] = float(crowd.get("score", 50.0)) + 1.5
                    add_notification(user, "Quest complete", q["title"])
                    log_activity(user, f"Completed quest: {q['title']}", icon="🧭")
                    save_current_user()
                    st.rerun()
        with b2:
            st.page_link(q["link"], label="Go →", width="stretch")

soft_divider()
callout(
    "info",
    "Why quests matter",
    "Quests are the “training wheels” for agentic payments: they build habits (limits, proof-of-receipt, crowd feedback) without risk.",
)

save_current_user()
