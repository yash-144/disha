"""Documents + anchoring: RBAC, campus tenancy, hashing/verification, lifecycle, disabled-chain behaviour."""
import hashlib
import unittest
from datetime import timedelta

from sqlalchemy import select

from ._harness006 import (ADMIN, ADMIN_C2, C1, COUNSELLOR, FACULTY, OTHER_COUNSELLOR, PDF, STUDENT, Harness)
from app.core.config import settings
from app.modules.documents import chain, storage
from app.modules.documents.anchoring import process_pending_anchors
from app.modules.documents.chain import TxReceipt
from app.modules.documents.models import Document
from app.shared.utils import utc_now

BASE = "/api/v1/documents"


class FakeChain:
    chain_id = 84532

    def __init__(self):
        self.anchors = {}
        self.sent = []
        self.receipt = TxReceipt(True, 77)
        self.receipt_ready = True

    async def submit_anchor(self, h):
        self.sent.append(h)
        self._pending = h
        return "0x" + "ab" * 32

    async def anchor_timestamp(self, h):
        return self.anchors.get(h, 0)

    async def get_receipt(self, tx):
        if not self.receipt_ready:
            return None
        if self.receipt.success:
            self.anchors[self._pending] = 1700000000
        return self.receipt


class DocumentsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.h = Harness()
        await self.h.start()
        self.c = self.h.client

    async def asyncTearDown(self):
        await self.h.stop()

    # ---- hashing / validation -----------------------------------------------------------
    async def test_upload_hashes_bytes_and_stores_draft(self):
        r = await self.h.upload(kind="case_attachment", case_id="case-1")
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertEqual(body["sha256"], hashlib.sha256(PDF).hexdigest())
        self.assertEqual(body["status"], "draft")
        self.assertTrue(body["document_ref"].startswith("DOC-"))
        self.assertEqual(body["size_bytes"], len(PDF))
        self.assertIn("document.uploaded", await self.h.audit_actions(body["id"]))

    async def test_rejects_bad_type_mismatch_oversize_and_empty(self):
        self.assertEqual((await self.h.upload(content_type="application/x-msdownload", data=b"MZ")).status_code, 415)
        self.assertEqual((await self.h.upload(data=b"not a pdf at all")).status_code, 415)  # sniffing
        settings.DISHA_DOCUMENTS_MAX_BYTES = 10
        self.assertEqual((await self.h.upload()).status_code, 413)
        settings.DISHA_DOCUMENTS_MAX_BYTES = 10_000
        self.assertEqual((await self.h.upload(data=b"", content_type="text/plain")).status_code, 422)

    async def test_filename_cannot_escape_storage(self):
        r = await self.h.upload(name="../../etc/passwd.pdf")
        self.assertEqual(r.json()["filename"], "passwd.pdf")
        with self.assertRaises(storage.StorageError):
            storage.LocalDocumentStorage(self.h.tmp.name)._path("../evil")

    # ---- RBAC ---------------------------------------------------------------------------
    async def test_rbac(self):
        self.assertEqual((await self.c.get(BASE)).status_code, 401)
        self.assertEqual((await self.c.get(BASE, headers=STUDENT)).status_code, 403)
        self.assertEqual((await self.h.upload(headers=STUDENT)).status_code, 403)
        doc = (await self.h.upload()).json()
        await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)
        # only institution admins may anchor
        self.assertEqual((await self.c.post(f"{BASE}/{doc['id']}/anchor", headers=COUNSELLOR)).status_code, 403)
        self.assertEqual((await self.c.post(f"{BASE}/{doc['id']}/anchor", headers=FACULTY)).status_code, 403)
        self.assertEqual((await self.c.get(f"{BASE}/anchoring/status", headers=COUNSELLOR)).status_code, 403)
        self.assertEqual((await self.c.get(f"{BASE}/anchoring/status", headers=ADMIN)).status_code, 200)

    async def test_object_level_access_within_campus(self):
        doc = (await self.h.upload(headers=COUNSELLOR)).json()
        self.assertEqual((await self.c.get(f"{BASE}/{doc['id']}", headers=COUNSELLOR)).status_code, 200)
        self.assertEqual((await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).status_code, 200)  # campus-wide role
        self.assertEqual((await self.c.get(f"{BASE}/{doc['id']}", headers=OTHER_COUNSELLOR)).status_code, 403)
        self.assertEqual((await self.c.get(BASE, headers=OTHER_COUNSELLOR)).json(), [])
        # the assigned counsellor sees a faculty member's upload on their case
        fdoc = (await self.h.upload(headers=FACULTY, case_id="case-1")).json()
        self.assertEqual((await self.c.get(f"{BASE}/{fdoc['id']}", headers=COUNSELLOR)).status_code, 200)

    # ---- tenancy ------------------------------------------------------------------------
    async def test_campus_isolation(self):
        doc = (await self.h.upload()).json()
        for method, path in [("get", ""), ("post", "/verify"), ("post", "/finalize"), ("get", "/download"), ("post", "/anchor")]:
            r = await getattr(self.c, method)(f"{BASE}/{doc['id']}{path}", headers=ADMIN_C2)
            self.assertEqual(r.status_code, 404, f"{method} {path}")
        self.assertEqual((await self.c.get(BASE, headers=ADMIN_C2)).json(), [])
        # cannot attach to a case of another campus
        self.assertEqual((await self.h.upload(headers=ADMIN_C2, case_id="case-1")).status_code, 404)
        self.assertEqual((await self.h.upload(case_id="case-2")).status_code, 404)

    # ---- lifecycle / verification -------------------------------------------------------
    async def test_finalize_freezes_and_versions_do_not_modify_original(self):
        doc = (await self.h.upload()).json()
        self.assertEqual((await self.c.post(f"{BASE}/{doc['id']}/versions", headers=COUNSELLOR,
                                            files={"file": ("v2.pdf", PDF + b"x", "application/pdf")})).status_code, 422)  # draft
        fin = await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)
        self.assertEqual(fin.json()["status"], "finalized")
        self.assertEqual((await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)).status_code, 422)
        v2 = await self.c.post(f"{BASE}/{doc['id']}/versions", headers=COUNSELLOR, files={"file": ("v2.pdf", PDF + b"x", "application/pdf")})
        self.assertEqual(v2.status_code, 201)
        self.assertEqual(v2.json()["version"], 2)
        self.assertEqual(v2.json()["previous_version_id"], doc["id"])
        orig = (await self.c.get(f"{BASE}/{doc['id']}", headers=COUNSELLOR)).json()
        self.assertEqual(orig["sha256"], doc["sha256"])

    async def test_verify_ok_then_detects_tampered_bytes(self):
        doc = (await self.h.upload()).json()
        await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)
        ok = (await self.c.post(f"{BASE}/{doc['id']}/verify", headers=COUNSELLOR)).json()
        self.assertTrue(ok["ok"])
        by_name = {c["name"]: c for c in ok["checks"]}
        self.assertTrue(by_name["db_hash_vs_bytes"]["ran"] and by_name["db_hash_vs_bytes"]["ok"])
        self.assertFalse(by_name["chain_record_exists"]["ran"])  # chain not configured: reported, not faked

        async with self.h.session() as s:
            d = (await s.execute(select(Document).where(Document.id == doc["id"]))).scalar_one()
            key = d.storage_key
        (storage.LocalDocumentStorage(self.h.tmp.name)._path(key)).write_bytes(PDF + b" tampered")
        bad = (await self.c.post(f"{BASE}/{doc['id']}/verify", headers=COUNSELLOR)).json()
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["status"], "verification_mismatch")
        self.assertEqual((await self.c.get(f"{BASE}/{doc['id']}/download", headers=COUNSELLOR)).status_code, 409)

    async def test_download_returns_exact_bytes_with_hash(self):
        doc = (await self.h.upload()).json()
        r = await self.c.get(f"{BASE}/{doc['id']}/download", headers=COUNSELLOR)
        self.assertEqual(r.content, PDF)
        self.assertEqual(r.headers["x-content-sha256"], doc["sha256"])
        u = (await self.c.get(f"{BASE}/{doc['id']}/download-url", headers=COUNSELLOR)).json()
        self.assertEqual(u["kind"], "api")

    # ---- anchoring disabled -------------------------------------------------------------
    async def test_anchor_disabled_returns_503_and_never_marks_anchored(self):
        settings.DISHA_BLOCKCHAIN_RPC_URL = ""
        doc = (await self.h.upload()).json()
        await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)
        st = (await self.c.get(f"{BASE}/anchoring/status", headers=ADMIN)).json()
        self.assertFalse(st["enabled"])
        self.assertIn("DISHA_BLOCKCHAIN_RPC_URL", st["missing"])
        r = await self.c.post(f"{BASE}/{doc['id']}/anchor", headers=ADMIN)
        self.assertEqual(r.status_code, 503)
        self.assertIn("not anchored", r.json()["detail"])
        after = (await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).json()
        self.assertEqual(after["status"], "finalized")
        self.assertIsNone(after["anchored_at"])
        self.assertIsNone(after["anchor_tx_hash"])

    async def test_worker_job_is_a_noop_when_not_configured(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "worker"))
        from jobs.anchor_confirmation import run_anchor_confirmation
        stats = await run_anchor_confirmation()
        self.assertEqual(stats, {"anchoring": "not_configured", "identity": "not_configured"})

    # ---- anchoring enabled (fake chain) -------------------------------------------------
    async def _pending_doc(self, fake):
        chain.set_chain_client_factory(lambda: fake)
        doc = (await self.h.upload()).json()
        await self.c.post(f"{BASE}/{doc['id']}/finalize", headers=COUNSELLOR)
        r = await self.c.post(f"{BASE}/{doc['id']}/anchor", headers=ADMIN)
        self.assertEqual(r.status_code, 202, r.text)
        self.assertEqual(r.json()["status"], "anchor_pending")
        return doc

    async def test_anchor_flow_submit_confirm_and_verify_against_chain(self):
        fake = FakeChain()
        doc = await self._pending_doc(fake)
        async with self.h.session() as s:
            self.assertEqual((await process_pending_anchors(s, fake))["submitted"], 1)
        self.assertEqual(fake.sent, [doc["sha256"]])
        cur = (await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).json()
        self.assertEqual(cur["status"], "anchor_pending")  # tx submitted, not yet confirmed
        async with self.h.session() as s:
            self.assertEqual((await process_pending_anchors(s, fake))["anchored"], 1)
        cur = (await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).json()
        self.assertEqual(cur["status"], "anchored")
        self.assertEqual(cur["anchor_block_number"], 77)
        self.assertIsNotNone(cur["anchored_at"])
        v = (await self.c.post(f"{BASE}/{doc['id']}/verify", headers=ADMIN)).json()
        self.assertTrue(v["ok"])
        self.assertTrue(all(c["ran"] for c in v["checks"]))

    async def test_pending_stays_pending_without_receipt_then_times_out(self):
        fake = FakeChain()
        fake.receipt_ready = False
        doc = await self._pending_doc(fake)
        async with self.h.session() as s:
            await process_pending_anchors(s, fake)
            self.assertEqual((await process_pending_anchors(s, fake))["waiting"], 1)
        async with self.h.session() as s:
            d = (await s.execute(select(Document).where(Document.id == doc["id"]))).scalar_one()
            d.anchor_submitted_at = utc_now() - timedelta(seconds=settings.DISHA_ANCHOR_CONFIRM_TIMEOUT_SECONDS + 5)
            await s.commit()
            self.assertEqual((await process_pending_anchors(s, fake))["failed"], 1)
        cur = (await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).json()
        self.assertEqual(cur["status"], "anchor_failed")
        self.assertIsNone(cur["anchored_at"])

    async def test_reverted_tx_is_anchor_failed_and_retryable(self):
        fake = FakeChain()
        fake.receipt = TxReceipt(False, 5)
        doc = await self._pending_doc(fake)
        async with self.h.session() as s:
            await process_pending_anchors(s, fake)
            self.assertEqual((await process_pending_anchors(s, fake))["failed"], 1)
        self.assertEqual((await self.c.get(f"{BASE}/{doc['id']}", headers=ADMIN)).json()["status"], "anchor_failed")
        r = await self.c.post(f"{BASE}/{doc['id']}/anchor", headers=ADMIN)  # retry allowed
        self.assertEqual(r.json()["status"], "anchor_pending")


if __name__ == "__main__":
    unittest.main()
