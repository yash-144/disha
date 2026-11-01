"""Ingestion -> scoring -> insights, end to end on a small trained bundle and canonical tables built in the test.

The tables and the bundle are test fixtures only (ml/tests/rolling_fixtures.py generates them); nothing in the
production code path produces data.
"""
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import httpx
import pandas as pd
from fastapi import FastAPI, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.dependencies import TenancyContext, get_tenancy_context
from app.core.exceptions import register_exception_handlers
from app.core.permissions import Role
from app.modules.audit.models import AuditEvent
from app.modules.ingestion import models as ing_models  # noqa: F401  (register tables)
from app.modules.ingestion.models import BATCH_COMMITTED, BATCH_SUPERSEDED, ImportBatch
from app.modules.ingestion.routes import router as ingestion_router
from app.modules.ml import models as ml_models  # noqa: F401
from app.modules.ml import jobs, services
from app.modules.ml.routes import router as ml_router
from app.modules.ml.schemas import RiskFlag
from app.modules.roster.models import Student
from app.modules.campus.models import CampusEntity
from app.shared.utils import utc_now

REPO = Path(__file__).resolve().parents[3]
LONG_AGO = "2020-01-06"


def _load_fixtures():
    spec = importlib.util.spec_from_file_location("rolling_fixtures", REPO / "ml" / "tests" / "rolling_fixtures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIX = _load_fixtures()
_BUNDLE_DIR = None


def bundle_dir() -> str:
    """Train a tiny bundle once per test process (test-only; production never trains)."""
    global _BUNDLE_DIR
    if _BUNDLE_DIR is None:
        from disha_ml.rolling import train
        from disha_ml.rolling.config import RollingConfig
        from disha_ml.rolling.schema import save_tables
        d = Path(tempfile.mkdtemp(prefix="disha-bundle-"))
        save_tables(FIX.make_tables(n=200), d / "tables")
        train.run(str(d / "tables"), str(d / "art"), RollingConfig(train_terms=("T1",), test_terms=("T2",), cv_folds=3))
        _BUNDLE_DIR = str(d / "art")
    return _BUNDLE_DIR


def term_tables(term="T2", term_start=LONG_AGO, max_day=None):
    """Canonical tables of one term (rows are what a college export would contain)."""
    t = {k: v.copy() for k, v in FIX.make_tables(n=200).items()}
    t["enrolments"] = t["enrolments"][t["enrolments"].term_id == term].copy()
    t["enrolments"]["term_start"] = term_start
    t["assessments"] = t["assessments"][t["assessments"].term_id == term]
    t["results"] = t["results"][t["results"].assessment_id.isin(t["assessments"].assessment_id)]
    t["activity"] = t["activity"][t["activity"].term_id == term]
    t["withdrawals"] = t["withdrawals"][t["withdrawals"].term_id == term]
    t["students"] = t["students"][t["students"].student_id.isin(t["enrolments"].student_id)]
    if max_day is not None:
        t["results"] = t["results"][t["results"].submitted_day <= max_day]
        t["activity"] = t["activity"][t["activity"].day <= max_day]
        t["withdrawals"] = t["withdrawals"][t["withdrawals"].day <= max_day]
    return t


def csv_files(tables):
    return {name: (f"{name}.csv", df.to_csv(index=False).encode(), "text/csv") for name, df in tables.items()
            if name in ("students", "enrolments", "assessments", "results", "activity", "withdrawals")}


class PipelineCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dbfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.dbfile.close()
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{self.dbfile.name}")
        self.sessions = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(ingestion_router, prefix="/api/v1/ingestion")
        app.include_router(ml_router, prefix="/api/v1/ml")

        async def _db():
            async with self.sessions() as s:
                yield s

        def _ctx(request: Request) -> TenancyContext:
            role = Role(request.headers.get("X-Test-Role", "institution_admin"))
            return TenancyContext(user_id=f"user-{role.value}", email="t@test.local",
                                  campus_id=request.headers.get("X-Campus-ID", "campus-a"), role=role)

        app.dependency_overrides[get_db] = _db
        app.dependency_overrides[get_tenancy_context] = _ctx
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        self._patches = [mock.patch.object(settings, "DISHA_ML_BUNDLE_PATH", bundle_dir()),
                         mock.patch.object(settings, "DISHA_ML_MEKO_HOOKS", False)]
        for p in self._patches:
            p.start()

    async def asyncTearDown(self):
        for p in self._patches:
            p.stop()
        await self.client.aclose()
        await self.engine.dispose()
        os.unlink(self.dbfile.name)

    def h(self, role="institution_admin", campus="campus-a"):
        return {"X-Test-Role": role, "X-Campus-ID": campus}

    async def upload(self, tables=None, campus="campus-a", role="institution_admin", **params):
        return await self.client.post("/api/v1/ingestion/imports", files=csv_files(tables or term_tables()),
                                      params=params, headers=self.h(role, campus))


class TestIngestion(PipelineCase):
    async def test_commit_stores_rows_links_roster_and_audits(self):
        t = term_tables()
        ref = t["enrolments"].student_id.iloc[0]
        async with self.sessions() as s:
            s.add(CampusEntity(id="campus-a", created_at=utc_now()))
            s.add(Student(id="roster-1", campus_id="campus-a", student_uid=ref, full_name="Test Student"))
            await s.commit()
        r = await self.upload(t)
        self.assertEqual(r.status_code, 201, r.text)
        b = r.json()
        self.assertEqual(b["status"], BATCH_COMMITTED)
        self.assertEqual(b["row_counts"]["enrolments"], len(t["enrolments"]))
        self.assertEqual((b["linked_students"], b["unlinked_students"]), (1, len(t["enrolments"]) - 1))
        self.assertEqual(len(b["file_sha256"]), 64)
        self.assertEqual(b["uploaded_by"], "user-institution_admin")
        async with self.sessions() as s:
            ev = (await s.execute(select(AuditEvent).where(AuditEvent.entity_id == b["id"]))).scalars().all()
        self.assertEqual([e.action for e in ev], ["ingestion.import.committed"])

    async def test_identical_upload_is_idempotent_and_new_upload_supersedes(self):
        t = term_tables()
        first = (await self.upload(t)).json()
        again = await self.upload(t)
        self.assertEqual(again.status_code, 200)
        self.assertTrue(again.json()["duplicate"])
        self.assertEqual(again.json()["id"], first["id"])
        t2 = term_tables()
        t2["results"] = t2["results"].iloc[:-1]
        second = (await self.upload(t2)).json()
        self.assertNotEqual(second["id"], first["id"])
        async with self.sessions() as s:
            st = {b.id: b.status for b in (await s.execute(select(ImportBatch))).scalars().all()}
        self.assertEqual(st[first["id"]], BATCH_SUPERSEDED)
        self.assertEqual(st[second["id"]], BATCH_COMMITTED)

    async def test_validation_errors_are_reported_and_recorded(self):
        t = term_tables()
        bad = {k: v.copy() for k, v in t.items()}
        bad["results"].loc[bad["results"].index[0], "assessment_id"] = "NOPE"
        bad["activity"].loc[bad["activity"].index[0], "student_id"] = "ghost"
        r = await self.upload(bad)
        self.assertEqual(r.status_code, 422)
        codes = {e["code"] for e in r.json()["validation_errors"]}
        self.assertEqual(codes, {"UNKNOWN_ASSESSMENT", "UNKNOWN_ENROLMENT"})
        self.assertEqual(r.json()["status"], "rejected")
        # nothing stored, attempt recorded and audited
        async with self.sessions() as s:
            self.assertEqual(len((await s.execute(select(ing_models.MlEnrolment))).scalars().all()), 0)
            ev = (await s.execute(select(AuditEvent))).scalars().all()
        self.assertEqual([e.action for e in ev], ["ingestion.import.rejected"])

    async def test_schema_violations(self):
        t = term_tables()
        no_col = {k: v.copy() for k, v in t.items()}
        no_col["enrolments"] = no_col["enrolments"].drop(columns=["term_length_days"])
        r = await self.upload(no_col)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["validation_errors"][0]["code"], "SCHEMA_INVALID")
        pct = {k: v.copy() for k, v in t.items()}
        pct["results"].loc[pct["results"].index[0], "score_pct"] = 140
        self.assertEqual((await self.upload(pct)).json()["validation_errors"][0]["code"], "SCHEMA_INVALID")
        missing = {k: v for k, v in t.items() if k != "assessments"}
        self.assertEqual((await self.upload(missing)).json()["validation_errors"][0]["code"], "MISSING_TABLE")

    async def test_future_dated_rows_are_rejected(self):
        start = (date.today() - timedelta(days=5)).isoformat()
        r = await self.upload(term_tables(term_start=start))   # results/activity run to day ~117
        self.assertEqual(r.status_code, 422)
        self.assertIn("INVALID_TEMPORAL_SEQUENCE", {e["code"] for e in r.json()["validation_errors"]})
        ok = await self.upload(term_tables(term_start=start, max_day=3))
        self.assertEqual(ok.status_code, 201, ok.text)

    async def test_partial_term_overlap_is_rejected_and_dry_run_stores_nothing(self):
        both = term_tables("T1")
        both2 = term_tables("T2")
        for k in both:
            both[k] = pd.concat([both[k], both2[k]], ignore_index=True)
        self.assertEqual((await self.upload(both)).status_code, 201)
        r = await self.upload(term_tables("T2"))
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["validation_errors"][0]["code"], "PARTIAL_TERM_OVERLAP")
        dry = await self.upload(term_tables("T1"), campus="campus-b", dry_run="true")
        self.assertEqual(dry.status_code, 201)
        self.assertEqual(dry.json()["status"], "validated")
        async with self.sessions() as s:
            rows = (await s.execute(select(ing_models.MlEnrolment).where(ing_models.MlEnrolment.campus_id == "campus-b"))).scalars().all()
        self.assertEqual(rows, [])

    async def test_xlsx_workbook(self):
        t = term_tables(max_day=20)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:
            for name in ("students", "enrolments", "assessments", "results", "activity", "withdrawals"):
                t[name].to_excel(xw, sheet_name=name, index=False)
        r = await self.client.post("/api/v1/ingestion/imports", headers=self.h(),
                                   files={"workbook": ("college.xlsx", buf.getvalue(), "application/vnd.ms-excel")})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["row_counts"]["enrolments"], len(t["enrolments"]))

    async def test_roles_and_empty_upload(self):
        for role in ("faculty", "student", "counsellor", "mentor"):
            self.assertEqual((await self.upload(role=role)).status_code, 403, role)
        r = await self.client.post("/api/v1/ingestion/imports", headers=self.h())
        self.assertEqual(r.status_code, 400)
        self.assertEqual((await self.client.get("/api/v1/ingestion/schema", headers=self.h("faculty"))).status_code, 403)
        sc = await self.client.get("/api/v1/ingestion/schema", headers=self.h())
        self.assertIn("enrolments", {x["name"] for x in sc.json()["tables"]})

    async def test_import_history_is_campus_scoped(self):
        b = (await self.upload()).json()
        mine = await self.client.get("/api/v1/ingestion/imports", headers=self.h())
        self.assertEqual(mine.json()["total"], 1)
        other = await self.client.get("/api/v1/ingestion/imports", headers=self.h(campus="campus-b"))
        self.assertEqual(other.json()["total"], 0)
        self.assertEqual((await self.client.get(f"/api/v1/ingestion/imports/{b['id']}", headers=self.h(campus="campus-b"))).status_code, 404)
        self.assertEqual((await self.client.get(f"/api/v1/ingestion/imports/{b['id']}", headers=self.h())).status_code, 200)


