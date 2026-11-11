"""Prepare an audited baseline copy without modifying the running database."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / 'backend/planner.db'
OUTPUT = ROOT / 'backend/backups/STAMMDATEN_BASELINE_V2_2026-11-10'
REMOVED = [
    'optimization_operations', 'lecturer_review_activity_events',
    'lecturer_review_feedback', 'lecturer_review_links',
    'lecturer_review_invalid_source_states', 'planning_outcomes',
    'schedule_revision_events', 'draft_sessions', 'draft_schedules',
    'exam_sessions', 'generation_constraint_windows',
    'generation_constraint_sets', 'schedule_revisions',
]


def snapshot(connection):
    result = {}
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    for (table,) in tables:
        rows = connection.execute(f'SELECT * FROM "{table}"').fetchall()
        encoded = sorted(json.dumps(row, ensure_ascii=False) for row in rows)
        result[table] = {
            'rows': len(rows),
            'sha256': hashlib.sha256('\n'.join(encoded).encode()).hexdigest(),
        }
    return result


def check(connection):
    assert connection.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def courses(connection):
    connection.row_factory = sqlite3.Row
    rows = {row['id']: dict(row) for row in connection.execute('SELECT * FROM courses')}
    connection.row_factory = None
    return rows


def main():
    if sys.argv[1:] != ['--prepare-only']:
        raise SystemExit('Use --prepare-only. This script never applies the baseline.')
    # Fixed directory prevents accidentally subtracting 8 a second time.
    OUTPUT.mkdir(exist_ok=False)
    full = OUTPUT / 'FULL_BEFORE_CLEANUP_V2_2026-11-10.db'
    clean = OUTPUT / 'STAMMDATEN_ONLY_V2_2026-11-10.db'
    report_path = OUTPUT / 'VERIFICATION.json'
    # The live database is opened read-only. Every mutation targets an isolated
    # in-memory copy captured with SQLite's consistent online backup API.
    source = sqlite3.connect(DATABASE.as_uri() + '?mode=ro', uri=True, timeout=15)
    connection = sqlite3.connect(':memory:')
    try:
        source.backup(connection)
    finally:
        source.close()
    connection.execute('PRAGMA foreign_keys=ON')
    try:
        connection.execute('BEGIN')
        check(connection)
        before = snapshot(connection)
        original_courses = courses(connection)
        assert len(original_courses) == 94
        assert all(row['total_units'] > 8 for row in original_courses.values())
        caps = [row['id'] for row in original_courses.values()
                if row['max_session_units'] > row['total_units'] - 8]
        assert sorted(caps) == [69, 70, 80, 94]
        assert all(original_courses[key]['total_units'] == 9 for key in caps)
        full.write_bytes(connection.serialize())
        with sqlite3.connect(full) as backup:
            check(backup)
            assert snapshot(backup) == before
        connection.execute('PRAGMA defer_foreign_keys=ON')
        for table in REMOVED:
            connection.execute(f'DELETE FROM "{table}"')
        connection.execute('UPDATE courses SET total_units=total_units-8, revision=revision+1')
        after = snapshot(connection)
        updated_courses = courses(connection)
        preserved = sorted(set(before) - set(REMOVED) - {'courses'})
        assert all(before[table] == after[table] for table in preserved)
        assert all(after[table]['rows'] == 0 for table in REMOVED)
        changes = []
        for key, original in original_courses.items():
            expected = dict(original)
            expected['total_units'] -= 8
            expected['revision'] += 1
            assert updated_courses[key] == expected
            assert expected['total_units'] > 0
            assert 0 < expected['min_session_units'] <= expected['max_session_units']
            preferred = expected['preferred_session_units']
            assert preferred is None or expected['min_session_units'] <= preferred <= expected['max_session_units']
            changes.append({
                'id': key, 'name': original['name'],
                'oldLehreinheiten': original['total_units'],
                'newLehreinheiten': expected['total_units'],
                'unchangedTotalEinheiten': original['overall_units'],
                'unchangedMinSessionUnits': original['min_session_units'],
                'unchangedMaxSessionUnits': original['max_session_units'],
                'unchangedPreferredSessionUnits': original['preferred_session_units'],
                'sessionSettingsExceedNewLehreinheiten': key in caps,
            })
        check(connection)
        clean.write_bytes(connection.serialize())
        with sqlite3.connect(clean) as backup:
            check(backup)
            assert snapshot(backup) == after
        with (OUTPUT / 'LV_CHANGES.csv').open('w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(changes[0]))
            writer.writeheader()
            writer.writerows(changes)
        report = {
            'createdAt': datetime.now(ZoneInfo('Europe/Vienna')).isoformat(),
            'version': 2, 'source': str(DATABASE),
            'fullRecoveryBackup': str(full), 'cleanStammdatenBackup': str(clean),
            'formula': 'new Lehreinheiten = previous Lehreinheiten - 8',
            'planningColumn': 'courses.total_units',
            'unchangedInformationColumn': 'courses.overall_units',
            'courseCount': len(changes), 'sessionSettingsUnchanged': True,
            'sessionSettingsConflictCourseIds': caps,
            'knownLimitation': 'Four LVs have 1 LE but retain min=2, max=4, preferred=3 at user request; resolve before planning these LVs.',
            'totalLehreinheitenBefore': sum(row['total_units'] for row in original_courses.values()),
            'totalLehreinheitenAfter': sum(row['total_units'] for row in updated_courses.values()),
            'removedTables': REMOVED, 'preservedTables': preserved,
            'before': before, 'after': after,
            'integrityCheck': 'ok', 'foreignKeyCheck': 'ok',
            'activation': 'Prepared only; not applied to the running system',
            'liveDatabaseOpenedReadOnly': True,
            'backupFileSha256': hashlib.sha256(clean.read_bytes()).hexdigest(),
        }
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        (OUTPUT / 'README.txt').write_text(
            'STAMMDATEN BASELINE V2 - 2026-11-10\n\n'
            f'Clean baseline: {clean.name}\nFull recovery: {full.name}\n\n'
            'Created from the current database, preserving current master data and accounts.\n'
            'All teaching/exam plans, versions, history, outcomes, generation overrides,\n'
            'optimization receipts and lecturer-review records have been removed.\n'
            'All 94 LVs: Lehreinheiten reduced by 8 exactly once. Total Einheiten unchanged.\n'
            'All minimum/maximum/preferred session settings are unchanged, as requested.\n'
            'KNOWN LIMITATION: LV IDs 69, 70, 80, 94 now have 1 LE but retain min=2, max=4,\n'
            'preferred=3. These settings conflict with the application validation rules.\n'
            'Resolve their settings before planning these LVs. See LV_CHANGES.csv for names.\n'
            'Course revisions incremented to identify the changed course records.\n'
            'Other master data, resource eligibility, exam configurations, availability,\n'
            'accounts and authentication state are preserved. See VERIFICATION.json and LV_CHANGES.csv.\n\n'
            'REUSE: Restore this clean .db file with backend/scripts/restore_sqlite_db.py,\n'
            'with every process using the TARGET database stopped. Validate with a preview first.\n'
            'Restore the prepared baseline directly; DO NOT run the reduction script again.\n'
            'Restoring replaces the target data, accounts and authentication with this snapshot.\n'
            'PREPARED ONLY: This baseline has NOT been applied to the running system.\n'
            'No draft is precreated in the backup.\n'
            'The earlier baseline is retained unchanged.\n', encoding='utf-8',
        )
        connection.commit()
        connection.execute('BEGIN')
        check(connection)
        assert snapshot(connection) == after
        connection.rollback()
        report['backupDatabaseVerified'] = True
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({key: report[key] for key in (
            'cleanStammdatenBackup', 'fullRecoveryBackup', 'courseCount',
            'totalLehreinheitenBefore', 'totalLehreinheitenAfter', 'activation',
        )}, indent=2))
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == '__main__':
    main()
