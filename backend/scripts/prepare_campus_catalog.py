"""Build lecturer/course import files from saved, visible CAMPUSonline LV lists."""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re


def rounded_units(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError("Invalid source UE value")
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def excluded_course(title):
    return re.fullmatch(r"(?:bachelorprüfung|masterprüfung|masterarbeit)(?:\s+.*)?", title.strip().casefold()) is not None


def prepare(source_dir: Path, output_dir: Path, target_semester: str):
    sources, people, courses = [], {}, {}
    for path in sorted(source_dir.glob("curriculum-*-2026-S.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw["semester"] != "2026 S":
            raise ValueError(f"Wrong source semester: {path}")
        curriculum_id = re.search(r"curriculumVersionId=(\d+)", raw["url"]).group(1)
        pagination = re.fullmatch(r"1\s*-\s*(\d+)\s+von\s+(\d+)", raw["pagination"][0])
        if not pagination or int(pagination[1]) != int(pagination[2]) or int(pagination[2]) != len(raw["courses"]):
            raise ValueError(f"Incomplete source list: {path}")
        source = {"curriculumVersionId": curriculum_id, "curriculumName": raw["curriculum"],
                  "url": raw["url"], "capturedAt": raw["capturedAt"],
                  "courseCount": len(raw["courses"]), "file": path.name,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        sources.append(source)
        for course in raw["courses"]:
            if course["courseId"] in courses:
                raise ValueError("Duplicate course across source lists; reconcile explicitly")
            refs = []
            for person in course["lecturers"]:
                person_id, name = person["personId"], person["name"].strip()
                if not re.fullmatch(r"[0-9A-F]{16}", person_id) or not name:
                    raise ValueError("Invalid person ID or name")
                reference = f"campus02:{person_id}"
                if reference in people and people[reference]["name"] != name:
                    raise ValueError(f"Different names for person {person_id}")
                entry = people.setdefault(reference, {
                    "name": name, "referenceCode": reference, "sourcePersonId": person_id,
                    "sourcePersonUrl": f"https://online.campus02.at/C02online/ee/rest/pages/brm.pm.bc/business-card/{person_id}",
                    "sourceCourses": []})
                entry["sourceCourses"].append({"courseId": course["courseId"], "code": course["code"],
                                               "title": course["title"], "curriculumVersionId": curriculum_id})
                refs.append(reference)
            text_names = course["additionalText"].splitlines()[1:]
            if not course["teachingRolePresent"] or text_names != [p["name"] for p in course["lecturers"]]:
                raise ValueError(f"Incomplete visible lecturer links for course {course['code']}")
            if not refs or len(refs) != len(set(refs)):
                raise ValueError(f"Empty or duplicate lecturer assignment: {course['code']}")
            courses[course["courseId"]] = {
                "sourceCourseId": course["courseId"], "code": course["code"], "title": course["title"],
                "sourceUrl": f"https://online.campus02.at/C02online/ee/ui/ca2/app/desktop/#/slc.tm.cp/student/courses/{course['courseId']}",
                "curriculumVersionId": curriculum_id, "curriculumName": raw["curriculum"],
                "courseType": course["courseType"], "sourceUnits": course["sourceUnits"],
                "roundedTotalUnits": rounded_units(course["sourceUnits"]),
                "lecturerReferenceCodes": refs}
    if {s["curriculumVersionId"] for s in sources} != {"297", "301", "349", "362"}:
        raise ValueError("Exactly the four agreed curriculum versions are required")
    sorted_people = sorted(people.values(), key=lambda p: p["name"].casefold())
    excluded_ids = {c["sourceCourseId"] for c in courses.values() if excluded_course(c["title"])}
    sorted_courses = sorted((c for c in courses.values() if c["sourceCourseId"] not in excluded_ids),
                            key=lambda c: (c["curriculumVersionId"], c["code"]))
    metadata = {"schemaVersion": 1, "sourceSystem": "CAMPUSonline CAMPUS 02", "sourceSemester": "2026 S",
                "intendedTargetSemester": target_semester, "sources": sources,
                "referenceCodePolicy": "campus02:<business-card-person-id>; stability across future exports must be checked",
                "roundingPolicy": "nearest integer, ties rounded up (ROUND_HALF_UP); original UE retained",
                "courseExclusionPolicy": "Exclude Bachelorprüfung, Masterprüfung and Masterarbeit (including numbered suffixes)",
                "excludedCourseCount": len(excluded_ids)}
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {"lecturers.json": {**metadata, "lecturers": sorted_people},
               "courses.json": {**metadata, "courses": sorted_courses}}
    mapping = {"schemaVersion": 1, "semesterName": target_semester, "courses": []}
    for course in sorted_courses:
        mapping["courses"].append({
            "sourceCourseId": course["sourceCourseId"], "code": course["code"],
            "include": course["roundedTotalUnits"] > 0,
            "name": f"{course['title']} [{course['code']}] – {target_semester}",
            "cohortName": None,
            "lecturerReferenceCode": course["lecturerReferenceCodes"][0] if len(course["lecturerReferenceCodes"]) == 1 else None,
            "suggestedLecturerReferenceCodes": course["lecturerReferenceCodes"],
            "roomReferenceCode": None, "totalUnits": course["roundedTotalUnits"],
            "minSessionUnits": None, "maxSessionUnits": None,
            "note": "Zero UE: retained in source catalog, excluded from teaching import" if course["roundedTotalUnits"] == 0
                    else "Confirm cohort, lecturer, eligible room, and session unit limits before import"})
    # Remove only explicitly excluded source IDs; preserve all other planner edits.
    mapping_path = output_dir / f"courses-{target_semester.replace(' ', '-')}.mapping.json"
    if not mapping_path.exists():
        mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        existing_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        retained = [row for row in existing_mapping["courses"] if row["sourceCourseId"] not in excluded_ids]
        if len(retained) != len(existing_mapping["courses"]):
            existing_mapping["courses"] = retained
            mapping_path.write_text(json.dumps(existing_mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for filename, data in outputs.items():
        (output_dir / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overview = [f"# LV-Grundlage für {target_semester}", "", "Quelle: CAMPUSonline, 2026 S. Keine bestätigten Lehrzuordnungen für 2027 S.", "",
                "UE werden auf die nächstgelegene ganze Zahl gerundet; .5 wird aufgerundet. Bachelorprüfung, Masterarbeit und Masterprüfung sind ausgeschlossen. Andere 0-UE-Einträge werden nicht als Lehre importiert.", "",
                "| LV-Code | Titel | Studienplan-ID | Typ | Quell-UE | Gerundet | Vortragende aus 2026 S |", "|---|---|---|---|---:|---:|---|"]
    for course in sorted_courses:
        names = "; ".join(people[ref]["name"] for ref in course["lecturerReferenceCodes"])
        cells = [course["code"], course["title"], course["curriculumVersionId"], course["courseType"],
                 course["sourceUnits"], course["roundedTotalUnits"], names]
        overview.append("| " + " | ".join(str(v).replace("|", "\\|") for v in cells) + " |")
    (output_dir / "courses-overview.md").write_text("\n".join(overview) + "\n", encoding="utf-8")
    print(f"Prepared {len(sorted_people)} lecturers and {len(sorted_courses)} courses.")
    print(f"Positive rounded UE: {sum(c['roundedTotalUnits'] > 0 for c in sorted_courses)}; zero UE: {sum(c['roundedTotalUnits'] == 0 for c in sorted_courses)}")
    print(f"Mapping (existing edits preserved): {mapping_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--target-semester", default="2027 S")
    args = parser.parse_args()
    prepare(args.source_dir, args.output_dir, args.target_semester)
