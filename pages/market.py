import streamlit as st
import datetime as _dt


from crowdlike.ui import apply_ui, hero, soft_divider, link_button, status_bar, stepper, copy_to_clipboard, callout
from crowdlike.settings import bool_setting
from crowdlike.tour import maybe_run_tour, tour_complete_step
from crowdlike.auth import require_login, save_current_user
from crowdlike.game import record_visit, ensure_user_schema, grant_xp, add_notification, log_activity
from crowdlike.agents import get_active_agent, agent_label
from crowdlike.market_data import get_markets, get_market_chart_7d
from crowdlike.policy import PaymentPolicy
from crowdlike.layout import render_sidebar
from crowdlike.events import log_event
from crowdlike.arc import (
    cast_usdc_transfer_cmd,
    get_tx_receipt,
    verify_erc20_transfer,
    to_base_units,
    is_address,
    is_tx_hash,
    DEFAULT_EXPLORER,
    DEFAULT_RPC_URL,
)

from crowdlike.flow import flow_banner
st.set_page_config(page_title="Market", page_icon="📈", layout="wide")
apply_ui()

user = require_login(app_name="Crowdlike")

maybe_run_tour(user, current_page="market")
ensure_user_schema(user)
record_visit(user, "market")

render_sidebar(user, active_page="market")

active_agent = get_active_agent(user)

flow_banner(user, active="Verify a receipt")

hero("📈 Market", "Live prices, practice trading, and a judge-friendly USDC testnet checkout flow.", badge=agent_label(active_agent))

_demo = bool_setting("DEMO_MODE", True)
_wallet = (user.get("wallet") or {}) if isinstance(user.get("wallet"), dict) else {}
_wallet_set = bool((_wallet.get("address") or "").strip())
_crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
status_bar(wallet_set=_wallet_set, demo_mode=_demo, crowd_score=float(_crowd.get("score", 50.0) or 50.0))


wallet = user.setdefault("wallet", {})
rpc_url = wallet.get("rpc_url", DEFAULT_RPC_URL)
explorer = wallet.get("explorer", DEFAULT_EXPLORER)
usdc_erc20 = wallet.get("usdc_erc20")
usdc_decimals = int(wallet.get("usdc_decimals", 6))

WATCHLIST = ["bitcoin", "ethereum", "solana", "avalanche-2", "chainlink", "polygon-ecosystem-token"]

tab_live, tab_practice, tab_checkout = st.tabs(["Live prices", "Practice", "Testnet checkout"])

