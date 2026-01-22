from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import streamlit as st

@dataclass(frozen=True)
class Step:
    n: int
    title: str
    body: str
    page: str
    target_key: str

TOTAL = 7

STEPS: Dict[int, Step] = {
    1: Step(1, "Welcome", "Start with the main action. We’ll guide Agent → Market → Execute → Wallet.", "home", "cta_automate"),
    2: Step(2, "Agent plan", "Tap “Generate a plan”.", "coach", "coach_plan"),
    3: Step(3, "Go Market", "Tap “Go to Market”.", "coach", "coach_to_market"),
    4: Step(4, "Pick asset", "Choose an asset to trade.", "market", "mkt_asset"),
    5: Step(5, "Execute", "Execute one demo trade to learn the flow.", "market", "mkt_exec"),
    6: Step(6, "Save wallet", "Save your wallet for ArcScan proof links.", "profile", "pf_save"),
    7: Step(7, "Done", "You’re ready: Agent → Market → Execute → Track.", "home", "nav_home"),
}

def _set_step(n: int) -> None:
    st.session_state["tour_step"] = max(1, min(TOTAL, int(n)))

def _finish(user: Dict[str, Any]) -> None:
    user["tutorial_done"] = True
    st.session_state["tour_done"] = True
    try:
        from crowdlike.auth import save_current_user
        save_current_user()
    except Exception:
        pass

def tour_complete_step(n: int) -> None:
    """Call this from pages when the user completes the highlighted task."""
    cur = int(st.session_state.get("tour_step", 1))
    if n == cur:
        if cur >= TOTAL:
            st.session_state["tour_done"] = True
        else:
            _set_step(cur + 1)
        st.rerun()

def _ensure_base_css_loaded() -> None:
    # Load the heavy CSS ONCE to reduce flicker during reruns.
    if st.session_state.get("_tour_css_loaded"):
        return
    st.session_state["_tour_css_loaded"] = True

    st.markdown(
        """
        <style>
        :root{
          --tour-right: 18px;
          --tour-bottom: 160px;
          --tour-w: min(420px, calc(100vw - 36px));
          --tour-pad: 12px;
        }

        /* Soft dim (non-blocking). Keep it subtle to reduce perceived flicker */
        .tour-dim{
          position: fixed; inset: 0;
          background: rgba(2,6,23,0.12);
          pointer-events: none;
          z-index: 9990;
          transition: opacity 120ms linear;
          opacity: 1;
        }

        /* Popup shell (HTML only, no clicks needed -> pointer-events:none) */
        #tour-float{
          position: fixed;
          right: var(--tour-right);
          bottom: var(--tour-bottom);
          width: var(--tour-w);
          z-index: 9999;
          border-radius: 12px;
          border: 1px solid rgba(14,165,233,0.14);
          background: rgba(255,255,255,0.96);
          box-shadow: 0 18px 70px rgba(2,6,23,0.12);
          padding: var(--tour-pad);
          backdrop-filter: blur(10px);
          pointer-events: none; /* IMPORTANT: do not block underlying app clicks */
        }
        #tour-float .topline{
          height: 3px; border-radius: 999px;
          background: linear-gradient(90deg, rgba(14,165,233,0.32), rgba(167,139,250,0.10));
          margin-bottom: 10px;
        }
        #tour-float .kicker{
          font-size: 0.78rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: rgba(71,85,105,0.92);
          margin-bottom: 4px;
        }
        #tour-float .title{
          font-weight: 820;
          font-size: 1.02rem;
          margin-bottom: 6px;
          color: rgba(15,23,42,0.95);
        }
        #tour-float .body{
          color: rgba(51,65,85,0.95);
          line-height: 1.45;
          font-size: 0.95rem;
          margin-bottom: 8px;
        }
        #tour-float .hint{
          color: rgba(71,85,105,0.90);
          font-size: 0.90rem;
        }

        /* “Buttons inside popup” – we position the real Streamlit buttons OVER the popup */
        .tour-btn{
          position: fixed !important;
          right: calc(var(--tour-right) + var(--tour-pad)) !important;
          z-index: 10000 !important;
          width: calc(var(--tour-w) - (var(--tour-pad) * 2)) !important;
        }

        /* Keep these buttons clickable */
        .tour-btn, .tour-btn * { pointer-events: auto !important; }

        </style>
        """,
        unsafe_allow_html=True,
    )

