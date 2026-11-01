"""Point a seeded demo account at a real Google address, so that person signs in with Google and gets its role and data.

    python infra/scripts/link_google_account.py counsellor@demo.disha.edu someone@gmail.com
Demo accounts: admin@, counsellor@, faculty@, student@ (all @demo.disha.edu).
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))
from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402


async def main(demo: str, real: str) -> None:
    async with engine.begin() as c:
        n = (await c.execute(text("update disha_identity set email=:r where email=:d"), {"r": real.lower(), "d": demo.lower()})).rowcount
        await c.execute(text("update disha_roster set email=:r where email=:d"), {"r": real.lower(), "d": demo.lower()})
    print("linked" if n else "no such demo account", real)
    await engine.dispose()


asyncio.run(main(sys.argv[1], sys.argv[2]))
