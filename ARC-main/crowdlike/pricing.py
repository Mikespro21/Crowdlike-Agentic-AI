from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PriceQuote:
    agent_count: int
    risk: float
    total_per_day: float
    per_agent_per_day: float


def quote_daily(agent_count: int, risk: float) -> PriceQuote:
    """Per-day pricing model (Master Context v4).

    Final formula:
        price = (agentCount^2) * (risk / 100)

    - risk is a 0-100 value.
    - agentCount is the number of agents running/billed.
    """
    try:
        n = int(agent_count or 0)
    except Exception:
        n = 0
    n = max(0, n)

    try:
        r = float(risk or 0.0)
    except Exception:
        r = 0.0
    r = max(0.0, min(100.0, r))

    total = (float(n) ** 2) * (r / 100.0)
    per_agent = (total / float(n)) if n else 0.0
    return PriceQuote(agent_count=n, risk=r, total_per_day=float(total), per_agent_per_day=float(per_agent))
