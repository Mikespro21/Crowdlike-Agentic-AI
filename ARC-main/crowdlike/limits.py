
from __future__ import annotations

import time

def _now() -> int:
    return int(time.time())

def allow(d: dict, key: str, cooldown_s: int = 0, daily_max: int | None = None) -> tuple[bool, str | None]:
    """
    Simple rate limiter stored inside user data dict.
    - cooldown_s: seconds between allowed actions.
    - daily_max: max times per day (UTC/local server time).
    """
    d.setdefault("limits", {})
    limits = d["limits"]
    now = _now()

    # cooldown
    last = int(limits.get(f"{key}.last", 0) or 0)
    if cooldown_s and now - last < cooldown_s:
        wait = cooldown_s - (now - last)
        return False, f"Please wait {wait}s."

    # daily max
    if daily_max is not None:
        day = time.strftime("%Y-%m-%d")
        count_key = f"{key}.count.{day}"
        count = int(limits.get(count_key, 0) or 0)
        if count >= int(daily_max):
            return False, "Daily limit reached."
        limits[count_key] = count + 1

    limits[f"{key}.last"] = now
    return True, None
