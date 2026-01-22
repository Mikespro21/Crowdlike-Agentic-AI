from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from crowdlike.tools import is_address


@dataclass
class SuggestedAction:
    tool: str
    params: Dict[str, Any]
    label: str


@dataclass
class AgentReply:
    message: str
    plan: List[str]
    actions: List[SuggestedAction]


def _extract_first_address(text: str) -> Optional[str]:
    parts = (text or "").replace(",", " ").split()
    for p in parts:
        if is_address(p):
            return p
    return None


def respond(user_text: str, context: Dict[str, Any]) -> AgentReply:
    """
    Rule-based placeholder agent.
    Later this becomes Gemini function calling using the SAME tool names.
    """
    t = (user_text or "").strip()
    t_low = t.lower()

    rpc = context.get("rpc_url", "https://rpc.testnet.arc.network")
    merchant = context.get("merchant_address", "") or _extract_first_address(t) or ""
    hello = context.get("hello_address", "")

    actions: List[SuggestedAction] = [
        SuggestedAction("ping_rpc", {"rpc_url": rpc}, "Ping RPC (chainId)")
    ]

    if any(k in t_low for k in ["balance", "fund", "how much", "have usdc"]):
        plan = [
            "Paste a wallet address.",
            "Read USDC balance via Arc USDC interface.",
            "If low, use faucet and retry.",
        ]
        addr = _extract_first_address(t) or ""
        if addr:
            actions.append(
                SuggestedAction(
                    "read_usdc_balance",
                    {"rpc_url": rpc, "address": addr},
                    "Check USDC balance for provided address",
                )
            )
        return AgentReply(
            message="Paste a wallet address (0x...) and I’ll check its USDC balance on Arc testnet.",
            plan=plan,
            actions=actions,
        )

    if any(k in t_low for k in ["pay", "transfer", "unlock", "micropay"]):
        plan = [
            "Pick a merchant address (can be your own wallet for demo).",
            "Choose an amount (e.g., 0.10 USDC).",
            "Generate a safe `cast send transfer(...)` command.",
            "Run it locally, then paste tx hash for ArcScan proof.",
        ]
        actions.append(
            SuggestedAction(
                "prepare_usdc_transfer_command",
                {"rpc_url": rpc, "to_address": merchant, "amount_usdc": "0.10"},
                "Generate USDC transfer command (0.10)",
            )
        )
        msg = "Let’s do a pay-to-unlock demo. I’ll generate a safe command you run locally (no keys in the app)."
        if not merchant:
            msg += " Paste a merchant address (0x...) so I can fill it in."
        return AgentReply(message=msg, plan=plan, actions=actions)

    if any(k in t_low for k in ["tx", "hash", "arcscan"]):
        plan = ["Paste the tx hash.", "Generate an ArcScan link for proof."]
        actions.append(
            SuggestedAction(
                "arcscan_tx_link",
                {"tx_hash": ""},
                "Generate ArcScan link from tx hash",
            )
        )
        return AgentReply(
            message="Paste your transaction hash (0x...) and I’ll generate the ArcScan link.",
            plan=plan,
            actions=actions,
        )

    plan = [
        "Confirm Arc connectivity (chainId).",
        "Prepare a USDC transfer command (manual).",
        "Paste tx hash and generate ArcScan proof link.",
    ]
    if hello:
        plan.append("Optionally call HelloArchitect after payment (later).")

    return AgentReply(
        message=(
            "I’m the placeholder agent. Try:\n"
            "• `pay 0.10 usdc to unlock`\n"
            "• `check balance 0x...`\n"
            "• `tx 0x...`"
        ),
        plan=plan,
        actions=actions,
    )
