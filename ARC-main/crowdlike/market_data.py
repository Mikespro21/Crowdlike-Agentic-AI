from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
import streamlit as st


@dataclass
class MarketRow:
    id: str
    symbol: str
    name: str
    image: str
    current_price: float
    price_change_percentage_24h: float | None
    total_volume: float | None
    market_cap_rank: int | None


_CG_BASE = "https://api.coingecko.com/api/v3"


@st.cache_data(ttl=60, show_spinner=False)
def get_markets(vs_currency: str = "usd", ids: Optional[List[str]] = None) -> List[MarketRow]:
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    if ids:
        params["ids"] = ",".join(ids)

    r = requests.get(f"{_CG_BASE}/coins/markets", params=params, timeout=15)
    r.raise_for_status()
    rows = []
    for x in r.json():
        rows.append(
            MarketRow(
                id=x.get("id", ""),
                symbol=(x.get("symbol") or "").upper(),
                name=x.get("name", ""),
                image=x.get("image", ""),
                current_price=float(x.get("current_price") or 0.0),
                price_change_percentage_24h=x.get("price_change_percentage_24h"),
                total_volume=x.get("total_volume"),
                market_cap_rank=x.get("market_cap_rank"),
            )
        )
    return rows


@st.cache_data(ttl=300, show_spinner=False)
def get_market_chart_7d(coin_id: str, vs_currency: str = "usd") -> List[Tuple[int, float]]:
    params = {"vs_currency": vs_currency, "days": 7}
    r = requests.get(f"{_CG_BASE}/coins/{coin_id}/market_chart", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    prices = data.get("prices") or []
    # prices: [[timestamp_ms, price], ...]
    out: List[Tuple[int, float]] = []
    for p in prices:
        if not isinstance(p, list) or len(p) < 2:
            continue
        out.append((int(p[0]), float(p[1])))
    return out
