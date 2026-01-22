import re
import streamlit as st

from crowdlike.settings import bool_setting

from crowdlike.ui import apply_ui, hero, link_button, soft_divider, status_bar, callout, button_style, metric_card
from crowdlike.tour import maybe_run_tour
from crowdlike.auth import require_login, save_current_user, logout
from crowdlike.arc import (
    DEFAULT_RPC_URL,
    DEFAULT_EXPLORER,
    DEFAULT_USDC_ERC20,
    DEFAULT_USDC_DECIMALS,
    is_address,
)
from crowdlike.game import record_visit, ensure_user_schema, grant_xp, add_notification
from crowdlike.layout import render_sidebar


DEMO_MODE = bool_setting("DEMO_MODE", True)

AVATARS = ["🧊","🦋","🧠","🛰️","🪙","🦊","🦄","🐉","🧿","🪐","🌊","⚡","🫧","🧑‍🚀","🤖","🦈","🐙","🦜"]


def _is_safe_public_https_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u.startswith("https://"):
        return False
    if "localhost" in u or "127." in u or "0.0.0.0" in u:
        return False
    return True


from crowdlike.flow import flow_banner
st.set_page_config(page_title="Profile", page_icon="🧑‍🚀", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")
maybe_run_tour(user, current_page="profile")
ensure_user_schema(user)
record_visit(user, "profile")
render_sidebar(user, active_page="profile")
save_current_user()

flow_banner(user, active="Add your wallet")

hero("🧑‍🚀 Profile", "Identity, wallet, and autonomy settings.", badge="Settings")

wallet = user.setdefault("wallet", {}) if isinstance(user.get("wallet"), dict) else {}
user["wallet"] = wallet
wallet_addr = (wallet.get("address") or "").strip()
crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}

status_bar(wallet_set=bool(wallet_addr), demo_mode=DEMO_MODE, crowd_score=float(crowd.get("score", 50.0) or 50.0))

tabs = st.tabs(["Identity", "Wallet", "Limits", "Advanced"])