class TestScoring(PipelineCase):
    async def run_scoring(self, **body):
        return await self.client.post("/api/v1/ml/runs", json=body or {"as_of_day": 60, "term_id": "T2"}, headers=self.h())

    async def test_no_data_and_no_bundle_are_409_never_fake(self):
        r = await self.run_scoring()
        self.assertEqual((r.status_code, r.json()["details"]["code"]), (409, "NO_INGESTED_DATA"))
        await self.upload()
        with mock.patch.object(settings, "DISHA_ML_BUNDLE_PATH", "/nonexistent/bundle"):
            r = await self.run_scoring()
            self.assertEqual((r.status_code, r.json()["details"]["code"]), (409, "MODEL_UNAVAILABLE"))
            self.assertEqual((await self.client.get("/api/v1/ml/model-info", headers=self.h())).status_code, 409)
        # no scores or runs exist
        for path in ("students", "cohorts", "drift"):
            g = await self.client.get(f"/api/v1/ml/{path}", headers=self.h())
            self.assertEqual((g.status_code, g.json()["details"]["code"]), (404, "NO_SCORING_RUN"), path)
        self.assertEqual((await self.client.get("/api/v1/ml/runs", headers=self.h())).json()["total"], 0)

    async def test_roles(self):
        await self.upload()
        for role in ("faculty", "counsellor", "mentor", "hod"):
            self.assertEqual((await self.client.post("/api/v1/ml/runs", json={"as_of_day": 60}, headers=self.h(role))).status_code, 403, role)
        self.assertEqual((await self.run_scoring()).status_code, 201)
        for role in ("faculty", "counsellor", "mentor", "hod", "institution_admin"):
            self.assertEqual((await self.client.get("/api/v1/ml/students", headers=self.h(role))).status_code, 200, role)
        for role in ("student", "finance"):
            self.assertEqual((await self.client.get("/api/v1/ml/students", headers=self.h(role))).status_code, 403, role)

    async def test_as_of_validation(self):
        await self.upload()
        r = await self.client.post("/api/v1/ml/runs", json={"term_id": "T2"}, headers=self.h())
        self.assertEqual((r.status_code, r.json()["details"]["code"]), (422, "AS_OF_REQUIRED"))
        r = await self.client.post("/api/v1/ml/runs", json={"as_of_date": "2020-03-01", "term_id": "T2"}, headers=self.h())
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["as_of_day"], (date(2020, 3, 1) - date(2020, 1, 6)).days)
        r = await self.client.post("/api/v1/ml/runs", json={"as_of_day": 30, "term_id": "TX"}, headers=self.h())
        self.assertEqual(r.status_code, 409)

    async def test_end_to_end_run_insights_flags_and_audit(self):
        t = term_tables()
        ref = t["enrolments"].student_id.iloc[0]
        async with self.sessions() as s:
            s.add(Student(id="roster-1", campus_id="campus-a", student_uid=ref, full_name="Test Student"))
            await s.commit()
        await self.upload(t)

        r = await self.run_scoring()
        self.assertEqual(r.status_code, 201, r.text)
        run = r.json()
        self.assertEqual((run["status"], run["as_of_day"], run["triggered_by"]), ("completed", 60, "user-institution_admin"))
        self.assertGreater(run["n_scored"], 100)
        self.assertEqual(sum(run["tier_counts"].values()), run["n_scored"])
        self.assertTrue(run["model_version"].startswith("rolling-hgb-isotonic/v"))

        info = (await self.client.get("/api/v1/ml/model-info", headers=self.h("faculty"))).json()
        self.assertEqual(info["bundle_sha256"], run["bundle_sha256"])
        self.assertIn("alert_precision_at_cutoff", info["headline_metrics"])

        page = (await self.client.get("/api/v1/ml/students", params={"page_size": 10}, headers=self.h("faculty"))).json()
        self.assertEqual((page["run_id"], page["total"], len(page["items"])), (run["id"], run["n_scored"], 10))
        probs = [i["probability"] for i in page["items"]]
        self.assertEqual(probs, sorted(probs, reverse=True))
        p2 = (await self.client.get("/api/v1/ml/students", params={"page_size": 10, "page": 2}, headers=self.h())).json()
        self.assertFalse({i["id"] for i in page["items"]} & {i["id"] for i in p2["items"]})
        for it in page["items"]:
            self.assertTrue(it["external_student_ref_hash"].startswith("s_"))
            self.assertNotIn(it["student_ref"], it["external_student_ref_hash"])
        tier = next(iter(run["tier_counts"]))
        by_tier = (await self.client.get("/api/v1/ml/students", params={"tier": tier.lower(), "page_size": 100}, headers=self.h())).json()
        self.assertEqual(by_tier["total"], run["tier_counts"][tier])
        self.assertTrue(all(i["tier"] == tier for i in by_tier["items"]))
        bad = await self.client.get("/api/v1/ml/students", params={"tier": "bogus"}, headers=self.h())
        self.assertEqual(bad.status_code, 422)

        one = page["items"][0]
        ins = (await self.client.get(f"/api/v1/ml/students/{one['external_student_ref_hash']}/insight", headers=self.h("counsellor"))).json()
        self.assertEqual(ins["student_ref"], one["student_ref"])
        self.assertIn("risk", ins["items"][0]["insight"])            # StudentInsight (spec section 5)
        self.assertEqual(ins["items"][0]["insight"]["risk"]["tier"], one["tier"])
        self.assertEqual((await self.client.get("/api/v1/ml/students/s_nope/insight", headers=self.h())).status_code, 404)

        coh = (await self.client.get("/api/v1/ml/cohorts", params={"course_id": "C1"}, headers=self.h())).json()
        self.assertEqual(len(coh["cohorts"]), 1)
        self.assertEqual(coh["cohorts"][0]["term_id"], "T2")
        drift = (await self.client.get("/api/v1/ml/drift", headers=self.h())).json()
        self.assertIn("max_psi", drift["data_drift"])
        self.assertEqual((await self.client.get(f"/api/v1/ml/runs/{run['id']}", headers=self.h())).json()["id"], run["id"])

        async with self.sessions() as s:
            flags = await services.flags_for_run(s, run["id"])
            actions = [e.action for e in (await s.execute(select(AuditEvent).where(AuditEvent.entity_id == run["id"]))).scalars().all()]
        self.assertEqual(actions, ["ml.scoring_run.completed"])
        self.assertEqual(len(flags), run["n_scored"])
        f0 = flags[0]
        self.assertIsInstance(f0, RiskFlag)
        self.assertEqual(set(f0.__dataclass_fields__),
                         {"campus_id", "student_id", "external_student_ref_hash", "course_ref", "as_of", "tier", "probability",
                          "reasons", "model_version", "score_id"})
        self.assertEqual((f0.campus_id, f0.course_ref), ("campus-a", "C1:T2"))
        self.assertIn(f0.tier, {"high", "medium", "watch", "none"})
        self.assertTrue(f0.as_of.startswith("2020-"))
        self.assertEqual({f.tier for f in flags}, {{"HIGH": "high", "MEDIUM": "medium", "WATCH": "watch", "ON_TRACK": "none"}[k] for k in run["tier_counts"]})
        linked = [f for f in flags if f.student_id]
        self.assertTrue(all(f.student_id == "roster-1" for f in linked))

    async def test_tenancy_isolation(self):
        await self.upload(campus="campus-a")
        run = (await self.run_scoring()).json()
        a_hash = (await self.client.get("/api/v1/ml/students", headers=self.h())).json()["items"][0]["external_student_ref_hash"]

        B = self.h(campus="campus-b")
        self.assertEqual((await self.client.get("/api/v1/ml/students", headers=B)).status_code, 404)
        self.assertEqual((await self.client.get("/api/v1/ml/students", params={"run_id": run["id"]}, headers=B)).status_code, 404)
        self.assertEqual((await self.client.get(f"/api/v1/ml/runs/{run['id']}", headers=B)).status_code, 404)
        self.assertEqual((await self.client.get(f"/api/v1/ml/students/{a_hash}/insight", headers=B)).status_code, 404)
        self.assertEqual((await self.client.get("/api/v1/ml/cohorts", params={"run_id": run["id"]}, headers=B)).status_code, 404)
        self.assertEqual((await self.client.get("/api/v1/ml/drift", headers=B)).status_code, 404)
        self.assertEqual((await self.client.get("/api/v1/ml/runs", headers=B)).json()["total"], 0)
        # campus B has no data of its own, and cannot score campus A's
        r = await self.client.post("/api/v1/ml/runs", json={"as_of_day": 60}, headers=B)
        self.assertEqual((r.status_code, r.json()["details"]["code"]), (409, "NO_INGESTED_DATA"))
        # while A still sees its own
        self.assertEqual((await self.client.get("/api/v1/ml/students", headers=self.h())).status_code, 200)

    async def test_meko_hook_receives_payload_and_failures_are_ignored(self):
        await self.upload()
        seen = []
        with mock.patch.object(settings, "DISHA_ML_MEKO_HOOKS", True), \
                mock.patch("disha_ml.meko_hooks.record_assessment_updates", side_effect=lambda p: seen.append(p) or 0):
            self.assertEqual((await self.run_scoring()).status_code, 201)
        self.assertEqual(len(seen), 1)
        self.assertIn("students", seen[0])
        with mock.patch.object(settings, "DISHA_ML_MEKO_HOOKS", True), \
                mock.patch("disha_ml.meko_hooks.record_assessment_updates", side_effect=RuntimeError("meko down")):
            self.assertEqual((await self.client.post("/api/v1/ml/runs", json={"as_of_day": 70, "term_id": "T2"}, headers=self.h())).status_code, 201)

    async def test_scoring_failure_is_recorded_on_the_run(self):
        await self.upload()
        with mock.patch("disha_ml.rolling.score.score_snapshot", side_effect=ValueError("boom")):
            r = await self.run_scoring()
        self.assertEqual((r.status_code, r.json()["details"]["code"]), (422, "SCORING_FAILED"))
        runs = (await self.client.get("/api/v1/ml/runs", headers=self.h())).json()["items"]
        self.assertEqual((runs[0]["status"], runs[0]["error"]), ("failed", "boom"))
        self.assertEqual((await self.client.get("/api/v1/ml/students", headers=self.h())).status_code, 404)


