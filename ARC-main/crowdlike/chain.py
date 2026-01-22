
from __future__ import annotations

import requests

# Common ERC20 method selectors (keccak-256 first 4 bytes)
BALANCE_OF = "0x70a08231"  # balanceOf(address)
DECIMALS   = "0x313ce567"  # decimals()

# ERC20 Transfer event topic0 = keccak256("Transfer(address,address,uint256)")
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def _pad32(hex_no0x: str) -> str:
    return hex_no0x.rjust(64, "0")

def _addr_to_32(addr: str) -> str:
    a = addr.lower().replace("0x", "")
    return _pad32(a)

def _rpc(rpc_url: str, method: str, params: list):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(rpc_url, json=payload, timeout=12)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]

def get_erc20_decimals(rpc_url: str, token: str) -> int:
    data = DECIMALS
    res = _rpc(rpc_url, "eth_call", [{"to": token, "data": data}, "latest"])
    return int(res, 16)

def get_erc20_balance(rpc_url: str, token: str, wallet: str) -> int:
    data = BALANCE_OF + _addr_to_32(wallet)
    res = _rpc(rpc_url, "eth_call", [{"to": token, "data": data}, "latest"])
    return int(res, 16)

def get_tx_receipt(rpc_url: str, tx_hash: str) -> dict | None:
    res = _rpc(rpc_url, "eth_getTransactionReceipt", [tx_hash])
    return res  # may be None if not mined yet

def _topic_addr(topic_hex: str) -> str:
    # last 40 hex chars
    t = (topic_hex or "").lower().replace("0x", "")
    if len(t) < 40:
        return ""
    return "0x" + t[-40:]

def verify_erc20_transfer(
    receipt: dict,
    *,
    token: str,
    to_address: str,
    min_amount_base_units: int | None = None,
) -> tuple[bool, str]:
    """
    Verify a tx receipt includes an ERC20 Transfer to to_address on token.
    """
    if not receipt:
        return False, "Receipt not found yet (still pending)."

    token_l = (token or "").lower()
    to_l = (to_address or "").lower()

    logs = receipt.get("logs") or []
    for lg in logs:
        try:
            addr = (lg.get("address") or "").lower()
            topics = lg.get("topics") or []
            data = lg.get("data") or "0x0"
        except Exception:
            continue
        if addr != token_l:
            continue
        if not topics or (topics[0] or "").lower() != TRANSFER_TOPIC0:
            continue

        if len(topics) >= 3:
            to_topic = _topic_addr(topics[2])
            if to_topic.lower() != to_l:
                continue

        # parse amount from data
        try:
            amount = int(str(data), 16)
        except Exception:
            amount = 0

        if min_amount_base_units is not None and amount < int(min_amount_base_units):
            return False, "Transfer found but amount is smaller than expected."

        return True, "Transfer verified."

    return False, "No matching ERC20 Transfer found in this tx."
