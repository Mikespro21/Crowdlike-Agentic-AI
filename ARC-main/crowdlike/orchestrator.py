from __future__ import annotations

"""Agent orchestrator (v0.50 vision-aligned).

Key principles (Master Context):
- Agents can propose actions (trade/payment/copy); user approvals gate sensitive actions.
- Auto mode may execute *practice trades* only when constraints are satisfied.
- Copy modes: mirror trades, copy rules/settings, copy model/strategy.
- Trustless AI logging: write an audit log (admin/bot-only visibility).
- Crowd deviation constraint: if deviation exceeds user's max, proposals require approval and auto-exec is blocked.
"""

import datetime as _dt
import random
from typing import Any, Dict, Optional

from .audit import log_audit
from .crowd_deviation import cohort_for_agent, deviation_pct


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def ensure_agent_runtime(agent: Dict[str, Any]) -> None:
    agent.setdefault("approvals", [])
    if not isinstance(agent.get("approvals"), list):
        agent["approvals"] = []
    agent.setdefault("mode", "assist")
    if str(agent.get("mode") or "") not in ("off", "assist", "auto"):
        agent["mode"] = "assist"


def _max_deviation(user: Dict[str, Any]) -> float:
    pol = user.get("policy") if isinstance(user.get("policy"), dict) else {}
    try:
        return float(pol.get("max_deviation_pct", 20.0) or 20.0)
    except Exception:
        return 20.0


def _current_deviation(user: Dict[str, Any], agent: Dict[str, Any]) -> float:
    cohort = cohort_for_agent(user, agent)
    dev, _, _ = deviation_pct(user, agent, cohort_agents=cohort, price_map={})
    return float(dev)


def _choose_copy_mode(user: Dict[str, Any], agent: Dict[str, Any]) -> str:
    """Pick a copy mode automatically (demo heuristics)."""
    # If crowd score is low, prefer copying strategy/settings to stabilize.
    crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
    try:
        score = float(crowd.get("score", 50.0) or 50.0)
    except Exception:
        score = 50.0
    r = random.random()
    if score < 45:
        return "copy_settings" if r < 0.55 else "copy_strategy"
    if score > 65:
        return "mirror_trades" if r < 0.55 else "copy_strategy"
    # default mix
    return "mirror_trades" if r < 0.40 else ("copy_settings" if r < 0.70 else "copy_strategy")


def propose_next_action(user: Dict[str, Any], agent: Dict[str, Any], markets: Any = None) -> Dict[str, Any]:
    """Create and enqueue a proposal.

    Proposal types:
    - trade: practice trade
    - payment: demo payment intent (requires manual confirmation)
    - copy: crowd-copy behavior
    """
    ensure_agent_runtime(agent)

    pol = user.get("policy") if isinstance(user.get("policy"), dict) else {}
    try:
        risk = float(pol.get("risk", 25.0) or 25.0)
    except Exception:
        risk = 25.0

    dev = _current_deviation(user, agent)
    max_dev = _max_deviation(user)

    # Higher deviation increases probability of suggesting a "copy" action.
    p_copy = 0.15 + min(0.35, max(0.0, (dev - 10.0) / 60.0))
    p_trade = 0.55
    p_payment = 0.30

    r = random.random()
    if r < p_copy:
        # pick a source agent to copy from
        agents = user.get("agents") if isinstance(user.get("agents"), list) else []
        sources = [a for a in agents if isinstance(a, dict) and str(a.get("id")) != str(agent.get("id"))]
        src = random.choice(sources) if sources else None
        mode = _choose_copy_mode(user, agent)
        proposal = {
            "id": f"appr_{random.randint(100000,999999)}",
            "ts": _now_iso(),
            "type": "copy",
            "title": f"Copy from crowd ({mode.replace('_',' ')})",
            "payload": {"mode": mode, "source_agent_id": str((src or {}).get("id") or "")},
            "status": "pending",
            "constraints": {"deviation_pct": dev, "max_deviation_pct": max_dev},
        }
        log_audit(
            user,
            kind="proposal",
            msg=f"Agent proposed COPY ({mode}) dev={dev:.1f}% max={max_dev:.1f}%",
            agent_id=str(agent.get("id")),
            proposal_id=proposal["id"],
            meta={"mode": mode, "source_agent_id": proposal["payload"]["source_agent_id"]},
        )
    elif r < p_copy + p_trade:
        asset = random.choice(["bitcoin", "ethereum", "solana", "matic-network"])
        side = random.choice(["BUY", "SELL"])
        qty = round(0.01 + (risk/100.0)*0.05, 4)
        proposal = {
            "id": f"appr_{random.randint(100000,999999)}",
            "ts": _now_iso(),
            "type": "trade",
            "title": f"{side} {qty} {asset}",
            "payload": {"asset": asset, "side": side, "qty": qty},
            "status": "pending",
            "constraints": {"deviation_pct": dev, "max_deviation_pct": max_dev},
        }
        log_audit(
            user,
            kind="proposal",
            msg=f"Agent proposed TRADE {side} {asset} qty={qty} dev={dev:.1f}% max={max_dev:.1f}%",
            agent_id=str(agent.get("id")),
            proposal_id=proposal["id"],
            meta={"asset": asset, "side": side, "qty": qty},
        )
    else:
        amt = round(0.05 + (risk/100.0)*0.10, 2)  # $0.05-$0.15 demo
        proposal = {
            "id": f"appr_{random.randint(100000,999999)}",
            "ts": _now_iso(),
            "type": "payment",
            "title": f"Pay {amt} USDC (requires confirmation)",
            "payload": {"amount_usdc": amt, "to": "treasury"},
            "status": "pending",
            "constraints": {"deviation_pct": dev, "max_deviation_pct": max_dev},
        }
        log_audit(
            user,
            kind="proposal",
            msg=f"Agent proposed PAYMENT amt={amt} dev={dev:.1f}% max={max_dev:.1f}%",
            agent_id=str(agent.get("id")),
            proposal_id=proposal["id"],
            meta={"amount_usdc": amt},
        )

    agent["approvals"].insert(0, proposal)
    agent["approvals"] = agent["approvals"][:50]
    return proposal


def decide_auto_execute(user: Dict[str, Any], agent: Dict[str, Any], proposal: Dict[str, Any]) -> bool:
    """Auto mode rules.

    - Only trade proposals are eligible.
    - If crowd deviation exceeds max, auto-exec is blocked.
    - Payments/copy actions always require manual approval in the demo.
    """
    ensure_agent_runtime(agent)

    if str(agent.get("mode")) != "auto":
        return False

    if str(proposal.get("type")) != "trade":
        return False

    # Deviation constraint blocks auto execution
    try:
        dev = float((proposal.get("constraints") or {}).get("deviation_pct", _current_deviation(user, agent)))
    except Exception:
        dev = _current_deviation(user, agent)
    if dev > _max_deviation(user):
        return False

    return True