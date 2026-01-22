cd /c/Users/mange/Downloads/ARC

# sanity: must be a git repo
test -d .git || { echo "NOT A GIT REPO: re-clone ARC first"; exit 1; }

# overwrite the JS file
mkdir -p assets
cat > assets/interactivity.js <<'JS'
/* CROWDLIKE_INTERACTIVITY_V2 */
(function () {
  "use strict";

  const STORE = "crowdlike_state_v2";

  function $(id) { return document.getElementById(id); }

  function safeJSONParse(s, fallback) {
    try { return JSON.parse(s); } catch { return fallback; }
  }

  function loadState() {
    return safeJSONParse(localStorage.getItem(STORE) || "{}", {});
  }

  function saveState(patch) {
    const cur = loadState();
    localStorage.setItem(STORE, JSON.stringify({ ...cur, ...patch }));
  }

  function toast(msg) {
    let wrap = document.getElementById("toast-wrap");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.id = "toast-wrap";
      wrap.style.position = "fixed";
      wrap.style.right = "16px";
      wrap.style.bottom = "16px";
      wrap.style.zIndex = "999999";
      wrap.style.display = "flex";
      wrap.style.flexDirection = "column";
      wrap.style.gap = "8px";
      document.body.appendChild(wrap);
    }

    const t = document.createElement("div");
    t.textContent = msg;
    t.style.background = "rgba(17, 24, 39, 0.92)";
    t.style.color = "white";
    t.style.padding = "10px 12px";
    t.style.borderRadius = "12px";
    t.style.fontSize = "13px";
    t.style.boxShadow = "0 10px 20px rgba(0,0,0,0.25)";
    t.style.maxWidth = "320px";
    t.style.lineHeight = "1.25";
    wrap.appendChild(t);

    setTimeout(() => t.remove(), 1800);
  }

  function fireConfetti() {
    if (typeof window.confetti !== "function") return;
    try {
      window.confetti({
        particleCount: 70,
        spread: 65,
        origin: { y: 0.7 },
      });
    } catch {}
  }

  function getPagesFromDOM() {
    const sections = Array.from(document.querySelectorAll('section[id^="page-"]'));
    return sections.map((sec) => {
      const id = sec.id.replace(/^page-/, "");
      const h = sec.querySelector("h1,h2,h3");
      const label = (h && h.textContent && h.textContent.trim()) ? h.textContent.trim() : id;
      return { id, label };
    });
  }

  function showPage(pageId) {
    const sections = Array.from(document.querySelectorAll('section[id^="page-"]'));
    sections.forEach((s) => s.classList.add("hidden"));
    const target = document.getElementById("page-" + pageId);
    if (target) target.classList.remove("hidden");
    saveState({ page: pageId });

    document.querySelectorAll("[data-nav-page]").forEach((btn) => {
      const isActive = btn.getAttribute("data-nav-page") === pageId;
      btn.classList.toggle("bg-purple-100", isActive);
      btn.classList.toggle("text-purple-700", isActive);
    });
  }

  function buildNav() {
    const nav = $("nav");
    if (!nav) return;

    const pages = getPagesFromDOM();
    nav.innerHTML = "";

    pages.forEach((p) => {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("data-nav-page", p.id);
      b.className =
        "w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors";
      b.textContent = p.label;
      b.addEventListener("click", () => showPage(p.id));
      nav.appendChild(b);
    });

    if (window.lucide && typeof window.lucide.createIcons === "function") {
      try { window.lucide.createIcons(); } catch {}
    }
  }

  function bindSearch() {
    const input = $("search");
    const clearBtn = $("clear-search");
    const nav = $("nav");
    if (!input || !nav) return;

    function applyFilter() {
      const q = (input.value || "").trim().toLowerCase();
      if (clearBtn) clearBtn.classList.toggle("hidden", q.length === 0);

      nav.querySelectorAll("[data-nav-page]").forEach((btn) => {
        const txt = (btn.textContent || "").toLowerCase();
        btn.style.display = (!q || txt.includes(q)) ? "" : "none";
      });
    }

    input.addEventListener("input", applyFilter);
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        input.value = "";
        applyFilter();
        input.focus();
      });
    }
  }

  function bindGlobalClicks() {
    document.addEventListener("click", (e) => {
      const el = e.target && e.target.closest ? e.target.closest("button, a, [role='button']") : null;
      if (!el) return;
      if (el.hasAttribute("data-nav-page")) return;

      const label = (el.textContent || "").trim().slice(0, 60);
      if (label) toast(label);

      if (el.getAttribute("data-confetti") === "true") fireConfetti();
    }, true);
  }

  function boot() {
    buildNav();
    bindSearch();
    bindGlobalClicks();

    const st = loadState();
    const pages = getPagesFromDOM();
    const fallback = (pages[0] && pages[0].id) ? pages[0].id : "home";
    showPage(st.page || fallback);

    try { console.log("CROWDLIKE_INTERACTIVITY_V2: loaded"); } catch {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
JS

git add assets/interactivity.js
git commit -m "Fix interactivity script crash (boot) + enable page nav & click feedback"
git push
