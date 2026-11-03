import importlib.util
import json
from pathlib import Path
import shutil
import sys
import unittest
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import import_academic_data as importer
import prepare_campus_catalog as preparation


class FakeAPI:
    def __init__(self, kind):
        self.kind, self.rows, self.posts = kind, [], 0
        self.fail_after_commit = False
        self.eligibility = {}
        self.puts = 0
        self.fail_before_put = False

    def request(self, method, path, payload=None):
        if self.kind == "holidays":
            if method == "GET":
                assert path == "/api/holidays"
                return self.rows
            assert method == "POST" and path == "/api/holidays"
            self.posts += 1
            row = {**payload, "id": self.posts, "revision": 1}
            self.rows.append(row)
            if self.fail_after_commit:
                raise importer.ImportFailure("Lost response")
            return row
        if path.endswith("/resource-eligibility"):
            course_id = int(path.split("/")[-2])
            current = self.eligibility[course_id]
            if method == "PUT":
                if self.fail_before_put:
                    raise importer.ImportFailure("Lost configuration request")
                assert payload["expectedRevision"] == current["courseRevision"]
                self.puts += 1
                current.update(eligibleLecturerIds=payload["lecturerIds"], eligibleRoomIds=payload["roomIds"],
                               courseRevision=current["courseRevision"] + 1)
            return current
        if method == "GET":
            return {"items": self.rows, "total": len(self.rows)}
        self.posts += 1
        if self.kind == "lecturers":
            row = {**payload, "id": self.posts, "isActive": True}
        else:
            row = {k: payload[k] for k in ("name", "totalUnits", "minSessionUnits", "maxSessionUnits")}
            row.update({"id": self.posts, "isActive": True})
            for response, field in (("semester", "semesterId"), ("cohort", "cohortId"), ("studyType", "studyTypeId"),
                                    ("lecturer", "lecturerId"), ("room", "roomId")):
                row[response] = {"id": payload[field]}
            self.eligibility[row["id"]] = {"eligibleLecturerIds": [payload["lecturerId"]],
                                           "eligibleRoomIds": [payload["roomId"]], "courseRevision": 1}
        self.rows.append(row)
        if self.fail_after_commit:
            raise importer.ImportFailure("Lost response")
        return row


