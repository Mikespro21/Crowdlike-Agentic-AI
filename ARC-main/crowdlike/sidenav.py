from __future__ import annotations

"""Sidebar navigation rail.

Design goals:
- Replace button-heavy navigation with a single, scrollable nav rail.
- Allow the nav rail to hide/show with smooth animations on scroll.
- Allow manual hide/show via a small floating toggle (not a Streamlit button).

Implementation notes:
- We intentionally avoid third-party components so this works in Streamlit Cloud.
- The scroll listener attaches to the element that actually scrolls in Streamlit
  ("section.main"), falling back to window.
"""

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st
import streamlit.components.v1 as components

from crowdlike.registry import all_pages, Page
from crowdlike.version import VERSION


def _run_id() -> Optional[str]:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore

        ctx = get_script_run_ctx()
        return getattr(ctx, "script_run_id", None) or getattr(ctx, "run_id", None)
    except Exception:
        return None


def _once_per_run(key: str) -> bool:
    """Return True if we should proceed; False if this already ran this script run."""
    rid = _run_id()
    if not rid:
        # Best-effort fallback; don't block.
        if st.session_state.get(key):
            return False
        st.session_state[key] = True
        return True

    if st.session_state.get(key) == rid:
        return False
    st.session_state[key] = rid
    return True


def _group_pages(pages: Iterable[Page]) -> List[tuple[str, List[Page]]]:
    grouped: Dict[str, List[Page]] = defaultdict(list)
    for p in pages:
        grouped[p.group].append(p)
    # stable order by group then page order
    out: List[tuple[str, List[Page]]] = []
    for g in ["Website", "App", "Engagement", "Controls", "Settings", "More"]:
        if g in grouped:
            out.append((g, sorted(grouped[g], key=lambda x: (x.order, x.label))))
    for g in sorted([k for k in grouped.keys() if k not in {x[0] for x in out}]):
        out.append((g, sorted(grouped[g], key=lambda x: (x.order, x.label))))
    return out


def _inject_nav_behavior() -> None:
    """Inject toggle + scroll-hide behavior.

    This is Cloud-safe (pure JS/CSS) and does not require Streamlit widgets.
    """
    if not _once_per_run("_cl_nav_behavior_run_id"):
        return

    components.html(
        """
        <div id="cl-nav-toggle" aria-label="Toggle navigation" title="Toggle navigation" role="button">☰</div>
        <script>
        (function(){
          const body = document.body;
          const TOGGLE_ID = 'cl-nav-toggle';
          const CLS_HIDDEN = 'cl-nav-hidden';
          const CLS_MANUAL = 'cl-nav-manual-hidden';
          const CLS_READY  = 'cl-nav-js-ready';

          if (body.classList.contains(CLS_READY)) return;
          body.classList.add(CLS_READY);

          // Ensure toggle stays present across reruns.
          const toggle = document.getElementById(TOGGLE_ID);
          if (toggle){
            toggle.addEventListener('click', () => {
              const isHidden = body.classList.contains(CLS_HIDDEN);
              if (isHidden){
                body.classList.remove(CLS_HIDDEN);
                body.classList.remove(CLS_MANUAL);
              } else {
                body.classList.add(CLS_HIDDEN);
                body.classList.add(CLS_MANUAL);
              }
            });
          }

          // Scroll listener: hide on scroll down, show on scroll up.
          let lastY = 0;
          const threshold = 18;

          function getScrollEl(){
            // Streamlit typically scrolls inside section.main
            return document.querySelector('section.main') || document.scrollingElement || window;
          }
          const scrollEl = getScrollEl();

          function getY(){
            if (scrollEl === window) return window.scrollY || 0;
            // @ts-ignore
            return (scrollEl && scrollEl.scrollTop) ? scrollEl.scrollTop : (window.scrollY || 0);
          }

          function onScroll(){
            if (body.classList.contains(CLS_MANUAL)) return; // user explicitly hid it
            const y = getY();
            const dy = y - lastY;
            if (dy > threshold){
              body.classList.add(CLS_HIDDEN);
              lastY = y;
            } else if (dy < -threshold){
              body.classList.remove(CLS_HIDDEN);
              lastY = y;
            }
          }

          if (scrollEl && scrollEl.addEventListener){
            scrollEl.addEventListener('scroll', onScroll, {passive: true});
          } else {
            window.addEventListener('scroll', onScroll, {passive: true});
          }
        })();
        </script>
        """,
        height=0,
    )


def render_sidenav(
    user: Optional[Dict[str, Any]] = None,
    *,
    active_page: str = "home",
) -> None:
    """Render the scrollable nav rail.

    - No navigation buttons. Uses page links.
    - Full page list.
    - Hide/show behavior handled by injected JS + CSS.
    """

    # Normalize
    a = (active_page or "home").strip().lower()
    a = {"launch app": "dashboard", "leaderboard": "compare", "leaderboards": "compare"}.get(a, a)

    role = "human"
    if isinstance(user, dict):
        role = str(user.get("role") or "human").lower()

    pages = all_pages(role)
    groups = _group_pages(pages)

    _inject_nav_behavior()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="cl-nav-brand">
              <div class="cl-nav-logo">🫧</div>
              <div class="cl-nav-meta">
                <div class="cl-nav-title">Crowdlike</div>
                <div class="cl-nav-sub">v{VERSION}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="cl-nav-scroll">', unsafe_allow_html=True)
        for g, items in groups:
            st.markdown(f'<div class="cl-nav-group">{g}</div>', unsafe_allow_html=True)
            for p in items:
                label = f"{p.icon} {p.label}".strip()
                if p.id == a:
                    label = f"• {label}"
                st.page_link(p.path, label=label)
        st.markdown("</div>", unsafe_allow_html=True)
