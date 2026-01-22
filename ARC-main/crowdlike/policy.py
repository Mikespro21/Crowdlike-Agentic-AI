from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple
import time

from .limits import allow


def _day_key() -> str:
    # Uses server local time; good enough for demo.
    return time.strftime("%Y-%m-%d")


def _crowd_score(user: Dict[str, Any]) -> float:
    crowd = user.get("crowd") if isinstance(user.get("crowd"), dict) else {}
    try:
        return float(crowd.get("score", 50.0))
    except Exception:
        return 50.0


def _boost_from_crowd(score: float) -> float:
    """Return a gentle multiplier based on crowd score.

    - score 50 -> 1.00
    - score 0  -> 0.80
    - score 100-> 1.20

    Keep it small so safety rails remain meaningful.
    """
    try:
        s = max(0.0, min(100.0, float(score)))
    except Exception:
        s = 50.0
    boost = 0.8 + 0.4 * (s / 100.0)
    return max(0.8, min(1.2, boost))


@dataclass
class PaymentPolicy:
    """Simple safety rails for on-chain USDC payments (demo).

    Stored in user['policy'] and enforced in checkout before presenting a payment action.

    Crowd influence: limits get a small +/- boost based on user['crowd']['score'].
    """

    max_per_tx_usdc: float = 0.10
    daily_cap_usdc: float = 0.50
    cooldown_s: int = 15

    @classmethod
    def from_user(cls, user: Dict[str, Any]) -> "PaymentPolicy":
        p = user.get("policy") if isinstance(user.get("policy"), dict) else {}

        def _f(key: str, default: float) -> float:
            try:
                return float(p.get(key, default))
            except Exception:
                return default

        def _i(key: str, default: int) -> int:
            try:
                return int(p.get(key, default))
            except Exception:
                return default

        return cls(
            max_per_tx_usdc=max(0.0, _f("max_per_tx_usdc", cls.max_per_tx_usdc)),
            daily_cap_usdc=max(0.0, _f("daily_cap_usdc", cls.daily_cap_usdc)),
            cooldown_s=max(0, _i("cooldown_s", cls.cooldown_s)),
        )

    def effective(self, user: Dict[str, Any]) -> "PaymentPolicy":
        """Return a policy with limits adjusted by crowd score (gentle multiplier)."""
        score = _crowd_score(user)
        boost = _boost_from_crowd(score)
        return PaymentPolicy(
            max_per_tx_usdc=round(self.max_per_tx_usdc * boost, 6),
            daily_cap_usdc=round(self.daily_cap_usdc * boost, 6),
            cooldown_s=self.cooldown_s,
        )

    def authorize_payment(self, user: Dict[str, Any], amount_usdc: float, commit: bool = True) -> Tuple[bool, str]:
        """Return (ok, message). If commit=True, updates counters/totals in user state."""
        try:
            amt = float(amount_usdc or 0.0)
        except Exception:
            return False, "Invalid amount."
        if amt <= 0:
            return False, "Amount must be > 0."

        eff = self.effective(user)

        if eff.max_per_tx_usdc > 0 and amt > eff.max_per_tx_usdc + 1e-9:
            return False, f"Policy: max per tx is ${eff.max_per_tx_usdc:.2f}."

        limits = user.setdefault("limits", {})
        total_key = f"usdc_total_{_day_key()}"
        try:
            total = float(limits.get(total_key, 0.0) or 0.0)
        except Exception:
            total = 0.0
        if eff.daily_cap_usdc > 0 and (total + amt) > eff.daily_cap_usdc + 1e-9:
            return False, f"Policy: daily cap is ${eff.daily_cap_usdc:.2f} (today: ${total:.2f})."

        # Cooldown gate (prevents spam / repeated clicks)
        if commit:
            ok, why = allow(user, key="pay.usdc", cooldown_s=eff.cooldown_s, daily_max=None)
            if not ok:
                return False, f"Policy: {why or 'cooldown active'}"

            limits[total_key] = round(total + amt, 6)

        return True, "Allowed."
