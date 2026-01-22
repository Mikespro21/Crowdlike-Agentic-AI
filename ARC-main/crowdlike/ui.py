from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from crowdlike.version import VERSION

# Enforced by background gradient stops:
# Blue = 0-30% (30)
# White = 30-90% (60)
# Purple = 90-100% (10)
_BG_RATIO = {"blue": 30, "white": 60, "purple": 10}


def apply_ui() -> None:
    """Global UI skin: premium glass cards, soft gradient, consistent pills/badges/steppers."""
    css = r"""
    <style>
    :root{
        --white: #FFFFFF;
        --blue: #0EA5E9;
        --blue-soft: rgba(14,165,233,0.10);
        --purple: #A78BFA;
        --purple-soft: rgba(167,139,250,0.10);

        --text: #0F172A;
        --muted: #64748B;

        --green: #16A34A;
        --red: #EF4444;
        --amber: #F59E0B;

        --r-card: 12px;
        --r-hero: 14px;
        --r-btn: 14px;

        --border: rgba(148,163,184,0.16);
        --shadow: 0 14px 34px rgba(15, 23, 42, 0.10);
        --shadow-soft: 0 10px 22px rgba(15,23,42,0.06);
        --focus: 0 0 0 3px rgba(14,165,233,0.20);

        --baseline: 8px;
--gutter: 24px;
--content-max: 1120px;
        --grid-col-gap: 24px;
        --grid-row-gap: 16px;
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 24px;
--space-6: 32px;
--space-7: 40px;
--space-8: 48px;
--space-9: 56px;
--space-10: 64px;
--line: rgba(148,163,184,0.10);
}

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @media (prefers-reduced-motion: reduce){
      *{ animation: none !important; transition: none !important; }
    }

    /* Mostly-white background with soft blue + minimal purple */
    .stApp{
        background:
          radial-gradient(900px 360px at 16% 6%, rgba(14,165,233,0.10) 0%, rgba(14,165,233,0.00) 62%),
          radial-gradient(780px 320px at 86% 10%, rgba(167,139,250,0.06) 0%, rgba(167,139,250,0.00) 60%),
          linear-gradient(135deg,
            rgba(255,255,255,0.997) 0%,
            rgba(255,255,255,0.997) 58%,
            rgba(14,165,233,0.035) 100%
          );
        color: var(--text);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    header[data-testid="stHeader"]{ background: transparent; }
    #MainMenu {visibility: hidden;}
    footer{ visibility:hidden; }

    .main .block-container{
    padding-top: var(--space-5);
    padding-bottom: var(--space-10);
    padding-left: var(--gutter);
    padding-right: var(--gutter);
    max-width: var(--content-max);
}

    section[data-testid="stSidebar"]{
        background: rgba(255,255,255,0.92);
        border-right: 1px solid rgba(148,163,184,0.14);
        width: 280px;
        min-width: 280px;
        max-width: 280px;
        overflow: hidden;
        transition: width 220ms ease, min-width 220ms ease, max-width 220ms ease;
    }

    /* --- Sidebar nav rail (scrollable) --- */
    .cl-nav-brand{
        display:flex; align-items:center; gap: 10px;
        padding: 12px 10px 10px 10px;
        margin-bottom: 8px;
        border-bottom: 1px solid rgba(148,163,184,0.14);
    }
    .cl-nav-logo{ font-size: 1.25rem; line-height: 1; }
    .cl-nav-title{ font-weight: 820; letter-spacing: -0.02em; }
    .cl-nav-sub{ color: var(--muted); font-size: 0.82rem; margin-top: -2px; }

    .cl-nav-scroll{
        max-height: calc(100vh - 92px);
        overflow-y: auto;
        padding: 6px 8px 14px 8px;
    }

    .cl-nav-group{
        margin-top: 12px;
        margin-bottom: 6px;
        font-size: 0.78rem;
        font-weight: 750;
        color: rgba(100,116,139,0.90);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Tighten page_link spacing inside the sidebar */
    section[data-testid="stSidebar"] a{
        display: block;
        padding: 8px 10px;
        border-radius: 10px;
        margin: 2px 0;
        text-decoration: none !important;
        color: var(--text) !important;
    }
    section[data-testid="stSidebar"] a:hover{
        background: rgba(14,165,233,0.08);
        box-shadow: 0 0 0 3px rgba(14,165,233,0.10);
    }

    /* Toggle control (not a Streamlit button) */
    #cl-nav-toggle{
        position: fixed;
        top: 14px;
        left: 14px;
        z-index: 99999;
        width: 42px;
        height: 42px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius: 12px;
        border: 1px solid rgba(148,163,184,0.22);
        background: rgba(255,255,255,0.92);
        box-shadow: 0 10px 22px rgba(15,23,42,0.08);
        cursor: pointer;
        user-select: none;
        transition: transform 160ms ease, box-shadow 160ms ease;
    }
    #cl-nav-toggle:hover{ transform: translateY(-1px); box-shadow: 0 14px 28px rgba(15,23,42,0.10); }

    /* Hide/show behavior driven by JS (scroll + manual toggle) */
    body.cl-nav-hidden section[data-testid="stSidebar"]{
        width: 0px !important;
        min-width: 0px !important;
        max-width: 0px !important;
        border-right: none !important;
    }
    body.cl-nav-hidden section[data-testid="stSidebar"] *{
        opacity: 0;
        pointer-events: none;
        transition: opacity 120ms ease;
    }

    /* Typography tightening (subtle) */
    h1,h2,h3{ letter-spacing: -0.015em; }
.stCaption, .stMarkdown small{ color: var(--muted); }

    /* Hero */
    .hero{
        border-radius: var(--r-hero);
        padding: 1.0rem 1.1rem;
        border: 1px solid rgba(14,165,233,0.18);
        background: rgba(255,255,255,0.90);
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
        margin-bottom: 0.8rem;
        animation: fadeUp 220ms ease both;
    }
    .hero-title{ font-size: 1.42rem; font-weight: 820; letter-spacing: -0.02em; margin: 0; }
    .hero-subtitle{ margin-top: 0.20rem; font-size: 0.96rem; color: var(--muted); }
    .hero-badge{
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding: 0.36rem 0.62rem;
        border-radius: 999px;
        border: 1px solid rgba(167,139,250,0.26);
        background: rgba(167,139,250,0.10);
        color: rgba(15,23,42,0.92);
        font-weight: 760;
        font-size: 0.86rem;
        white-space: nowrap;
    }

    /* Cards */
    .card{
        border-radius: var(--r-card);
        padding: var(--space-5);
        border: 1px solid rgba(148,163,184,0.16);
        background: rgba(255,255,255,0.88);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(14px);
        animation: fadeUp 220ms ease both;
    }
    .card:hover{
        border-color: rgba(14,165,233,0.20);
        box-shadow: 0 14px 30px rgba(2,6,23,0.08);
        transform: translateY(-1px);
        transition: 160ms ease;
    }
    .card-strong{ background: rgba(255,255,255,0.94); }

    .divider-soft{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148,163,184,0.22), transparent);
        margin: 0.85rem 0;
    }

    /* Pills / badges */
    .pill-row{ display:flex; gap:0.45rem; flex-wrap:wrap; margin: 0.15rem 0 0.65rem; }
    .pill{
        display:inline-flex;
        align-items:center;
        gap:0.45rem;
        padding: 0.32rem 0.58rem;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.86);
        font-weight: 680;
        font-size: 0.86rem;
        color: rgba(15,23,42,0.92);
    }
    .pill .k{ color: var(--muted); font-weight: 720; }
    .pill.info{ border-color: rgba(14,165,233,0.20); background: rgba(14,165,233,0.06); }
    .pill.good{ border-color: rgba(22,163,74,0.20); background: rgba(22,163,74,0.06); }
    .pill.warn{ border-color: rgba(245,158,11,0.22); background: rgba(245,158,11,0.07); }
    .pill.bad{ border-color: rgba(239,68,68,0.18); background: rgba(239,68,68,0.06); }

    .badge{
        display:inline-flex;
        align-items:center;
        gap:0.35rem;
        padding: 0.28rem 0.50rem;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.86);
        color: rgba(15,23,42,0.90);
        font-size: 0.84rem;
        font-weight: 740;
    }
    .badge-dot{
        width: 8px; height: 8px; border-radius: 999px;
        background: rgba(14,165,233,0.55);
        box-shadow: 0 0 0 3px rgba(14,165,233,0.12);
    }

    /* Callouts */
    .callout{
        border-radius: 12px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.90);
        padding: 0.78rem 0.92rem;
        box-shadow: var(--shadow-soft);
    }
    .callout .t{ font-weight: 820; }
    .callout .b{ color: var(--muted); margin-top: 0.22rem; }
    .callout.info{ border-color: rgba(14,165,233,0.20); background: rgba(14,165,233,0.06); }
    .callout.warn{ border-color: rgba(245,158,11,0.22); background: rgba(245,158,11,0.07); }
    .callout.bad{ border-color: rgba(239,68,68,0.18); background: rgba(239,68,68,0.06); }
    .callout.good{ border-color: rgba(22,163,74,0.20); background: rgba(22,163,74,0.06); }

    /* XP bar */
    .xp-track{
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(148,163,184,0.14);
        overflow: hidden;
        border: 1px solid rgba(148,163,184,0.14);
    }
    .xp-fill{
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(14,165,233,0.75), rgba(167,139,250,0.25));
    }

    /* Stepper */
    .stepper{
        display:flex;
        gap: 0.55rem;
        flex-wrap:wrap;
        margin: 0.05rem 0 0.55rem;
    }
    .step{
        display:inline-flex;
        align-items:center;
        gap: 0.45rem;
        padding: 0.35rem 0.62rem;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.88);
        font-weight: 760;
        font-size: 0.86rem;
        color: rgba(15,23,42,0.92);
    }
    .step .n{
        width: 18px; height: 18px; border-radius: 999px;
        display:inline-flex; align-items:center; justify-content:center;
        font-size: 0.80rem;
        background: rgba(148,163,184,0.14);
        border: 1px solid rgba(148,163,184,0.18);
        color: rgba(15,23,42,0.82);
    }
    .step.active{ border-color: rgba(167,139,250,0.26); background: rgba(167,139,250,0.10); }
    .step.active .n{ border-color: rgba(167,139,250,0.30); background: rgba(167,139,250,0.12); }
    .step.done{ border-color: rgba(22,163,74,0.22); background: rgba(22,163,74,0.06); }
    .step.done .n{ border-color: rgba(22,163,74,0.22); background: rgba(22,163,74,0.10); }

    /* Links */
    .btn-link{
        display:inline-flex;
        align-items:center;
        justify-content:center;
        gap:0.5rem;
        padding: 0.54rem 0.86rem;
        border-radius: var(--r-btn);
        border: 1px solid rgba(14,165,233,0.22);
        background: rgba(255,255,255,0.86);
        color: var(--text);
        text-decoration:none !important;
        font-weight: 650;
    }
    .btn-link:hover{
        border-color: rgba(167,139,250,0.22);
        box-shadow: 0 0 0 3px rgba(167,139,250,0.18), 0 12px 26px rgba(2,6,23,0.10);
        transform: translateY(-1px);
    }

    /* Buttons: glassy but not loud; purple only for highlighted CTAs */
    .main div[data-testid="stButton"] button,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button{
        border-radius: var(--r-btn) !important;
        border: 1px solid rgba(14,165,233,0.20) !important;
        background: linear-gradient(135deg, rgba(14,165,233,0.11), rgba(255,255,255,0.86)) !important;
        color: rgba(15,23,42,0.95) !important;
        font-weight: 670 !important;
    }
    .main div[data-testid="stButton"] button:hover,
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{
        transform: translateY(-1px);
        box-shadow: 0 0 0 3px rgba(167,139,250,0.22), 0 12px 26px rgba(2,6,23,0.10);
    }
    
    /* ---- Crowdlike v1 polish ---- */
    :root{
      --content-max: 1180px;
      --h1: 2.0rem;
      --h2: 1.35rem;
      --h3: 1.10rem;
      --text: 0.98rem;
    }
    .block-container{
      max-width: var(--content-max);
      padding-top: 1.2rem !important;
      padding-bottom: 3.0rem !important;
    }
    /* Typography */
    h1, h2, h3 { letter-spacing: -0.02em; }
    h1{ font-size: var(--h1) !important; }
    h2{ font-size: var(--h2) !important; }
    h3{ font-size: var(--h3) !important; }
    p, li, div { font-size: var(--text); }
    /* Buttons: clearer hierarchy */
    .stButton > button{
      border-radius: var(--r-btn) !important;
      font-weight: 650 !important;
      transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
    }
    .stButton > button:hover{ filter: brightness(1.01); box-shadow: var(--shadow-soft); }
    .stButton > button:active{ transform: translateY(1px); }

    /* --- v1.1.1 spacing pass: reduce button clustering --- */
    /* More vertical air between stacked buttons */
    div[data-testid="stButton"]{ margin: 0.42rem 0 !important; }
    section[data-testid="stSidebar"] div[data-testid="stButton"]{ margin: 0.34rem 0 !important; }

    /* More horizontal air inside columns/button rows */
/* Active nav button: disabled state looks selected */
    .stButton > button:disabled{
      opacity: 1 !important;
      background: rgba(255,255,255,0.55) !important;
      border: 1px solid rgba(99,102,241,0.28) !important;
      box-shadow: 0 10px 24px rgba(99,102,241,0.10) !important;
      color: rgba(15,23,42,0.92) !important;
    }
    /* Tabs: pill style */
    div[data-baseweb="tabs"]{ background: transparent !important; }
    button[data-baseweb="tab"]{
      border-radius: 999px !important;
      padding: 8px 14px !important;
      margin-right: 8px !important;
      border: 1px solid rgba(148,163,184,0.18) !important;
      background: rgba(255,255,255,0.42) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"]{
      background: rgba(255,255,255,0.70) !important;
      border: 1px solid rgba(99,102,241,0.26) !important;
      box-shadow: 0 10px 22px rgba(99,102,241,0.10) !important;
    }
    /* Sidebar polish */
    section[data-testid="stSidebar"]{
      border-right: 1px solid rgba(148,163,184,0.18) !important;
      background: rgba(255,255,255,0.40) !important;
      backdrop-filter: blur(14px);
    }
    /* Reduce visual noise */
    .stCaption { color: var(--muted) !important; }

    /* --- Website layout (official) --- */
    .site-header{
        position: sticky;
        top: 0;
        z-index: 100;
        padding: 16px 14px 10px 14px;
        margin-bottom: 6px;
        background: rgba(255,255,255,0.70);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        box-shadow: var(--shadow-soft);
    }
    .site-logo{
        font-weight: 800;
        letter-spacing: -0.02em;
        font-size: 18px;
        color: rgba(2,6,23,0.92);
    }
    .site-logo span{ margin-left: 6px; }
    .site-tag{
        margin-top: 2px;
        font-size: 12px;
        color: rgba(71,85,105,0.75);
    }
    .site-links{
        margin-top: 12px;
        font-size: 13px;
        color: rgba(71,85,105,0.75);
        text-align: center;
    }
    .site-hero{
        padding: 34px 24px 22px 24px;
        border-radius: 22px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.84);
        box-shadow: var(--shadow-soft);
    }
    .site-kicker{
        font-size: 12px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(100,116,139,0.85);
        margin-bottom: 10px;
    }
    .site-title{
        font-size: 44px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: rgba(2,6,23,0.93);
        margin-bottom: 12px;
    }
    .site-subtitle{
        font-size: 16px;
        line-height: 1.5;
        color: rgba(30,41,59,0.78);
        max-width: 72ch;
    }
    .site-section{
        padding: var(--space-5) var(--space-5);
        border-radius: var(--r-card);
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.82);
        box-shadow: var(--shadow-soft);
        min-height: 140px;
    }
    .site-section-full{ min-height: auto; }
    .site-section-icon{ font-size: 20px; margin-bottom: 10px; }
    .site-section-title{
        font-weight: 800;
        letter-spacing: -0.01em;
        margin-bottom: 6px;
        color: rgba(2,6,23,0.90);
    }
    .site-section-body{
        color: rgba(30,41,59,0.78);
        line-height: 1.5;
        font-size: 14px;
    }
    .site-footer{
        margin-top: 34px;
        padding: 22px 18px;
        border-radius: 22px;
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(255,255,255,0.82);
        box-shadow: var(--shadow-soft);
    }
    .site-footer-grid{
        display: grid;
        grid-template-columns: 1.6fr 1fr 1fr;
        gap: 16px;
    }
    .site-footer-title{ font-weight: 800; margin-bottom: 6px; }
    .site-footer-muted{ color: rgba(71,85,105,0.75); font-size: 13px; line-height: 1.4; }
    .site-footer-links{ color: rgba(71,85,105,0.78); font-size: 13px; }
    .site-footer-bottom{
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(148,163,184,0.16);
        color: rgba(100,116,139,0.70);
        font-size: 12px;
    }

    /* --- Global spacing: reduce clustering --- */
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stButton"]){
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .stButton>button{
        padding: 12px 14px !important;
        border-radius: 14px !important;
    }

/* v{VERSION}: global spacing + web polish */
.block-container { padding-top: 1.25rem !important; padding-bottom: 3.5rem !important; max-width: 1220px; }
div[data-testid="stVerticalBlock"] > div { gap: 0.95rem !important; }
.stButton > button { padding: 0.72rem 0.95rem !important; border-radius: 16px !important; }
.stButton { margin-top: 0.10rem; margin-bottom: 0.35rem; }
.topbar { position: sticky; top: 0; z-index: 999; padding: 0.9rem 1.0rem; margin: -0.5rem -1rem 1.0rem -1rem; backdrop-filter: blur(14px); background: rgba(255,255,255,0.55); border-bottom: 1px solid var(--border); }
.topbar-logo { font-weight: 900; font-size: 1.05rem; letter-spacing: -0.02em; display:flex; gap: .45rem; align-items:center; }
.topbar-logo span { color: rgba(15,23,42,0.95); }
@media (max-width: 900px){
  .block-container { padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
  .topbar { padding: 0.75rem 0.65rem; }
}


/* Baseline rhythm & alignment */
h1{ margin: var(--space-6) 0 var(--space-3) 0; }
h2{ margin: var(--space-6) 0 var(--space-3) 0; }
h3{ margin: var(--space-4) 0 var(--space-2) 0; }
p{ margin: 0 0 var(--space-3) 0; }

.form-card{
    border: 1px solid var(--border);
    border-radius: var(--r-card);
    padding: var(--space-5);
    background: rgba(255,255,255,0.86);
    box-shadow: var(--shadow-soft);
}
.button-stack .stButton{ margin-top: var(--space-2); }
.button-row{ display:flex; gap: var(--space-4); align-items:center; flex-wrap:wrap; }



/* Compact navigation option lists (popovers / menus) */
div[data-testid="stPopover"], div[data-testid="stPopoverBody"], .stPopover {
  --nav-item-y: 0.10rem;
}
div[data-testid="stPopover"] .stButton,
div[data-testid="stPopoverBody"] .stButton,
.stPopover .stButton {
  margin-top: var(--nav-item-y) !important;
  margin-bottom: var(--nav-item-y) !important;
}
div[data-testid="stPopover"] .stButton > button,
div[data-testid="stPopoverBody"] .stButton > button,
.stPopover .stButton > button {
  padding: 0.46rem 0.70rem !important;
  border-radius: 12px !important;
}
div[data-testid="stPopover"] p,
div[data-testid="stPopoverBody"] p,
.stPopover p {
  margin-bottom: 0.35rem !important;
}


/* Grid rails: consistent gaps & snap-to-columns feel */
div[data-testid="stHorizontalBlock"]{ gap: var(--grid-col-gap) !important; align-items: flex-start; }
div[data-testid="stHorizontalBlock"] > div{ min-width: 0; }
div[data-testid="column"]{ padding-left: 0 !important; padding-right: 0 !important; }
div[data-testid="stVerticalBlock"]{ gap: var(--grid-row-gap) !important; }
div[data-testid="stVerticalBlock"] > div{ padding-top: 0 !important; padding-bottom: 0 !important; }

form[data-testid="stForm"], div[data-testid="stForm"]{
    border: 1px solid var(--border);
    border-radius: var(--r-card);
    padding: var(--space-5);
    background: rgba(255,255,255,0.86);
    box-shadow: var(--shadow-soft);
}
div[data-testid="stMetric"], [data-testid="stMetric"]{
    border: 1px solid var(--border);
    border-radius: var(--r-card);
    padding: var(--space-4) !important;
    background: rgba(255,255,255,0.86);
}
div[data-testid="stDataFrame"], div[data-testid="stTable"]{
    border-radius: var(--r-card) !important;
    overflow: hidden !important;
}

/* Tabs + expanders align to the same rails */
div[data-testid="stTabs"]{ margin-top: var(--space-3) !important; }
div[data-testid="stTabs"] [data-baseweb="tab-list"]{ gap: var(--space-3) !important; }
div[data-testid="stExpander"]{ border-radius: var(--r-card) !important; overflow:hidden; }
div[data-testid="stExpander"] details{ border-radius: var(--r-card) !important; }


    /* --- Arc-main shell integration --- */
    /* Hide Streamlit's native sidebar; we render the arc-main sidebar as a fixed HTML component */
    section[data-testid="stSidebar"]{ display: none !important; }

    /* Reserve space for the fixed arc-main sidebar */
    section.main{ margin-left: 280px !important; }

    /* Keep content comfortably aligned next to the sidebar */
    .main .block-container{
        max-width: calc(var(--content-max) + 280px) !important;
    }

</style>
    

"""
    st.markdown(css, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", badge: str | None = None) -> None:
    """Top hero banner used across pages."""
    badge_html = f'<div class="hero-badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="hero">
          <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:12px;">
            <div>
              <div class="hero-title">{title}</div>
              <div class="hero-subtitle">{subtitle}</div>
            </div>
            {badge_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def soft_divider() -> None:
    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)


def xp_bar(pct: float, left: str, right: str) -> None:
    pct = max(0.0, min(1.0, float(pct or 0.0)))
    st.markdown(
        f"""
        <div style="margin-top:0.15rem; margin-bottom:0.1rem;">
          <div class="xp-track"><div class="xp-fill" style="width:{pct*100:.1f}%"></div></div>
          <div style="display:flex; justify-content:space-between; color: var(--muted); font-size: 0.85rem; margin-top: 0.32rem;">
            <span>{left}</span><span>{right}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def link_button(label: str, url: str) -> None:
    st.markdown(
        f'<a class="btn-link" href="{url}" target="_blank" rel="noopener noreferrer">{label} ↗</a>',
        unsafe_allow_html=True,
    )


def pills(items: list[tuple[str, str, str]]) -> None:
    """Render a compact row of pills: [(key, value, kind)]. kind in info|good|warn|bad."""
    html = ['<div class="pill-row">']
    for k, v, kind in items:
        kind = kind if kind in ("info", "good", "warn", "bad") else "info"
        html.append(f'<div class="pill {kind}"><span class="k">{k}</span><span>{v}</span></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def status_bar(
    *,
    wallet_set: bool,
    demo_mode: bool,
    crowd_score: float | None = None,
    network_label: str = "Arc testnet",
) -> None:
    """Small status strip to reduce confusion during demos."""
    crowd_score = float(crowd_score) if crowd_score is not None else None
    items: list[tuple[str, str, str]] = []
    items.append(("Network", network_label, "info"))
    items.append(("Demo", "ON" if demo_mode else "OFF", "good" if demo_mode else "warn"))
    items.append(("Wallet", "Connected" if wallet_set else "Missing", "good" if wallet_set else "bad"))
    if crowd_score is not None:
        kind = "good" if crowd_score >= 70 else ("warn" if crowd_score < 40 else "info")
        items.append(("Crowd", f"{crowd_score:.0f}", kind))
    pills(items)


def callout(
    *args,
    tone: str | None = None,
    kind: str | None = None,
    title: str | None = None,
    body: str | None = None,
) -> None:
    """Render a small callout card.

    Backwards compatible with the original signature:
        callout(kind, title, body)

    And supports a simpler signature used by newer pages:
        callout(message, tone="muted"|"warning"|"success"|...)
    """

    import html as _html
    import re as _re

    def _fmt(text: str) -> str:
        """Safely format lightweight markdown (**bold**) + newlines inside HTML."""
        s = _html.escape(str(text or ""))
        s = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = s.replace("\n", "<br/>")
        return s

    # --- Parse args ---
    if len(args) == 3:
        kind_, title_, body_ = args
        kind_ = str(kind_)
        title_ = _fmt(title_)
        body_ = _fmt(body_)
    elif len(args) == 1:
        # message-only mode
        msg = str(args[0])
        title_ = _fmt(title or "")
        body_ = _fmt(body or msg)
        # Map tone -> kind (CSS classes)
        tone_norm = str(tone or kind or "info").strip().lower()
        tone_map = {
            "muted": "info",
            "info": "info",
            "warning": "warn",
            "warn": "warn",
            "success": "good",
            "good": "good",
            "danger": "bad",
            "error": "bad",
            "bad": "bad",
        }
        kind_ = tone_map.get(tone_norm, "info")
    else:
        # Fallback: allow keyword-only usage
        title_ = _fmt(title or "")
        body_ = _fmt(body or "")
        kind_ = str(kind or "info")

    kind_ = kind_ if kind_ in ("info", "good", "warn", "bad") else "info"
    title_html = f'<div class="t">{title_}</div>' if title_ else ""
    st.markdown(
        f'<div class="callout {kind_}">{title_html}<div class="b">{body_}</div></div>',
        unsafe_allow_html=True,
    )


def stepper(current: int, labels: list[str]) -> None:
    """Visual stepper (display-only). Use alongside radio/flow state."""
    current = int(current or 1)
    html = ['<div class="stepper">']
    for i, lab in enumerate(labels, start=1):
        cls = "step"
        if i < current:
            cls += " done"
        elif i == current:
            cls += " active"
        html.append(f'<div class="{cls}"><span class="n">{i}</span><span>{lab}</span></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def toast(msg: str, kind: str = "info") -> None:
    """Nice feedback without breaking older Streamlit versions."""
    try:
        # Newer Streamlit
        st.toast(msg, icon="✅" if kind == "good" else "⚠️" if kind == "warn" else "ℹ️")
        return
    except Exception:
        pass
    if kind == "good":
        st.success(msg)
    elif kind == "warn":
        st.warning(msg)
    elif kind == "bad":
        st.error(msg)
    else:
        st.info(msg)


def copy_to_clipboard(text: str, key: str, label: str = "Copy") -> None:
    """Small inline copy-to-clipboard button (uses browser clipboard API)."""
    # Use JSON encoding so newlines/quotes/backticks can't break the JS string.
    import json as _json  # local import to keep ui.py lightweight

    payload = _json.dumps(text or "")

    html = f"""
    <div style="display:flex; gap:10px; align-items:center; margin-top: 0.35rem;">
      <button id="btn_{key}" style="
        cursor:pointer; padding: 8px 12px; border-radius: 12px;
        border: 1px solid rgba(14,165,233,0.22);
        background: rgba(255,255,255,0.86);
        font-weight: 700;
      ">{label}</button>
      <span id="msg_{key}" style="color: rgba(100,116,139,0.95); font-size: 0.88rem;"></span>
    </div>
    <script>
      const payload = {payload};
      const btn = document.getElementById("btn_{key}");
      const msg = document.getElementById("msg_{key}");
      btn.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(payload);
          msg.textContent = "Copied ✓";
          setTimeout(() => msg.textContent = "", 1200);
        }} catch (e) {{
          msg.textContent = "Copy failed (browser blocked)";
          setTimeout(() => msg.textContent = "", 1600);
        }}
      }});
    </script>
    """
    components.html(html, height=46)


def metric_card(title: str, value: str, caption: str = "", *, accent: str = "blue") -> None:
    accents = {
        "blue": "rgba(14,165,233,0.18)",
        "purple": "rgba(167,139,250,0.22)",
        "none": "rgba(148,163,184,0.16)",
    }
    border = accents.get(accent, accents["blue"])
    cap_html = f'<div style="color:var(--muted);font-size:0.9rem">{caption}</div>' if caption else ""
    st.markdown(
        '<div class="card card-strong" style="border:1px solid ' + border + '; background: rgba(255,255,255,0.94);">'
        f'<div style="font-weight:780">{title}</div>'
        f'<div style="font-size:1.45rem;font-weight:900;margin-top:4px">{value}</div>'
        f'{cap_html}'
        '</div>',
        unsafe_allow_html=True,
    )


def button_style(key: str, variant: str) -> None:
    """
    Style ONE Streamlit button by key using #st-key-<key>.
    Keep palette aligned with 60/30/10 (white/blue/purple).
    """
    palette = {
        # Neutral / nav
        "white": ("rgba(255,255,255,0.92)", "rgba(255,255,255,0.92)", "rgba(148,163,184,0.18)"),
        "ghost": ("rgba(255,255,255,0.00)", "rgba(255,255,255,0.86)", "rgba(148,163,184,0.12)"),
        # Primary
        "blue": ("rgba(14,165,233,0.16)", "rgba(255,255,255,0.86)", "rgba(14,165,233,0.28)"),
        # Accent (use sparingly)
        "purple": ("rgba(167,139,250,0.14)", "rgba(255,255,255,0.86)", "rgba(167,139,250,0.28)"),
        # Subtle flavors (still within palette)
        "teal": ("rgba(14,165,233,0.10)", "rgba(255,255,255,0.92)", "rgba(14,165,233,0.22)"),
        "slate": ("rgba(148,163,184,0.12)", "rgba(255,255,255,0.92)", "rgba(148,163,184,0.22)"),
        "rose": ("rgba(167,139,250,0.10)", "rgba(255,255,255,0.92)", "rgba(167,139,250,0.22)"),
        "active": ("rgba(167,139,250,0.16)", "rgba(255,255,255,0.90)", "rgba(167,139,250,0.32)"),
    }
    a, b, border = palette.get(variant, palette["blue"])
    st.markdown(
        f"""
        <style>
        #st-key-{key} button {{
            border: 1px solid {border} !important;
            background: linear-gradient(135deg, {a}, {b}) !important;
        }}
        #st-key-{key} button:hover {{
            box-shadow: 0 0 0 3px rgba(167,139,250,0.22), 0 12px 26px rgba(2,6,23,0.10) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def nav(active: str = "home") -> None:
    """Render the global top navigation exactly once per Streamlit script run.

    In Streamlit's multipage execution model, the main script and a page script can
    both execute in the same run, which can lead to duplicate widgets (duplicate keys).
    We guard using the current script_run_id when available.
    """
    a = (active or "home").strip().lower()

    # normalize common aliases
    a = {
        "launch app": "dashboard",
        "leaderboards": "compare",
        "leaderboard": "compare",
    }.get(a, a)

    # Per-run guard to avoid duplicate navbar rendering
    run_id = None
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
        ctx = get_script_run_ctx()
        run_id = getattr(ctx, "script_run_id", None) or getattr(ctx, "run_id", None)
    except Exception:
        run_id = None

    if run_id is not None:
        if st.session_state.get("_crowdlike_nav_last_run_id") == run_id:
            return
        st.session_state["_crowdlike_nav_last_run_id"] = run_id

    from crowdlike.navbar import render_navbar as _render_navbar
    _render_navbar(active=a)


