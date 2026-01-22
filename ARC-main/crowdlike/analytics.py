from __future__ import annotations

"""Analytics helpers (v0.60).

This is intentionally lightweight: the goal is to make the demo feel like a real product by
providing legible, comparable metrics across agents.
"""

import datetime as _dt
from typing import Any, Dict, List, Tuple

from .performance import portfolio_value, returns_windows, since_inception
from .crowd_deviation import cohort_for_agent, deviation_pct


def _today() -> _dt.date:
    return _dt.date.today()


def _values_series(agent: Dict[str, Any]) -> List[Tuple[_dt.date, float]]:
    hist = agent.get("value_history")
    if not isinstance(hist, list):
        return []
    out: List[Tuple[_dt.date, float]] = []
    for row in hist:
        if not isinstance(row, dict):
            continue
        d = row.get("d")
        v = row.get("v")
        try:
            dd = _dt.date.fromisoformat(str(d))
            vv = float(v)
            out.append((dd, vv))
        except Exception:
            continue
    # hist is newest-first; return oldest-first for math
    out.sort(key=lambda x: x[0])
    return out


def max_drawdown_pct(agent: Dict[str, Any]) -> float:
    series = _values_series(agent)
    if len(series) < 2:
        return 0.0
    peak = series[0][1]
    max_dd = 0.0
    for _, v in series:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
    return float(max_dd)


def volatility_proxy_pct(agent: Dict[str, Any], window_days: int = 30) -> float:
    """Std-dev of daily percent returns over a window (simple proxy)."""
    series = _values_series(agent)
    if len(series) < 3:
        return 0.0
    cutoff = _today() - _dt.timedelta(days=int(window_days))
    xs = [(d, v) for d, v in series if d >= cutoff]
    if len(xs) < 3:
        xs = series[-min(15, len(series)):]
    rets: List[float] = []
    for i in range(1, len(xs)):
        prev = xs[i-1][1]
        cur = xs[i][1]
        if prev > 0:
            rets.append((cur - prev) / prev * 100.0)
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return float(var ** 0.5)


def compute_agent_metrics(user: Dict[str, Any], agent: Dict[str, Any], price_map: Dict[str, float]) -> Dict[str, Any]:
    port = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    cur_v = portfolio_value(port, price_map)
    windows = returns_windows(agent, cur_v)
    inc = since_inception(agent, cur_v)

    # Deviation vs cohort
    try:
        cohort = cohort_for_agent(user, agent)
        dev = float(deviation_pct(agent, cohort))
    except Exception:
        dev = 0.0

    runs = agent.get("runs") if isinstance(agent.get("runs"), list) else []
    approvals = agent.get("approvals") if isinstance(agent.get("approvals"), list) else []
    executed_runs = sum(1 for r in runs if isinstance(r, dict) and bool(r.get("executed")))
    queued_runs = sum(1 for r in runs if isinstance(r, dict) and bool(r.get("queued")))

    trades = port.get("trades") if isinstance(port.get("trades"), list) else []
    buys = sum(1 for t in trades if isinstance(t, dict) and str(t.get("side") or "").upper() == "BUY")
    sells = sum(1 for t in trades if isinstance(t, dict) and str(t.get("side") or "").upper() == "SELL")

    return {
        "value_usdc": float(cur_v),
        "since": inc,
        "windows": windows,
        "max_drawdown_pct": max_drawdown_pct(agent),
        "volatility_proxy_pct": volatility_proxy_pct(agent, 30),
        "deviation_pct": float(dev),
        "runs_total": len(runs),
        "runs_executed": int(executed_runs),
        "runs_queued": int(queued_runs),
        "approvals_pending": len([a for a in approvals if isinstance(a, dict) and str(a.get("status") or "pending") == "pending"]),
        "trades_total": len(trades),
        "buys": int(buys),
        "sells": int(sells),
        "mode": str(agent.get("mode") or "assist"),
        "strategy": agent.get("strategy") if isinstance(agent.get("strategy"), dict) else {},
    }


def agents_table(user: Dict[str, Any], agents: List[Dict[str, Any]], price_map: Dict[str, float]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for a in agents:
        if not isinstance(a, dict):
            continue
        m = compute_agent_metrics(user, a, price_map)
        rows.append({
            "agent_id": str(a.get("id") or ""),
            "label": str(a.get("label") or ""),
            "mode": m["mode"],
            "strategy": str((m.get("strategy") or {}).get("name") or ""),
            "value_usdc": round(float(m["value_usdc"]), 2),
            "profit_usdc": round(float((m["since"] or {}).get("profit", 0.0) or 0.0), 2),
            "return_pct": round(float((m["since"] or {}).get("return_pct", 0.0) or 0.0), 2),
            "dd_pct": round(float(m["max_drawdown_pct"]), 2),
            "vol_pct": round(float(m["volatility_proxy_pct"]), 2),
            "deviation_pct": round(float(m["deviation_pct"]), 1),
            "pending": int(m["approvals_pending"]),
            "runs": int(m["runs_total"]),
            "trades": int(m["trades_total"]),
        })
    return rows
