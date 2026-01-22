
from __future__ import annotations

import html

def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)

def metamask_usdc_transfer_embed(
    *,
    chain_id: int,
    chain_name: str,
    rpc_url: str,
    explorer_url: str,
    token: str,
    to_address: str,
    amount_base_units: int,
    height: int = 240,
) -> tuple[str, int]:
    """
    Returns (html, height) to embed via st.components.v1.html.

    Notes:
    - This is an embed (not a full Streamlit custom component), so it cannot return
      values to Python. It will display the tx hash + explorer link in the iframe,
      and the user can paste the receipt code into the app (easy UX).
    """
    chain_id_hex = hex(int(chain_id))
    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
    margin: 0;
    padding: 12px;
    background: rgba(255,255,255,.60);
  }}
  .box {{
    border: 1px solid rgba(120,160,255,.22);
    border-radius: 16px;
    padding: 12px;
    background: rgba(255,255,255,.78);
  }}
  button {{
    border-radius: 14px;
    border: 1px solid rgba(120,160,255,.45);
    background: linear-gradient(90deg, rgba(116,184,255,.16), rgba(255,255,255,.60), rgba(183,166,255,.12));
    padding: 10px 12px;
    font-weight: 700;
    cursor: pointer;
  }}
  button:disabled {{ opacity: .55; cursor: not-allowed; }}
  code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace;
    font-size: 12px;
  }}
  .row {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:10px; }}
  .muted {{ opacity:.70; }}
  .ok {{ color: #0b7a3b; font-weight: 800; }}
  .err {{ color: #b91c1c; font-weight: 800; }}
  a {{ color: rgba(11,18,32,.92); }}
</style>
</head>
<body>
  <div class="box">
    <div><b>Pay with MetaMask (testnet)</b></div>
    <div class="muted">1-click payment — your wallet will show a receipt code.</div>

    <div class="row">
      <button id="connect">Connect</button>
      <button id="pay" disabled>Pay</button>
    </div>

    <div style="margin-top:10px" class="muted">
      <div>To: <code>{_esc(to_address)}</code></div>
      <div>Amount: <code>{_esc(str(amount_base_units))}</code> (base units)</div>
      <div>Token: <code>{_esc(token)}</code></div>
    </div>

    <div style="margin-top:10px" id="status" class="muted">Status: waiting…</div>
    <div style="margin-top:8px" id="tx" class="muted"></div>
  </div>

<script>
const CHAIN_ID = "{_esc(chain_id_hex)}";
const RPC_URL = "{_esc(rpc_url)}";
const EXPLORER = "{_esc(explorer_url)}";
const CHAIN_NAME = "{_esc(chain_name)}";
const TOKEN = "{_esc(token)}";
const TO = "{_esc(to_address)}";
const AMOUNT = "{_esc(str(int(amount_base_units)))}";

function setStatus(msg, cls="muted") {{
  const el = document.getElementById("status");
  el.className = cls;
  el.textContent = "Status: " + msg;
}}

function setTx(hash) {{
  const el = document.getElementById("tx");
  const url = EXPLORER.replace(/\/$/, "") + "/tx/" + hash;
  el.innerHTML = `<div class="ok">Receipt code: <code>${{hash}}</code></div>
                  <div style="margin-top:6px"><a href="${{url}}" target="_blank" rel="noopener">Open in explorer</a></div>
                  <div style="margin-top:6px"><button id="copy">Copy receipt</button></div>`;
  const btn = document.getElementById("copy");
  btn.onclick = async () => {{
    try {{
      await navigator.clipboard.writeText(hash);
      btn.textContent = "Copied ✅";
    }} catch(e) {{
      btn.textContent = "Copy failed";
    }}
  }};
}}

function pad32(hexNo0x) {{
  return hexNo0x.padStart(64, "0");
}}
function encodeTransfer(to, amount) {{
  // transfer(address,uint256) selector = 0xa9059cbb
  const selector = "a9059cbb";
  const toClean = to.toLowerCase().replace(/^0x/, "");
  const amtHex = BigInt(amount).toString(16);
  return "0x" + selector + pad32(toClean) + pad32(amtHex);
}}

async function ensureChain() {{
  try {{
    await window.ethereum.request({{
      method: "wallet_switchEthereumChain",
      params: [{{ chainId: CHAIN_ID }}]
    }});
  }} catch (e) {{
    // 4902 = unknown chain
    if (e && e.code === 4902) {{
      await window.ethereum.request({{
        method: "wallet_addEthereumChain",
        params: [{{
          chainId: CHAIN_ID,
          chainName: CHAIN_NAME,
          rpcUrls: [RPC_URL],
          nativeCurrency: {{ name: "USDC", symbol: "USDC", decimals: 6 }},
          blockExplorerUrls: [EXPLORER]
        }}]
      }});
    }} else {{
      throw e;
    }}
  }}
}}

let account = null;

document.getElementById("connect").onclick = async () => {{
  if (!window.ethereum) {{
    setStatus("MetaMask not found. Install the extension.", "err");
    return;
  }}
  try {{
    setStatus("Connecting…");
    const accounts = await window.ethereum.request({{ method: "eth_requestAccounts" }});
    account = accounts[0];
    await ensureChain();
    setStatus("Connected: " + account.slice(0,6) + "…" + account.slice(-4), "ok");
    document.getElementById("pay").disabled = false;
  }} catch (e) {{
    setStatus("Connect failed.", "err");
    console.error(e);
  }}
}};

document.getElementById("pay").onclick = async () => {{
  if (!window.ethereum || !account) return;
  try {{
    setStatus("Preparing transaction…");
    await ensureChain();
    const data = encodeTransfer(TO, AMOUNT);
    const txHash = await window.ethereum.request({{
      method: "eth_sendTransaction",
      params: [{{
        from: account,
        to: TOKEN,
        data: data,
        value: "0x0"
      }}]
    }});
    setStatus("Sent ✅", "ok");
    setTx(txHash);
  }} catch(e) {{
    setStatus("Payment failed.", "err");
    console.error(e);
  }}
}};
</script>
</body>
</html>
""", int(height)
