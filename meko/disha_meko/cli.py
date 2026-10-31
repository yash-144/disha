"""python -m disha_meko {doctor,tools,sync-catalog,recall}"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging

from .client import MekoClient
from .catalog import load_catalog, sync_catalog


async def doctor(client: MekoClient) -> int:
    cfg = client.cfg
    print(f"Meko URL:   {cfg.url}\nDatapack:   {cfg.datapack}")
    print(f"API key:    {'set' if cfg.api_key else 'MISSING (set MEKO_API_KEY)'}   enabled: {cfg.enabled}")
    if not client.active:
        print("Meko is inactive; DISHA runs normally without it.")
        return 1
    tools = await client.list_tools()
    if not tools:
        print(f"Cannot reach Meko: {client.last_error or 'no tools returned'}")
        return 1
    print(f"\nConnected. {len(tools)} tools discovered:")
    for t in tools:
        print(f"  - {t['name']}({', '.join(t['params'])})")
    print("\nLogical operation -> tool (exact defaults; override with MEKO_TOOL_MAP):")
    for op, name in (await client.mapping()).items():
        print(f"  {op:18} -> {name or 'NOT MAPPED'}")
    ready = await client.ensure_datapack()
    print(f"\nDatapack '{cfg.datapack}' ready: {ready}" + (f" (id {client.datapack_id})" if ready else ""))
    return 0


async def amain(args) -> int:
    client = MekoClient(component="disha-cli")
    if args.cmd == "doctor":
        return await doctor(client)
    if args.cmd == "tools":
        print(json.dumps(await client.list_tools(), indent=2))
    elif args.cmd == "recall":
        print(await client.recall(args.query, args.k) or "(nothing recalled)")
    elif args.cmd == "sync-catalog":
        entries = load_catalog(args.path)
        if not entries:
            print(f"No interventions found in {args.path}")
            return 1
        await client.ensure_datapack()
        print(json.dumps(await sync_catalog(client, entries, args.campus), indent=2))
    return 0


def main(argv=None) -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="disha_meko", description="DISHA <-> Meko tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check connection, list tools and the operation mapping")
    sub.add_parser("tools", help="print discovered Meko tools as JSON")
    s = sub.add_parser("sync-catalog", help="upload the campus intervention catalogue (one document each)")
    s.add_argument("path", help="catalogue JSON file")
    s.add_argument("--campus", default="default")
    r = sub.add_parser("recall", help="search Meko memory")
    r.add_argument("query")
    r.add_argument("-k", type=int, default=5)
    raise SystemExit(asyncio.run(amain(ap.parse_args(argv))))
