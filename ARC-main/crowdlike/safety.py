from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Tuple

from .performance import portfolio_value, ensure_daily_snapshot, _find_value_on_or_before


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def trigger_panic(agent: Dict[str, Any]) -> None:
    s = agent.setdefault("safety", {})
    if isinstance(s, dict):
        s["panic"] = True


def set_fraud_alert(agent: Dict[str, Any], on: bool) -> None:
    s = agent.setdefault("safety", {})
    if isinstance(s, dict):
        s["fraud_alert"] = bool(on)


def safety_exit(agent: Dict[str, Any], price_map: Dict[str, float], reason: str) -> Tuple[bool, str]:
    """Sell positions to USDC immediately (demo)."""
    port = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    if not isinstance(port, dict):
        return False, "Portfolio missing."

    cur_v = portfolio_value(port, price_map)
    cash = float(port.get("cash_usdc", 0.0) or 0.0)
    positions = port.get("positions") if isinstance(port.get("positions"), dict) else {}

    sold = 0
    for cid, qty in list(positions.items()):
        try:
            q = float(qty or 0.0)
        except Exception:
            q = 0.0
        if abs(q) < 1e-12:
            continue
        px = float(price_map.get(str(cid), 0.0) or 0.0)
        cash += q * px
        sold += 1
        positions[cid] = 0.0

    port["cash_usdc"] = float(cash)
    port["positions"] = {k: v for k, v in positions.items() if abs(float(v or 0.0)) > 1e-12}

    s = agent.setdefault("safety", {})
    if isinstance(s, dict):
        s["panic"] = False
        s["last_exit"] = {"ts": _now_iso(), "reason": reason, "value": float(cur_v), "sold_assets": sold}

    # Snapshot after exit
    ensure_daily_snapshot(agent, float(port.get("cash_usdc", 0.0) or 0.0))

    return True, f"Safety exit executed. Sold {sold} assets into USDC (demo)."


def check_safety_triggers(agent: Dict[str, Any], price_map: Dict[str, float]) -> Tuple[bool, str]:
    """Check drawdown/daily loss/fraud/panic triggers; executes exit when triggered."""
    s = agent.get("safety") if isinstance(agent.get("safety"), dict) else {}
    if not bool(s.get("enabled", True)):
        return False, "Safety exits disabled."

    port = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    cur_v = portfolio_value(port, price_map)

    # Maintain peak for drawdown logic
    peak = s.get("peak_value")
    try:
        peak_f = float(peak) if peak is not None else None
    except Exception:
        peak_f = None
    if peak_f is None or cur_v > peak_f:
        s["peak_value"] = float(cur_v)
        peak_f = float(cur_v)

    # Panic or fraud alert overrides
    if bool(s.get("panic")):
        return safety_exit(agent, price_map, "Panic sell")
    if bool(s.get("fraud_alert")):
        return safety_exit(agent, price_map, "Fraud alert")

    # Daily loss trigger (USDC)
    try:
        max_daily_loss = float(s.get("max_daily_loss_usdc", 50.0) or 0.0)
    except Exception:
        max_daily_loss = 0.0
    if max_daily_loss > 0:
        hist = agent.get("value_history")
        if isinstance(hist, list) and hist:
            yesterday = _dt.date.today() - _dt.timedelta(days=1)
            base = _find_value_on_or_before(hist, yesterday)
            if base is not None:
                loss = float(base) - float(cur_v)
                if loss >= max_daily_loss:
                    return safety_exit(agent, price_map, f"Auto safety exit (daily loss ${loss:.2f} ≥ ${max_daily_loss:.2f})")

    # Drawdown trigger (%)
    try:
        max_dd = float(s.get("max_drawdown_pct", 25.0) or 0.0)
    except Exception:
        max_dd = 0.0

    if peak_f and max_dd > 0:
        dd = (peak_f - cur_v) / peak_f * 100.0
        if dd >= max_dd:
            return safety_exit(agent, price_map, f"Auto safety exit (drawdown {dd:.1f}% ≥ {max_dd:.1f}%)")

    return False, "No safety triggers."
