from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import time
import streamlit as st

from crowdlike.state import get_state, set_state, spend, earn, add_xp

@dataclass
class ShopItem:
    id: str
    name: str
    desc: str
    price: int
    currency: str  # "coins" or "gems"
    tags: List[str]
    slot: str      # "theme", "badge", "boost", "utility"

SHOP_SECTIONS: List[Dict] = [
    {
        "title": "Boosts",
        "subtitle": "Faster XP, streak protection, and momentum upgrades.",
        "items": [
            ShopItem("boost_xp_1", "XP Booster I", "+15 XP instantly", 90, "coins", ["xp", "starter"], "boost"),
            ShopItem("boost_xp_2", "XP Booster II", "+40 XP instantly", 2, "gems", ["xp", "premium"], "boost"),
            ShopItem("boost_streak", "Streak Shield", "Prevents 1 streak break", 3, "gems", ["streak", "premium"], "boost"),
        ],
    },
    {
        "title": "Cosmetics",
        "subtitle": "Themes and badges (pure UI flex).",
        "items": [
            ShopItem("theme_aurora", "Aurora Theme", "Blue/Purple neon accent pack", 180, "coins", ["theme", "blue"], "theme"),
            ShopItem("theme_glacier", "Glacier Theme", "Cool minimalist glass UI", 1, "gems", ["theme", "clean"], "theme"),
            ShopItem("badge_builder", "Builder Badge", "Shows on your profile", 120, "coins", ["badge"], "badge"),
        ],
    },
    {
        "title": "Utilities",
        "subtitle": "Helpful tools for your Arc flow.",
        "items": [
            ShopItem("util_receipts", "Receipt Mode", "More detailed tx receipt UI", 150, "coins", ["arc", "tools"], "utility"),
            ShopItem("util_watchlist", "Watchlist+", "Adds extra market watch slots", 1, "gems", ["market"], "utility"),
        ],
    },
]

def _owned(item_id: str) -> bool:
    s = get_state()
    return item_id in (s.get("inventory") or {})

def _equip(slot: str, item_id: str) -> None:
    s = get_state()
    s.setdefault("equipped", {})
    s["equipped"][slot] = item_id
    set_state(s)

def _buy(item: ShopItem) -> bool:
    if _owned(item.id):
        return True
    if not spend(item.currency, item.price):
        return False
    s = get_state()
    s.setdefault("inventory", {})
    s["inventory"][item.id] = {"name": item.name, "slot": item.slot, "ts": int(time.time())}
    set_state(s)
    add_xp(8, reason=f"shop:{item.id}")
    return True

def render_shop():
    st.subheader("Shop")
    st.caption("Buy items with Coins/Gems. Equip themes/badges. Boosts apply instantly.")

    s = get_state()
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Level", str(__import__("crowdlike.state").state.level_from_xp(s.get("xp", 0))))
    with colB:
        st.metric("Coins", str(s.get("coins", 0)))
    with colC:
        st.metric("Gems", str(s.get("gems", 0)))

    q = st.text_input("Search", "", key="shop_search")
    tag = st.selectbox("Tag filter", ["(all)", "xp", "streak", "theme", "badge", "arc", "tools", "market", "starter", "premium", "clean", "blue"], key="shop_tag")

    for si, section in enumerate(SHOP_SECTIONS):
        st.markdown(f"### {section['title']}")
        st.caption(section["subtitle"])
        items: List[ShopItem] = section["items"]

        # filter
        filtered = []
        for it in items:
            if q and (q.lower() not in (it.name + " " + it.desc).lower()):
                continue
            if tag != "(all)" and tag not in it.tags:
                continue
            filtered.append(it)

        if not filtered:
            st.info("No items match your filters.")
            continue

        cols = st.columns(3)
        for idx, it in enumerate(filtered):
            c = cols[idx % 3]
            with c:
                owned = _owned(it.id)
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"**{it.name}**")
                st.caption(it.desc)
                st.markdown(f"<span class='pill'>💳 {it.price} {it.currency}</span> "
                            f"<span class='pill'><small>slot</small> {it.slot}</span>",
                            unsafe_allow_html=True)

                btn_row = st.columns([1,1])
                with btn_row[0]:
                    if owned:
                        st.button("Owned", disabled=True, key=f"shop_owned_{si}_{it.id}")
                    else:
                        if st.button("Buy", key=f"shop_buy_{si}_{it.id}"):
                            ok = _buy(it)
                            if ok:
                                st.success("Purchased!")
                                st.rerun()
                            else:
                                st.error("Not enough balance.")
                with btn_row[1]:
                    if owned and it.slot in ("theme", "badge"):
                        if st.button("Equip", key=f"shop_equip_{si}_{it.id}"):
                            _equip(it.slot, it.id)
                            st.success("Equipped.")
                            st.rerun()
                    else:
                        st.button("Equip", disabled=True, key=f"shop_noequip_{si}_{it.id}")

                st.markdown("</div>", unsafe_allow_html=True)
