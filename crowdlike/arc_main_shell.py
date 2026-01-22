from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

from crowdlike.registry import all_pages, Page
from crowdlike.version import VERSION

def _group_pages(pages: List[Page]) -> List[Tuple[str, List[Page]]]:
    grouped: Dict[str, List[Page]] = defaultdict(list)
    for p in pages:
        grouped[p.group].append(p)

    preferred = ["Website", "App", "Engagement", "Controls", "Settings", "More"]
    out: List[Tuple[str, List[Page]]] = []
    for g in preferred:
        if g in grouped:
            out.append((g, sorted(grouped[g], key=lambda x: (x.order, x.label))))
    for g in sorted([k for k in grouped.keys() if k not in {x[0] for x in out}]):
        out.append((g, sorted(grouped[g], key=lambda x: (x.order, x.label))))
    return out

def render_arc_main_shell(
    user: Optional[Dict[str, Any]] = None,
    *,
    active_page: str = "home",
) -> None:
    """Render the ARC-main sidebar as a fixed, Tailwind-based HTML shell.

    Strategy:
    - Hide Streamlit's native sidebar (handled in apply_ui()).
    - Render a fixed-position sidebar via components.html (iframe) and reserve
      space for it via CSS (apply_ui()).
    - Navigation triggers a full-page reload to the root script with ?cl_page=<id>,
      and app.py routes via st.switch_page().
    """
    a = (active_page or "home").strip().lower()
    a = {"launch app": "dashboard", "leaderboard": "compare", "leaderboards": "compare"}.get(a, a)

    role = "human"
    if isinstance(user, dict):
        role = str(user.get("role") or "human").lower()

    pages = all_pages(role)
    groups = _group_pages(pages)

    nav_model: List[Dict[str, Any]] = []
    for g, items in groups:
        nav_model.append(
            {
                "group": g,
                "items": [
                    {
                        "id": p.id,
                        "label": p.label,
                        "icon": p.icon,
                    }
                    for p in items
                ],
            }
        )

    payload = json.dumps(
        {"active": a, "version": VERSION, "groups": nav_model},
        ensure_ascii=False,
    )

    # NOTE: This component is intentionally self-contained (no external JS build step).
    # It uses Tailwind + Lucide via CDN like ARC-main's current UI. If running in an
    # offline environment, replace CDN usage with local assets.
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
      html, body {{
        margin: 0; padding: 0;
        background: transparent;
        overflow: hidden;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      }}
      /* Make the Streamlit component iframe act like a fixed sidebar */
      body {{ width: 280px; height: 920px; }}  
      .muted {{ color: rgba(100,116,139,0.95); }}
      .group-title {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }}
      .nav-item.active {{
        background: rgba(167,139,250,0.12);
        border: 1px solid rgba(167,139,250,0.28);
      }}
      .nav-item {{
        border: 1px solid rgba(148,163,184,0.12);
      }}
      .nav-item:hover {{
        box-shadow: 0 10px 22px rgba(2,6,23,0.10);
      }}
    </style>
  </head>
  <body>
    <div class="h-screen w-[280px] bg-white/80 backdrop-blur-xl border-r border-slate-200/70">
      <div class="px-4 py-4 border-b border-slate-200/70">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-2xl bg-gradient-to-br from-sky-400/30 to-violet-400/25 flex items-center justify-center shadow-sm border border-slate-200/70">
            🫧
          </div>
          <div>
            <div class="font-extrabold tracking-tight text-slate-900">Crowdlike</div>
            <div class="text-xs muted -mt-[2px]">ARC Main · v<span id="ver"></span></div>
          </div>
        </div>

        <div class="mt-3">
          <div class="relative">
            <input id="q" class="w-full rounded-xl px-3 py-2 text-sm bg-white/70 border border-slate-200/70 outline-none focus:ring-2 focus:ring-violet-200"
              placeholder="Search..." />
            <div class="absolute right-3 top-2.5 muted">
              <i data-lucide="search" class="w-4 h-4"></i>
            </div>
          </div>
        </div>
      </div>

      <div id="nav" class="h-[calc(100vh-92px)] overflow-y-auto px-3 py-3 space-y-4"></div>

      <div class="px-4 py-3 border-t border-slate-200/70 text-xs muted">
        Tip: hover left edge to reveal · scroll to hide
      </div>
    </div>

    <script>
      (function() {{
        // Fix the iframe itself (Streamlit wraps this HTML in an iframe).
        try {{
          const f = window.frameElement;
          if (f) {{
            f.style.position = "fixed";
            f.style.top = "0";
            f.style.left = "0";
            f.style.width = "280px";
            f.style.height = "100vh";
            f.style.zIndex = "99999";
            f.style.border = "none";
            f.style.background = "transparent";
          }}
        }} catch(e) {{}}

        const model = {payload};
        document.getElementById("ver").textContent = model.version;

        function navTo(pageId) {{
          try {{
            const u = new URL(window.parent.location.href);
            u.pathname = "/";
            u.searchParams.set("cl_page", pageId);
            window.parent.location.href = u.toString();
          }} catch(e) {{
            window.parent.location.search = "?cl_page=" + encodeURIComponent(pageId);
          }}
        }}

        function render(filter) {{
          const root = document.getElementById("nav");
          root.innerHTML = "";
          const q = (filter || "").trim().toLowerCase();

          model.groups.forEach(g => {{
            const groupEl = document.createElement("div");
            const title = document.createElement("div");
            title.className = "group-title muted px-2";
            title.textContent = g.group;
            groupEl.appendChild(title);

            const list = document.createElement("div");
            list.className = "mt-2 space-y-2";
            let any = false;

            g.items.forEach(it => {{
              const hay = (it.label + " " + it.id).toLowerCase();
              if (q && !hay.includes(q)) return;

              any = true;
              const btn = document.createElement("button");
              btn.className = "nav-item w-full text-left rounded-2xl px-3 py-2 bg-white/70 flex items-center gap-2 text-sm text-slate-900";
              if (it.id === model.active) btn.classList.add("active");

              const ico = document.createElement("span");
              ico.className = "w-6 h-6 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-center text-base";
              ico.textContent = (it.icon || "•").trim();

              const label = document.createElement("span");
              label.className = "font-semibold";
              label.textContent = it.label;

              btn.appendChild(ico);
              btn.appendChild(label);
              btn.addEventListener("click", () => navTo(it.id));
              list.appendChild(btn);
            }});

            if (any) {{
              groupEl.appendChild(list);
              root.appendChild(groupEl);
            }}
          }});

          try {{
            lucide.createIcons();
          }} catch(e) {{}}
        }}

        const q = document.getElementById("q");
        q.addEventListener("input", () => render(q.value));
        render("");

        // Hide/show on scroll (ARC-main feel): hide when scrolling down, show when scrolling up.
        let lastY = 0;
        const threshold = 18;
        function getScrollEl() {{
          return window.parent.document.querySelector("section.main") || window.parent.document.scrollingElement || window.parent.window;
        }}
        const scrollEl = getScrollEl();

        function getY() {{
          try {{
            if (scrollEl === window.parent.window) return window.parent.window.scrollY || 0;
            return scrollEl.scrollTop || 0;
          }} catch(e) {{
            return 0;
          }}
        }}

        function onScroll() {{
          const y = getY();
          const dy = y - lastY;
          try {{
            const f = window.frameElement;
            if (!f) return;
            if (dy > threshold) {{
              f.style.transform = "translateX(-260px)";
              lastY = y;
            }} else if (dy < -threshold) {{
              f.style.transform = "translateX(0px)";
              lastY = y;
            }}
          }} catch(e) {{}}
        }}

        try {{
          if (scrollEl && scrollEl.addEventListener) {{
            scrollEl.addEventListener("scroll", onScroll, {{passive:true}});
          }} else {{
            window.parent.window.addEventListener("scroll", onScroll, {{passive:true}});
          }}
        }} catch(e) {{}}

        // Hover left edge to reveal
        try {{
          const parentDoc = window.parent.document;
          let edge = parentDoc.getElementById("cl-edge-reveal");
          if (!edge) {{
            edge = parentDoc.createElement("div");
            edge.id = "cl-edge-reveal";
            edge.style.position = "fixed";
            edge.style.top = "0";
            edge.style.left = "0";
            edge.style.width = "10px";
            edge.style.height = "100vh";
            edge.style.zIndex = "99998";
            edge.style.background = "transparent";
            parentDoc.body.appendChild(edge);
          }}
          edge.addEventListener("mouseenter", () => {{
            const f = window.frameElement;
            if (f) f.style.transform = "translateX(0px)";
          }});
        }} catch(e) {{}}
      }})();
    </script>
  </body>
</html>
""";
    # Height is overridden by the script (fixed 100vh) but some environments need a non-zero initial height.
    components.html(html, height=920, scrolling=False)