"""Prepare the approved SS2027 calendar in an isolated baseline; never activate it."""
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from create_stammdaten_baseline_v2_20261110 import REMOVED, check, snapshot

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'backend/planner.db'
OUTPUT = ROOT / 'backend/backups/STAMMDATEN_BASELINE_V3_2026-11-12'
START, END = date(2027, 2, 26), date(2027, 7, 9)
BB = {4: ('13:45', '21:30'), 5: ('08:00', '16:00')}
AI = {0: ('08:15', '16:15'), 1: ('13:45', '21:30'), 2: ('13:45', '19:45')}
BSD = {day: ('08:15', '17:00') for day in range(4)}
PROFILES = [
    ('Berufsbegleitend – WI – 2. Semester', [7], START, BB, '2027-04-26', '2027-04-30'),
    ('Berufsbegleitend – WI – 4. Semester', [8], START, BB, '2027-03-01', '2027-03-06'),
    ('Berufsbegleitend – WI – 6. Semester', [9], START, BB, '2027-03-08', '2027-03-13'),
    ('Berufsbegleitend – IT-Master – 2. Semester', [10], START, BB, '2027-04-05', '2027-04-10'),
    ('Vollzeit – BSD – 2. Semester', [1], date(2027, 3, 1), BSD, None, None),
    ('Vollzeit – BSD – 4./6. Semester', [2, 3], date(2027, 3, 1), {k: BSD[k] for k in (0, 1)}, None, None),
    ('AI – 2. Semester', [4], date(2027, 3, 1), AI, '2027-04-26', '2027-04-29'),
    ('AI – 4. Semester', [5], date(2027, 3, 1), AI, '2027-04-19', '2027-04-23'),
    ('AI – 6. Semester', [6], date(2027, 3, 1), AI, '2027-03-15', '2027-03-19'),
]


def days(first, last):
    while first <= last:
        yield first
        first += timedelta(days=1)


