import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location(
    "initialize_exams", Path(__file__).resolve().parents[2] / "scripts" / "initialize_exam_requirements.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixtures():
    options = {"courses": [{"id": 1, "name": "LV", "semesterId": 7,
                           "cohortSize": 30, "lecturer": {"id": 4, "name": "Person"}}],
               "lecturers": [{"id": 4, "isActive": True}]}
    overview = {"courses": [{"courseId": 1, "courseName": "LV", "configuration": None,
                             "activeExam": None}]}
    return options, overview


class InitializationTests(unittest.TestCase):
    def test_values_and_preview_does_not_write(self):
        options, overview = fixtures()
        api = Mock()
        plan = module.build_plan(options, overview, 7)
        module.execute(api, plan, 7, apply=False)
        api.request.assert_not_called()
        config = plan[0]["payload"]["configuration"]
        self.assertEqual(config["durationMinutes"], 90)
        self.assertEqual(config["examType"], "Schriftlich")
        self.assertEqual(config["requiredCapacity"], 30)
        self.assertEqual(config["responsibleLecturerId"], 4)
        self.assertIsNone(plan[0]["payload"]["expectedRevision"])

    def test_existing_even_disabled_configuration_is_preserved(self):
        options, overview = fixtures()
        overview["courses"][0]["configuration"] = {"enabled": False}
        self.assertEqual(module.build_plan(options, overview, 7)[0]["status"], "existing")

    def test_missing_or_inactive_lecturer_and_invalid_size(self):
        for field, value in [("lecturer", None), ("cohortSize", 0)]:
            options, overview = fixtures()
            options["courses"][0][field] = value
            self.assertEqual(module.build_plan(options, overview, 7)[0]["status"], "skipped")
        options, overview = fixtures()
        options["lecturers"] = []
        self.assertEqual(module.build_plan(options, overview, 7)[0]["status"], "skipped")

    def test_unavailable_course_is_reported(self):
        options, overview = fixtures()
        options["courses"] = []
        self.assertEqual(module.build_plan(options, overview, 7)[0]["status"], "skipped")

    def test_apply_and_repeated_execution(self):
        options, overview = fixtures()
        api = Mock()
        api.request.side_effect = [options, overview, {}]
        plan = module.build_plan(options, overview, 7)
        module.execute(api, plan, 7, apply=True)
        self.assertEqual(plan[0]["status"], "created")
        self.assertEqual(api.request.call_args.args[0], "PUT")
        overview["courses"][0]["configuration"] = {"revision": 1}
        api.reset_mock()
        module.execute(api, module.build_plan(options, overview, 7), 7, apply=True)
        api.request.assert_not_called()

    def test_changed_source_or_concurrent_configuration_is_skipped(self):
        for change in ["source", "configuration"]:
            options, overview = fixtures()
            plan = module.build_plan(options, overview, 7)
            if change == "source":
                options["courses"][0]["cohortSize"] = 31
            else:
                overview["courses"][0]["configuration"] = {"revision": 1}
            api = Mock()
            api.request.side_effect = [options, overview]
            module.execute(api, plan, 7, apply=True)
            self.assertEqual(plan[0]["status"], "skipped")
            self.assertEqual(api.request.call_count, 2)

    def test_uncertain_write_aborts_without_retry(self):
        options, overview = fixtures()
        api = Mock()
        api.request.side_effect = [options, overview, module.InitializationError("HTTP 409")]
        plan = module.build_plan(options, overview, 7)
        with self.assertRaises(module.InitializationError):
            module.execute(api, plan, 7, apply=True)
        self.assertEqual(plan[0]["status"], "failed_or_unknown")
        self.assertEqual(api.request.call_count, 3)

    def test_remote_http_rejected(self):
        with self.assertRaises(module.InitializationError):
            module.PlannerAPI("http://example.com")


if __name__ == "__main__":
    unittest.main()
