"""Run with: python -m unittest discover -s backend/tests/scripts -p test_import_rooms.py"""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from uuid import uuid4


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "import_rooms.py"
spec = importlib.util.spec_from_file_location("import_rooms", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeAPI:
    def __init__(self, existing=(), fail_after_write=False):
        self.rooms = {module.key(room["referenceCode"]): dict(room) for room in existing}
        self.posts = 0
        self.fail_after_write = fail_after_write

    def list_rooms(self):
        return self.rooms

    def request(self, method, path, payload):
        assert method == "POST" and path == "/api/resources/rooms"
        self.posts += 1
        room = {**payload, "id": self.posts + 100, "isActive": True}
        self.rooms[module.key(room["referenceCode"])] = room
        if self.fail_after_write:
            raise module.ImportFailure("Simulated lost response after successful server commit")
        return room


class RoomImportTests(unittest.TestCase):
    def setUp(self):
        self.root = SCRIPT.parents[2] / "tmp" / f"room-import-test-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.room = {"name": "CC202 – Campus Classic", "referenceCode": "CC202", "capacity": 56}

    def export(self, rows):
        path = self.root / "rooms.json"
        path.write_text(json.dumps({"resource": [
            {"content": {"MEINE_RAUM_V": row}} for row in rows]}), encoding="utf-8")
        return path

    def report(self, api, rooms=None):
        return {"plan": module.plan_rooms(rooms or [self.room], api.list_rooms())}

    def test_real_export_has_121_importable_unique_rooms(self):
        path = SCRIPT.parents[2] / "artifacts" / "export-import" / "rooms.json"
        if not path.exists():
            self.skipTest("Local source export is not part of the repository")
        rooms, skipped, duplicates = module.read_export(path)
        self.assertEqual((len(rooms), len(skipped), duplicates), (121, 103, 2))

    def test_capacity_types_and_identical_duplicates(self):
        row = {"RAUMCODE": "A", "GEBAEUDE": "Building", "SITZPLAETZE": 20}
        rows = [row, dict(row)] + [
            {"RAUMCODE": f"B{i}", "SITZPLAETZE": value}
            for i, value in enumerate([None, 0, -1, True, "20", 2.5])]
        rooms, skipped, duplicates = module.read_export(self.export(rows))
        self.assertEqual((len(rooms), len(skipped), duplicates), (1, 6, 1))

    def test_conflicting_duplicate_blocks_before_any_write(self):
        path = self.export([{"RAUMCODE": "A", "SITZPLAETZE": 20},
                            {"RAUMCODE": " a ", "SITZPLAETZE": 30}])
        with self.assertRaisesRegex(module.ImportFailure, "Conflicting duplicate"):
            module.read_export(path)

    def test_apply_then_repeat_does_not_create_duplicates(self):
        api = FakeAPI()
        first = self.report(api)
        module.apply_plan(api, first, self.root / "first.json")
        second = self.report(api)
        module.apply_plan(api, second, self.root / "second.json")
        self.assertEqual(api.posts, 1)
        self.assertTrue(first["verified"] and second["verified"])
        self.assertEqual(second["plan"][0]["status"], "existing")

    def test_changed_or_inactive_room_is_not_overwritten(self):
        for changes in [{"capacity": 30}, {"name": "Another name"}, {"isActive": False}]:
            with self.subTest(changes=changes):
                prior = {**self.room, "id": 1, "isActive": True, **changes}
                api = FakeAPI([prior])
                report = self.report(api)
                module.apply_plan(api, report, self.root / "conflict.json")
                self.assertEqual(api.posts, 0)
                self.assertEqual(report["plan"][0]["status"], "conflict")
                self.assertEqual(api.rooms["cc202"], prior)

    def test_lost_post_response_is_logged_and_reconciled_on_next_run(self):
        api = FakeAPI(fail_after_write=True)
        report = self.report(api)
        target = self.root / "failed.json"
        with self.assertRaises(module.ImportFailure):
            module.apply_plan(api, report, target)
        self.assertEqual(json.loads(target.read_text())["plan"][0]["status"], "uncertain_or_failed")
        api.fail_after_write = False
        module.apply_plan(api, self.report(api), self.root / "resumed.json")
        self.assertEqual(api.posts, 1)

    def test_verification_detects_missing_room(self):
        api = FakeAPI()
        report = {"plan": [{"room": self.room, "status": "existing", "id": 1}]}
        with self.assertRaisesRegex(module.ImportFailure, "verification failed"):
            module.apply_plan(api, report, self.root / "verify.json")

    def test_offline_preview_never_requires_network_or_login(self):
        source = self.export([{"RAUMCODE": "A", "SITZPLAETZE": 20}])
        self.assertEqual(module.main([str(source)]), 0)
        result = json.loads(next((self.root / "import-reports").glob("*.json")).read_text())
        self.assertEqual(result["status"], "preview")
        self.assertEqual(result["plan"][0]["status"], "candidate")

    def test_remote_plain_http_and_credential_urls_are_rejected(self):
        for url in ["http://si-resp-01:8080", "https://user:secret@example.org", "https://example.org/?token=x"]:
            with self.subTest(url=url), self.assertRaises(module.ImportFailure):
                module.PlannerAPI(url)

    def test_requests_use_json_and_csrf_header_without_logging_password(self):
        api = module.PlannerAPI("https://planner.example.org")
        api.opener = Mock()
        response = io.BytesIO(b'{"id": 7}')
        api.opener.open.return_value = response
        result = api.request("POST", "/api/resources/rooms", self.room)
        request = api.opener.open.call_args.args[0]
        headers = {name.lower(): value for name, value in request.header_items()}
        self.assertEqual(result, {"id": 7})
        self.assertEqual(json.loads(request.data), self.room)
        self.assertEqual(headers["x-csrf-protection"], "1")
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(api.opener.open.call_args.kwargs["timeout"], 45)

    def test_existing_room_pagination_includes_inactive_rooms(self):
        api = module.PlannerAPI("https://planner.example.org")
        api.request = Mock(side_effect=[
            {"items": [{"referenceCode": " A ", "id": 1}], "total": 2},
            {"items": [{"referenceCode": "B", "id": 2}], "total": 2}])
        self.assertEqual(set(api.list_rooms()), {"a", "b"})
        self.assertIn("status=all", api.request.call_args_list[0].args[1])
        self.assertIn("page=2", api.request.call_args_list[1].args[1])

    def test_http_error_does_not_expose_server_body_or_login_payload(self):
        api = module.PlannerAPI("https://planner.example.org")
        api.opener = Mock()
        api.opener.open.side_effect = HTTPError(
            "https://planner.example.org/api/auth/login", 401, "Unauthorized", {},
            io.BytesIO(b"secret-server-body"))
        with self.assertRaises(module.ImportFailure) as raised:
            api.request("POST", "/api/auth/login", {"password": "secret-password"})
        self.assertIn("HTTP 401", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