def main():
    if sys.argv[1:] != ['--prepare-only']:
        raise SystemExit('Use --prepare-only. This script never changes the source database.')
    OUTPUT.mkdir(exist_ok=False)
    source = sqlite3.connect(SOURCE.as_uri() + '?mode=ro', uri=True, timeout=15)
    db = sqlite3.connect(':memory:')
    try:
        source.backup(db)
    finally:
        source.close()
    db.execute('PRAGMA foreign_keys=ON')
    check(db)
    before = snapshot(db)
    recovery = OUTPUT / 'FULL_BEFORE_V3.db'
    recovery.write_bytes(db.serialize())
    original_courses = {r[0]: r for r in db.execute('SELECT * FROM courses')}
    course_columns = [r[1] for r in db.execute('PRAGMA table_info(courses)')]
    assert len(original_courses) == 94
    assert db.execute('SELECT id,name FROM semesters').fetchall() == [(1, '2027 S')]
    expected_cohorts = {
        1: 'Business Software Development – 2. Semester',
        2: 'Business Software Development – 4. Semester',
        3: 'Business Software Development – 6. Semester',
        4: 'Business Analytics & AI - 2.Semester',
        5: 'Business Analytics & AI - 4.Semester',
        6: 'Business Analytics & AI - 6.Semester',
        7: 'Wirtschaftsinformatik - 2.Semester',
        8: 'Wirtschaftsinformatik - 4.Semester',
        9: 'Wirtschaftsinformatik - 6.Semester',
        10: 'MA IT & Wirtschaftsinformatik - 2.Semester',
    }
    assert dict(db.execute('SELECT id,name FROM cohorts')) == expected_cohorts
    assert set(db.execute('SELECT DISTINCT current_semester_id FROM courses')) == {(1,)}
    db.execute('BEGIN')
    db.execute('PRAGMA defer_foreign_keys=ON')
    for table in REMOVED:
        db.execute(f'DELETE FROM "{table}"')
    db.execute('UPDATE semesters SET start_date=?,end_date=?,revision=revision+1 WHERE id=1', (START.isoformat(), END.isoformat()))
    db.execute('UPDATE study_types SET is_active=0,revision=revision+1 WHERE is_active=1')
    db.execute('UPDATE study_type_time_windows SET is_active=0,revision=revision+1 WHERE is_active=1')
    db.execute("DELETE FROM institution_holidays WHERE date IN ('2027-03-20','2027-03-21')")
    for day in days(date(2027, 3, 22), date(2027, 3, 30)):
        db.execute('INSERT INTO institution_holidays(date,name,revision) SELECT ?,?,1 WHERE NOT EXISTS (SELECT 1 FROM institution_holidays WHERE date=?)', (day.isoformat(), 'Osterferien (unterrichtsfrei)', day.isoformat()))
    required = {'2027-05-01': 'Staatsfeiertag', '2027-05-06': 'Christi Himmelfahrt', '2027-05-17': 'Pfingstmontag', '2027-05-27': 'Fronleichnam'}
    for day, name in required.items():
        db.execute('INSERT INTO institution_holidays(date,name,revision) SELECT ?,?,1 WHERE NOT EXISTS (SELECT 1 FROM institution_holidays WHERE date=?)', (day, name, day))
    holidays = {r[0] for r in db.execute('SELECT date FROM institution_holidays')}
    calendar, mappings, profiles, cohort_profile = [], [], [], {}
    for name, cohorts, first, regular, intensive_first, intensive_last in PROFILES:
        normalized = name.casefold()
        profile_id = db.execute('INSERT INTO study_types(name,normalized_name,normalized_name_key,name_repair_required,is_active,revision) VALUES (?,?,?,0,1,1)', (name, normalized, normalized)).lastrowid
        for cohort in cohorts:
            cohort_profile[cohort] = profile_id
            db.execute('UPDATE courses SET study_type_id=?,revision=revision+1 WHERE cohort_id=?', (profile_id, cohort))
        count = intensive_count = 0
        for day in days(first, END):
            intensive = bool(intensive_first and intensive_first <= day.isoformat() <= intensive_last)
            hours = ('08:15', '17:00') if intensive else regular.get(day.weekday())
            if not hours or day.isoformat() in holidays:
                continue
            start, end = hours
            db.execute("INSERT INTO study_type_time_windows(study_type_id,kind,weekday,date,is_intensive,start_time,end_time,sort_order,is_active,revision) VALUES (?,'dated',NULL,?,?,?,?,?,1,1)", (profile_id, day.isoformat(), int(intensive), start+':00.000000', end+':00.000000', count))
            calendar.append({'studyTypeId': profile_id, 'profile': name, 'date': day.isoformat(), 'start': start, 'end': end, 'intensive': intensive})
            count += 1
            intensive_count += int(intensive)
        profiles.append({'id': profile_id, 'name': name, 'cohortIds': cohorts, 'start': first.isoformat(), 'end': END.isoformat(), 'regularHours': regular, 'intensiveStart': intensive_first, 'intensiveEnd': intensive_last, 'windows': count, 'intensiveWindows': intensive_count})
    # Verify every field of every course: only the profile and revision may change.
    for row in db.execute('SELECT * FROM courses'):
        previous = dict(zip(course_columns, original_courses[row[0]]))
        expected = dict(previous, study_type_id=cohort_profile[previous['cohort_id']], revision=previous['revision']+1)
        assert dict(zip(course_columns, row)) == expected
        mappings.append({'courseId': row[0], 'courseName': previous['name'], 'cohortId': previous['cohort_id'], 'oldStudyTypeId': previous['study_type_id'], 'newStudyTypeId': expected['study_type_id']})
    changed = set(REMOVED) | {'semesters', 'study_types', 'study_type_time_windows', 'courses', 'institution_holidays'}
    after = snapshot(db)
    assert all(before[t] == after[t] for t in set(before)-changed)
    assert all(after[t]['rows'] == 0 for t in REMOVED)
    assert db.execute('SELECT count(*) FROM study_types WHERE is_active=1').fetchone()[0] == 9
    assert len(calendar) == len({(r['studyTypeId'],r['date']) for r in calendar})
    assert all(START.isoformat() <= r['date'] <= END.isoformat() and r['date'] not in holidays for r in calendar)
    assert all((r['start'],r['end']) == ('08:15','17:00') for r in calendar if r['intensive'])
    assert [p['intensiveWindows'] for p in profiles] == [5,6,6,6,0,0,4,5,5]
    check(db)
    db.commit()
    clean = OUTPUT / 'STAMMDATEN_ONLY_V3_2026-11-12.db'
    clean.write_bytes(db.serialize())
    db.close()
    with sqlite3.connect(clean.as_uri()+'?mode=ro', uri=True) as saved:
        check(saved)
        assert snapshot(saved) == after
    for filename, rows in [('TEACHING_CALENDAR.csv', calendar), ('LV_PROFILE_CHANGES.csv', mappings)]:
        with (OUTPUT / filename).open('w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    report = {'version': 3, 'status': 'Prepared only; not activated', 'source': str(SOURCE), 'baseline': str(clean), 'recovery': str(recovery), 'semesterStart': START.isoformat(), 'semesterEnd': END.isoformat(), 'sourceOpenedReadOnly': True, 'courseCount': len(mappings), 'calendarWindowCount': len(calendar), 'profiles': profiles, 'removedTables': REMOVED, 'preservedTables': sorted(set(before)-changed), 'before': before, 'after': after, 'sha256': hashlib.sha256(clean.read_bytes()).hexdigest(), 'integrityCheck': 'ok', 'foreignKeyCheck': 'ok', 'intensiveMode': 'Replace regular hours on each intensive date', 'calendarRepresentation': 'All active teaching windows are dated; no active weekly windows', 'knownLimitation': 'Existing course IDs 69,70,80,94 have 1 LE with minimum 2 LE. Their unit and session settings have not been changed.'}
    (OUTPUT / 'VERIFICATION.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUTPUT / 'README.md').write_text('# Stammdaten baseline V3 — SS2027\n\nPrepared only; the running database has not been changed.\n\nSemester: 26 February–9 July 2027 inclusive. BSD and AI teaching starts on 1 March.\nAll ten cohorts and all course unit/session settings are preserved. All 94 courses have been assigned to nine active calendar profiles. The two legacy profiles and their windows remain inactive.\n\nRegular availability is expanded to dated windows to enforce intensive-week replacement without an application change. Intensive dates use 08:15–17:00, including specified Saturdays. Holidays take precedence. Easter closure is 22–30 March inclusive. The four May holidays are retained; other existing holidays are preserved. No teaching windows exist outside the requested dates.\n\nTeaching/exam schedules, schedule revisions/history, generation overrides, outcomes, optimization operations and lecturer-review records are removed. Accounts, authentication and other master data are preserved.\n\nReview TEACHING_CALENDAR.csv, LV_PROFILE_CHANGES.csv and VERIFICATION.json. The SQLite file is STAMMDATEN_ONLY_V3_2026-11-12.db. FULL_BEFORE_V3.db is the full source snapshot. Both files contain accounts/authentication and should be kept private.\n\nKnown existing limitation: LV IDs 69,70,80,94 have 1 LE but minimum session size 2 LE; resolve before planning these courses. V3 does not repeat the V2 reduction.\n\nActivation is a separate operation. Use backend/scripts/restore_sqlite_db.py with a preview and all processes using the target database stopped. Restoring replaces target data and accounts with this snapshot. Do not activate against a different environment without checking its current data.\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','baseline','courseCount','calendarWindowCount','integrityCheck','foreignKeyCheck']}, indent=2))


if __name__ == '__main__':
    main()
