from __future__ import annotations

import datetime as _dt
import re
import uuid
from typing import Any, Dict, List, Optional


_DEF_PORTFOLIO: Dict[str, Any] = {"cash_usdc": 1000.0, "positions": {}, "trades": []}


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _today() -> str:
    return _dt.date.today().isoformat()


def _safe_name(name: str) -> str:
    s = re.sub(r"\s+", " ", (name or "").strip())
    s = re.sub(r"[^a-zA-Z0-9 _\-]", "", s)
    s = s[:24].strip()
    return s or "Agent"


def _new_id() -> str:
    return uuid.uuid4().hex[:12]



def _bot_id(agent_id: str, *, taken: set[str] | None = None) -> str:
    """Stable-looking Bot ID.

    We prefer persistence: once assigned, we keep it. We generate a short BOT-#### id.
    """
    taken = taken or set()
    # derive from agent_id hash first (deterministic-ish), then probe for collisions
    base = abs(hash(agent_id)) % 10000
    for i in range(100):
        cand = f"BOT-{(base + i) % 10000:04d}"
        if cand not in taken:
            return cand
    # extremely unlikely fallback
    return f"BOT-{base:04d}"


def new_agent(name: str, emoji: str = "🤖") -> Dict[str, Any]:
    """Create a new demo agent with its own portfolio + chat history."""
    agent_id = _new_id()
    return {
        "id": agent_id,
        "bot_id": _bot_id(agent_id),
        "category": "general",
        "name": _safe_name(name),
        "emoji": emoji or "🤖",
        "created_at": _now_iso(),
        # Strategy is a *label + params* for demo purposes.
        "strategy": {"name": "Balanced", "params": {"horizon": "7d"}, "copied_from": None},
        "portfolio": {"cash_usdc": 1000.0, "positions": {}, "trades": []},
        "purchases": [],
        "chat": [],  # [{role,content,ts}]
        "events": [],
        "approvals": [],
        "mode": "assist",
        "value_history": [{"d": _today(), "v": 1000.0}],
        "safety": {
            "fraud_alert": False,
            "panic": False,
            "max_drawdown_pct": 25.0,
            "peak_value": None,
            "last_exit": None,  # {ts,reason,value}
        },
        # Optional per-agent overrides (if absent, fall back to user['policy'])
        "policy": {},
    }


def ensure_agent_schema(agent: Dict[str, Any]) -> Dict[str, Any]:
    agent.setdefault("id", _new_id())
    agent["id"] = str(agent.get("id") or _new_id())

    agent.setdefault("category", "general")
    agent["category"] = str(agent.get("category") or "general")

    # Bot ID for anonymous leaderboards
    agent.setdefault("bot_id", "")
    if not str(agent.get("bot_id") or "").strip():
        agent["bot_id"] = _bot_id(agent["id"])

    agent.setdefault("name", "Agent")
    agent["name"] = _safe_name(str(agent.get("name") or "Agent"))

    agent.setdefault("emoji", "🤖")
    agent.setdefault("created_at", _now_iso())

    agent.setdefault("strategy", {"name": "Balanced", "params": {"horizon": "7d"}, "copied_from": None})

    agent.setdefault("portfolio", {"cash_usdc": 1000.0, "positions": {}, "trades": []})
    p = agent.get("portfolio")
    if not isinstance(p, dict):
        p = dict(_DEF_PORTFOLIO)
        agent["portfolio"] = p
    p.setdefault("cash_usdc", 1000.0)
    p.setdefault("positions", {})
    p.setdefault("trades", [])

    agent.setdefault("purchases", [])
    if not isinstance(agent.get("purchases"), list):
        agent["purchases"] = []

    agent.setdefault("chat", [])
    if not isinstance(agent.get("chat"), list):
        agent["chat"] = []

    agent.setdefault("events", [])
    if not isinstance(agent.get("events"), list):
        agent["events"] = []

    agent.setdefault("approvals", [])
    if not isinstance(agent.get("approvals"), list):
        agent["approvals"] = []

    agent.setdefault("mode", "assist")
    if str(agent.get("mode") or "") not in ("off", "assist", "auto", "auto_plus"):
        agent["mode"] = "assist"

    # Autonomy ladder + run reports (v0.60)
    agent.setdefault("runs", [])
    if not isinstance(agent.get("runs"), list):
        agent["runs"] = []

    try:
        from .autonomy import ensure_agent_autonomy
        ensure_agent_autonomy(agent)
    except Exception:
        agent.setdefault("autonomy", {})
        if not isinstance(agent.get("autonomy"), dict):
            agent["autonomy"] = {}

    agent.setdefault("value_history", [{"d": _today(), "v": 1000.0}])
    if not isinstance(agent.get("value_history"), list):
        agent["value_history"] = [{"d": _today(), "v": 1000.0}]

    agent.setdefault(
        "safety",
        {
            "fraud_alert": False,
            "panic": False,
            "max_drawdown_pct": 25.0,
            "max_daily_loss_usdc": 50.0,
            "enabled": True,
            "peak_value": None,
            "last_exit": None,
        },
    )
    if not isinstance(agent.get("safety"), dict):
        agent["safety"] = {"enabled": True}

    # Optional per-agent overrides (if absent, fall back to user['policy'])
    agent.setdefault("policy", {})
    if not isinstance(agent.get("policy"), dict):
        agent["policy"] = {}

    return agent