def bg_ratio() -> dict:
    return dict(_BG_RATIO)


def event_feed(events: list[dict], title: str = "Recent activity", *, compact: bool = True) -> None:
    """Render an event timeline (newest first)."""
    if title:
        st.markdown(f"### {title}")
    if not events:
        st.caption("No activity yet. Make a trade, run the coach, or verify a receipt.")
        return

    icon_for = {
        "trade": "📈",
        "payment": "💸",
        "receipt": "🧾",
        "quest": "🧩",
        "social": "❤️",
        "agent": "🧠",
        "safety": "🛡️",
        "system": "⚙️",
        "event": "🫧",
    }
    sev_border = {
        "info": "rgba(148,163,184,0.18)",
        "success": "rgba(34,197,94,0.22)",
        "warn": "rgba(245,158,11,0.22)",
        "danger": "rgba(239,68,68,0.22)",
    }

    for e in events[:60]:
        kind = str(e.get("kind") or "event")
        icon = icon_for.get(kind, "🫧")
        sev = str(e.get("severity") or "info")
        border = sev_border.get(sev, sev_border["info"])
        title_line = str(e.get("title") or "")
        details = str(e.get("details") or "")
        ts = str(e.get("ts") or "")
        st.markdown(
            f'''
<div class="card" style="border:1px solid {border}; padding: 10px 12px; margin-bottom: 10px;">
  <div style="display:flex; gap:10px; align-items:flex-start;">
    <div style="font-size:1.2rem; line-height:1.2">{icon}</div>
    <div style="flex:1">
      <div style="font-weight:800">{title_line}</div>
      <div style="color:var(--muted); font-size:0.92rem; margin-top:2px">{details}</div>
      <div style="color:var(--muted); font-size:0.78rem; margin-top:6px">{ts}</div>
    </div>
  </div>
</div>
''',
            unsafe_allow_html=True,
        )