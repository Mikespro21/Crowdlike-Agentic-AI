from __future__ import annotations

"""Agent runs & run reports (v0.60).

A "run" is a structured cycle:
- Snapshot context (strategy, risk, deviation, autonomy)
- Ask orchestrator to propose the next action
- Decide: auto-execute (practice trade only) vs queue for approval
- Write: run report + events + audit entries
"""

import datetime as _dt
import random
from typing import Any, Dict, List, Optional, Tuple

from .autonomy import TrustSignals, trust_signals, effective_mode, can_auto_execute_trade
from .events import log_event
from .audit import log_audit
from .orchestrator import propose_next_action, decide_auto_execute
from .performance import portfolio_value, ensure_daily_snapshot


def _now_iso() -> str:
    return _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _today() -> str:
    return _dt.date.today().isoformat()


def ensure_runs_schema(agent: Dict[str, Any]) -> None:
    agent.setdefault("runs", [])
    if not isinstance(agent.get("runs"), list):
        agent["runs"] = []


def _trades_today(portfolio: Dict[str, Any]) -> int:
    trades = portfolio.get("trades") if isinstance(portfolio.get("trades"), list) else []
    d = _today()
    n = 0
    for t in trades:
        if not isinstance(t, dict):
            continue
        ts = str(t.get("ts") or "")
        if ts.startswith(d):
            n += 1
    return n