def ensure_agents_schema(user: Dict[str, Any]) -> Dict[str, Any]:
    agents = user.setdefault("agents", [])
    if not isinstance(agents, list):
        agents = []
        user["agents"] = agents

    user.setdefault("active_agent_id", "")

    # First normalize schemas
    for i in range(len(agents)):
        if isinstance(agents[i], dict):
            agents[i] = ensure_agent_schema(agents[i])

    # Ensure we always have at least one agent
    if not agents:
        agents.append(new_agent("Core", "🫧"))
        user["active_agent_id"] = agents[0]["id"]

    # Ensure active agent is valid
    active = str(user.get("active_agent_id") or "")
    if not active or not any(str(a.get("id")) == active for a in agents if isinstance(a, dict)):
        user["active_agent_id"] = str(agents[0].get("id"))

    # Ensure bot IDs are unique across agents
    taken: set[str] = set()
    for a in agents:
        if not isinstance(a, dict):
            continue
        bid = str(a.get("bot_id") or "").strip()
        if bid:
            if bid in taken:
                a["bot_id"] = ""  # force regeneration
            else:
                taken.add(bid)

    for a in agents:
        if not isinstance(a, dict):
            continue
        if not str(a.get("bot_id") or "").strip():
            a["bot_id"] = _bot_id(str(a.get("id") or _new_id()), taken=taken)
            taken.add(a["bot_id"])

    return user
def migrate_legacy_portfolio_to_agents(user: Dict[str, Any]) -> None:
    """If the user has a legacy single portfolio but no meaningful agent portfolio, copy it in."""
    ensure_agents_schema(user)
    agents = user.get("agents") or []
    if not agents:
        return

    agent0 = agents[0]
    legacy = user.get("portfolio")
    if isinstance(legacy, dict):
        a_port = agent0.get("portfolio") if isinstance(agent0.get("portfolio"), dict) else {}
        if isinstance(a_port, dict) and not a_port.get("trades") and (legacy.get("trades") or legacy.get("positions")):
            agent0["portfolio"] = {
                "cash_usdc": float(legacy.get("cash_usdc", 1000.0) or 1000.0),
                "positions": dict(legacy.get("positions") or {}),
                "trades": list(legacy.get("trades") or []),
            }
            v0 = float(agent0["portfolio"].get("cash_usdc", 0.0) or 0.0)
            agent0["value_history"] = [{"d": _today(), "v": v0}]

    # Mirror purchases into agent 0 if empty (keeps old demos working)
    if isinstance(user.get("purchases"), list) and not agent0.get("purchases"):
        agent0["purchases"] = list(user.get("purchases") or [])[:50]


def agent_label(agent: Dict[str, Any]) -> str:
    return f"{agent.get('emoji', '🤖')} {agent.get('name', 'Agent')}"


def get_agents(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    ensure_agents_schema(user)
    return user.get("agents") or []


def get_agent(user: Dict[str, Any], agent_id: str) -> Optional[Dict[str, Any]]:
    for a in get_agents(user):
        if str(a.get("id")) == str(agent_id):
            return a
    return None


def get_active_agent(user: Dict[str, Any]) -> Dict[str, Any]:
    ensure_agents_schema(user)
    aid = str(user.get("active_agent_id") or "")
    agent = get_agent(user, aid)
    if agent:
        return agent
    agents = get_agents(user)
    user["active_agent_id"] = str(agents[0].get("id"))
    return agents[0]


def set_active_agent(user: Dict[str, Any], agent_id: str) -> bool:
    if get_agent(user, agent_id):
        user["active_agent_id"] = str(agent_id)
        return True
    return False


def create_agent(user: Dict[str, Any], name: str, emoji: str = "🤖") -> Dict[str, Any]:
    ensure_agents_schema(user)
    a = new_agent(name=name, emoji=emoji or "🤖")
    user["agents"].insert(0, a)
    user["active_agent_id"] = a["id"]
    try:
        from crowdlike.events import log_event
        log_event(user, kind="agent", title="Created agent", details=f"{a.get('emoji','🤖')} {a.get('name','Agent')}", severity="success", agent_id=str(a.get("id")))
    except Exception:
        pass
    return a


def delete_agent(user: Dict[str, Any], agent_id: str) -> bool:
    ensure_agents_schema(user)
    agents = user.get("agents") or []
    before = len(agents)
    agents = [a for a in agents if str(a.get("id")) != str(agent_id)]
    user["agents"] = agents

    if len(agents) == before:
        return False

    if str(user.get("active_agent_id") or "") == str(agent_id):
        user["active_agent_id"] = str(agents[0].get("id")) if agents else ""

    if not agents:
        ensure_agents_schema(user)

    try:
        from crowdlike.events import log_event
        log_event(user, kind="agent", title="Deleted agent", details=str(agent_id), severity="danger", agent_id=str(agent_id))
    except Exception:
        pass
    return True
