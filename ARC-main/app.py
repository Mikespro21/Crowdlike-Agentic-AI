
import streamlit as st
import streamlit.components.v1 as components

CLARITY_PROJECT_ID = "v2ghymedzy"

st.set_page_config(page_title="Crowdlike", layout="wide")

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
    # 2) Also load in the component iframe via the HTML <head> (see below).
    components.html(
        f"""
        <script type="text/javascript">
        (function(){{
            try {{
                // Avoid double inject
                if (window.parent && window.parent.__clarityLoaded) return;
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
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
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
          <!-- Buttons injected by JS to preserve one source of truth for pages -->
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

        <!-- HOME -->
        <section id="page-home" class="space-y-8">
          <div class="text-center py-12">
            <h1 class="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Welcome to Crowdlike
            </h1>
            <p class="text-xl text-gray-600 mb-8">
              A personal finance app where AI agents trade and compare performance
            </p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div class="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
                <div class="text-4xl mb-4">🤖</div>
                <h3 class="text-lg font-bold mb-2">AI Agents</h3>
                <p class="text-gray-600">Create and manage multiple AI trading agents with different strategies</p>
              </div>
              <div class="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
                <div class="text-4xl mb-4">📊</div>
                <h3 class="text-lg font-bold mb-2">Real Market Data</h3>
                <p class="text-gray-600">Paper trading with real-time market data from CoinGecko</p>
              </div>
              <div class="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow">
                <div class="text-4xl mb-4">🏆</div>
                <h3 class="text-lg font-bold mb-2">Leaderboards</h3>
                <p class="text-gray-600">Compare agent performance across daily, weekly, and monthly timeframes</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-8">
            <h2 class="text-2xl font-bold mb-4">Getting Started</h2>
            <ol class="space-y-4 text-gray-700">
              <li class="flex items-start gap-3">
                <span class="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">1</span>
                <div>
                  <strong>Create Your First Agent</strong>
                  <p class="text-gray-600">Navigate to the Agents page and set up your AI trading agent</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <span class="flex-shrink-0 w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold">2</span>
                <div>
                  <strong>Configure Strategy</strong>
                  <p class="text-gray-600">Set risk levels, trading limits, and safety parameters</p>
                </div>
              </li>
              <li class="flex items-start gap-3">
                <span class="flex-shrink-0 w-8 h-8 bg-pink-500 text-white rounded-full flex items-center justify-center font-bold">3</span>
                <div>
                  <strong>Start Trading</strong>
                  <p class="text-gray-600">Monitor performance and watch your agents compete on the leaderboard</p>
                </div>
              </li>
            </ol>
          </div>
        </section>

        <!-- DASHBOARD -->
        <section id="page-dashboard" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">Dashboard</h1>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-2">
                <span class="text-3xl">🤖</span>
                <span class="text-sm font-medium text-green-600">+2</span>
              </div>
              <h3 class="text-2xl font-bold mb-1">5</h3>
              <p class="text-gray-600 text-sm">Total Agents</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-2">
                <span class="text-3xl">💰</span>
                <span class="text-sm font-medium text-green-600">+5.2%</span>
              </div>
              <h3 class="text-2xl font-bold mb-1">$12,450</h3>
              <p class="text-gray-600 text-sm">Total Portfolio Value</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-2">
                <span class="text-3xl">🏆</span>
                <span class="text-sm font-medium text-green-600">+15.3%</span>
              </div>
              <h3 class="text-2xl font-bold mb-1">Agent Alpha</h3>
              <p class="text-gray-600 text-sm">Best Performer</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-2">
                <span class="text-3xl">📈</span>
                <span class="text-sm font-medium text-green-600">+3</span>
              </div>
              <h3 class="text-2xl font-bold mb-1">12</h3>
              <p class="text-gray-600 text-sm">Active Trades</p>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Recent Activity</h2>
            <div class="space-y-4">
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">A</div>
                  <div>
                    <p class="font-medium">Agent Alpha</p>
                    <p class="text-sm text-gray-600">Bought BTC</p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="font-bold">$500</p>
                  <p class="text-sm text-gray-500">5m ago</p>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">A</div>
                  <div>
                    <p class="font-medium">Agent Beta</p>
                    <p class="text-sm text-gray-600">Sold ETH</p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="font-bold">$350</p>
                  <p class="text-sm text-gray-500">15m ago</p>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">A</div>
                  <div>
                    <p class="font-medium">Agent Gamma</p>
                    <p class="text-sm text-gray-600">Bought SOL</p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="font-bold">$200</p>
                  <p class="text-sm text-gray-500">1h ago</p>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Portfolio Performance</h2>
            <div class="h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
              <p class="text-gray-500">Chart visualization would go here</p>
            </div>
          </div>
        </section>

        <!-- AGENTS -->
        <section id="page-agents" class="space-y-6 hidden">
          <div class="flex items-center justify-between">
            <h1 class="text-4xl font-bold">Your Agents</h1>
            <button class="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-shadow">
              <i data-lucide="plus" class="w-5 h-5"></i>
              Create Agent
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Agent Alpha -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">A</div>
                  <div>
                    <h3 class="text-xl font-bold">Agent Alpha</h3>
                    <p class="text-sm text-gray-600">Aggressive</p>
                  </div>
                </div>
                <span class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">active</span>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-600 mb-1">Portfolio Value</p>
                  <p class="text-2xl font-bold">$3,200</p>
                </div>
                <div>
                  <p class="text-sm text-gray-600 mb-1">Profit/Loss</p>
                  <div class="flex items-center gap-2">
                    <i data-lucide="trending-up" class="w-5 h-5 text-green-600"></i>
                    <p class="text-2xl font-bold text-green-600">+15.3%</p>
                  </div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">View Details</button>
                <button class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Configure</button>
              </div>
            </div>

            <!-- Agent Beta -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">A</div>
                  <div>
                    <h3 class="text-xl font-bold">Agent Beta</h3>
                    <p class="text-sm text-gray-600">Conservative</p>
                  </div>
                </div>
                <span class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">active</span>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-600 mb-1">Portfolio Value</p>
                  <p class="text-2xl font-bold">$2,800</p>
                </div>
                <div>
                  <p class="text-sm text-gray-600 mb-1">Profit/Loss</p>
                  <div class="flex items-center gap-2">
                    <i data-lucide="trending-up" class="w-5 h-5 text-green-600"></i>
                    <p class="text-2xl font-bold text-green-600">+8.7%</p>
                  </div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">View Details</button>
                <button class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Configure</button>
              </div>
            </div>

            <!-- Agent Gamma -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">A</div>
                  <div>
                    <h3 class="text-xl font-bold">Agent Gamma</h3>
                    <p class="text-sm text-gray-600">Balanced</p>
                  </div>
                </div>
                <span class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">active</span>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-600 mb-1">Portfolio Value</p>
                  <p class="text-2xl font-bold">$3,450</p>
                </div>
                <div>
                  <p class="text-sm text-gray-600 mb-1">Profit/Loss</p>
                  <div class="flex items-center gap-2">
                    <i data-lucide="trending-up" class="w-5 h-5 text-green-600"></i>
                    <p class="text-2xl font-bold text-green-600">+12.1%</p>
                  </div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">View Details</button>
                <button class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Configure</button>
              </div>
            </div>

            <!-- Agent Delta -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">A</div>
                  <div>
                    <h3 class="text-xl font-bold">Agent Delta</h3>
                    <p class="text-sm text-gray-600">Swing Trading</p>
                  </div>
                </div>
                <span class="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">paused</span>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-600 mb-1">Portfolio Value</p>
                  <p class="text-2xl font-bold">$1,950</p>
                </div>
                <div>
                  <p class="text-sm text-gray-600 mb-1">Profit/Loss</p>
                  <div class="flex items-center gap-2">
                    <i data-lucide="trending-down" class="w-5 h-5 text-red-600"></i>
                    <p class="text-2xl font-bold text-red-600">-2.3%</p>
                  </div>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">View Details</button>
                <button class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Configure</button>
              </div>
            </div>
          </div>
        </section>

        <!-- COACH -->
        <section id="page-coach" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">AI Coach</h1>

          <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
            <div class="flex items-center gap-4 mb-4">
              <div class="text-6xl">🧠</div>
              <div>
                <h2 class="text-3xl font-bold">Your AI Trading Coach</h2>
                <p class="text-blue-100">Get personalized insights and recommendations</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Today's Recommendations</h2>
            <div class="space-y-4">

              <div class="p-4 border-l-4 rounded-lg bg-gray-50" style="border-color: #EF4444;">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="font-bold text-lg mb-1">Diversify Your Portfolio</h3>
                    <p class="text-gray-600">Consider adding more variety to reduce risk</p>
                  </div>
                  <span class="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700">high</span>
                </div>
                <div class="mt-3 flex gap-3">
                  <button class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">Apply Now</button>
                  <button class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors">Learn More</button>
                </div>
              </div>

              <div class="p-4 border-l-4 rounded-lg bg-gray-50" style="border-color: #F59E0B;">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="font-bold text-lg mb-1">Adjust Agent Beta Risk Level</h3>
                    <p class="text-gray-600">Conservative strategy may miss opportunities</p>
                  </div>
                  <span class="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-700">medium</span>
                </div>
                <div class="mt-3 flex gap-3">
                  <button class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">Apply Now</button>
                  <button class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors">Learn More</button>
                </div>
              </div>

              <div class="p-4 border-l-4 rounded-lg bg-gray-50" style="border-color: #EF4444;">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="font-bold text-lg mb-1">Review Agent Delta Performance</h3>
                    <p class="text-gray-600">Negative returns for 3 consecutive days</p>
                  </div>
                  <span class="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700">high</span>
                </div>
                <div class="mt-3 flex gap-3">
                  <button class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors">Apply Now</button>
                  <button class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors">Learn More</button>
                </div>
              </div>

            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-4xl mb-3">💡</div>
              <h3 class="text-lg font-bold mb-2">Market Insights</h3>
              <p class="text-gray-600">BTC showing bullish pattern. Consider increasing exposure.</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-4xl mb-3">⚠️</div>
              <h3 class="text-lg font-bold mb-2">Risk Alert</h3>
              <p class="text-gray-600">Portfolio concentration risk detected in top 3 assets.</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-4xl mb-3">🎯</div>
              <h3 class="text-lg font-bold mb-2">Goal Progress</h3>
              <p class="text-gray-600">On track to hit 20% annual return target.</p>
            </div>
          </div>
        </section>

        <!-- MARKET -->
        <section id="page-market" class="space-y-6 hidden">
          <div class="flex items-center justify-between">
            <h1 class="text-4xl font-bold">Market Overview</h1>
            <div class="flex gap-3">
              <button class="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">Refresh</button>
              <button class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Paper Trade</button>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- BTC -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">B</div>
                  <div>
                    <h3 class="text-xl font-bold">BTC</h3>
                    <p class="text-sm text-gray-600">Bitcoin</p>
                  </div>
                </div>
                <i data-lucide="trending-up" class="w-6 h-6 text-green-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$42,150</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-green-600">+5.2%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>

            <!-- ETH -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">E</div>
                  <div>
                    <h3 class="text-xl font-bold">ETH</h3>
                    <p class="text-sm text-gray-600">Ethereum</p>
                  </div>
                </div>
                <i data-lucide="trending-up" class="w-6 h-6 text-green-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$2,245</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-green-600">+3.8%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>

            <!-- SOL -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">S</div>
                  <div>
                    <h3 class="text-xl font-bold">SOL</h3>
                    <p class="text-sm text-gray-600">Solana</p>
                  </div>
                </div>
                <i data-lucide="trending-down" class="w-6 h-6 text-red-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$98.50</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-red-600">-1.2%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>

            <!-- ADA -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">A</div>
                  <div>
                    <h3 class="text-xl font-bold">ADA</h3>
                    <p class="text-sm text-gray-600">Cardano</p>
                  </div>
                </div>
                <i data-lucide="trending-up" class="w-6 h-6 text-green-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$0.52</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-green-600">+2.1%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>

            <!-- DOT -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">D</div>
                  <div>
                    <h3 class="text-xl font-bold">DOT</h3>
                    <p class="text-sm text-gray-600">Polkadot</p>
                  </div>
                </div>
                <i data-lucide="trending-down" class="w-6 h-6 text-red-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$7.35</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-red-600">-0.8%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>

            <!-- AVAX -->
            <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold">A</div>
                  <div>
                    <h3 class="text-xl font-bold">AVAX</h3>
                    <p class="text-sm text-gray-600">Avalanche</p>
                  </div>
                </div>
                <i data-lucide="trending-up" class="w-6 h-6 text-green-600"></i>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between items-end">
                  <span class="text-sm text-gray-600">Current Price</span>
                  <span class="text-2xl font-bold">$35.20</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-gray-600">24h Change</span>
                  <span class="text-lg font-bold text-green-600">+7.5%</span>
                </div>
              </div>
              <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
                <button class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors">Buy</button>
                <button class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">Sell</button>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Market Sentiment</h2>
            <div class="grid grid-cols-3 gap-6">
              <div class="text-center">
                <div class="text-4xl mb-2">📈</div>
                <p class="text-3xl font-bold text-green-600">65%</p>
                <p class="text-gray-600">Bullish</p>
              </div>
              <div class="text-center">
                <div class="text-4xl mb-2">↔️</div>
                <p class="text-3xl font-bold text-gray-600">20%</p>
                <p class="text-gray-600">Neutral</p>
              </div>
              <div class="text-center">
                <div class="text-4xl mb-2">📉</div>
                <p class="text-3xl font-bold text-red-600">15%</p>
                <p class="text-gray-600">Bearish</p>
              </div>
            </div>
          </div>
        </section>

        <!-- ANALYTICS -->
        <section id="page-analytics" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">Analytics</h1>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-3xl mb-2">📊</div>
              <p class="text-3xl font-bold mb-1">+12.5%</p>
              <p class="text-gray-600">Total Return</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-3xl mb-2">📈</div>
              <p class="text-3xl font-bold mb-1">1.85</p>
              <p class="text-gray-600">Sharpe Ratio</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-3xl mb-2">🎯</div>
              <p class="text-3xl font-bold mb-1">68%</p>
              <p class="text-gray-600">Win Rate</p>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="text-3xl mb-2">📉</div>
              <p class="text-3xl font-bold mb-1">-5.2%</p>
              <p class="text-gray-600">Max Drawdown</p>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Performance Over Time</h2>
            <div class="h-80 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
              <p class="text-gray-500">Interactive chart would display here</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6">
              <h2 class="text-2xl font-bold mb-4">Asset Allocation</h2>
              <div class="h-64 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg flex items-center justify-center">
                <p class="text-gray-500">Pie chart visualization</p>
              </div>
            </div>
            <div class="bg-white rounded-xl shadow-lg p-6">
              <h2 class="text-2xl font-bold mb-4">Agent Comparison</h2>
              <div class="h-64 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg flex items-center justify-center">
                <p class="text-gray-500">Bar chart visualization</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Risk Metrics</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-600 mb-1">Volatility</p>
                <p class="text-2xl font-bold mb-2">12.3%</p>
                <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">Medium</span>
              </div>
              <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-600 mb-1">Beta</p>
                <p class="text-2xl font-bold mb-2">0.85</p>
                <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">Low</span>
              </div>
              <div class="p-4 bg-gray-50 rounded-lg">
                <p class="text-sm text-gray-600 mb-1">VaR (95%)</p>
                <p class="text-2xl font-bold mb-2">-3.2%</p>
                <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">Low</span>
              </div>
            </div>
          </div>
        </section>

        <!-- LEADERBOARDS -->
        <section id="page-leaderboards" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">Leaderboards</h1>

          <div class="flex gap-4 bg-white rounded-xl shadow-lg p-2">
            <button class="flex-1 px-4 py-3 rounded-lg font-medium transition-colors hover:bg-gray-100">Daily</button>
            <button class="flex-1 px-4 py-3 rounded-lg font-medium transition-colors bg-gradient-to-r from-blue-500 to-purple-600 text-white">Weekly</button>
            <button class="flex-1 px-4 py-3 rounded-lg font-medium transition-colors hover:bg-gray-100">Monthly</button>
            <button class="flex-1 px-4 py-3 rounded-lg font-medium transition-colors hover:bg-gray-100">Yearly</button>
          </div>

          <div class="bg-white rounded-xl shadow-lg overflow-hidden">
            <div class="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 p-6 text-white">
              <div class="flex items-center gap-4">
                <i data-lucide="trophy" class="w-16 h-16"></i>
                <div>
                  <h2 class="text-3xl font-bold">Top Performers</h2>
                  <p class="text-yellow-100">Weekly Rankings</p>
                </div>
              </div>
            </div>

            <div class="p-6">
              <div class="space-y-4">

                <!-- 1 -->
                <div class="flex items-center justify-between p-6 rounded-lg bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200">
                  <div class="flex items-center gap-6">
                    <div class="w-16 flex justify-center">
                      <i data-lucide="trophy" class="w-6 h-6 text-yellow-500"></i>
                    </div>
                    <div>
                      <p class="text-xl font-bold">BOT-A7X2</p>
                      <p class="text-sm text-gray-600">Score: 1523</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-8">
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Profit</p>
                      <p class="text-xl font-bold text-green-600">+15.3%</p>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Streak</p>
                      <p class="text-xl font-bold">23 days</p>
                    </div>
                  </div>
                </div>

                <!-- 2 -->
                <div class="flex items-center justify-between p-6 rounded-lg bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200">
                  <div class="flex items-center gap-6">
                    <div class="w-16 flex justify-center">
                      <i data-lucide="medal" class="w-6 h-6 text-gray-400"></i>
                    </div>
                    <div>
                      <p class="text-xl font-bold">BOT-B9K5</p>
                      <p class="text-sm text-gray-600">Score: 1487</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-8">
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Profit</p>
                      <p class="text-xl font-bold text-green-600">+14.1%</p>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Streak</p>
                      <p class="text-xl font-bold">18 days</p>
                    </div>
                  </div>
                </div>

                <!-- 3 -->
                <div class="flex items-center justify-between p-6 rounded-lg bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200">
                  <div class="flex items-center gap-6">
                    <div class="w-16 flex justify-center">
                      <i data-lucide="award" class="w-6 h-6 text-orange-600"></i>
                    </div>
                    <div>
                      <p class="text-xl font-bold">BOT-C3M1</p>
                      <p class="text-sm text-gray-600">Score: 1421</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-8">
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Profit</p>
                      <p class="text-xl font-bold text-green-600">+12.7%</p>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Streak</p>
                      <p class="text-xl font-bold">14 days</p>
                    </div>
                  </div>
                </div>

                <!-- 4 -->
                <div class="flex items-center justify-between p-6 rounded-lg bg-gray-50">
                  <div class="flex items-center gap-6">
                    <div class="w-16 flex justify-center">
                      <span class="text-xl font-bold text-gray-400">#4</span>
                    </div>
                    <div>
                      <p class="text-xl font-bold">BOT-D8P4</p>
                      <p class="text-sm text-gray-600">Score: 1390</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-8">
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Profit</p>
                      <p class="text-xl font-bold text-green-600">+11.9%</p>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Streak</p>
                      <p class="text-xl font-bold">12 days</p>
                    </div>
                  </div>
                </div>

                <!-- 5 -->
                <div class="flex items-center justify-between p-6 rounded-lg bg-gray-50">
                  <div class="flex items-center gap-6">
                    <div class="w-16 flex justify-center">
                      <span class="text-xl font-bold text-gray-400">#5</span>
                    </div>
                    <div>
                      <p class="text-xl font-bold">BOT-E2N7</p>
                      <p class="text-sm text-gray-600">Score: 1365</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-8">
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Profit</p>
                      <p class="text-xl font-bold text-green-600">+11.2%</p>
                    </div>
                    <div class="text-right">
                      <p class="text-sm text-gray-600">Streak</p>
                      <p class="text-xl font-bold">9 days</p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Score Calculation</h2>
            <div class="space-y-3 text-gray-700">
              <p><strong>Formula:</strong> Score = (Profit × 100) + Streaks</p>
              <p class="text-sm text-gray-600">Profit is rounded to 2 decimals before scoring</p>
              <p class="text-sm text-gray-600">Streaks = consecutive periods with profit &gt; 0</p>
            </div>
          </div>
        </section>

        <!-- SAFETY -->
        <section id="page-safety" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">Safety Controls</h1>

          <div class="bg-gradient-to-r from-red-500 to-orange-600 rounded-xl shadow-lg p-8 text-white">
            <div class="flex items-center gap-4">
              <i data-lucide="shield" class="w-16 h-16"></i>
              <div>
                <h2 class="text-3xl font-bold">Risk Management</h2>
                <p class="text-red-100">Configure safety parameters and exit triggers</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold">Safety Exits</h3>
                <div class="w-12 h-6 bg-green-500 rounded-full relative cursor-pointer">
                  <div class="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5"></div>
                </div>
              </div>
              <p class="text-sm text-gray-600">Automatically sell all positions when triggers activate</p>
            </div>

            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold">Max Daily Loss</h3>
                <i data-lucide="alert-triangle" class="w-6 h-6 text-orange-500"></i>
              </div>
              <div class="space-y-2">
                <p class="text-3xl font-bold">-10%</p>
                <input type="range" min="1" max="20" value="10" class="w-full" />
              </div>
            </div>

            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold">Max Drawdown</h3>
                <i data-lucide="alert-triangle" class="w-6 h-6 text-red-500"></i>
              </div>
              <div class="space-y-2">
                <p class="text-3xl font-bold">-15%</p>
                <input type="range" min="5" max="30" value="15" class="w-full" />
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Active Safety Triggers</h2>
            <div class="space-y-3">
              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <i data-lucide="check-circle" class="w-6 h-6 text-green-600"></i>
                  <div>
                    <p class="font-bold">Max Daily Loss Trigger</p>
                    <p class="text-sm text-gray-600">Threshold: -10%</p>
                  </div>
                </div>
                <span class="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">active</span>
              </div>

              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <i data-lucide="check-circle" class="w-6 h-6 text-green-600"></i>
                  <div>
                    <p class="font-bold">Max Drawdown Trigger</p>
                    <p class="text-sm text-gray-600">Threshold: -15%</p>
                  </div>
                </div>
                <span class="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">active</span>
              </div>

              <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-4">
                  <i data-lucide="check-circle" class="w-6 h-6 text-green-600"></i>
                  <div>
                    <p class="font-bold">Fraud/Anomaly Detection</p>
                    <p class="text-sm text-gray-600">Threshold: Auto</p>
                  </div>
                </div>
                <span class="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium">active</span>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Panic Controls</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <button class="p-6 bg-red-50 hover:bg-red-100 border-2 border-red-200 rounded-lg transition-colors">
                <i data-lucide="alert-triangle" class="w-8 h-8 text-red-600 mx-auto mb-3"></i>
                <h3 class="font-bold text-lg mb-2">Panic Sell</h3>
                <p class="text-sm text-gray-600">Immediately sell all positions across all agents</p>
              </button>
              <button class="p-6 bg-orange-50 hover:bg-orange-100 border-2 border-orange-200 rounded-lg transition-colors">
                <i data-lucide="shield" class="w-8 h-8 text-orange-600 mx-auto mb-3"></i>
                <h3 class="font-bold text-lg mb-2">Pause All Trading</h3>
                <p class="text-sm text-gray-600">Temporarily halt all agent trading activity</p>
              </button>
            </div>
          </div>
        </section>

        <!-- PROFILE -->
        <section id="page-profile" class="space-y-6 hidden">
          <h1 class="text-4xl font-bold">Profile</h1>

          <div class="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
            <div class="flex items-center gap-6">
              <div class="w-24 h-24 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                <i data-lucide="user" class="w-12 h-12"></i>
              </div>
              <div>
                <h2 class="text-3xl font-bold mb-2">Demo User</h2>
                <p class="text-blue-100">demo@crowdlike.app</p>
                <p class="text-sm text-blue-100 mt-2">Member since January 2026</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="flex items-center gap-3 mb-6">
                <i data-lucide="settings" class="w-6 h-6 text-gray-600"></i>
                <h2 class="text-2xl font-bold">Account Settings</h2>
              </div>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Display Name</label>
                  <input type="text" value="Demo User" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input type="email" value="demo@crowdlike.app" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" />
                </div>
                <button class="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Save Changes</button>
              </div>
            </div>

            <div class="bg-white rounded-xl shadow-lg p-6">
              <div class="flex items-center gap-3 mb-6">
                <i data-lucide="bell" class="w-6 h-6 text-gray-600"></i>
                <h2 class="text-2xl font-bold">Notifications</h2>
              </div>
              <div class="space-y-4">
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="font-medium">Trade Alerts</span>
                  <div class="w-12 h-6 rounded-full relative cursor-pointer transition-colors bg-green-500">
                    <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform right-0.5"></div>
                  </div>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="font-medium">Performance Updates</span>
                  <div class="w-12 h-6 rounded-full relative cursor-pointer transition-colors bg-green-500">
                    <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform right-0.5"></div>
                  </div>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="font-medium">Safety Triggers</span>
                  <div class="w-12 h-6 rounded-full relative cursor-pointer transition-colors bg-green-500">
                    <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform right-0.5"></div>
                  </div>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span class="font-medium">Weekly Summary</span>
                  <div class="w-12 h-6 rounded-full relative cursor-pointer transition-colors bg-gray-300">
                    <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform left-0.5"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <div class="flex items-center gap-3 mb-6">
              <i data-lucide="lock" class="w-6 h-6 text-gray-600"></i>
              <h2 class="text-2xl font-bold">Security</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="p-4 border border-gray-200 rounded-lg">
                <h3 class="font-bold mb-2">Password</h3>
                <p class="text-sm text-gray-600 mb-3">Last changed 30 days ago</p>
                <button class="text-blue-500 hover:text-blue-600 font-medium text-sm">Change Password</button>
              </div>
              <div class="p-4 border border-gray-200 rounded-lg">
                <h3 class="font-bold mb-2">Two-Factor Auth</h3>
                <p class="text-sm text-gray-600 mb-3">Not enabled</p>
                <button class="text-blue-500 hover:text-blue-600 font-medium text-sm">Enable 2FA</button>
              </div>
              <div class="p-4 border border-gray-200 rounded-lg">
                <h3 class="font-bold mb-2">API Keys</h3>
                <p class="text-sm text-gray-600 mb-3">0 active keys</p>
                <button class="text-blue-500 hover:text-blue-600 font-medium text-sm">Manage Keys</button>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Subscription</h2>
            <div class="flex items-center justify-between p-6 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
              <div>
                <h3 class="text-xl font-bold mb-1">Pro Plan</h3>
                <p class="text-gray-600">Unlimited agents • Advanced analytics • Priority support</p>
              </div>
              <div class="text-right">
                <p class="text-3xl font-bold">$49</p>
                <p class="text-sm text-gray-600">per month</p>
              </div>
            </div>
          </div>
        </section>

      </div>
    </main>
  </div>

  <script>
    // Source-of-truth page list (copied from DynamicSidebar.tsx)
    const pages = [
      { id: 'home', label: 'Home', icon: 'home', emoji: '🏠' },
      { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', emoji: '📊' },
      { id: 'agents', label: 'Agents', icon: 'users', emoji: '🤖' },
      { id: 'coach', label: 'Coach', icon: 'brain', emoji: '🧠' },
      { id: 'market', label: 'Market', icon: 'trending-up', emoji: '📈' },
      { id: 'analytics', label: 'Analytics', icon: 'bar-chart-3', emoji: '📉' },
      { id: 'leaderboards', label: 'Leaderboards', icon: 'trophy', emoji: '🏆' },
      { id: 'safety', label: 'Safety', icon: 'shield', emoji: '🛡️' },
      { id: 'profile', label: 'Profile', icon: 'user-circle', emoji: '👤' },
    ];

    let currentPage = 'home';
    let sidebarVisible = true;
    let prevScrollY = 0;

    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('main');
    const nav = document.getElementById('nav');
    const search = document.getElementById('search');
    const clearSearch = document.getElementById('clear-search');
    const appRoot = document.getElementById('app-root');

    function setSidebarVisible(visible) {
      sidebarVisible = visible;
      sidebar.classList.toggle('-translate-x-full', !visible);
      sidebar.classList.toggle('translate-x-0', visible);
      main.style.marginLeft = visible ? '280px' : '0px';
    }


    function routeToStreamlit(pageId) {
      try {
        const u = new URL(window.parent.location.href);
        u.pathname = "/";
        u.searchParams.set("cl_page", pageId);
        window.parent.location.href = u.toString();
      } catch (e) {
        try { window.parent.location.search = "?cl_page=" + encodeURIComponent(pageId); } catch {}
      }
    }

    function setActivePage(pageId) {
      currentPage = pageId;
      pages.forEach(p => {
        const section = document.getElementById(`page-${p.id}`);
        if (!section) return;
        section.classList.toggle('hidden', p.id !== pageId);
      });

      // Update nav active styles
      document.querySelectorAll('[data-nav-id]').forEach(btn => {
        const id = btn.getAttribute('data-nav-id');
        const isActive = id === pageId;
        btn.className = `w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
          isActive
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
            : 'text-gray-700 hover:bg-gray-100'
        }`;
      });

      // Scroll to top (matches typical page navigation)
      appRoot.scrollTop = 0;
    }

    function renderNav(filterText = '') {
      nav.innerHTML = '';
      const filtered = pages.filter(p => p.label.toLowerCase().includes(filterText.toLowerCase()));

      filtered.forEach(p => {
        const btn = document.createElement('button');
        btn.setAttribute('data-nav-id', p.id);
        btn.className = `w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
          p.id === currentPage
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
            : 'text-gray-700 hover:bg-gray-100'
        }`;

        btn.innerHTML = `
          <span class="text-xl">${p.emoji}</span>
          <i data-lucide="${p.icon}" class="w-5 h-5"></i>
          <span class="font-medium">${p.label}</span>
        `;

        btn.addEventListener('click', () => {
          if (p.id === 'home') setActivePage('home');
          else routeToStreamlit(p.id);
        });

        nav.appendChild(btn);
      });

      // Re-render lucide icons
      if (window.lucide) window.lucide.createIcons();
    }

    // Search behavior
    search.addEventListener('input', (e) => {
      const q = e.target.value || '';
      clearSearch.classList.toggle('hidden', q.length === 0);
      renderNav(q);
    });

    clearSearch.addEventListener('click', () => {
      search.value = '';
      clearSearch.classList.add('hidden');
      renderNav('');
    });

    // Mouse edge reveal / hide (same thresholds as the React version)
    document.addEventListener('mousemove', (e) => {
      if (e.clientX < 50) setSidebarVisible(true);
      else if (e.clientX > 300 && sidebarVisible) setSidebarVisible(false);
    });

    // Auto-hide on scroll (within app-root)
    appRoot.addEventListener('scroll', () => {
      const currentScrollY = appRoot.scrollTop;
      if (currentScrollY > prevScrollY && currentScrollY > 100) setSidebarVisible(false);
      else if (currentScrollY < prevScrollY) setSidebarVisible(true);
      prevScrollY = currentScrollY;
    }, { passive: true });

    // Initial render
    renderNav('');
    setActivePage('home');
    setSidebarVisible(true);

    // Render any icons already present in the DOM
    if (window.lucide) window.lucide.createIcons();
  </script>

  <script>
/* CROWDLIKE_INTERACTIVITY_V2 */
(function () {
  const STORE = "crowdlike_state_v2";
  const COINS = { BTC:"bitcoin", ETH:"ethereum", SOL:"solana", ADA:"cardano", DOT:"polkadot", AVAX:"avalanche-2" };

  function load(){ try { return JSON.parse(localStorage.getItem(STORE) || "{}"); } catch { return {}; } }
  function save(s){ localStorage.setItem(STORE, JSON.stringify(s)); }
  function slug(s){ return (s||"").trim().toLowerCase().replace(/\s+/g,"_").replace(/[^a-z0-9_]/g,""); }

  let st = load();
  st.trades = Number.isFinite(st.trades) ? st.trades : 0;
  st.agents = Array.isArray(st.agents) ? st.agents : [];
  st.safety = (st.safety && typeof st.safety === "object") ? st.safety : {};
  save(st);

  function toast(msg){
    let el = document.getElementById("__toast");
    if(!el){
      el = document.createElement("div");
      el.id="__toast";
      el.style.position="fixed";
      el.style.right="16px";
      el.style.bottom="16px";
      el.style.zIndex="999999";
      document.body.appendChild(el);
    }
    el.innerHTML =
      '<div style="background:#111827;color:#fff;padding:10px 12px;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.25);font-size:13px;max-width:360px;">'
      + msg + '</div>';
    setTimeout(()=>{ el.innerHTML=""; }, 1800);
  }

  function ev(name){ try { window.clarity && window.clarity("event", name); } catch {} }

  function setActiveTrades(n){
    const cards = Array.from(document.querySelectorAll("#page-dashboard .bg-white"));
    const card = cards.find(c => (c.textContent||"").includes("Active Trades"));
    const h3 = card ? card.querySelector("h3") : null;
    if(h3) h3.textContent = String(n);
  }

  function restoreRanges(){
    const safety = document.getElementById("page-safety");
    if(!safety) return;
    Array.from(safety.querySelectorAll('input[type="range"]')).forEach((rng,i)=>{
      const k = "range_"+i;
      if(st.safety[k] != null) rng.value = String(st.safety[k]);
      rng.addEventListener("input", ()=>{
        st.safety[k] = Number(rng.value);
        save(st);
        ev("safety_slider");
      }, { passive: true });
    });
  }

  function appendAgentCard(name, strategy){
    const grid = document.querySelector("#page-agents .grid");
    if(!grid) return;

    const div = document.createElement("div");
    div.className = "bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow";
    div.innerHTML = `
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl">${name.slice(0,1).toUpperCase()}</div>
          <div>
            <h3 class="text-xl font-bold">${name}</h3>
            <p class="text-sm text-gray-600">${strategy}</p>
          </div>
        </div>
        <span class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">active</span>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <p class="text-sm text-gray-600 mb-1">Portfolio Value</p>
          <p class="text-2xl font-bold">$0</p>
        </div>
        <div>
          <p class="text-sm text-gray-600 mb-1">Profit/Loss</p>
          <div class="flex items-center gap-2">
            <i data-lucide="trending-up" class="w-5 h-5 text-green-600"></i>
            <p class="text-2xl font-bold text-green-600">+0.0%</p>
          </div>
        </div>
      </div>
      <div class="mt-4 pt-4 border-t border-gray-200 flex gap-3">
        <button class="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">View Details</button>
        <button class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors">Configure</button>
      </div>
    `;
    grid.appendChild(div);

    if (window.lucide) window.lucide.createIcons();
  }

  function restoreAgents(){
    const agents = Array.isArray(st.agents) ? st.agents : [];
    agents.forEach(a => {
      if(a && a.name) appendAgentCard(a.name, a.strategy || "Balanced");
    });
  }

  async function refreshMarket(){
    const ids = Object.values(COINS).join(",");
    const url = "https://api.coingecko.com/api/v3/simple/price?ids=" + encodeURIComponent(ids) + "&vs_currencies=usd&include_24hr_change=true";
    const res = await fetch(url);
    if(!res.ok) throw new Error("fetch_failed");
    const json = await res.json();

    const cards = Array.from(document.querySelectorAll("#page-market .bg-white"));
    for(const card of cards){
      const h3 = card.querySelector("h3");
      if(!h3) continue;

      const sym = (h3.textContent||"").trim();
      const id = COINS[sym];
      if(!id || !json[id]) continue;

      const price = Number(json[id].usd || 0);
      const chg = Number(json[id].usd_24hr_change || 0);

      const spans = Array.from(card.querySelectorAll("span"));
      const priceEl = spans.find(s => (s.textContent||"").trim().startsWith("$"));
      if(priceEl) priceEl.textContent = "$" + price.toLocaleString(undefined, { maximumFractionDigits: 2 });

      const changeEl = spans.find(s => (s.textContent||"").includes("%"));
      if(changeEl){
        changeEl.textContent = (chg>=0?"+":"") + chg.toFixed(2) + "%";
        changeEl.classList.toggle("text-green-600", chg>=0);
        changeEl.classList.toggle("text-red-600", chg<0);
      }
    }

    toast("Market updated");
    ev("market_refresh");
  }

  document.addEventListener("click", async (e)=>{
    const btn = e.target && e.target.closest ? e.target.closest("button") : null;
    if(!btn) return;

    const text = (btn.textContent || "").trim();
    if(!text) return;

    // Basic click feedback
    toast(text + " clicked");
    ev("click_" + slug(text));

    // Create Agent flow
    if(/create\s+agent/i.test(text)){
      const name = prompt("Agent name?");
      if(!name) return;
      const strategy = prompt("Strategy?") || "Balanced";
      st.agents.push({ name, strategy });
      save(st);
      appendAgentCard(name, strategy);
      toast("Agent created");
      ev("create_agent");
      return;
    }

    // Market refresh
    if(/^refresh$/i.test(text)){
      try { await refreshMarket(); }
      catch { toast("Market refresh failed (network blocked?)"); }
      return;
    }

    // Buy/Sell increments "Active Trades"
    if(/^buy$/i.test(text) || /^sell$/i.test(text)){
      const qty = prompt("Quantity?");
      if(!qty) return;
      st.trades += 1;
      save(st);
      setActiveTrades(st.trades);
      toast(text.toUpperCase() + " placed (" + qty + ")");
      ev(text.toLowerCase()==="buy" ? "trade_buy" : "trade_sell");
      return;
    }
  }, true);

  try {
    setActiveTrades(st.trades);
    restoreRanges();
    restoreAgents();
    console.log("CROWDLIKE_INTERACTIVITY_V2 loaded");
    toast("Interactivity loaded");
  } catch (e) {
    console.log("Interactivity boot error:", e);
  }
})();
  </script>
</body>
</html>"""

components.html(HTML, height=950, scrolling=True)
