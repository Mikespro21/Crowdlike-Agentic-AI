from __future__ import annotations

"""Compatibility layer for older imports.

Earlier versions rendered a top navigation bar with many buttons/popovers.
For v1.6.2, navigation is consolidated into a single scrollable sidebar rail.
We keep the `render_navbar(...)` entry point because pages call it via
`crowdlike.ui.nav(...)`.
"""

from typing import Any

import streamlit as st

from crowdlike.auth import current_user
from crowdlike.sidenav import render_sidenav


def render_navbar(*, active: str = "home", **_: Any) -> None:
    """Render the unified sidebar navigation.

    Notes:
    - Uses page links (not Streamlit buttons) for navigation.
    - Adds a scroll-based hide/show animation plus a manual toggle.
    """

    user = current_user() or {}
    render_sidenav(user, active_page=active)

    # Keep sidebar open on first paint if the user hasn't interacted yet.
    # (This is a no-op for most versions, but helps avoid confusion in Cloud.)
    st.session_state.setdefault("_cl_nav_seen", True)