with tab_live:
    st.subheader("Live prices (CoinGecko)")
    try:
        rows = get_markets("usd", WATCHLIST)
    except Exception as e:
        rows = []
        st.error("Market data is unavailable right now.")
        with st.expander("Details"):
            st.exception(e)

    if rows:
        # Card grid
        cols = st.columns(3)
        for i, r in enumerate(rows):
            chg = r.price_change_percentage_24h
            chg_txt = "—" if chg is None else f"{chg:+.2f}%"
            chg_color = "var(--muted)"
            if chg is not None:
                if chg > 0:
                    chg_color = "var(--green)"
                elif chg < 0:
                    chg_color = "var(--red)"

            with cols[i % 3]:
                st.markdown(
                    f'''
                    <div class="card" style="margin-bottom:0.75rem">
                      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
                        <div>
                          <div style="font-weight:800">{r.name} <span style="color:var(--muted)">({r.symbol})</span></div>
                          <div style="font-size:1.35rem;font-weight:850">${r.current_price:,.2f}</div>
                        </div>
                        <div class="badge"><span class="badge-dot"></span>
                          <span style="font-weight:800;color:{chg_color}">{chg_txt}</span>
                        </div>
                      </div>
                      <div style="color:var(--muted);font-size:0.82rem;margin-top:0.45rem">
                        Rank #{r.market_cap_rank or "—"} · Volume {r.total_volume or 0:,.0f}
                      </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    soft_divider()
    if rows:
        coin_id = st.selectbox("View a 7‑day chart", [r.id for r in rows], key="mkt_chart_coin")
        try:
            pts = get_market_chart_7d(coin_id, "usd")
            if pts:
                st.line_chart([p[1] for p in pts], height=260)
        except Exception as e:
            st.warning("Chart unavailable right now.")
            with st.expander("Details"):
                st.exception(e)

    st.caption("Tip: Live prices are for the UI demo. Testnet checkout below is the on-chain part.")

with tab_practice:
    st.subheader("Practice buy/sell (simple + fun)")
    st.markdown(
        '<div class="card">This is a <b>practice</b> portfolio using live prices. '
        'It helps you demo trading UX without needing a DEX integration.</div>',
        unsafe_allow_html=True,
    )
    st.write("")



    # Each agent has its own practice portfolio (v0.30+).
    portfolio = active_agent.setdefault("portfolio", {"cash_usdc": 1000.0, "positions": {}, "trades": []})
    if not isinstance(portfolio, dict):
        portfolio = {"cash_usdc": 1000.0, "positions": {}, "trades": []}
        active_agent["portfolio"] = portfolio
    portfolio.setdefault("cash_usdc", 1000.0)
    portfolio.setdefault("positions", {})
    portfolio.setdefault("trades", [])

    try:
        rows = get_markets("usd", WATCHLIST)
    except Exception:
        rows = []
    price_map = {r.id: r.current_price for r in rows}

    if not rows:
        st.warning("Practice mode needs market prices. Try again later.")
    else:
        c1, c2, c3 = st.columns([1.2, 0.9, 0.9])
        with c1:
            coin = st.selectbox("Asset", [r.id for r in rows], format_func=lambda x: x, key="practice_coin")

        # Tutorial auto-advance: when the user *changes* the asset during step 4
        if st.session_state.get("tour_step") == 4:
            base = st.session_state.get("_tour_step4_base")
            if base is None:
                st.session_state["_tour_step4_base"] = coin
            elif coin != base:
                tour_complete_step(4)
        with c2:
            side = st.selectbox("Side", ["BUY", "SELL"], key="practice_side")
        with c3:
            amt = st.number_input("Amount (cash)", min_value=1.0, value=25.0, step=1.0, key="practice_amt")

        px = float(price_map.get(coin, 0.0) or 0.0)
        if px <= 0:
            st.error("Price missing.")
        else:
            qty = float(amt) / px
            st.write(f"Price: **${px:,.2f}** → Qty: **{qty:.6f}**")
            st.write("")

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Cash", f"${float(portfolio['cash_usdc']):.2f}")
            with m2:
                pos = float(portfolio["positions"].get(coin, 0.0))
                st.metric("Position", f"{pos:.6f}")
            with m3:
                st.metric("Pos value", f"${pos*px:.2f}")

            if st.button("Execute", type="primary", key="practice_exec"):
                if side == "BUY":
                    if float(portfolio["cash_usdc"]) < float(amt):
                        st.error("Not enough cash.")
                    else:
                        portfolio["cash_usdc"] = float(portfolio["cash_usdc"]) - float(amt)
                        portfolio["positions"][coin] = float(portfolio["positions"].get(coin, 0.0)) + qty
                        portfolio["trades"].insert(0, {"ts": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds")+"Z", "side": "BUY", "coin": coin, "cash": float(amt), "qty": qty, "price": px})
                        grant_xp(user, 45, "Market", "Practice BUY")
                        log_activity(user, f"Practice BUY {coin} (${amt:.2f})", icon="📈")
                        log_event(user, kind="trade", title=f"Practice BUY {coin}", details=f"${amt:.2f} on {coin}", severity="info", agent_id=str(active_agent.get("id")))
                        save_current_user()
                        st.success("Done ✅")
                        st.rerun()
                else:
                    pos = float(portfolio["positions"].get(coin, 0.0))
                    if pos < qty:
                        st.error("Not enough position to sell.")
                    else:
                        portfolio["cash_usdc"] = float(portfolio["cash_usdc"]) + float(amt)
                        portfolio["positions"][coin] = pos - qty
                        portfolio["trades"].insert(0, {"ts": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds")+"Z", "side": "SELL", "coin": coin, "cash": float(amt), "qty": qty, "price": px})
                        grant_xp(user, 45, "Market", "Practice SELL")
                        log_activity(user, f"Practice SELL {coin} (${amt:.2f})", icon="📉")
                        log_event(user, kind="trade", title=f"Practice SELL {coin}", details=f"${amt:.2f} on {coin}", severity="info", agent_id=str(active_agent.get("id")))
                        save_current_user()
                        st.success("Done ✅")
                        st.rerun()

            with st.expander("Portfolio & trade history", expanded=False):
                st.write("**Positions**")
                if not portfolio["positions"]:
                    st.caption("No positions yet.")
                else:
                    for k, v in portfolio["positions"].items():
                        if abs(float(v)) > 1e-12:
                            st.write(f"- {k}: {float(v):.6f}")

                st.write("**Trades**")
                if not portfolio["trades"]:
                    st.caption("No trades yet.")
                else:
                    st.dataframe(portfolio["trades"][:25], width="stretch", hide_index=True)

with tab_checkout:
    st.subheader("Testnet checkout (USDC on Arc testnet)")
    callout("info", "On-chain checkout (safe demo)", "You generate a command, run it locally, then paste the tx hash as proof. Private keys never enter the app.")
    st.markdown(
        '<div class="card card-strong">'
        '<b>This is the on-chain part.</b> You pay using testnet USDC and paste the “receipt ID” (tx hash). '
        '<div style="color:var(--muted);margin-top:0.35rem">Private keys never enter the app — you run the command locally.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if not wallet.get("address"):
        st.warning("First: set your wallet address in **Profile**.")
        st.page_link("pages/profile.py", label="Go to Profile")
    else:
        offers = [
            {"id": "vip_pass", "name": "VIP Pass", "desc": "Unlock VIP shop drops + flex badge.", "price": "1.00"},
            {"id": "creator_tip", "name": "Creator Tip", "desc": "Tip the community treasury (demo).", "price": "0.10"},
        ]

        def _fmt(o: dict) -> str:
            return f'{o["name"]} — ${o["price"]} USDC'

        # Stepper (visual)
        stepper(int(st.session_state.get('checkout_step', 1) or 1), ['Configure', 'Pay', 'Verify'])
        step_labels = {1: "Configure", 2: "Pay", 3: "Verify"}
        step = st.radio(
            "Checkout step",
            options=[1, 2, 3],
            format_func=lambda x: step_labels.get(x, str(x)),
            horizontal=True,
            key="checkout_step",
            label_visibility="collapsed",
        )

        # Shared state
        offer_id = st.selectbox(
            "What are you buying?",
            options=[o["id"] for o in offers],
            format_func=lambda oid: _fmt(next(o for o in offers if o["id"] == oid)),
            key="checkout_offer_id",
        )
        offer = next(o for o in offers if o["id"] == offer_id)

        c1, c2 = st.columns([2, 1])
        with c1:
            treasury = st.text_input(
                "Treasury (recipient) address",
                value=wallet.get("treasury_address", ""),
                placeholder="0x...",
                help="Where USDC will be sent on testnet.",
                key="checkout_treasury",
            )
            wallet["treasury_address"] = treasury.strip()
        with c2:
            st.markdown(
                '<div class="card">'
                f'<div style="font-weight:780">Selected</div>'
                f'<div style="margin-top:0.35rem">{offer["name"]}</div>'
                f'<div style="color:var(--muted);font-size:0.9rem">{offer["desc"]}</div>'
                f'<div style="margin-top:0.65rem;font-size:1.35rem;font-weight:900">${offer["price"]} USDC</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Policy summary (crowd-influenced). Allow per-agent overrides.
        _ctx = dict(user)
        _ap = active_agent.get("policy") if isinstance(active_agent.get("policy"), dict) else {}
        if isinstance(user.get("policy"), dict):
            _ctx["policy"] = {**(user.get("policy") or {}), **(_ap or {})}
        else:
            _ctx["policy"] = _ap or {}
        base_policy = PaymentPolicy.from_user(_ctx)
        eff = base_policy.effective(user)
        crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
        score = float(crowd.get("score", 50.0) or 50.0)
        st.markdown(
            '<div class="card">'
            '<div style="font-weight:760">Safety rails</div>'
            f'<div style="color:var(--muted);margin-top:4px">Crowd Score: <b>{score:.0f}</b> (gently boosts limits)</div>'
            f'<div style="margin-top:0.4rem">Max/tx: <b>${eff.max_per_tx_usdc:.2f}</b> · Daily cap: <b>${eff.daily_cap_usdc:.2f}</b> · Cooldown: <b>{eff.cooldown_s}s</b></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Step 1: validate config
        if step == 1:
            ok_addr = is_address(treasury.strip())
            if not ok_addr:
                st.error("Enter a valid treasury address to continue.")
            if st.button("Continue to Pay →", type="primary", disabled=not ok_addr):
                st.session_state["checkout_step"] = 2
                st.rerun()

        # Step 2: show payment command
        if step == 2:
            if not is_address(treasury.strip()):
                st.error("Enter a valid treasury address (Step 1).")
            else:
                ok_policy, why = base_policy.authorize_payment(user, offer["price"], commit=False)
                if not ok_policy:
                    st.error(why)
                    st.caption("Tip: adjust your limits in Profile → Autonomy & Limits.")
                else:
                    cmd = cast_usdc_transfer_cmd(
                        to_address=treasury.strip(),
                        amount_usdc=offer["price"],
                        rpc_url=rpc_url,
                        usdc_erc20=usdc_erc20,
                        usdc_decimals=usdc_decimals,
                        private_key_env="$PRIVATE_KEY",
                    )
                    st.markdown('<div class="card"><div style="font-weight:760">Run this locally</div></div>', unsafe_allow_html=True)
                    st.code(cmd, language="bash")
                    copy_to_clipboard(cmd, key="mkt_cast_cmd", label="Copy command")
                    st.caption("Do **not** paste private keys into the app. Use an env var: $PRIVATE_KEY.")
                    if st.button("I’ve paid — go to Verify →", type="primary"):
                        st.session_state["checkout_step"] = 3
                        st.rerun()

        # Step 3: verify receipt
        if step == 3:
            txh = st.text_input("Receipt ID (tx hash)", value="", placeholder="0x...", key="checkout_txh")
            if txh and not is_tx_hash(txh.strip()):
                st.error("That doesn’t look like a tx hash.")
            can_verify = bool(txh.strip()) and is_tx_hash(txh.strip())
            if st.button("Verify receipt", type="primary", disabled=not can_verify):
                txh = txh.strip()
                try:
                    receipt = get_tx_receipt(rpc_url, txh)
                    if not receipt:
                        st.warning("Receipt not found yet. Wait ~10–20s and try again.")
                        log_event(user, kind="receipt", title="Receipt not found yet", details=f"{txh}", severity="warn", agent_id=str(active_agent.get("id")))
                    else:
                        # Require success status
                        status = str(receipt.get("status", "")).lower()
                        if status not in ("0x1", "1", "true"):
                            st.error("Transaction failed (status not successful).")
                            log_event(user, kind="receipt", title="Receipt failed", details=f"{txh} (status {status})", severity="danger", agent_id=str(active_agent.get("id")))
                        else:
                            ok, msg = verify_erc20_transfer(
                                receipt=receipt,
                                token_address=usdc_erc20,
                                to_address=treasury.strip(),
                                min_amount_base_units=to_base_units(offer["price"], usdc_decimals),
                            )
                            if ok:
                                # Commit policy counters only after verified
                                base_policy.authorize_payment(user, offer["price"], commit=True)

                                # Idempotent save by tx_hash (agent + global history)
                                agent_purchases = active_agent.get("purchases") if isinstance(active_agent.get("purchases"), list) else []
                                purchases = user.get("purchases") if isinstance(user.get("purchases"), list) else []

                                def _dedupe(items):
                                    existing_i = None
                                    for i, p in enumerate(items):
                                        if (p or {}).get("tx_hash") == txh:
                                            existing_i = i
                                            break
                                    return existing_i

                                existing_i_agent = _dedupe(agent_purchases)
                                existing_i_user = _dedupe(purchases)
                                rec = {
                                    "ts": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                                    "item_id": offer["id"],
                                    "name": offer["name"],
                                    "price": offer["price"],
                                    "currency": "USDC",
                                    "tx_hash": txh,
                                    "status": "verified",
                                }
                                if existing_i_agent is not None:
                                    agent_purchases.pop(existing_i_agent)
                                if existing_i_user is not None:
                                    purchases.pop(existing_i_user)
                                agent_purchases.insert(0, rec)
                                purchases.insert(0, rec)
                                active_agent["purchases"] = agent_purchases[:50]
                                user["purchases"] = purchases[:50]

                                grant_xp(user, 25, "Checkout", f"Verified {offer['name']}")
                                add_notification(user, "Verified ✅", f"{offer['name']} saved to your profile.")
                                save_current_user()
                                st.success("Verified ✅ (saved to your profile)")
                                st.caption(msg)
                            else:
                                st.warning("Not verified yet.")
                                st.caption(msg)
                except Exception as e:
                    st.error("Couldn’t verify via RPC. You can still use ArcScan as proof.")
                    with st.expander("Details"):
                        st.exception(e)

            if explorer:
                st.caption("Explorer")
                if txh and is_tx_hash(txh.strip()):
                    link_button("Open in ArcScan", f"{explorer.rstrip('/')}/tx/{txh.strip()}")

save_current_user()

# Guided tutorial (spotlight tour)