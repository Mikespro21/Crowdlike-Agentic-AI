from __future__ import annotations

"""Copying behaviors between agents (Master Context).

Copy modes:
- mirror_trades: mirror the most recent trade (practice) from a source agent
- copy_settings: copy policy/rules from source agent
- copy_strategy: copy strategy/model metadata from source agent
"""

from typing import Any, Dict, Tuple

from .events import log_event


def apply_copy(
    user: Dict[str, Any],
    *,
    dest_agent: Dict[str, Any],
    source_agent: Dict[str, Any],
    mode: str,
    price_map: Dict[str, float] | None = None,
) -> Tuple[bool, str]:
    price_map = price_map or {}

    mode = str(mode or "").strip().lower()
    if mode not in ("mirror_trades", "copy_settings", "copy_strategy"):
        return False, f"Unknown copy mode: {mode}"

    if mode == "copy_settings":
        sp = source_agent.get("policy") if isinstance(source_agent.get("policy"), dict) else {}
        dp = dest_agent.setdefault("policy", {})
        if not isinstance(dp, dict):
            dp = {}
            dest_agent["policy"] = dp
        # overwrite only known keys
        for k in ("risk", "max_per_tx_usdc", "daily_cap_usdc", "cooldown_s", "max_deviation_pct"):
            if k in sp:
                dp[k] = sp[k]
        log_event(user, kind="agent", title="Copied rules/settings", details=f"mode=copy_settings from {source_agent.get('bot_id','')}", severity="success", agent_id=str(dest_agent.get("id")))
        return True, "Copied settings."

    if mode == "copy_strategy":
        strat = source_agent.get("strategy") if isinstance(source_agent.get("strategy"), dict) else {}
        if strat:
            dest_agent["strategy"] = dict(strat)
            # mark copied_from (bot id) for explainability
            try:
                dest_agent["strategy"].setdefault("copied_from", source_agent.get("bot_id") or source_agent.get("id"))
            except Exception:
                pass
        log_event(user, kind="agent", title="Copied strategy/model", details=f"mode=copy_strategy from {source_agent.get('bot_id','')}", severity="success", agent_id=str(dest_agent.get("id")))
        return True, "Copied strategy."

    # mirror_trades
    sp = source_agent.get("portfolio") if isinstance(source_agent.get("portfolio"), dict) else {}
    trades = sp.get("trades") if isinstance(sp.get("trades"), list) else []
    if not trades:
        return False, "Source agent has no trades to mirror."

    t = trades[0] if isinstance(trades[0], dict) else {}
    asset = str(t.get("coin") or t.get("asset") or "").strip()
    side = str(t.get("side") or "BUY").upper()
    qty = float(t.get("qty", 0.0) or 0.0)
    cash = float(t.get("cash", 0.0) or 0.0)

    if not asset:
        return False, "Source trade missing asset."

    dp = dest_agent.get("portfolio") if isinstance(dest_agent.get("portfolio"), dict) else {}
    dp.setdefault("cash_usdc", 1000.0)
    dp.setdefault("positions", {})
    dp.setdefault("trades", [])

    px = float(price_map.get(asset, 0.0) or 0.0)
    if px <= 0:
        # fall back to trade price
        try:
            px = float(t.get("price", 0.0) or 0.0)
        except Exception:
            px = 0.0
    if px <= 0:
        px = 100.0

    # derive qty if missing but cash exists
    if qty <= 0 and cash > 0 and px > 0:
        qty = cash / px

    positions = dp.get("positions") if isinstance(dp.get("positions"), dict) else {}
    cur = float(positions.get(asset, 0.0) or 0.0)
    if side == "BUY":
        notional = float(qty) * px
        if float(dp.get("cash_usdc") or 0.0) < notional:
            return False, "Not enough cash to mirror BUY trade."
        dp["cash_usdc"] = float(dp.get("cash_usdc") or 0.0) - notional
        positions[asset] = cur + qty
    else:
        if cur < qty:
            return False, "Not enough position to mirror SELL trade."
        dp["cash_usdc"] = float(dp.get("cash_usdc") or 0.0) + float(qty) * px
        positions[asset] = cur - qty

    dp["positions"] = {k: v for k, v in positions.items() if abs(float(v or 0.0)) > 1e-12}
    dp["trades"].insert(0, {"ts": t.get("ts"), "asset": asset, "side": side, "qty": qty, "price": px, "notional": round(float(qty)*px,2), "source": str(source_agent.get("bot_id") or "")})
    dp["trades"] = dp["trades"][:200]
    dest_agent["portfolio"] = dp

    log_event(user, kind="trade", title="Mirrored trade", details=f"{side} {asset} from {source_agent.get('bot_id','')}", severity="success", agent_id=str(dest_agent.get("id")))
    return True, "Mirrored latest trade."
