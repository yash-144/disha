"""Student identity collectible: disabled state, RBAC, wallet-ownership proof, mint flow, public-data privacy."""
import re
import unittest

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy import select

from ._harness006 import (ADMIN, COUNSELLOR, STUDENT, STUDENT_EMAIL, STUDENT_NAME, STUDENT_UID, Harness, hdr)
from app.modules.documents import chain
from app.modules.documents.chain import TxReceipt
from app.modules.student_identity.models import StudentIdentity
from app.modules.student_identity.services import process_pending_mints

BASE = "/api/v1/student-identity"


class FakeChain:
    chain_id = 84532

    def __init__(self):
        self.owners = {}
        self.pending = None

    async def submit_mint(self, h, wallet):
        self.pending = (h, wallet)
        return "0x" + "cd" * 32

    async def identity_owner(self, h):
        return self.owners.get(h, chain.ZERO_ADDRESS)

    async def get_receipt(self, tx):
        h, wallet = self.pending
        self.owners[h] = wallet
        return TxReceipt(True, 12)


class IdentityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.h = Harness()
        await self.h.start()
        self.c = self.h.client
        self.acct = Account.create()

    async def asyncTearDown(self):
        await self.h.stop()

    def enable(self):
        self.fake = FakeChain()
        chain.set_chain_client_factory(lambda: self.fake)

    async def _linked_wallet(self, acct=None):
        acct = acct or self.acct
        await self.c.post(f"{BASE}/me/issue", headers=STUDENT)
        ch = (await self.c.post(f"{BASE}/me/wallet/challenge", headers=STUDENT, json={"address": acct.address})).json()
        sig = acct.sign_message(encode_defunct(text=ch["message"])).signature.hex()
        return ch, sig

    # ---- disabled -----------------------------------------------------------------------
    async def test_disabled_without_chain_config(self):
        st = (await self.c.get(f"{BASE}/status", headers=STUDENT)).json()
        self.assertFalse(st["enabled"])
        self.assertIn("DISHA_IDENTITY_NFT_ADDRESS", st["missing"])
        for method, path in [("post", "/me/issue"), ("get", "/me"), ("post", "/me/mint")]:
            r = await getattr(self.c, method)(f"{BASE}{path}", headers=STUDENT)
            self.assertEqual(r.status_code, 503, path)
            self.assertIn("disabled", r.json()["detail"])
        async with self.h.session() as s:
            self.assertEqual((await s.execute(select(StudentIdentity))).scalars().all(), [])

    # ---- RBAC ---------------------------------------------------------------------------
    async def test_only_linked_students_can_use_it(self):
        self.enable()
        self.assertEqual((await self.c.post(f"{BASE}/me/issue")).status_code, 401)
        for hd in (COUNSELLOR, ADMIN):
            self.assertEqual((await self.c.post(f"{BASE}/me/issue", headers=hd)).status_code, 403)
        unlinked = hdr("u-nolink", "student")
        self.assertEqual((await self.c.post(f"{BASE}/me/issue", headers=unlinked)).status_code, 403)
        self.assertEqual((await self.c.post(f"{BASE}/me/issue", headers=hdr(STUDENT["X-Test-User"], "student", "campus-2"))).status_code, 403)

    async def test_issue_is_idempotent_and_hides_seed(self):
        self.enable()
        a = await self.c.post(f"{BASE}/me/issue", headers=STUDENT)
        b = await self.c.post(f"{BASE}/me/issue", headers=STUDENT)
        self.assertEqual((a.status_code, b.status_code), (201, 200))
        self.assertEqual(a.json()["disha_id"], b.json()["disha_id"])
        self.assertRegex(a.json()["disha_id"], r"^DISHA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
        self.assertNotIn("art_seed", a.text)

    # ---- wallet ownership ---------------------------------------------------------------
    async def test_mint_requires_proven_wallet(self):
        self.enable()
        await self.c.post(f"{BASE}/me/issue", headers=STUDENT)
        self.assertEqual((await self.c.post(f"{BASE}/me/mint", headers=STUDENT)).status_code, 409)

    async def test_signature_must_come_from_claimed_address(self):
        self.enable()
        ch, _ = await self._linked_wallet()
        impostor = Account.create()
        bad_sig = impostor.sign_message(encode_defunct(text=ch["message"])).signature.hex()
        r = await self.c.post(f"{BASE}/me/wallet/verify", headers=STUDENT, json={"challenge_id": ch["challenge_id"], "signature": bad_sig})
        self.assertEqual(r.status_code, 403)
        self.assertEqual((await self.c.post(f"{BASE}/me/mint", headers=STUDENT)).status_code, 409)

    async def test_challenge_single_use_and_bad_address(self):
        self.enable()
        ch, sig = await self._linked_wallet()
        ok = await self.c.post(f"{BASE}/me/wallet/verify", headers=STUDENT, json={"challenge_id": ch["challenge_id"], "signature": sig})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["wallet_address"], self.acct.address)
        again = await self.c.post(f"{BASE}/me/wallet/verify", headers=STUDENT, json={"challenge_id": ch["challenge_id"], "signature": sig})
        self.assertEqual(again.status_code, 409)
        r = await self.c.post(f"{BASE}/me/wallet/challenge", headers=STUDENT, json={"address": "0x" + "z" * 40})
        self.assertEqual(r.status_code, 422)

    # ---- mint ---------------------------------------------------------------------------
    async def test_full_mint_flow_one_mint_per_identity(self):
        self.enable()
        ch, sig = await self._linked_wallet()
        await self.c.post(f"{BASE}/me/wallet/verify", headers=STUDENT, json={"challenge_id": ch["challenge_id"], "signature": sig})
        r = await self.c.post(f"{BASE}/me/mint", headers=STUDENT)
        self.assertEqual((r.status_code, r.json()["status"]), (202, "mint_pending"))
        self.assertEqual((await self.c.post(f"{BASE}/me/mint", headers=STUDENT)).status_code, 422)  # one mint only
        async with self.h.session() as s:
            self.assertEqual((await process_pending_mints(s, self.fake))["submitted"], 1)
        self.assertEqual((await self.c.get(f"{BASE}/me", headers=STUDENT)).json()["status"], "mint_pending")  # unconfirmed
        async with self.h.session() as s:
            self.assertEqual((await process_pending_mints(s, self.fake))["minted"], 1)
        me = (await self.c.get(f"{BASE}/me", headers=STUDENT)).json()
        self.assertEqual((me["status"], me["mint_block_number"]), ("minted", 12))
        self.assertEqual((await self.c.post(f"{BASE}/me/mint", headers=STUDENT)).status_code, 422)

    # ---- public data ----------------------------------------------------------------------
    async def test_public_endpoints_leak_no_pii_or_seed(self):
        self.enable()
        disha_id = (await self.c.post(f"{BASE}/me/issue", headers=STUDENT)).json()["disha_id"]
        meta = await self.c.get(f"{BASE}/public/{disha_id}/metadata")  # no auth header
        art = await self.c.get(f"{BASE}/public/{disha_id}/art.svg")
        self.assertEqual((meta.status_code, art.status_code), (200, 200))
        self.assertEqual(art.headers["content-type"], "image/svg+xml")
        async with self.h.session() as s:
            seed = (await s.execute(select(StudentIdentity))).scalar_one().art_seed
        blob = meta.text + art.text
        for secret in (STUDENT_NAME, "Aarav", "Sharma", STUDENT_EMAIL, STUDENT_UID, "stu-1", "campus-1", seed):
            self.assertNotIn(secret, blob)
        self.assertEqual((await self.c.get(f"{BASE}/public/DISHA-AAAA-BBBB-CCCC/metadata")).status_code, 404)
        self.assertEqual((await self.c.get(f"{BASE}/public/not-an-id/art.svg")).status_code, 404)
        self.assertIsNone(re.search(r"<script|href=", art.text))


if __name__ == "__main__":
    unittest.main()
