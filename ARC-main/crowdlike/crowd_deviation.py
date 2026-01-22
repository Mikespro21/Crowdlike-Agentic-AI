from __future__ import annotations

"""Crowd deviation constraint (percentile-based).

Spec (Master Context):
- Define a cohort: agents in the same category/time window.
- Track metrics: riskness (0-100), trades/day, position size (% portfolio per trade).
- Compute each metric's percentile rank in cohort.
- deviation% = average(|percentile - 50|) across metrics.
"""

import datetime as _dt
import math
from typing import Any, Dict, List, Tuple

from .performance import portfolio_value


def _today() -> _dt.date:
    return _dt.date.today()


def _parse_iso(ts: str) -> _dt.datetime | None:
    if not ts:
        return None
    s = str(ts)
    try:
        if s.endswith("Z"):
            s = s[:-1]
        return _dt.datetime.fromisoformat(s)
    except Exception:
        return None


def _riskness(user: Dict[str, Any], agent: Dict[str, Any]) -> float:
    # Per spec, riskness is user-set 0-100; agent policy overrides can exist.
    base = user.get("policy") if isinstance(user.get("policy"), dict) else {}
    ap = agent.get("policy") if isinstance(agent.get("policy"), dict) else {}
    try:
        r = ap.get("risk", None)
        if r is None:
            r = base.get("risk", 25)
        return float(r)
    except Exception:
        return 25.0


def _trades_per_day(agent: Dict[str, Any], *, window_days: int = 30) -> float:
    port = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    trades = port.get("trades") if isinstance(port.get("trades"), list) else []
    if not trades:
        return 0.0

    cutoff = _dt.datetime.utcnow() - _dt.timedelta(days=max(1, int(window_days)))
    c = 0
    has_ts = False
    for t in trades:
        if not isinstance(t, dict):
            continue
        ts = t.get("ts") or t.get("time") or t.get("date")
        dt = _parse_iso(ts) if ts else None
        if dt is not None:
            has_ts = True
            if dt >= cutoff:
                c += 1
        else:
            # no timestamp info
            c += 1

    if has_ts:
        return float(c) / float(window_days)

    # fallback: approximate from total trades / days since created (cap at 30d)
    created = _parse_iso(agent.get("created_at", "")) or _dt.datetime.utcnow()
    days = max(1.0, min(30.0, (_dt.datetime.utcnow() - created).total_seconds() / 86400.0))
    return float(len(trades)) / float(days)


def _avg_position_size_pct(user: Dict[str, Any], agent: Dict[str, Any], price_map: Dict[str, float] | None = None) -> float:
    price_map = price_map or {}
    port = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    trades = port.get("trades") if isinstance(port.get("trades"), list) else []
    if not trades:
        return 0.0

    cur_v = portfolio_value(port, price_map)
    if cur_v <= 1e-9:
        return 0.0

    # For demo: use trade cash / current portfolio value as proxy.
    xs: List[float] = []
    for t in trades[:60]:
        if not isinstance(t, dict):
            continue
        try:
            cash = float(t.get("cash", 0.0) or 0.0)
        except Exception:
            cash = 0.0
        if cash <= 0:
            continue
        xs.append((cash / cur_v) * 100.0)
    if not xs:
        return 0.0
    return float(sum(xs) / len(xs))


def _percentile(values: List[float], x: float) -> float:
    """Percentile rank in [0,100]. Uses midrank for ties."""
    if not values:
        return 50.0
    vs = sorted(float(v) for v in values)
    n = len(vs)
    # count strictly less + ties
    lt = sum(1 for v in vs if v < x)
    eq = sum(1 for v in vs if v == x)
    # midrank position
    rank = lt + (eq - 1) / 2 if eq else lt
    if n <= 1:
        return 50.0
    return float(rank) / float(n - 1) * 100.0


def deviation_pct(
    user: Dict[str, Any],
    agent: Dict[str, Any],
    *,
    cohort_agents: List[Dict[str, Any]],
    price_map: Dict[str, float] | None = None,
) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    """Return (deviation_pct, metrics, percentiles)."""
    price_map = price_map or {}
    # metrics for each agent in cohort
    cohort_metrics = []
    for a in cohort_agents:
        cohort_metrics.append(
            {
                "riskness": _riskness(user, a),
                "trades_per_day": _trades_per_day(a),
                "position_size_pct": _avg_position_size_pct(user, a, price_map),
            }
        )

    # this agent
    m = {
        "riskness": _riskness(user, agent),
        "trades_per_day": _trades_per_day(agent),
        "position_size_pct": _avg_position_size_pct(user, agent, price_map),
    }

    # percentiles
    ps = {}
    devs = []
    for k in ("riskness", "trades_per_day", "position_size_pct"):
        vals = [cm[k] for cm in cohort_metrics]
        p = _percentile(vals, float(m[k]))
        ps[k] = p
        devs.append(abs(p - 50.0))

    dev = float(sum(devs) / len(devs)) if devs else 0.0
    return dev, m, ps


def cohort_for_agent(user: Dict[str, Any], agent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Define cohort: same category when available; otherwise all agents."""
    agents = user.get("agents") if isinstance(user.get("agents"), list) else []
    cat = str(agent.get("category") or "general")
    cohort = [a for a in agents if isinstance(a, dict) and str(a.get("category") or "general") == cat]
    if len(cohort) < 3:
        cohort = [a for a in agents if isinstance(a, dict)]
    return cohort
