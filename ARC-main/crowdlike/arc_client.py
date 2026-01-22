from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any, Optional

try:
    from web3 import Web3  # type: ignore
except Exception:  # pragma: no cover
    Web3 = None  # type: ignore



USDC_ERC20_INTERFACE = "0x3600000000000000000000000000000000000000"  # Arc testnet USDC ERC-20 interface

ERC20_ABI: list[dict[str, Any]] = [
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bool"}],
    },
]


def to_base_units(amount: str, decimals: int) -> int:
    """
    "0.10" -> 100000 (if decimals=6)
    """
    q = Decimal(10) ** -decimals
    d = Decimal(amount).quantize(q, rounding=ROUND_DOWN)
    return int(d * (10**decimals))


@dataclass
class ArcClient:

    rpc_url: str

    def __post_init__(self) -> None:
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

    def chain_id(self) -> int:
        return int(self.w3.eth.chain_id)

    def native_usdc_balance_18(self, address: str) -> int:
        """
        Native USDC balance (gas token) uses 18 decimals of precision on Arc. 
        """
        return int(self.w3.eth.get_balance(Web3.to_checksum_address(address)))

    def usdc_contract(self):
        return self.w3.eth.contract(address=Web3.to_checksum_address(USDC_ERC20_INTERFACE), abi=ERC20_ABI)

    def usdc_decimals(self) -> int:
        return int(self.usdc_contract().functions.decimals().call())

    def usdc_balance(self, address: str) -> int:
        """
        USDC ERC-20 interface balance uses 6 decimals. 
        """
        return int(self.usdc_contract().functions.balanceOf(Web3.to_checksum_address(address)).call())

    def send_usdc_transfer_demo_signer(self, to_addr: str, amount_str: str, private_key: str) -> str:
        """
        Optional: sends tx using a demo private key (testnet only). Keep the key in Streamlit secrets.
        """
        pk = private_key.strip()
        if not pk:
            raise ValueError("Empty private key.")
        if not pk.startswith("0x"):
            pk = "0x" + pk

        acct = self.w3.eth.account.from_key(pk)
        from_addr = acct.address

        usdc = self.usdc_contract()
        dec = self.usdc_decimals()
        amount = to_base_units(amount_str, dec)

        nonce = self.w3.eth.get_transaction_count(from_addr)
        tx = usdc.functions.transfer(Web3.to_checksum_address(to_addr), amount).build_transaction(
            {
                "from": from_addr,
                "nonce": nonce,
                "maxFeePerGas": self.w3.eth.gas_price,
                "maxPriorityFeePerGas": 0,
            }
        )

        # estimate gas (fallback if estimate fails)
        try:
            tx["gas"] = self.w3.eth.estimate_gas(tx)
        except Exception:
            tx["gas"] = 200_000

        signed = self.w3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash.hex()
