from __future__ import annotations

"""Leaderboards and scoring (Master Context v4).

- Separate leaderboards: daily/weekly/monthly/yearly.
- Bot IDs used for identity.
- Profit rounded to 2 decimals BEFORE scoring.
- Score: s = (profit * 100) + streaks
- Streaks: consecutive scoring periods where profit stayed above 0.
"""

import datetime as _dt
from typing import Any, Dict, List, Literal, Tuple

from .performance import portfolio_value, ensure_daily_snapshot, returns_windows, _find_value_on_or_before


Window = Literal["daily", "weekly", "monthly", "yearly"]


def _profit_for_window(agent: Dict[str, Any], *, current_value: float, window: Window) -> float:
    win = returns_windows(agent, current_value)
    try:
        return float(win.get(window, {}).get("profit", 0.0) or 0.0)
    except Exception:
        return 0.0


def _streak_for_window(agent: Dict[str, Any], *, window: Window) -> int:
    hist = agent.get("value_history")
    if not isinstance(hist, list) or len(hist) < 2:
        return 0

    today = _dt.date.today()
    days = {"daily": 1, "weekly": 7, "monthly": 30, "yearly": 365}[window]
    streak = 0

    # We define consecutive *periods* ending at today: [today, today-days], then [today-days, today-2*days], etc.
    end = today
    while True:
        start = end - _dt.timedelta(days=days)
        base_v = _find_value_on_or_before(hist, start)
        end_v = _find_value_on_or_before(hist, end)
        if base_v is None or end_v is None:
            break
        profit = float(end_v) - float(base_v)
        if profit > 0:
            streak += 1
            end = start
            # stop if we can't step further meaningfully
            if streak > 200:
                break
        else:
            break
    return int(streak)


def leaderboard_rows(
    user: Dict[str, Any],
    agents: List[Dict[str, Any]],
    *,
    price_map: Dict[str, float] | None = None,
    window: Window = "weekly",
    role: str = "human",
) -> List[Dict[str, Any]]:
    price_map = price_map or {}
    rows: List[Dict[str, Any]] = []
    for a in agents:
        if not isinstance(a, dict):
            continue
        port = a.get("portfolio") if isinstance(a.get("portfolio"), dict) else {}
        v = portfolio_value(port, price_map)
        ensure_daily_snapshot(a, v)
        profit = _profit_for_window(a, current_value=v, window=window)
        # spec: round profit to 2 decimals before scoring
        profit_r = float(f"{profit:.2f}")
        streak = _streak_for_window(a, window=window)
        score = (profit_r * 100.0) + float(streak)

        bot_id = str(a.get("bot_id") or a.get("id") or "")
        base = {
            "bot_id": bot_id,
            "score": float(score),
            "profit": float(profit_r),
            "streaks": int(streak),
        }

        # Visibility rules: bots/admin see everything; humans see minimal.
        if role in ("bot", "admin"):
            base.update(
                {
                    "agent_id": str(a.get("id")),
                    "agent": f"{a.get('emoji','🤖')} {a.get('name','Agent')}",
                    "value": float(v),
                    "category": str(a.get("category") or "general"),
                }
            )

        rows.append(base)

    rows.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)
    return rows
