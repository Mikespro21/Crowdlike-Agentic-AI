from __future__ import annotations

import os
from typing import Any

import streamlit as st

try:
    # Streamlit raises if no secrets.toml exists when accessed.
    from streamlit.errors import StreamlitSecretNotFoundError
except Exception:  # pragma: no cover
    StreamlitSecretNotFoundError = Exception  # type: ignore


def get_setting(key: str, default: Any = None) -> Any:
    """Read a setting from Streamlit secrets if available; otherwise env; otherwise default.

    This avoids crashing when no secrets.toml is present (common in local dev / judge machines).
    """
    # 1) Try st.secrets
    try:
        return st.secrets.get(key, default)  # type: ignore[attr-defined]
    except StreamlitSecretNotFoundError:
        pass
    except Exception:
        # Parse errors or other secrets issues: fall back to env
        pass

    # 2) Env var
    return os.environ.get(key, default)


def bool_setting(key: str, default: bool = False) -> bool:
    v = str(get_setting(key, str(default))).strip().lower()
    return v not in ("0", "false", "no", "off", "")
