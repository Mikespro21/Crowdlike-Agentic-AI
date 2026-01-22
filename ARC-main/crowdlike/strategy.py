from __future__ import annotations

from typing import Any, Dict, List, Optional


STRATEGY_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Balanced",
        "tag": "Default",
        "about": "Spread across large caps; small adjustments on momentum.",
        "params": {"horizon": "7d", "turnover": "low", "max_assets": 5},
    },
    {
        "name": "Momentum",
        "tag": "Trend",
        "about": "Buy winners, cut losers. Higher churn.",
        "params": {"horizon": "7d", "turnover": "high", "max_assets": 8},
    },
    {
        "name": "Mean Reversion",
        "tag": "Contrarian",
        "about": "Buy dips, take profits on spikes.",
        "params": {"horizon": "30d", "turnover": "medium", "max_assets": 6},
    },
    {
        "name": "Index",
        "tag": "Slow & steady",
        "about": "Mostly hold top market-cap assets.",
        "params": {"horizon": "90d", "turnover": "very_low", "max_assets": 10},
    },
    {
        "name": "Copycat",
        "tag": "Crowd",
        "about": "Copies parts of another agent’s strategy (demo).",
        "params": {"copy_mode": "params", "copy_source": ""},
    },
]


def template_by_name(name: str) -> Optional[Dict[str, Any]]:
    for t in STRATEGY_TEMPLATES:
        if str(t.get("name") or "").lower() == str(name or "").lower():
            return t
    return None


def apply_template(agent: Dict[str, Any], template_name: str) -> None:
    t = template_by_name(template_name) or template_by_name("Balanced")
    if not t:
        return
    agent.setdefault("strategy", {})
    agent["strategy"] = {
        "name": t["name"],
        "params": dict(t.get("params") or {}),
        "copied_from": None,
    }


def copy_strategy(source: Dict[str, Any], target: Dict[str, Any], mode: str = "full") -> None:
    """Copy strategy from source to target.

    - mode=full: copy name+params
    - mode=params: keep name but copy params
    """
    s = source.get("strategy") if isinstance(source.get("strategy"), dict) else {}
    t = target.get("strategy") if isinstance(target.get("strategy"), dict) else {}

    mode = str(mode or "full").lower()
    if mode == "params":
        t.setdefault("name", "Balanced")
        t["params"] = dict(s.get("params") or {})
    else:
        t["name"] = str(s.get("name") or "Balanced")
        t["params"] = dict(s.get("params") or {})

    t["copied_from"] = str(source.get("id") or "")
    target["strategy"] = t
