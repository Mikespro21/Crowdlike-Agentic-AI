from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from web3 import Web3

from crowdlike.arc_client import ArcClient, USDC_ERC20_INTERFACE, to_base_units

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_address(s: str) -> bool:
    return bool(ADDRESS_RE.match((s or "").strip()))


def checksum(s: str) -> str:
    return Web3.to_checksum_address(s.strip())


@dataclass
class ToolResult:
    ok: bool
    title: str
    data: Dict[str, Any]
    error: Optional[str] = None


def tool_ping_rpc(rpc_url: str) -> ToolResult:
    try:
        client = ArcClient(rpc_url=rpc_url)
        cid = client.chain_id()
        return ToolResult(True, "RPC Ping", {"chain_id": cid, "expected": 5042002})
    except Exception as e:
        return ToolResult(False, "RPC Ping", {}, error=str(e))


def tool_read_usdc_balance(rpc_url: str, address: str) -> ToolResult:
    try:
        if not is_address(address):
            return ToolResult(False, "USDC Balance", {}, error="Invalid address format.")
        client = ArcClient(rpc_url=rpc_url)
        dec = client.usdc_decimals()
        bal = client.usdc_balance(address)
        return ToolResult(
            True,
            "USDC Balance",
            {
                "address": checksum(address),
                "decimals": dec,
                "balance_raw": bal,
                "balance": bal / (10**dec),
            },
        )
    except Exception as e:
        return ToolResult(False, "USDC Balance", {}, error=str(e))


def tool_prepare_usdc_transfer_command(rpc_url: str, to_address: str, amount_usdc: str) -> ToolResult:
    """
    Generates a SAFE command you run locally. No keys in the app.
    """
    try:
        if not is_address(to_address):
            return ToolResult(False, "Prepare USDC Transfer", {}, error="Invalid merchant address.")
        client = ArcClient(rpc_url=rpc_url)
        dec = client.usdc_decimals()
        base_units = to_base_units(amount_usdc, dec)

        cmd = (
            f'cast send {USDC_ERC20_INTERFACE} "transfer(address,uint256)" {checksum(to_address)} {base_units} '
            f'--rpc-url "{rpc_url}" --private-key "$PRIVATE_KEY"'
        )

        return ToolResult(
            True,
            "Prepare USDC Transfer",
            {
                "to": checksum(to_address),
                "amount_usdc": amount_usdc,
                "decimals": dec,
                "base_units": base_units,
                "command": cmd,
                "usdc_contract": str(USDC_ERC20_INTERFACE),
                "tx_hint": "Run the command locally. Then paste the tx hash here to generate an ArcScan link.",
            },
        )
    except Exception as e:
        return ToolResult(False, "Prepare USDC Transfer", {}, error=str(e))


def tool_arcscan_tx_link(tx_hash: str) -> ToolResult:
    tx = (tx_hash or "").strip()
    if not tx:
        return ToolResult(False, "ArcScan Tx Link", {}, error="No tx hash provided.")
    if not re.match(r"^0x[a-fA-F0-9]{64}$", tx):
        return ToolResult(False, "ArcScan Tx Link", {}, error="Tx hash should look like 0x + 64 hex chars.")
    return ToolResult(True, "ArcScan Tx Link", {"tx_hash": tx, "url": f"https://testnet.arcscan.app/tx/{tx}"})


def tool_arcscan_address_link(address: str) -> ToolResult:
    addr = (address or "").strip()
    if not is_address(addr):
        return ToolResult(False, "ArcScan Address Link", {}, error="Invalid address.")
    addr = checksum(addr)
    return ToolResult(True, "ArcScan Address Link", {"address": addr, "url": f"https://testnet.arcscan.app/address/{addr}"})
