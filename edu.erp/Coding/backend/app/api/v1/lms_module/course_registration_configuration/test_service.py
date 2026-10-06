"""Service and HTTP contract tests. Never write to the application database."""
import unittest
import asyncio
import json
import time
from jose import jwt
from datetime import datetime
from types import SimpleNamespace as Row
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request, HTTPException
from .router import router, service, actor, demo_identity
from .service import RegistrationService
from .schemas import ConfigurationSave, CourseSave


class TestClient:
    """Minimal ASGI HTTP driver using stdlib (no optional httpx dependency)."""
    def __init__(self, app): self.app = app

    def request(self, method, path, headers=None, json_body=None):
        async def run():
            body = json.dumps(json_body).encode() if json_body is not None else b""
            sent, incoming = [], False
            async def receive():
                nonlocal incoming
                if not incoming:
                    incoming = True
                    return {"type": "http.request", "body": body, "more_body": False}
                await asyncio.sleep(0)
                return {"type": "http.disconnect"}
            async def send(message): sent.append(message)
            scope = dict(type="http", asgi={"version": "3.0"}, http_version="1.1", method=method,
                scheme="http", path=path, raw_path=path.encode(), query_string=b"", root_path="",
                headers=[(k.lower().encode(), v.encode()) for k, v in {"content-type": "application/json", **(headers or {})}.items()],
                server=("test", 80), client=("test", 123))
            await self.app(scope, receive, send)
            start = next(m for m in sent if m["type"] == "http.response.start")
            content = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
            return Row(status_code=start["status"], content=content, headers={k.decode():v.decode() for k,v in start["headers"]}, json=lambda: json.loads(content))
        return asyncio.run(run())

    def get(self, path, headers=None): return self.request("GET", path, headers)
    def put(self, path, json=None): return self.request("PUT", path, json_body=json)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.svc = RegistrationService(self.db, dict(user_id=1, org_id=1, all_departments=True, instructor_only=False))
        self.term = Row(academic_batch_id=3, semester_id=4, semester=1, enroll_start_date=datetime(2026, 9, 10).date(),
            enroll_start_time=datetime(2026, 9, 10, 9).time(), enroll_end_date=datetime(2026, 9, 11).date(),
            enroll_end_time=datetime(2026, 9, 11, 10).time(), total_crs_enroll=12, own_crclm_elective=0,
            other_crclm_elective=0, term_name="Term 1", semester_desc="", semester_code="")
        self.svc.term = MagicMock(return_value=self.term)
        self.svc.settings = MagicMock(return_value={"mode": "credits", "enabled": True})
        self.svc.batch = MagicMock(return_value=Row(academic_batch_desc="Test curriculum"))

    def course_rows(self):
        kind, component = Row(course_type_id=1, course_type_desc="Elective"), Row(crclm_comp_alias_name="ELECTIVE")
        return [(Row(crs_id=1, crs_code="E1", total_credits=9, reg_start_date=None, reg_end_date=None), kind, component)]

    def test_summary_uses_highest_credits_not_largest_course_count(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.svc.course_rows = MagicMock(return_value=self.course_rows())
        # Student A: three one-credit courses; student B: one nine-credit course.
        self.svc.enrollment_rows = MagicMock(return_value=[(1, 1, 1, 1), (1, 2, 1, 1), (1, 3, 1, 1), (2, 4, 1, 9)])
        summary = self.svc.summary(3, 4)
        self.assertEqual(summary["max_registered"], 9)
        self.assertEqual(summary["types"][0]["max_registered"], 9)
        self.assertEqual(summary["types"][0]["registered"], 4)

    def payload(self):
        return ConfigurationSave(start="2026-09-10T09:00", end="2026-09-11T10:00", total=12,
            limits=[dict(course_type_id=1, minimum=3, maximum=9)])

    def prepare_save(self):
        self.svc.summary = MagicMock(return_value={"mode": "credits", "max_registered": 6,
            "types": [dict(course_type_id=1, name="Elective", total=9, minimum_allowed=3, max_registered=6)]})
        self.svc.course_rows = MagicMock(return_value=self.course_rows())

    def test_invalid_save_writes_nothing(self):
        self.prepare_save()
        payload = self.payload(); payload.total = 5
        with self.assertRaises(ValueError): self.svc.save_configuration(3, 4, payload)
        self.db.add.assert_not_called(); self.db.commit.assert_not_called(); self.db.rollback.assert_called_once()

    def test_save_uses_server_totals_and_single_commit(self):
        self.prepare_save()
        self.svc.save_configuration(3, 4, self.payload())
        self.assertEqual(self.db.add.call_args.args[0].crs_type_total, 9)
        self.db.commit.assert_called_once()
        self.svc.term.assert_called_once_with(3, 4, lock=True)

    def test_commit_failure_rolls_back(self):
        self.prepare_save(); self.db.commit.side_effect = RuntimeError("simulated failure")
        with self.assertRaises(RuntimeError): self.svc.save_configuration(3, 4, self.payload())
        self.db.rollback.assert_called_once()

    def test_narrower_term_window_rejects_existing_course_dates(self):
        self.prepare_save()
        course, kind, component = self.course_rows()[0]
        component.crclm_comp_alias_name = "OPEN_ELECTIVE"
        course.reg_start_date = datetime(2026, 9, 10, 8)
        course.reg_end_date = datetime(2026, 9, 10, 10)
        self.svc.course_rows.return_value = [(course, kind, component)]
        with self.assertRaisesRegex(ValueError, "outside"):
            self.svc.save_configuration(3, 4, self.payload())
        self.db.add.assert_not_called(); self.db.commit.assert_not_called()

    def test_invalid_second_course_does_not_update_first(self):
        self.svc.course_details = MagicMock(return_value=[dict(course_id=1, code="E1", alias="ELECTIVE", registered=2), dict(course_id=2, code="E2", alias="ELECTIVE", registered=5)])
        data = CourseSave(courses=[dict(course_id=1, capacity=3), dict(course_id=2, capacity=4)])
        with self.assertRaisesRegex(ValueError, "capacity"): self.svc.save_courses(3, 4, 1, data)
        self.db.commit.assert_not_called(); self.db.rollback.assert_called_once()


class HttpContractTest(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI(); self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_authentication_required(self):
        response = self.client.get("/course-registration-configuration/options", headers={"org-id": "1"})
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret", "ALGORITHM": "HS256"}):
            response = self.client.get("/course-registration-configuration/options", headers={"org-id": "1", "Authorization": "Bearer invalid"})
        self.assertEqual(response.status_code, 401)

    def test_expired_token_reports_expiry(self):
        token = jwt.encode({"id": 7, "exp": int(time.time()) - 60}, "test-secret", algorithm="HS256")
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret", "ALGORITHM": "HS256"}):
            response = self.client.get("/course-registration-configuration/options", headers={"org-id": "1", "Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.json()["detail"])

    def test_staff_login_token_is_accepted(self):
        token = jwt.encode({"id": 7, "username": "test", "exp": int(time.time()) + 60}, "test-secret", algorithm="HS256")
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = Row(
            id=7, active=True, is_locked=False, org_id=1, super_admin=True, user_dept_id=2)
        db.execute.return_value.all.return_value = []
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret", "ALGORITHM": "HS256"}):
            result = actor(request=Request({"type": "http", "client": ("127.0.0.1", 123)}), token=token, org_id=1, db=db)
        self.assertEqual(result["user_id"], 7)
        self.assertEqual(result["org_id"], 1)

    def test_validation_error_status_and_body(self):
        svc = MagicMock(); svc.save_configuration.side_effect = ValueError("Enrollment limit cannot be reduced")
        self.app.dependency_overrides[service] = lambda: svc
        response = self.client.put("/course-registration-configuration/curricula/3/terms/4", json={
            "start": "2026-09-10T09:00", "end": "2026-09-11T10:00", "total": 6,
            "limits": [{"course_type_id": 1, "minimum": 3, "maximum": 6}]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "Enrollment limit cannot be reduced")

    def test_pdf_export(self):
        svc = MagicMock()
        svc.summary.return_value = dict(saved=True, curriculum_name="Curriculum & test", term_name="Term 1", start="2026-09-10 09:00", end="2026-09-11 10:00",
            mode="credits", total_available=12, total=9, own_electives=1, other_electives=1,
            types=[dict(course_type_id=1, name="Open <elective>", total=12, minimum=3, maximum=9, registered=2)])
        svc.course_details.return_value = [dict(code="OE1", title="A long elective course title " * 6, credits=3, capacity=None, registered=2, start="2026-09-10 10:00", end="2026-09-10 11:00")]
        self.app.dependency_overrides[service] = lambda: svc
        response = self.client.get("/course-registration-configuration/curricula/3/terms/4/export.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("application/pdf", response.headers["content-type"])


class LocalDemoTest(unittest.TestCase):
    def setUp(self):
        self.env = dict(ENV="development", APP_ENV="", ENVIRONMENT="", COURSE_REGISTRATION_ALLOW_LOCAL_DEMO="true",
            COURSE_REGISTRATION_DEMO_USER_ID="1", COURSE_REGISTRATION_DEMO_ORG_ID="1")
        self.request = Request({"type": "http", "client": ("127.0.0.1", 123)})

    def test_explicit_local_demo_identity(self):
        with patch.dict("os.environ", self.env):
            self.assertEqual(demo_identity("demo-token-12345", self.request, 1), 1)

    def test_disabled_production_and_remote_demo_rejected(self):
        for values, host in [({"COURSE_REGISTRATION_ALLOW_LOCAL_DEMO": "false"}, "127.0.0.1"),
            ({"ENV": "production"}, "127.0.0.1"), ({"APP_ENV": "production"}, "127.0.0.1"), ({}, "192.168.1.2")]:
            with self.subTest(values=values, host=host), patch.dict("os.environ", {**self.env, **values}), self.assertRaises(HTTPException) as raised:
                demo_identity("demo-token-12345", Request({"type": "http", "client": (host, 123)}), 1)
            self.assertEqual(raised.exception.status_code, 401)

    def test_cannot_choose_another_organisation(self):
        with patch.dict("os.environ", self.env), self.assertRaises(HTTPException) as raised:
            demo_identity("demo-token-12345", self.request, 2)
        self.assertEqual(raised.exception.status_code, 403)

    def test_other_tokens_never_use_demo_identity(self):
        with patch.dict("os.environ", self.env):
            self.assertIsNone(demo_identity("random-invalid-token", self.request, 1))

    def test_demo_still_requires_active_account(self):
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with patch.dict("os.environ", self.env), self.assertRaises(HTTPException) as raised:
            actor(request=self.request, token="demo-token-12345", org_id=1, db=db)
        self.assertEqual(raised.exception.status_code, 403)

    def test_legacy_unspecified_active_flag_and_explicit_disabled_flag(self):
        for active, allowed in [(None, True), (True, True), (False, False)]:
            db = MagicMock()
            db.query.return_value.options.return_value.filter.return_value.first.return_value = Row(
                id=1, active=active, is_locked=False, org_id=1, super_admin=True, user_dept_id=None)
            db.execute.return_value.all.return_value = []
            with self.subTest(active=active), patch.dict("os.environ", self.env):
                if allowed:
                    self.assertEqual(actor(request=self.request, token="demo-token-12345", org_id=1, db=db)["user_id"], 1)
                else:
                    with self.assertRaises(HTTPException) as raised:
                        actor(request=self.request, token="demo-token-12345", org_id=1, db=db)
                    self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__": unittest.main()
