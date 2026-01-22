from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, Iterable, List, Tuple


def _today() -> str:
    return _dt.date.today().isoformat()


def portfolio_value(portfolio: Dict[str, Any], price_map: Dict[str, float] | None = None) -> float:
    """Compute portfolio value using a simple cash + spot-prices model (demo)."""
    price_map = price_map or {}
    try:
        cash = float((portfolio or {}).get("cash_usdc", 0.0) or 0.0)
    except Exception:
        cash = 0.0

    positions = (portfolio or {}).get("positions")
    if not isinstance(positions, dict):
        positions = {}

    total = cash
    for coin_id, qty in positions.items():
        try:
            q = float(qty or 0.0)
        except Exception:
            q = 0.0
        if abs(q) < 1e-12:
            continue
        px = float(price_map.get(str(coin_id), 0.0) or 0.0)
        total += q * px
    return float(total)


def ensure_daily_snapshot(agent: Dict[str, Any], value: float) -> None:
    """Upsert today's value into agent['value_history']."""
    hist = agent.get("value_history")
    if not isinstance(hist, list):
        hist = []
        agent["value_history"] = hist

    d = _today()
    if hist and isinstance(hist[0], dict) and hist[0].get("d") == d:
        hist[0]["v"] = float(value)
        return

    # Insert newest first
    hist.insert(0, {"d": d, "v": float(value)})
    # Keep it light
    agent["value_history"] = hist[:450]


def _find_value_on_or_before(hist: List[Dict[str, Any]], target_date: _dt.date) -> float | None:
    """Find the value for the most recent snapshot on/before target_date."""
    best_v = None
    best_d = None
    for row in hist:
        if not isinstance(row, dict):
            continue
        d = row.get("d")
        v = row.get("v")
        try:
            dd = _dt.date.fromisoformat(str(d))
            vv = float(v)
        except Exception:
            continue
        if dd <= target_date and (best_d is None or dd > best_d):
            best_d = dd
            best_v = vv
    return best_v


def returns_windows(agent: Dict[str, Any], current_value: float) -> Dict[str, Dict[str, float]]:
    """Return profit/return% for daily/weekly/monthly/yearly windows.

    Uses sparse daily snapshots; when missing, falls back to the closest snapshot before the target date.
    """
    hist = agent.get("value_history")
    if not isinstance(hist, list):
        hist = []

    today = _dt.date.today()
    windows = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
        "yearly": 365,
    }

    out: Dict[str, Dict[str, float]] = {}

    for k, days in windows.items():
        base_date = today - _dt.timedelta(days=days)
        base_v = _find_value_on_or_before(hist, base_date)
        if base_v is None:
            # If we have anything, use the oldest known as baseline, else current.
            if hist:
                try:
                    base_v = float(hist[-1].get("v"))
                except Exception:
                    base_v = float(current_value)
            else:
                base_v = float(current_value)

        profit = float(current_value) - float(base_v)
        ret = (profit / float(base_v) * 100.0) if base_v else 0.0
        out[k] = {"profit": profit, "return_pct": ret}

    return out


def since_inception(agent: Dict[str, Any], current_value: float) -> Dict[str, float]:
    hist = agent.get("value_history")
    if not isinstance(hist, list) or not hist:
        return {"profit": 0.0, "return_pct": 0.0}

    try:
        base_v = float(hist[-1].get("v"))
    except Exception:
        base_v = float(current_value)

    profit = float(current_value) - float(base_v)
    ret = (profit / float(base_v) * 100.0) if base_v else 0.0
    return {"profit": profit, "return_pct": ret}