class AcademicImportTests(unittest.TestCase):
    def setUp(self):
        self.root = SCRIPTS.parents[1] / "tmp" / f"academic-import-test-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.lecturers = {"lecturers": [{"referenceCode": "campus02:AAA", "name": "Person, Test"}]}
        self.document = {"courses": [{"sourceCourseId": "1", "code": "LV1"}]}
        self.mapping = {"semesterName": "2027 S", "courses": [{
            "sourceCourseId": "1", "include": True, "name": "Test [LV1] – 2027 S",
            "cohortName": "BSD – 2. Semester", "studyTypeName": "Vollzeit",
            "lecturerReferenceCode": "campus02:AAA", "roomReferenceCode": "CC202",
            "totalUnits": 26, "minSessionUnits": 2, "maxSessionUnits": 4}]}
        self.catalogs = {
            "semesters": [{"id": 10, "name": "2027 S", "isActive": True}],
            "cohorts": [{"id": 20, "name": "BSD – 2. Semester", "studentCount": 30, "isActive": True}],
            "study-types": [{"id": 30, "name": "Vollzeit", "isActive": True, "timeWindows": [{"isActive": True}]}],
            "lecturers": [{"id": 40, "referenceCode": "campus02:AAA", "isActive": True}],
            "rooms": [{"id": 50, "referenceCode": "CC202", "capacity": 56, "isActive": True}], "courses": []}

    def test_rounding_is_nearest_integer_with_half_up(self):
        for source, expected in [(25.5, 26), (8.5, 9), (46.75, 47), (29.75, 30), (59.5, 60), (0, 0), (34, 34), (3.49, 3)]:
            with self.subTest(source=source):
                self.assertEqual(preparation.rounded_units(source), expected)
        with self.assertRaises(ValueError):
            preparation.rounded_units(True)

    def test_prepared_data_matches_full_sources_and_preserves_mapping_edits(self):
        source_dir = SCRIPTS.parents[1] / "artifacts" / "export-import" / "lecturers-sources"
        if not source_dir.exists():
            self.skipTest("Captured source files not available")
        preparation.prepare(source_dir, self.root, "2027 S")
        people = json.loads((self.root / "lecturers.json").read_text(encoding="utf-8"))["lecturers"]
        courses = json.loads((self.root / "courses.json").read_text(encoding="utf-8"))["courses"]
        self.assertEqual((len(people), len(courses)), (73, 95))
        self.assertEqual(sum(c["roundedTotalUnits"] == 0 for c in courses), 1)
        self.assertFalse(any(preparation.excluded_course(c["title"]) for c in courses))
        self.assertEqual(sum(len(p["sourceCourses"]) for p in people), 217)
        ids = {p["referenceCode"] for p in people}
        self.assertTrue(all(set(c["lecturerReferenceCodes"]) <= ids for c in courses))
        mapping = self.root / "courses-2027-S.mapping.json"
        edited = json.loads(mapping.read_text(encoding="utf-8"))
        edited["courses"][0]["cohortName"] = "Keep planner edit"
        edited["courses"].append({"sourceCourseId": "117799", "name": "Bachelorprüfung"})
        mapping.write_text(json.dumps(edited), encoding="utf-8")
        preparation.prepare(source_dir, self.root, "2027 S")
        regenerated = json.loads(mapping.read_text(encoding="utf-8"))
        self.assertEqual(regenerated["courses"][0]["cohortName"], "Keep planner edit")
        self.assertEqual(len(regenerated["courses"]), 95)
        self.assertNotIn("117799", {row["sourceCourseId"] for row in regenerated["courses"]})

    def test_exclusion_rule_covers_numbered_masterarbeit_and_preserves_other_courses(self):
        for title in ["Bachelorprüfung", "Masterprüfung", "Masterarbeit", "Masterarbeit 1", " Masterarbeit 2 "]:
            self.assertTrue(preparation.excluded_course(title), title)
        for title in ["Accompanying Project", "Bachelorarbeit", "Projektmanagement"]:
            self.assertFalse(preparation.excluded_course(title), title)

    def test_lecturer_import_can_be_repeated_without_duplicates(self):
        api = FakeAPI("lecturers")
        for number in range(2):
            report = {"plan": importer.lecturer_plan(self.lecturers, api.rows)}
            importer.apply_plan(api, "lecturers", report, self.root / f"run{number}.json")
            self.assertTrue(report["verified"])
        self.assertEqual(api.posts, 1)

    def test_existing_lecturer_with_changed_name_blocks_before_write(self):
        api = FakeAPI("lecturers")
        api.rows = [{"id": 1, "referenceCode": "campus02:AAA", "name": "Different", "isActive": True}]
        report = {"plan": importer.lecturer_plan(self.lecturers, api.rows)}
        with self.assertRaises(importer.ImportFailure):
            importer.apply_plan(api, "lecturers", report, self.root / "blocked.json")
        self.assertEqual(api.posts, 0)

    def test_course_resolves_ids_and_uses_2027_s(self):
        plan = importer.course_plan(self.document, self.mapping, self.catalogs)
        self.assertEqual(plan[0]["status"], "would_create")
        self.assertEqual(plan[0]["payload"]["semesterId"], 10)
        self.assertEqual(plan[0]["payload"]["lecturerId"], 40)
        api = FakeAPI("courses")
        report = {"plan": plan}
        importer.apply_plan(api, "courses", report, self.root / "course.json")
        self.catalogs["courses"] = api.rows
        second = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs)}
        importer.apply_plan(api, "courses", second, self.root / "course-repeat.json")
        self.assertEqual(api.posts, 1)
        self.assertTrue(second["verified"])

    def test_missing_or_ambiguous_dependencies_block(self):
        for change in ["missing", "ambiguous", "inactive", "capacity", "windows"]:
            with self.subTest(change=change):
                catalogs = json.loads(json.dumps(self.catalogs))
                if change == "missing":
                    catalogs["cohorts"] = []
                elif change == "ambiguous":
                    catalogs["cohorts"] *= 2
                elif change == "inactive":
                    catalogs["lecturers"][0]["isActive"] = False
                elif change == "capacity":
                    catalogs["rooms"][0]["capacity"] = 10
                else:
                    catalogs["study-types"][0]["timeWindows"] = []
                plan = importer.course_plan(self.document, self.mapping, catalogs)
                self.assertEqual(plan[0]["status"], "blocked")
                api = FakeAPI("courses")
                with self.assertRaises(importer.ImportFailure):
                    importer.apply_plan(api, "courses", {"plan": plan}, self.root / "blocked.json")
                self.assertEqual(api.posts, 0)

    def test_units_and_explicit_selection_are_validated(self):
        row = self.mapping["courses"][0]
        for changes in [{"totalUnits": 0}, {"minSessionUnits": 5}, {"include": "false"}, {"roomReferenceCode": None}]:
            with self.subTest(changes=changes):
                mapping = {**self.mapping, "courses": [{**row, **changes}]}
                self.assertEqual(importer.course_plan(self.document, mapping)[0]["status"], "blocked")
        mapping = {**self.mapping, "courses": [{**row, "include": False, "totalUnits": 0}]}
        self.assertEqual(importer.course_plan(self.document, mapping)[0]["status"], "skipped")

    def test_lost_post_response_is_reconciled_on_repeat(self):
        api = FakeAPI("lecturers")
        api.fail_after_commit = True
        report = {"plan": importer.lecturer_plan(self.lecturers, api.rows)}
        with self.assertRaises(importer.ImportFailure):
            importer.apply_plan(api, "lecturers", report, self.root / "lost.json")
        self.assertEqual(report["plan"][0]["status"], "uncertain_or_failed")
        api.fail_after_commit = False
        repeat = {"plan": importer.lecturer_plan(self.lecturers, api.rows)}
        importer.apply_plan(api, "lecturers", repeat, self.root / "repeat.json")
        self.assertEqual(api.posts, 1)

    def test_course_conflict_does_not_reassign_existing_semester(self):
        payload = importer.course_plan(self.document, self.mapping, self.catalogs)[0]["payload"]
        api = FakeAPI("courses")
        prior = api.request("POST", "/api/academic/courses", payload)
        prior["semester"]["id"] = 99
        self.catalogs["courses"] = [prior]
        self.assertEqual(importer.course_plan(self.document, self.mapping, self.catalogs)[0]["status"], "conflict")

    def enable_two_lecturers(self):
        self.mapping["courses"][0]["additionalLecturerReferenceCodes"] = ["campus02:BBB"]
        self.catalogs["lecturers"].append({"id": 41, "referenceCode": "campus02:BBB", "isActive": True})

    def test_two_lecturers_are_saved_and_verified_without_duplicate_course_on_repeat(self):
        self.enable_two_lecturers()
        api = FakeAPI("courses")
        report = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        importer.apply_plan(api, "courses", report, self.root / "two.json")
        self.assertEqual(set(api.eligibility[1]["eligibleLecturerIds"]), {40, 41})
        self.assertTrue(report["verified"])
        self.catalogs["courses"] = api.rows
        api.rows[0]["lecturer"]["id"] = 41
        repeat = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        self.assertEqual(repeat["plan"][0]["status"], "existing")
        importer.apply_plan(api, "courses", repeat, self.root / "two-repeat.json")
        self.assertEqual((api.posts, api.puts), (1, 1))

    def test_interrupted_resource_configuration_resumes_without_another_course(self):
        self.enable_two_lecturers()
        api = FakeAPI("courses")
        api.fail_before_put = True
        first = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        with self.assertRaises(importer.ImportFailure):
            importer.apply_plan(api, "courses", first, self.root / "pending.json")
        self.assertEqual(first["plan"][0]["status"], "uncertain_or_failed")
        self.catalogs["courses"] = api.rows
        repeat = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        self.assertEqual(repeat["plan"][0]["status"], "would_configure")
        api.fail_before_put = False
        importer.apply_plan(api, "courses", repeat, self.root / "resumed.json")
        self.assertEqual((api.posts, api.puts), (1, 1))
        self.assertTrue(repeat["verified"])

    def test_unexpected_existing_lecturer_is_never_removed(self):
        self.enable_two_lecturers()
        api = FakeAPI("courses")
        payload = importer.course_plan(self.document, self.mapping, self.catalogs, api=api)[0]["payload"]
        api.request("POST", "/api/academic/courses", payload)
        api.eligibility[1]["eligibleLecturerIds"].append(999)
        self.catalogs["courses"] = api.rows
        plan = importer.course_plan(self.document, self.mapping, self.catalogs, api=api)
        self.assertEqual(plan[0]["status"], "conflict")
        self.assertEqual(api.puts, 0)

    def test_preferred_ue_requires_optimizer_midpoint(self):
        self.mapping["courses"][0]["preferredSessionUnits"] = 3
        self.assertEqual(importer.course_plan(self.document, self.mapping)[0]["status"], "candidate")
        self.mapping["courses"][0]["preferredSessionUnits"] = 4
        self.assertEqual(importer.course_plan(self.document, self.mapping)[0]["status"], "blocked")

    def test_first_batch_preserves_confirmed_session_limits_and_lecturers(self):
        root = SCRIPTS.parents[1] / "artifacts" / "export-import"
        path = root / "courses-2027-S.batch-01-BAAI-2.mapping.json"
        if not path.exists():
            self.skipTest("Local batch mapping not available")
        rows = {row["code"]: row for row in json.loads(path.read_text(encoding="utf-8"))["courses"] if row["include"]}
        self.assertEqual(len(rows), 10)
        self.assertTrue(all((r["minSessionUnits"], r["preferredSessionUnits"], r["maxSessionUnits"]) == (2, 3, 4) for r in rows.values()))
        self.assertEqual(rows["0864VZ2004"]["lecturerReferenceCode"], "campus02:4B9FD052DF069DEC")
        self.assertEqual(rows["0864VZ2004"]["additionalLecturerReferenceCodes"], [])
        for code in ("0864VZ2007", "0864VZ2008"):
            self.assertEqual(len(rows[code]["additionalLecturerReferenceCodes"]), 1)
        self.assertTrue(all(r["roomReferenceCode"] == "CZ108" and r["additionalRoomReferenceCodes"] == ["RC409"] for r in rows.values()))

    def test_multiple_rooms_are_saved_and_verified_on_repeat(self):
        self.mapping["courses"][0]["additionalRoomReferenceCodes"] = ["RC409"]
        self.catalogs["rooms"].append({"id": 51, "referenceCode": "RC409", "capacity": 78, "isActive": True})
        api = FakeAPI("courses")
        first = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        importer.apply_plan(api, "courses", first, self.root / "rooms.json")
        self.assertEqual(set(api.eligibility[1]["eligibleRoomIds"]), {50, 51})
        api.rows[0]["room"]["id"] = 51
        self.catalogs["courses"] = api.rows
        repeat = {"plan": importer.course_plan(self.document, self.mapping, self.catalogs, api=api)}
        self.assertEqual(repeat["plan"][0]["status"], "existing")
        importer.apply_plan(api, "courses", repeat, self.root / "rooms-repeat.json")
        self.assertEqual((api.posts, api.puts), (1, 1))

    def test_additional_room_must_be_large_enough_and_distinct(self):
        row = self.mapping["courses"][0]
        row["additionalRoomReferenceCodes"] = ["RC409"]
        self.catalogs["rooms"].append({"id": 51, "referenceCode": "RC409", "capacity": 10, "isActive": True})
        self.assertEqual(importer.course_plan(self.document, self.mapping, self.catalogs)[0]["status"], "blocked")
        row["additionalRoomReferenceCodes"] = ["cc202"]
        self.assertEqual(importer.course_plan(self.document, self.mapping)[0]["status"], "blocked")

    def holiday_document(self):
        return {"rangeStart": "2027-02-19", "rangeEnd": "2027-08-17", "holidays": [
            {"date": "2027-03-29", "name": "Ostermontag"}, {"date": "2027-08-15", "name": "Mariä Himmelfahrt"}]}

    def test_holiday_import_is_repeatable_and_preserves_other_years(self):
        api = FakeAPI("holidays")
        api.rows.append({"id": 99, "date": "2026-12-25", "name": "Christtag", "revision": 1})
        for run in range(2):
            plan = importer.holiday_plan(self.holiday_document(), importer.list_all(api, "/api/holidays"))
            report = {"plan": plan}
            importer.apply_plan(api, "holidays", report, self.root / f"holidays{run}.json")
            self.assertTrue(report["verified"])
        self.assertEqual((api.posts, len(api.rows)), (2, 3))
        self.assertEqual(api.rows[0]["date"], "2026-12-25")

    def test_holiday_name_conflict_blocks_without_overwriting(self):
        api = FakeAPI("holidays")
        api.rows = [{"id": 1, "date": "2027-03-29", "name": "Existing closure", "revision": 1}]
        plan = importer.holiday_plan(self.holiday_document(), api.rows)
        self.assertEqual(plan[0]["status"], "conflict")
        with self.assertRaises(importer.ImportFailure):
            importer.apply_plan(api, "holidays", {"plan": plan}, self.root / "holiday-conflict.json")
        self.assertEqual(api.posts, 0)

    def test_holiday_range_and_duplicate_validation(self):
        for rows in [[{"date": "2027-01-01", "name": "Neujahr"}],
                     [{"date": "2027-05-01", "name": "Staatsfeiertag"}] * 2,
                     [{"date": "2027-5-1", "name": "Staatsfeiertag"}]]:
            with self.subTest(rows=rows), self.assertRaises((ValueError, importer.ImportFailure)):
                importer.holiday_plan({**self.holiday_document(), "holidays": rows})

    def test_holiday_source_contains_six_dates_inside_semester(self):
        path = SCRIPTS.parents[1] / "artifacts/export-import/holidays-AT-2027-S.json"
        if not path.exists():
            self.skipTest("Local holiday input not available")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([entry["sourceKey"] for entry in importer.holiday_plan(data)],
                         ["2027-03-29", "2027-05-01", "2027-05-06", "2027-05-17", "2027-05-27", "2027-08-15"])

    def test_easter_closure_covers_all_ten_days_and_preserves_ostermontag(self):
        path = SCRIPTS.parents[1] / "artifacts/export-import/nonteaching-AT-2027-S.json"
        if not path.exists():
            self.skipTest("Local combined closure input not available")
        data = json.loads(path.read_text(encoding="utf-8"))
        plan = importer.holiday_plan(data)
        dates = {entry["sourceKey"]: entry["payload"]["name"] for entry in plan}
        self.assertEqual(len(dates), 15)
        self.assertTrue(all(f"2027-03-{day:02}" in dates for day in range(20, 30)))
        self.assertNotIn("2027-03-19", dates)
        self.assertNotIn("2027-03-30", dates)
        self.assertEqual(dates["2027-03-29"], "Ostermontag")

    def test_combined_closure_reuses_six_existing_holidays(self):
        root = SCRIPTS.parents[1] / "artifacts/export-import"
        if not (root / "nonteaching-AT-2027-S.json").exists():
            self.skipTest("Local closure input not available")
        data = json.loads((root / "nonteaching-AT-2027-S.json").read_text(encoding="utf-8"))
        base = json.loads((root / "holidays-AT-2027-S.json").read_text(encoding="utf-8"))
        api = FakeAPI("holidays")
        api.rows = [{**row, "id": index + 101, "revision": 1} for index, row in enumerate(base["holidays"])]
        plan = importer.holiday_plan(data, api.rows)
        self.assertEqual(sum(e["status"] == "existing" for e in plan), 6)
        self.assertEqual(sum(e["status"] == "would_create" for e in plan), 9)
        report = {"plan": plan}
        importer.apply_plan(api, "holidays", report, self.root / "easter.json")
        repeat = {"plan": importer.holiday_plan(data, api.rows)}
        importer.apply_plan(api, "holidays", repeat, self.root / "easter-repeat.json")
        self.assertEqual((api.posts, len(api.rows)), (9, 15))
        self.assertTrue(repeat["verified"])


if __name__ == "__main__":
    unittest.main()
