import streamlit as st

from crowdlike.ui import apply_ui, hero, soft_divider, status_bar, callout
from crowdlike.settings import bool_setting
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import ensure_user_schema, record_visit
from crowdlike.layout import render_sidebar
from crowdlike.audit import ensure_audit_schema


st.set_page_config(page_title="Admin", page_icon="🧾", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
ensure_user_schema(user)
record_visit(user, "admin")

render_sidebar(user, active_page="admin")

_demo = bool_setting("DEMO_MODE", True)
wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((wallet.get("address") or "").strip())
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(crowd.get("score", 50.0) or 50.0))

hero("🧾 Admin audit", "Trustless AI log. Visible only to bot/admin roles.", badge="Audit")

role = str(user.get("role") or "human").lower()
if role not in ("admin", "bot"):
    callout("warn", "Hidden", "This page is hidden for human users. Set ROLE=admin in settings to view the audit log.")
    st.stop()

ensure_audit_schema(user)
logs = user.get("audit_log") if isinstance(user.get("audit_log"), list) else []

q = st.text_input("Search", placeholder="Filter by kind, msg, agent_id, proposal_id…")
sev = st.multiselect("Severity", ["info","success","warn","error"], default=["info","success","warn","error"])
kinds = st.multiselect("Kind", sorted(list({(l.get('kind') or '') for l in logs if isinstance(l, dict)})) or [], default=[])

def match(row: dict) -> bool:
    if str(row.get("severity","info")) not in sev:
        return False
    if kinds and str(row.get("kind") or "") not in kinds:
        return False
    if q:
        hay = f"{row.get('ts','')} {row.get('kind','')} {row.get('severity','')} {row.get('msg','')} {row.get('agent_id','')} {row.get('proposal_id','')}"
        if q.lower() not in hay.lower():
            return False
    return True

rows = [r for r in logs if isinstance(r, dict) and match(r)]
st.caption(f"Showing {len(rows)} / {len(logs)} log entries")

st.dataframe(rows, width="stretch", hide_index=True)

save_current_user()
