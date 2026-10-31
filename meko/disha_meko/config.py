"""Meko settings, read from MEKO_* environment variables."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

log = logging.getLogger("disha_meko")

DEFAULT_URL = "https://mcp.mekodata.ai/mcp"  # self-hosted: MEKO_MCP_URL=http://localhost:8080/mcp


def _flag(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() not in ("0", "false", "no", "off", "")


@dataclass
class MekoConfig:
    api_key: str = ""
    url: str = DEFAULT_URL
    datapack: str = "disha"
    datapack_id: str = ""  # optional: skip the name -> id lookup
    enabled: bool = True
    # optional overrides, only needed if Meko renames a tool: {"remember": "tool_name"} or {"remember": {"tool": "x", "args": {"text": "content"}}}
    tool_map: dict = field(default_factory=dict)
    pii_salt: str = ""
    promote_min: int = 3  # same intervention + reason codes improving this often -> promote to the playbook
    timeout: float = 8.0  # seconds per Meko call; never block training or requests longer

    @classmethod
    def from_env(cls) -> "MekoConfig":
        raw = os.getenv("MEKO_TOOL_MAP", "").strip()
        tool_map: dict = {}
        if raw:
            try:
                tool_map = json.loads(raw)
            except ValueError:
                log.warning("MEKO_TOOL_MAP is not valid JSON; ignoring it")
        return cls(
            api_key=os.getenv("MEKO_API_KEY", "").strip(),
            url=os.getenv("MEKO_MCP_URL", DEFAULT_URL).strip() or DEFAULT_URL,
            datapack=os.getenv("MEKO_DATAPACK", "disha").strip() or "disha",
            datapack_id=os.getenv("MEKO_DATAPACK_ID", "").strip(),
            enabled=_flag("MEKO_ENABLED", True),
            tool_map=tool_map,
            pii_salt=os.getenv("MEKO_PII_SALT", ""),
            promote_min=int(os.getenv("MEKO_PROMOTE_MIN", "3")),
            timeout=float(os.getenv("MEKO_TIMEOUT", "8")),
        )

    @property
    def active(self) -> bool:
        return self.enabled and bool(self.api_key)