def _inject_step_css(target_key: str, k_skip: str, k_back: str, k_next: str) -> None:
    # Step-specific CSS (small) — spotlight + yellow required action + buttons placed inside popup
    st.markdown(
        f"""
        <style>
        /* Spotlight target container above dim */
        #st-key-{target_key} {{
          position: relative !important;
          z-index: 9992 !important;
        }}

        /* If target is a BUTTON: make it yellow */
        #st-key-{target_key} button {{
          background: rgba(250, 204, 21, 0.90) !important;
          color: rgba(15,23,42,0.98) !important;
          border: 1px solid rgba(234, 179, 8, 0.70) !important;
          box-shadow: 0 0 0 3px rgba(250,204,21,0.18), 0 18px 55px rgba(2,6,23,0.16) !important;
        }}

        /* If target is an input/select: highlight border in yellow */
        #st-key-{target_key} input,
        #st-key-{target_key} textarea {{
          outline: none !important;
          border: 1px solid rgba(234,179,8,0.80) !important;
          box-shadow: 0 0 0 3px rgba(250,204,21,0.14) !important;
        }}

        /* Place tutorial buttons INSIDE the popup: stacked at the bottom area */
        #st-key-{k_next} {{ bottom: calc(var(--tour-bottom) + 12px) !important; }}
        #st-key-{k_back} {{ bottom: calc(var(--tour-bottom) + 60px) !important; }}
        #st-key-{k_skip} {{ bottom: calc(var(--tour-bottom) + 108px) !important; }}

        #st-key-{k_next}, #st-key-{k_back}, #st-key-{k_skip} {{
          right: calc(var(--tour-right) + var(--tour-pad)) !important;
          z-index: 10000 !important;
          width: calc(var(--tour-w) - (var(--tour-pad) * 2)) !important;
          position: fixed !important;
        }}

        /* Ensure those buttons don’t take layout space */
        #st-key-{k_next}, #st-key-{k_back}, #st-key-{k_skip} {{
          margin: 0 !important;
          padding: 0 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def maybe_run_tour(user: Dict[str, Any] | None, current_page: str) -> None:
    """
    Overlay tutorial that persists across reruns (Streamlit 1.52.2 friendly).
    - Popup HTML is pointer-events:none so it never blocks the app.
    - Real Streamlit buttons are positioned over the popup so they feel “inside it”.
    """
    if not user:
        return
    if user.get("tutorial_done") or st.session_state.get("tour_done"):
        return

    _ensure_base_css_loaded()

    step = int(st.session_state.get("tour_step", 1))
    _set_step(step)
    s = STEPS[step]

    # Namespace button keys per page (prevents duplicate key errors)
    k_skip = f"tour_skip_{current_page}"
    k_back = f"tour_back_{current_page}"
    k_next = f"tour_next_{current_page}"

    # Dim overlay (non-blocking)
    st.markdown('<div class="tour-dim"></div>', unsafe_allow_html=True)

    # Popup text (fixed)
    wrong_page = (current_page != s.page)
    extra = ""
    if wrong_page:
        extra = f"<div class='hint' style='margin-top:6px;'>This step is on: <b>{s.page}</b>. You can keep clicking around here or use Next.</div>"

    st.markdown(
        f"""
        <div id="tour-float">
          <div class="topline"></div>
          <div class="kicker">Step {step} of {TOTAL}</div>
          <div class="title">{s.title}</div>
          <div class="body">{s.body}</div>
          <div class="hint">Tip: the highlighted action turns yellow. The guide stays open while you use the app.</div>
          {extra}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Step CSS: spotlight + yellow target + put buttons visually inside popup
    _inject_step_css(s.target_key, k_skip, k_back, k_next)

    # Render the buttons (they get positioned by CSS into the popup)
    if st.button("Next", key=k_next, disabled=(step >= TOTAL), width="stretch"):
        _set_step(step + 1); st.rerun()

    if st.button("Back", key=k_back, disabled=(step <= 1), width="stretch"):
        _set_step(step - 1); st.rerun()

    if st.button("Skip", key=k_skip, width="stretch"):
        _finish(user); st.rerun()
