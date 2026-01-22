from __future__ import annotations

"""Shared layout helpers.

This project is intentionally Streamlit-first.

UX goal: keep the demo "impossible to get lost" during judge runs.
"""

from typing import Any, Dict

import streamlit as st

from crowdlike.arc_main_shell import render_arc_main_shell


def render_sidebar(
    user: Dict[str, Any],
    *,
    active_page: str = "",
    active: str | None = None,
    **_: Any,
) -> None:
    """Unified, button-free navigation.

    The app previously used a mixture of top-nav popovers and in-sidebar
    call-to-action buttons. For v1.6.2, we intentionally reduce the sidebar
    to a single scrollable nav rail (links only), with auto hide/show behavior.
    """

    # Backwards-compat: older pages passed `active="..."`.
    if (not active_page) and active:
        active_page = str(active)

    render_arc_main_shell(user, active_page=active_page or "home")