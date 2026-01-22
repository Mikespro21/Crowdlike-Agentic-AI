from __future__ import annotations

"""Event logging for audits + judge-proof timelines.

We keep it local-only (JSON saved on device) to match the demo storage model.
"""

import datetime as _dt
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def ensure_events_schema(user: Dict[str, Any]) -> None:
    user.setdefault("events", [])  # global events (across agents)
    if not isinstance(user.get("events"), list):
        user["events"] = []
    # Agents store their own events too (optional)
    agents = user.get("agents")
    if isinstance(agents, list):
        for a in agents:
            if isinstance(a, dict):
                a.setdefault("events", [])
                if not isinstance(a.get("events"), list):
                    a["events"] = []


def log_event(
    user: Dict[str, Any],
    *,
    kind: str,
    title: str,
    details: str = "",
    severity: str = "info",
    agent_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ensure_events_schema(user)
    evt = {
        "ts": _now_iso(),
        "kind": (kind or "event")[:40],
        "title": (title or "")[:140],
        "details": (details or "")[:500],
        "severity": severity,
        "agent_id": str(agent_id) if agent_id is not None else None,
        "meta": meta or {},
    }
    # prepend (newest first)
    user["events"].insert(0, evt)

    if agent_id and isinstance(user.get("agents"), list):
        for a in user["agents"]:
            if isinstance(a, dict) and str(a.get("id")) == str(agent_id):
                a.setdefault("events", [])
                if isinstance(a["events"], list):
                    a["events"].insert(0, evt)
                break
    # bound growth
    user["events"] = user["events"][:300]
    return evt


def recent_events(user: Dict[str, Any], agent_id: Optional[str] = None, limit: int = 40) -> List[Dict[str, Any]]:
    ensure_events_schema(user)
    evts = user.get("events") if isinstance(user.get("events"), list) else []
    if agent_id is None:
        return evts[:limit]
    out = [e for e in evts if str(e.get("agent_id")) == str(agent_id)]
    return out[:limit]
