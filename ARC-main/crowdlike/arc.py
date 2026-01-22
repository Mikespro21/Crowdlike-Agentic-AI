from __future__ import annotations

import decimal
import re
from typing import Any, Dict, Optional, Tuple

import requests

# Defaults (Arc testnet)
DEFAULT_RPC_URL = "https://rpc.testnet.arc.network"
DEFAULT_EXPLORER = "https://testnet.arcscan.app"

# Arc USDC ERC-20 interface (precompile)
DEFAULT_USDC_ERC20 = "0x3600000000000000000000000000000000000000"
DEFAULT_USDC_DECIMALS = 6  # ERC-20 interface uses 6 decimals

# ERC-20 Transfer event signature topic
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def is_address(addr: str) -> bool:
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", (addr or "").strip()))


def is_tx_hash(tx: str) -> bool:
    return bool(re.match(r"^0x[a-fA-F0-9]{64}$", (tx or "").strip()))


def to_base_units(amount: str, decimals: int) -> int:
    """Convert a human amount string to base units int (safe for 6-decimals)."""
    q = decimal.Decimal(10) ** int(decimals)
    d = decimal.Decimal(str(amount).strip())
    # Normalize (avoid scientific notation)
    base = int((d * q).to_integral_value(rounding=decimal.ROUND_DOWN))
    return max(0, base)


def from_base_units(amount_int: int, decimals: int) -> str:
    q = decimal.Decimal(10) ** int(decimals)
    d = decimal.Decimal(int(amount_int)) / q
    return format(d.normalize(), "f")


def _rpc(rpc_url: str, method: str, params: list) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(rpc_url, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")


def get_tx_receipt(rpc_url: str, tx_hash: str) -> Optional[Dict[str, Any]]:
    if not is_tx_hash(tx_hash):
        return None
    return _rpc(rpc_url, "eth_getTransactionReceipt", [tx_hash])


def _topic_to_address(topic_hex: str) -> str:
    t = (topic_hex or "").lower()
    if t.startswith("0x"):
        t = t[2:]
    return "0x" + t[-40:]


def verify_erc20_transfer(
    receipt: Dict[str, Any],
    token_address: str,
    to_address: str,
    min_amount_base_units: int,
) -> Tuple[bool, str]:
    """Verify that an ERC-20 Transfer(to=to_address) happened for >= min_amount."""
    try:
        token_address = token_address.lower()
        to_address = to_address.lower()
        logs = receipt.get("logs") or []
        for log in logs:
            if (log.get("address") or "").lower() != token_address:
                continue
            topics = log.get("topics") or []
            if len(topics) < 3:
                continue
            if (topics[0] or "").lower() != TRANSFER_TOPIC0:
                continue
            to = _topic_to_address(topics[2])
            if to.lower() != to_address:
                continue
            data_hex = log.get("data") or "0x0"
            val = int(data_hex, 16)
            if val >= int(min_amount_base_units):
                return True, f"Found Transfer(to={to}, amount={val})"
        return False, "No matching Transfer log found (yet)."
    except Exception as e:
        return False, f"Verification error: {e}"


def cast_usdc_transfer_cmd(
    to_address: str,
    amount_usdc: str,
    rpc_url: str = DEFAULT_RPC_URL,
    usdc_erc20: str = DEFAULT_USDC_ERC20,
    usdc_decimals: int = DEFAULT_USDC_DECIMALS,
    private_key_env: str = "$PRIVATE_KEY",
) -> str:
    amount_base = to_base_units(amount_usdc, usdc_decimals)
    return (
        f'cast send {usdc_erc20} "transfer(address,uint256)" {to_address} {amount_base} '
        f'--rpc-url "{rpc_url}" --private-key "{private_key_env}"'
    )


def cast_usdc_approve_cmd(
    spender: str,
    amount_usdc: str,
    rpc_url: str = DEFAULT_RPC_URL,
    usdc_erc20: str = DEFAULT_USDC_ERC20,
    usdc_decimals: int = DEFAULT_USDC_DECIMALS,
    private_key_env: str = "$PRIVATE_KEY",
) -> str:
    amount_base = to_base_units(amount_usdc, usdc_decimals)
    return (
        f'cast send {usdc_erc20} "approve(address,uint256)" {spender} {amount_base} '
        f'--rpc-url "{rpc_url}" --private-key "{private_key_env}"'
    )