class TestWorkerJobs(PipelineCase):
    async def test_scheduled_scoring_and_drift_summary(self):
        start = date.today() - timedelta(days=40)
        t = term_tables(term_start=start.isoformat(), max_day=40)
        self.assertEqual((await self.upload(t)).status_code, 201)
        # a second term with no start date is skipped, never guessed
        runs = await jobs.run_scheduled_scoring(self.sessions)
        self.assertEqual(len(runs), 1)
        self.assertEqual(await jobs.run_scheduled_scoring(self.sessions), [])   # once per day and term
        async with self.sessions() as s:
            run = (await s.execute(select(ml_models.MlScoringRun))).scalar_one()
        self.assertEqual((run.triggered_by, run.as_of_day, run.term_id), ("scheduler", 40, "T2"))
        summ = await jobs.drift_summaries(self.sessions)
        self.assertEqual(len(summ), 1)
        self.assertEqual(summ[0]["run_id"], run.id)
        self.assertIsNotNone(summ[0]["max_psi"])


    async def test_terms_without_term_start_are_not_scheduled(self):
        await self.upload(term_tables(term_start=""))
        async with self.sessions() as s:
            self.assertEqual(await jobs.active_terms(s), [])


class TestNoSyntheticData(unittest.TestCase):
    def test_synthetic_generators_are_not_imported_by_the_api_path(self):
        code = (
            "import sys\n"
            "import app.modules.ingestion.routes, app.modules.ml.routes, app.modules.ml.services, app.modules.ml.jobs\n"
            "import disha_ml.rolling.score, disha_ml.rolling.insights, disha_ml.meko_hooks, disha_ml.clo.link\n"
            "bad = [m for m in sys.modules if m.endswith('synthetic')]\n"
            "assert not bad, bad\n")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)})
        self.assertEqual(r.returncode, 0, r.stderr[-800:])


if __name__ == "__main__":
    unittest.main()
