import streamlit as st
import streamlit.components.v1 as components

CLARITY_PROJECT_ID = "v2ghymedzy"

st.set_page_config(page_title="Crowdlike", layout="wide")


# --- CL_PAGE_ROUTER_START ---
# Route ARC-main HTML navigation (?cl_page=...) into Streamlit multipage.
# Must execute BEFORE we render the big HTML UI.
from pathlib import Path

def _cl_get_param(key: str):
    try:
        # Streamlit modern API (returns last value for dict-like access)
        return st.query_params.get(key)
    except Exception:
        # Back-compat
        params = st.experimental_get_query_params()
        vals = params.get(key, [])
        return vals[-1] if vals else None

cl_page = _cl_get_param("cl_page")
if cl_page:
    key = str(cl_page).strip().lower()

    # Normalize common variants
    aliases = {
        "home": "dashboard",
        "dash": "dashboard",
        "leaderboard": "leaderboards",
        "leaders": "leaderboards",
    }
    key = aliases.get(key, key)

    # Explicit mapping for ARC-main nav labels
    page_map = {
        "dashboard": "pages/dashboard.py",
        "agents": "pages/agents.py",
        "market": "pages/market.py",
        "analytics": "pages/analytics.py",
        "leaderboards": "pages/social.py",   # ARC-main "Leaderboards" -> Social page
        "chat": "pages/chat.py",
        "profile": "pages/profile.py",
        # Add more if your HTML nav includes them:
        "safety": "pages/safety.py",
        "quests": "pages/quests.py",
        "shop": "pages/shop.py",
        "journey": "pages/journey.py",
        "coach": "pages/coach.py",
        "compare": "pages/compare.py",
        "pricing": "pages/pricing.py",
        "admin": "pages/admin.py",
    }

    target = page_map.get(key)

    # Fallback: if pages/<key>.py exists, route there automatically
    if target is None:
        candidate = Path("pages") / f"{key}.py"
        if candidate.exists():
            target = str(candidate)

    if target:
        # Clear query params on switch to avoid getting "stuck" redirecting on refresh
        st.switch_page(target, query_params={})
        st.stop()
# --- CL_PAGE_ROUTER_END ---

# --- ARC-main router: allow the custom sidebar to route into Streamlit pages ---
def _get_query_param(name: str) -> str | None:
    try:
        # Streamlit >= 1.30
        v = st.query_params.get(name)
        if isinstance(v, list):
            return v[0] if v else None
        return v
    except Exception:
        qp = st.experimental_get_query_params()
        v = qp.get(name)
        if isinstance(v, list):
            return v[0] if v else None
        return v

try:
    from crowdlike.registry import all_pages
except Exception:
    all_pages = None  # type: ignore

def _route_if_requested() -> None:
    page_id = (_get_query_param("cl_page") or "").strip().lower()
    if not page_id or page_id == "home":
        return
    if not all_pages:
        return
    # Route without assuming login state.
    for p in all_pages("human"):
        if p.id == page_id:
            # For pages/, Streamlit expects the file path.
            if p.path and p.path != "app.py":
                try:
                    st.switch_page(p.path)
                except Exception:
                    # If switch_page is unavailable, fall back to showing home.
                    pass
            return

_route_if_requested()

def inject_clarity(project_id: str) -> None:
    # Best-effort injection for Microsoft Clarity.
    # 1) Inject into the Streamlit top window (outside the component iframe) using window.parent.
    # 2) Also load in the component iframe via the HTML <head>
    try:
        components.html(
            f"""
            <script type="text/javascript">
            (function(){{
                try {{
                    # Avoid double inject
                    if (window.parent and window.parent.__clarityLoaded) return;
                    if (window.parent) window.parent.__clarityLoaded = true;

                    (function(c,l,a,r,i,t,y){{
                        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
                        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
                    }})(window.parent, window.parent.document, "clarity", "script", "{project_id}");
                }} catch (e) {{
                    console.log("Clarity inject failed:", e);
                }}
            }})();
            </script>
            """,
            height=0,
            width=0,
        )
    except Exception:
        # Best-effort; do not fail app startup if components is unavailable
        pass

# Call once per browser session
if "clarity_loaded" not in st.session_state:
    inject_clarity(CLARITY_PROJECT_ID)
    st.session_state.clarity_loaded = True

# Hide Streamlit chrome as much as possible.
st.markdown(
    """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 0rem; padding-bottom: 0rem;}
</style>
""",
    unsafe_allow_html=True,
)
# --- CL_NAV_ITEMS_START ---
# Build sidebar nav from ALL Streamlit pages/ files so it never goes empty.
import json as _json
from pathlib import Path as _Path