def _price_map_from_markets(markets: List[Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for r in markets or []:
        try:
            cid = getattr(r, "id", None) or r.get("id")  # type: ignore
            px = getattr(r, "current_price", None) or r.get("current_price")  # type: ignore
            if cid:
                out[str(cid)] = float(px)
        except Exception:
            continue
    return out


def _apply_practice_trade(agent: Dict[str, Any], *, side: str, asset: str, qty: float, price: float) -> Tuple[bool, str, float]:
    """Apply a practice BUY/SELL to the agent portfolio.

    Returns (ok, message, notional_usdc).
    """
    portfolio = agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}
    portfolio.setdefault("cash_usdc", 1000.0)
    portfolio.setdefault("positions", {})
    portfolio.setdefault("trades", [])

    try:
        cash = float(portfolio.get("cash_usdc", 0.0) or 0.0)
    except Exception:
        cash = 0.0

    positions = portfolio.get("positions") if isinstance(portfolio.get("positions"), dict) else {}
    portfolio["positions"] = positions
    trades = portfolio.get("trades") if isinstance(portfolio.get("trades"), list) else []
    portfolio["trades"] = trades

    side = str(side or "").upper()
    asset = str(asset or "")
    qty = float(qty or 0.0)
    price = float(price or 0.0)
    if qty <= 0 or price <= 0 or not asset:
        return False, "Invalid trade parameters", 0.0

    notional = qty * price

    if side == "BUY":
        if cash < notional:
            return False, "Insufficient cash for BUY", notional
        cash -= notional
        positions[asset] = float(positions.get(asset, 0.0) or 0.0) + qty
    elif side == "SELL":
        have = float(positions.get(asset, 0.0) or 0.0)
        if have < qty:
            return False, "Insufficient position for SELL", notional
        cash += notional
        positions[asset] = have - qty
        if positions[asset] <= 1e-12:
            positions.pop(asset, None)
    else:
        return False, "Unknown side", notional

    portfolio["cash_usdc"] = float(cash)
    trades.insert(0, {"ts": _now_iso(), "side": side, "coin": asset, "qty": qty, "price": price, "cash": float(notional)})

    agent["portfolio"] = portfolio
    return True, "Executed", float(notional)


def run_agent_cycle(
    user: Dict[str, Any],
    agent: Dict[str, Any],
    *,
    markets: Optional[List[Any]] = None,
    reason: str = "manual",
) -> Dict[str, Any]:
    """Run one orchestrated cycle for an agent and return the run report."""
    ensure_runs_schema(agent)

    sig: TrustSignals = trust_signals(user, agent)
    eff_mode, eff_reason = effective_mode(agent, sig)

    # Propose action (even in assist) unless OFF
    proposal = None
    decision = {"status": "skipped", "reason": "Autonomy OFF"}
    executed = False
    queued = False

    if eff_mode != "off":
        proposal = propose_next_action(user, agent, markets=markets)
        if proposal:
            # Payments & copy always require approval (demo legibility)
            ptype = str(proposal.get("type") or "")
            if ptype != "trade":
                agent.setdefault("approvals", [])
                if isinstance(agent.get("approvals"), list):
                    agent["approvals"].insert(0, proposal)
                queued = True
                decision = {"status": "queued", "reason": "Non-trade actions require approval"}
                log_event(user, kind="run", title=f"Queued {ptype} for approval", details=str(proposal.get("title") or ""), agent_id=str(agent.get("id")))
            else:
                # Potential auto-execution (practice trade only)
                payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else {}
                asset = str(payload.get("asset") or "")
                side = str(payload.get("side") or "")
                try:
                    qty = float(payload.get("qty") or 0.0)
                except Exception:
                    qty = 0.0

                # Need a price map
                pm = _price_map_from_markets(markets or [])
                price = float(pm.get(asset, 0.0) or 0.0)

                # Notional
                notional = qty * price if price else 0.0
                trades_today = _trades_today(agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {})

                auto_ok, auto_why = can_auto_execute_trade(agent, eff_mode, notional, trades_today)
                policy_ok = decide_auto_execute(user, agent, proposal)

                if eff_mode in ("auto", "auto_plus") and auto_ok and policy_ok and price > 0:
                    ok, msg, _ = _apply_practice_trade(agent, side=side, asset=asset, qty=qty, price=price)
                    if ok:
                        executed = True
                        decision = {"status": "executed", "reason": f"Auto: {auto_why}"}
                        log_event(user, kind="trade", title=f"AUTO {side} {asset}", details=f"qty={qty} notional=${notional:.2f}", agent_id=str(agent.get("id")))
                        log_audit(user, kind="auto_exec", msg=f"Auto executed trade {side} {asset} qty={qty} notional={notional:.2f}", agent_id=str(agent.get("id")), proposal_id=str(proposal.get("id")))
                    else:
                        # fall back to queue
                        agent.setdefault("approvals", [])
                        if isinstance(agent.get("approvals"), list):
                            agent["approvals"].insert(0, proposal)
                        queued = True
                        decision = {"status": "queued", "reason": f"Auto failed: {msg}"}
                        log_event(user, kind="run", title=f"Queued trade for approval", details=f"{msg}", agent_id=str(agent.get("id")))
                else:
                    agent.setdefault("approvals", [])
                    if isinstance(agent.get("approvals"), list):
                        agent["approvals"].insert(0, proposal)
                    queued = True
                    why = "Approval mode"
                    if eff_mode in ("auto", "auto_plus") and not auto_ok:
                        why = auto_why
                    elif eff_mode in ("auto", "auto_plus") and not policy_ok:
                        why = "Policy/deviation constraint blocked auto"
                    elif price <= 0:
                        why = "Missing live price"
                    decision = {"status": "queued", "reason": why}
                    log_event(user, kind="run", title="Queued trade for approval", details=why, agent_id=str(agent.get("id")))

    # Snapshot value history after any portfolio mutation
    try:
        pm = _price_map_from_markets(markets or [])
        v = portfolio_value(agent.get("portfolio") if isinstance(agent.get("portfolio"), dict) else {}, pm)
        ensure_daily_snapshot(agent, v)
    except Exception:
        pass

    run_id = f"run_{_today()}_{random.randint(100000, 999999)}"
    report: Dict[str, Any] = {
        "id": run_id,
        "ts": _now_iso(),
        "reason": str(reason or "manual"),
        "agent_id": str(agent.get("id") or ""),
        "autonomy": {"requested": str(agent.get("mode") or "assist"), "effective": eff_mode, "note": eff_reason},
        "signals": {
            "crowd_score": float(sig.crowd_score),
            "verified_receipts": int(sig.verified_receipts),
            "deviation_pct": float(sig.deviation_pct),
            "safety_ok": bool(sig.safety_ok),
        },
        "proposal": {
            "type": str((proposal or {}).get("type") or ""),
            "title": str((proposal or {}).get("title") or ""),
            "id": str((proposal or {}).get("id") or ""),
        } if proposal else None,
        "decision": decision,
        "executed": bool(executed),
        "queued": bool(queued),
        "strategy": agent.get("strategy") if isinstance(agent.get("strategy"), dict) else {},
    }

    agent["runs"].insert(0, report)
    agent["runs"] = agent["runs"][:250]
    return report
