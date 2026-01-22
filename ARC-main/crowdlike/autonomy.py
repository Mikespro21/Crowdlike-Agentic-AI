from __future__ import annotations

"""Autonomy ladder (v0.60).

Goal: make agent behavior feel product-grade and predictable.

Levels (per agent):
- off: no proposals, no execution
- assist: can propose, but requires approval
- auto: may auto-execute *practice trades* within tight caps
- auto_plus: may auto-execute *practice trades* with higher caps when trust signals allow

Notes:
- Payments are never auto-executed in the demo.
- Copy actions are proposed and require approval (keeps the demo legible).
"""

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .crowd_deviation import cohort_for_agent, deviation_pct


@dataclass(frozen=True)
class TrustSignals:
    crowd_score: float
    verified_receipts: int
    deviation_pct: float
    safety_ok: bool


DEFAULT_AUTONOMY: Dict[str, Any] = {
    # Hard caps for auto execution (practice trades only)
    "auto_max_trades_per_day": 2,
    "auto_plus_max_trades_per_day": 6,
    # How large a single auto trade may be (in USDC notional)
    "auto_max_notional_usdc": 10.0,
    "auto_plus_max_notional_usdc": 40.0,
    # Unlock requirements for auto_plus (demo-grade trust)
    "unlock_auto_plus": {
        "min_verified_receipts": 1,
        "min_crowd_score": 55.0,
        "max_deviation_pct": 20.0,
    },
}


def ensure_agent_autonomy(agent: Dict[str, Any]) -> None:
    """Ensure autonomy settings exist on an agent."""
    cfg = agent.get("autonomy")
    if not isinstance(cfg, dict):
        cfg = {}
        agent["autonomy"] = cfg

    # Fill defaults without clobbering user tweaks
    for k, v in DEFAULT_AUTONOMY.items():
        if k not in cfg:
            cfg[k] = v

    # Normalize mode string
    mode = str(agent.get("mode") or "assist").lower()
    if mode not in ("off", "assist", "auto", "auto_plus"):
        mode = "assist"
    agent["mode"] = mode


def trust_signals(user: Dict[str, Any], agent: Dict[str, Any]) -> TrustSignals:
    crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
    try:
        crowd_score = float(crowd.get("score", 50.0) or 50.0)
    except Exception:
        crowd_score = 50.0

    # Receipts are stored both globally and per-agent; count agent receipts first
    receipts = agent.get("purchases")
    if not isinstance(receipts, list):
        receipts = []
    verified = 0
    for r in receipts:
        if isinstance(r, dict) and str(r.get("status") or "").lower() in ("verified", "success", "confirmed"):
            verified += 1

    # Deviation
    try:
        cohort = cohort_for_agent(user, agent)
        dev = float(deviation_pct(agent, cohort))
    except Exception:
        dev = 0.0

    # Safety state
    safety = agent.get("safety") if isinstance(agent.get("safety"), dict) else {}
    enabled = bool(safety.get("enabled", True))
    fraud = bool(safety.get("fraud_alert", False))
    panic = bool(safety.get("panic", False))
    safety_ok = enabled and (not fraud) and (not panic)

    return TrustSignals(
        crowd_score=crowd_score,
        verified_receipts=int(verified),
        deviation_pct=float(dev),
        safety_ok=bool(safety_ok),
    )


def effective_mode(agent: Dict[str, Any], signals: TrustSignals) -> Tuple[str, str]:
    """Return (effective_mode, reason)."""
    ensure_agent_autonomy(agent)
    requested = str(agent.get("mode") or "assist").lower()
    if requested == "off":
        return "off", "Autonomy is OFF"

    if requested == "auto_plus":
        cfg = agent.get("autonomy") if isinstance(agent.get("autonomy"), dict) else {}
        unlock = cfg.get("unlock_auto_plus") if isinstance(cfg.get("unlock_auto_plus"), dict) else {}
        min_rcpt = int(unlock.get("min_verified_receipts", 1) or 1)
        min_score = float(unlock.get("min_crowd_score", 55.0) or 55.0)
        max_dev = float(unlock.get("max_deviation_pct", 20.0) or 20.0)

        if not signals.safety_ok:
            return "assist", "Safety state requires approval"
        if signals.verified_receipts < min_rcpt:
            return "auto", "AUTO+ locked: needs verified receipt"
        if signals.crowd_score < min_score:
            return "auto", "AUTO+ locked: crowd score too low"
        if signals.deviation_pct > max_dev:
            return "assist", "AUTO+ locked: deviation too high"
        return "auto_plus", "AUTO+ unlocked"

    if requested == "auto":
        if not signals.safety_ok:
            return "assist", "Safety state requires approval"
        return "auto", "AUTO enabled"

    # assist (default)
    return "assist", "Approval-first"


def auto_caps(agent: Dict[str, Any], effective: str) -> Dict[str, float]:
    ensure_agent_autonomy(agent)
    cfg = agent.get("autonomy") if isinstance(agent.get("autonomy"), dict) else {}
    if effective == "auto_plus":
        return {
            "max_trades_per_day": float(cfg.get("auto_plus_max_trades_per_day", 6) or 6),
            "max_notional_usdc": float(cfg.get("auto_plus_max_notional_usdc", 40.0) or 40.0),
        }
    return {
        "max_trades_per_day": float(cfg.get("auto_max_trades_per_day", 2) or 2),
        "max_notional_usdc": float(cfg.get("auto_max_notional_usdc", 10.0) or 10.0),
    }


def can_auto_execute_trade(agent: Dict[str, Any], effective: str, notional_usdc: float, trades_today: int) -> Tuple[bool, str]:
    """Decide whether we can auto-execute a practice trade."""
    if effective not in ("auto", "auto_plus"):
        return False, "Autonomy requires approval"

    caps = auto_caps(agent, effective)
    if trades_today >= int(caps["max_trades_per_day"]):
        return False, "Daily auto-trade limit reached"

    if notional_usdc > float(caps["max_notional_usdc"]):
        return False, "Trade exceeds auto notional cap"

    return True, "Within auto caps"