def _cl_build_nav_items():
    pages_dir = _Path(__file__).parent / "pages"
    items = []
    if pages_dir.exists():
        for fp in pages_dir.glob("*.py"):
            name = fp.stem
            if name.startswith("_"):
                continue
            label = name.replace("_", " ").title()
            items.append({"id": name, "label": label})

    # Prefer a stable, human-friendly order for common pages; append the rest.
    preferred = [
        "dashboard","agents","market","analytics","journey","coach","compare",
        "quests","shop","social","chat","profile","pricing","safety","admin"
    ]
    order = {k:i for i,k in enumerate(preferred)}
    items.sort(key=lambda x: (order.get(x["id"], 999), x["label"]))
    return items

CL_NAV_ITEMS = _cl_build_nav_items()
CL_NAV_ITEMS_JSON = _json.dumps(CL_NAV_ITEMS)
# --- CL_NAV_ITEMS_END ---


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Crowdlike</title>

  <!-- Microsoft Clarity (iframe scope) -->
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "v2ghymedzy");
  </script>

  <!-- Tailwind (CDN) so the original classNames render without modification -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Lucide icons (CDN) -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    html, body { height: 100%; margin: 0; }
    body { overflow: hidden; }
    #app-root { height: 100vh; width: 100vw; overflow: auto; }
    #app-root { scroll-behavior: smooth; }
    .sidebar-z { z-index: 50; }
    input[type=range] { accent-color: #8B5CF6; }
  </style>
</head>

<body>
  <div id="app-root" class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">

    <!-- Sidebar -->
    <aside id="sidebar" class="fixed left-0 top-0 h-screen w-72 bg-white/95 backdrop-blur-sm border-r border-gray-200 shadow-lg transition-transform duration-300 ease-in-out sidebar-z translate-x-0">
      <div class="flex flex-col h-full">

        <!-- Header -->
        <div class="p-6 border-b border-gray-200">
          <div class="flex items-center justify-between mb-4">
            <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Crowdlike</h1>
            <span class="text-xs text-gray-500">v1.7.0</span>
          </div>

          <!-- Search -->
          <div class="relative">
            <i data-lucide="search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"></i>
            <input
              id="search"
              type="text"
              value=""
              placeholder="Search pages..."
              class="w-full pl-10 pr-10 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button id="clear-search" class="hidden absolute right-3 top-1/2 -translate-y-1/2" aria-label="Clear search">
              <i data-lucide="x" class="w-4 h-4 text-gray-400 hover:text-gray-600"></i>
            </button>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav id="nav" class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <!-- CL_NAV_AUTOGEN_START -->
          <!-- CL_NAV_AUTOGEN_END -->
        </nav>

        <!-- Footer -->
        <div class="p-4 border-t border-gray-200 text-xs text-gray-500">
          <p>Hover left edge to show</p>
          <p>Move right to hide</p>
          <p>Scroll down to hide</p>
        </div>

      </div>
    </aside>

    <!-- Main content -->
    <main id="main" class="transition-all duration-300 ease-in-out" style="margin-left: 280px;">
      <div class="max-w-7xl mx-auto px-6 py-8">
        <!-- Home & pages content omitted for brevity in this template -->
        <section id="page-home" class="space-y-8">
          <div class="text-center py-12">
            <h1 class="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Welcome to Crowdlike
            </h1>
            <p class="text-xl text-gray-600 mb-8">
              A personal finance app where AI agents trade and compare performance
            </p>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    // Client-side nav hardener and fallback: populate #nav from server-provided window.__CL_NAV_ITEMS
    (function () {
      try {
        // Replace placeholder with server-provided JSON via a safe var injection below:
        window.__CL_NAV_ITEMS = __CL_NAV_ITEMS__PLACEHOLDER__;
        const items = Array.isArray(window.__CL_NAV_ITEMS) ? window.__CL_NAV_ITEMS : [];

        const nav = document.getElementById('nav');
        if (nav && items.length && nav.children.length === 0) {
          const cur = new URL(window.location.href).searchParams.get('cl_page') || '';
          nav.innerHTML = items.map(it => {
            const active = (it.id === cur);
            const base = "group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors";
            const cls = active
              ? base + " bg-gray-100 text-gray-900"
              : base + " text-gray-700 hover:bg-gray-100 hover:text-gray-900";
            const href = `?cl_page=${encodeURIComponent(it.id)}`;
            return `<a href="${href}" data-cl-page="${it.id}" class="${cls}"><span class="truncate">${it.label}</span></a>`;
          }).join("");
        }
      } catch (e) {
        // Fail silently — sidebar will still function for pages that render their own nav.
        console.warn("Nav hardener failed:", e);
      }
    })();
  </script>

</body>
</html>""";