# -------------------- Identity --------------------
with tabs[0]:
    c1, c2 = st.columns([1.0, 1.1])
    with c1:
        st.markdown('<div class="card card-strong"><div style="font-weight:860">Identity</div><div style="color:var(--muted);margin-top:4px">This is local-only for the demo.</div></div>', unsafe_allow_html=True)
        st.write("")

        current_avatar = user.get("avatar", "🧊")
        try:
            avatar_index = AVATARS.index(current_avatar)
        except ValueError:
            avatar_index = 0

        user["avatar"] = st.selectbox("Avatar", AVATARS, index=avatar_index, key="pf_avatar")
        user["username"] = st.text_input("Display name", value=user.get("username", "Member"), key="pf_name")
        user["bio"] = st.text_area("Bio (optional)", value=user.get("bio", ""), placeholder="What are you building?", key="pf_bio")

        button_style("pf_save_identity", "blue")
        if st.button("Save identity", type="primary", key="pf_save_identity", width="stretch"):
            save_current_user()
            grant_xp(user, 30, "Profile", "Updated identity")
            add_notification(user, "Saved ✔️", "success")
            save_current_user()
            st.rerun()

    with c2:
        st.markdown(
            '<div class="card">'
            '<div style="font-weight:860">Preview</div>'
            '<div style="color:var(--muted);margin-top:4px">How you’ll appear in Social.</div>'
            '<div style="margin-top:0.85rem; display:flex; gap:12px; align-items:flex-start;">'
            f'<div style="font-size:2.2rem; line-height: 1">{user.get("avatar","🧊")}</div>'
            '<div>'
            f'<div style="font-weight:880; font-size:1.15rem">{user.get("username","Member")}</div>'
            f'<div style="color:var(--muted); margin-top:4px">{(user.get("bio","") or "No bio yet.").strip()[:140]}</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        button_style("pf_logout", "slate")
        if st.button("Log out", key="pf_logout", width="stretch"):
            logout()
            st.rerun()

# -------------------- Wallet --------------------
with tabs[1]:
    st.markdown(
        '<div class="card card-strong"><div style="font-weight:860">Wallet</div>'
        '<div style="color:var(--muted);margin-top:4px">Only paste a public address (never a private key).</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    wallet_addr_in = st.text_input(
        "Wallet address (public)",
        value=wallet_addr,
        placeholder="0x...",
        key="pf_wallet",
        help="Used to generate testnet checkout commands and to link you to ArcScan.",
    )
    if wallet_addr_in and not is_address(wallet_addr_in.strip()):
        callout("warn", "Address looks off", "A valid EVM address starts with 0x and is 42 characters long.")
    wallet["address"] = wallet_addr_in.strip()

    cols = st.columns([1, 1, 1])
    with cols[0]:
        button_style("pf_save_wallet", "purple")
        if st.button("Save wallet", type="primary", key="pf_save_wallet", width="stretch"):
            save_current_user()
            grant_xp(user, 45, "Profile", "Saved wallet")
            add_notification(user, "Saved ✔️", "success")
            save_current_user()
            st.rerun()
    with cols[1]:
        if wallet.get("address"):
            explorer = wallet.get("explorer", DEFAULT_EXPLORER)
            link_button("Open on ArcScan (testnet)", f"{explorer}/address/{wallet.get('address')}")
    with cols[2]:
        st.write("")

    st.caption("Tip: Any EVM wallet works (MetaMask, Rabby, etc.) — add Arc testnet network if needed.")

# -------------------- Limits --------------------
with tabs[2]:
    st.markdown(
        '<div class="card card-strong"><div style="font-weight:860">Autonomy & Limits</div>'
        '<div style="color:var(--muted);margin-top:4px">These are checked before generating any payment command.</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    policy = user.setdefault("policy", {}) if isinstance(user.get("policy"), dict) else {}
    user["policy"] = policy

    # Presets are helpful for fast judge demos
    preset_row = st.columns(3)
    with preset_row[0]:
        if st.button("Conservative", key="pf_preset_cons", width="stretch"):
            policy.update({"risk": 20, "max_per_tx_usdc": 0.05, "daily_cap_usdc": 0.25, "cooldown_s": 30})
            save_current_user(); st.rerun()
    with preset_row[1]:
        if st.button("Balanced", key="pf_preset_bal", width="stretch"):
            policy.update({"risk": 50, "max_per_tx_usdc": 0.10, "daily_cap_usdc": 0.50, "cooldown_s": 15})
            save_current_user(); st.rerun()
    with preset_row[2]:
        if st.button("Aggressive", key="pf_preset_aggr", width="stretch"):
            policy.update({"risk": 80, "max_per_tx_usdc": 0.25, "daily_cap_usdc": 1.00, "cooldown_s": 10})
            save_current_user(); st.rerun()

    st.write("")

    risk = int(policy.get("risk", 25) or 25)
    risk = st.slider("Risk level", 0, 100, value=risk, help="Guides suggested defaults.", key="pf_risk")
    policy["risk"] = risk

    max_dev = float(policy.get("max_deviation_pct", 20.0) or 20.0)
    max_dev = st.slider("Max crowd deviation (%)", 0.0, 50.0, value=float(max_dev), step=1.0, help="Average percentile distance from the crowd (Coach).", key="pf_max_dev")
    policy["max_deviation_pct"] = float(max_dev)

    if risk <= 33:
        tier, max_tx, daily_cap, cooldown = "Conservative", 0.05, 0.25, 30
    elif risk <= 66:
        tier, max_tx, daily_cap, cooldown = "Balanced", 0.10, 0.50, 15
    else:
        tier, max_tx, daily_cap, cooldown = "Aggressive", 0.25, 1.00, 10

    metric_cols = st.columns(3)
    with metric_cols[0]:
        metric_card("Tier", tier, "Suggested defaults", accent="none")
    with metric_cols[1]:
        metric_card("Max/tx", f"${float(policy.get('max_per_tx_usdc', max_tx) or max_tx):.2f}", "USDC", accent="none")
    with metric_cols[2]:
        metric_card("Daily cap", f"${float(policy.get('daily_cap_usdc', daily_cap) or daily_cap):.2f}", "USDC", accent="none")

    c1, c2, c3 = st.columns(3)
    with c1:
        policy["max_per_tx_usdc"] = st.number_input(
            "Max per transaction (USDC)",
            min_value=0.0,
            value=float(policy.get("max_per_tx_usdc", max_tx) or max_tx),
            step=0.01,
            format="%.2f",
            key="pf_max_tx",
        )
    with c2:
        policy["daily_cap_usdc"] = st.number_input(
            "Daily cap (USDC)",
            min_value=0.0,
            value=float(policy.get("daily_cap_usdc", daily_cap) or daily_cap),
            step=0.05,
            format="%.2f",
            key="pf_daily_cap",
        )
    with c3:
        policy["cooldown_s"] = st.number_input(
            "Cooldown (seconds)",
            min_value=0,
            value=int(policy.get("cooldown_s", cooldown) or cooldown),
            step=1,
            key="pf_cooldown",
        )

    button_style("pf_save_policy", "purple")
    if st.button("Save limits", type="primary", key="pf_save_policy", width="stretch"):
        save_current_user()
        add_notification(user, "Limits saved.", "success")
        grant_xp(user, 20, "Profile", "Updated limits")
        save_current_user()
        st.rerun()

# -------------------- Advanced --------------------
with tabs[3]:
    callout("info", "Advanced is optional", "Leave demo mode ON for the safest judge experience.")
    st.write("")

    adv = st.toggle("Developer mode (edit network)", value=False, key="pf_adv_toggle")

    if adv:
        st.markdown(
            '<div class="card"><div style="font-weight:860">Network</div>'
            '<div style="color:var(--muted);margin-top:4px">Demo mode locks settings to Arc testnet.</div></div>',
            unsafe_allow_html=True,
        )
        st.write("")

        if DEMO_MODE:
            wallet["rpc_url"] = DEFAULT_RPC_URL
            wallet["explorer"] = DEFAULT_EXPLORER
            wallet["usdc_erc20"] = DEFAULT_USDC_ERC20
            wallet["usdc_decimals"] = DEFAULT_USDC_DECIMALS

            st.info("Demo mode is ON: network settings are locked.")
            st.code(DEFAULT_RPC_URL); st.caption("RPC URL (locked)")
            st.code(DEFAULT_EXPLORER); st.caption("Explorer base (locked)")
            st.code(DEFAULT_USDC_ERC20); st.caption("USDC ERC-20 interface (locked)")
            st.caption(f"USDC decimals (locked): {DEFAULT_USDC_DECIMALS}")
        else:
            rpc_in = st.text_input("RPC URL (https only)", value=wallet.get("rpc_url", DEFAULT_RPC_URL), key="pf_rpc")
            exp_in = st.text_input("Explorer base (https only)", value=wallet.get("explorer", DEFAULT_EXPLORER), key="pf_explorer")
            usdc_in = st.text_input("USDC ERC-20 address", value=wallet.get("usdc_erc20", DEFAULT_USDC_ERC20), key="pf_usdc_addr")
            dec_in = st.number_input(
                "USDC decimals",
                min_value=0,
                max_value=18,
                value=int(wallet.get("usdc_decimals", DEFAULT_USDC_DECIMALS)),
                step=1,
                key="pf_usdc_dec",
            )

            if not _is_safe_public_https_url(rpc_in) or not _is_safe_public_https_url(exp_in):
                callout("warn", "Unsafe URL", "RPC/Explorer must be public https URLs (no localhost).")

            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("Reset to defaults", key="pf_reset_defaults", width="stretch"):
                    wallet["rpc_url"] = DEFAULT_RPC_URL
                    wallet["explorer"] = DEFAULT_EXPLORER
                    wallet["usdc_erc20"] = DEFAULT_USDC_ERC20
                    wallet["usdc_decimals"] = DEFAULT_USDC_DECIMALS
                    save_current_user()
                    st.rerun()
            with b2:
                button_style("pf_save_adv", "purple")
                if st.button("Save advanced settings", type="primary", key="pf_save_adv", width="stretch"):
                    if not _is_safe_public_https_url(rpc_in) or not _is_safe_public_https_url(exp_in):
                        st.error("Please provide safe public https URLs (no localhost).")
                    elif usdc_in and not is_address(usdc_in.strip()):
                        st.error("USDC address must be a valid 0x address.")
                    else:
                        wallet["rpc_url"] = rpc_in.strip()
                        wallet["explorer"] = exp_in.strip()
                        wallet["usdc_erc20"] = usdc_in.strip()
                        wallet["usdc_decimals"] = int(dec_in)
                        save_current_user()
                        add_notification(user, "Advanced settings saved.", "success")
                        save_current_user()
                        st.rerun()

save_current_user()