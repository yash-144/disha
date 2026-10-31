"""Chain access for anchoring and identity minting, using contracts/src (DishaDocumentRegistry,
DishaStudentIdentityNFT). The client is built only when RPC URL, signing key and the relevant contract
address are all configured; otherwise `get_chain_client()` returns None and callers must report the
feature as not configured. Nothing here ever fabricates a transaction or receipt.

All web3 I/O is blocking, so every call runs in a thread (DOC-05).
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from app.core.config import settings

logger = logging.getLogger("disha.chain")

ZERO_ADDRESS = "0x" + "0" * 40
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Minimal ABIs taken from contracts/src/*.sol
REGISTRY_ABI = [
    {"type": "function", "name": "anchorDocument", "stateMutability": "nonpayable",
     "inputs": [{"name": "documentHash", "type": "bytes32"}], "outputs": []},
    {"type": "function", "name": "documentAnchors", "stateMutability": "view",
     "inputs": [{"name": "", "type": "bytes32"}], "outputs": [{"name": "", "type": "uint256"}]},
]
IDENTITY_ABI = [
    {"type": "function", "name": "mintIdentity", "stateMutability": "nonpayable",
     "inputs": [{"name": "dishaIdHash", "type": "bytes32"}, {"name": "studentAddress", "type": "address"}],
     "outputs": []},
    {"type": "function", "name": "identityOwners", "stateMutability": "view",
     "inputs": [{"name": "", "type": "bytes32"}], "outputs": [{"name": "", "type": "address"}]},
]


@dataclass
class TxReceipt:
    success: bool
    block_number: int


class ChainClient(Protocol):
    chain_id: int

    async def submit_anchor(self, sha256_hex: str) -> str: ...

    async def anchor_timestamp(self, sha256_hex: str) -> int: ...

    async def submit_mint(self, id_hash_hex: str, wallet: str) -> str: ...

    async def identity_owner(self, id_hash_hex: str) -> str: ...

    async def get_receipt(self, tx_hash: str) -> Optional[TxReceipt]: ...


def is_address(value: Optional[str]) -> bool:
    return bool(value and _ADDR_RE.match(value) and value.lower() != ZERO_ADDRESS)


def _base_missing() -> list:
    missing = []
    if not settings.DISHA_BLOCKCHAIN_RPC_URL:
        missing.append("DISHA_BLOCKCHAIN_RPC_URL")
    if not settings.DISHA_ANCHOR_PRIVATE_KEY:
        missing.append("DISHA_ANCHOR_PRIVATE_KEY")
    return missing


def anchoring_missing_settings() -> list:
    missing = _base_missing()
    if not is_address(settings.DISHA_DOCUMENT_REGISTRY_ADDRESS):
        missing.append("DISHA_DOCUMENT_REGISTRY_ADDRESS")
    return missing


def identity_missing_settings() -> list:
    missing = _base_missing()
    if not is_address(settings.DISHA_IDENTITY_NFT_ADDRESS):
        missing.append("DISHA_IDENTITY_NFT_ADDRESS")
    return missing


def not_configured_message(feature: str, missing: list) -> str:
    return f"{feature} is not configured (missing: {', '.join(missing)})."


def to_bytes32(hex_str: str) -> bytes:
    raw = bytes.fromhex(hex_str)
    if len(raw) != 32:
        raise ValueError("expected a 32-byte hex digest")
    return raw


class Web3ChainClient:
    """web3.py implementation (pip install -e 'api[chain]')."""

    def __init__(self):
        from web3 import Web3  # type: ignore

        self._w3 = Web3(Web3.HTTPProvider(settings.DISHA_BLOCKCHAIN_RPC_URL, request_kwargs={"timeout": 20}))
        self._account = self._w3.eth.account.from_key(settings.DISHA_ANCHOR_PRIVATE_KEY)
        self.chain_id = settings.DISHA_BLOCKCHAIN_CHAIN_ID
        self._registry = (
            self._w3.eth.contract(address=Web3.to_checksum_address(settings.DISHA_DOCUMENT_REGISTRY_ADDRESS), abi=REGISTRY_ABI)
            if is_address(settings.DISHA_DOCUMENT_REGISTRY_ADDRESS) else None
        )
        self._identity = (
            self._w3.eth.contract(address=Web3.to_checksum_address(settings.DISHA_IDENTITY_NFT_ADDRESS), abi=IDENTITY_ABI)
            if is_address(settings.DISHA_IDENTITY_NFT_ADDRESS) else None
        )

    def _send(self, fn) -> str:
        tx = fn.build_transaction({
            "from": self._account.address,
            "nonce": self._w3.eth.get_transaction_count(self._account.address, "pending"),
            "chainId": self.chain_id,
        })
        signed = self._account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        return self._w3.eth.send_raw_transaction(raw).hex()

    async def submit_anchor(self, sha256_hex: str) -> str:
        return await asyncio.to_thread(lambda: self._send(self._registry.functions.anchorDocument(to_bytes32(sha256_hex))))

    async def anchor_timestamp(self, sha256_hex: str) -> int:
        return int(await asyncio.to_thread(lambda: self._registry.functions.documentAnchors(to_bytes32(sha256_hex)).call()))

    async def submit_mint(self, id_hash_hex: str, wallet: str) -> str:
        from web3 import Web3  # type: ignore

        return await asyncio.to_thread(
            lambda: self._send(self._identity.functions.mintIdentity(to_bytes32(id_hash_hex), Web3.to_checksum_address(wallet)))
        )

    async def identity_owner(self, id_hash_hex: str) -> str:
        return await asyncio.to_thread(lambda: self._identity.functions.identityOwners(to_bytes32(id_hash_hex)).call())

    async def get_receipt(self, tx_hash: str) -> Optional[TxReceipt]:
        def _get():
            try:
                r = self._w3.eth.get_transaction_receipt(tx_hash)
            except Exception:  # TransactionNotFound -> still pending
                return None
            return TxReceipt(success=int(r["status"]) == 1, block_number=int(r["blockNumber"]))

        return await asyncio.to_thread(_get)


_factory_override: Optional[Callable[[], Optional[ChainClient]]] = None


def set_chain_client_factory(factory: Optional[Callable[[], Optional[ChainClient]]]) -> None:
    """Test hook / explicit injection."""
    global _factory_override
    _factory_override = factory


def get_chain_client(feature: str = "anchoring") -> Optional[ChainClient]:
    """Return a ready client, or None when the feature's settings are absent or web3 is missing."""
    if _factory_override is not None:
        return _factory_override()
    missing = anchoring_missing_settings() if feature == "anchoring" else identity_missing_settings()
    if missing:
        return None
    try:
        return Web3ChainClient()
    except ImportError:
        logger.warning("Chain settings present but web3 is not installed (pip install -e 'api[chain]'); %s disabled", feature)
        return None
    except Exception as exc:
        logger.error("Chain client could not be created: %s", exc)
        return None


def feature_status(feature: str) -> dict:
    """Public description of whether anchoring/identity can run. Never contains secrets."""
    missing = anchoring_missing_settings() if feature == "anchoring" else identity_missing_settings()
    if _factory_override is not None:
        return {"enabled": _factory_override() is not None, "missing": []}
    if missing:
        return {"enabled": False, "missing": missing, "message": not_configured_message(feature, missing)}
    try:
        import web3  # type: ignore  # noqa: F401
    except ImportError:
        return {"enabled": False, "missing": ["web3 package"], "message": "web3 is not installed (pip install -e 'api[chain]')"}
    return {"enabled": True, "missing": [], "chain_id": settings.DISHA_BLOCKCHAIN_CHAIN_ID}
