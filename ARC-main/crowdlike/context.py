import streamlit as st

from crowdlike.settings import get_setting


try:
    from streamlit_cookies_manager import EncryptedCookieManager  # type: ignore
except Exception:  # pragma: no cover
    EncryptedCookieManager = None  # type: ignore

from crowdlike.db import init_db
from crowdlike.auth import get_user_by_session


def init_app_context():
    """Optional cookie/session context.

    Not used by the core demo flow. Safe to import even if cookies manager isn't installed.
    """
    init_db()

    if EncryptedCookieManager is None:
        raise RuntimeError(
            "streamlit_cookies_manager is not installed. Install it or avoid importing crowdlike.context."
        )

    cookie_pw = get_setting("COOKIE_PASSWORD", "change-me")
    cookies = EncryptedCookieManager(prefix="crowdlike/", password=str(cookie_pw))
    if not cookies.ready():
        st.stop()

    # Load once per session
    if "user" not in st.session_state:
        token = cookies.get("session", "")
        user = get_user_by_session(token) if token else None
        st.session_state.user = user
        st.session_state.session_token = token if user else ""

    return cookies, st.session_state.get("user")
