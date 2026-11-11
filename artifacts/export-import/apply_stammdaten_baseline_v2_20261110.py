"""Apply the prepared V2 course values and plan cleanup atomically in place."""
from datetime import datetime
import hashlib
import json
import sqlite3
from zoneinfo import ZoneInfo

from create_stammdaten_baseline_v2_20261110 import (
    DATABASE, OUTPUT, REMOVED, check, courses, snapshot,
)


def main():
    baseline_path = OUTPUT / 'STAMMDATEN_ONLY_V2_2026-11-10.db'
    report = json.loads((OUTPUT / 'VERIFICATION.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == report['backupFileSha256']
    with sqlite3.connect(baseline_path.as_uri() + '?mode=ro', uri=True) as baseline:
        check(baseline)
        expected = snapshot(baseline)
        baseline_courses = courses(baseline)
    assert expected == report['after']
    now = datetime.now(ZoneInfo('Europe/Vienna'))
    application_dir = OUTPUT / ('APPLICATION_' + now.strftime('%Y-%m-%d_%H-%M-%S'))
    application_dir.mkdir(exist_ok=False)
    recovery = application_dir / 'FULL_BEFORE_APPLICATION.db'
    audit_path = application_dir / 'APPLICATION.json'
    live = sqlite3.connect(DATABASE.as_uri() + '?mode=rw', uri=True, timeout=15)
    live.execute('PRAGMA foreign_keys=ON')
    try:
        live.execute('BEGIN EXCLUSIVE')
        check(live)
        assert live.execute(
            "SELECT COUNT(*) FROM optimization_operations WHERE phase IN ('preparing','optimizing','checking')"
        ).fetchone()[0] == 0, 'An optimization is active; update aborted.'
        before = snapshot(live)
        # Abort rather than silently discard master-data edits since preparation.
        auth_tables = {'planner_accounts', 'planner_account_access', 'planner_sessions',
                       'planner_startup_credentials'}
        for table in set(before) - set(REMOVED) - auth_tables - {'courses'}:
            assert before[table] == expected[table], f'Master data changed: {table}'
        current_courses = courses(live)
        assert current_courses == baseline_courses or before['courses'] == report['before']['courses'], (
            'Courses changed since baseline preparation; update aborted.'
        )
        recovery.write_bytes(live.serialize())
        with sqlite3.connect(recovery) as saved:
            check(saved)
            assert snapshot(saved) == before
        live.execute('PRAGMA defer_foreign_keys=ON')
        for table in REMOVED:
            live.execute(f'DELETE FROM "{table}"')
        # Set the prepared values directly; never subtract 8 again on a rerun.
        live.executemany(
            'UPDATE courses SET total_units=?,revision=? WHERE id=?',
            [(row['total_units'], row['revision'], key)
             for key, row in baseline_courses.items()],
        )
        after = snapshot(live)
        assert courses(live) == baseline_courses
        assert all(after[table]['rows'] == 0 for table in REMOVED)
        assert all(after[table] == before[table]
                   for table in set(before) - set(REMOVED) - {'courses'})
        check(live)
        audit = {
            'appliedAt': now.isoformat(), 'database': str(DATABASE),
            'baseline': str(baseline_path), 'recoveryBackup': str(recovery),
            'method': 'In-place exclusive SQLite transaction; server remains running',
            'status': 'prepared; commit pending', 'before': before, 'after': after,
            'courseCount': len(baseline_courses),
            'totalLehreinheiten': sum(row['total_units'] for row in baseline_courses.values()),
            'totalEinheitenUnchanged': True, 'sessionSettingsUnchanged': True,
            'currentAuthenticationPreserved': True,
            'integrityCheck': 'ok', 'foreignKeyCheck': 'ok',
            'knownLimitation': report['knownLimitation'],
        }
        audit_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
        live.commit()
        audit['status'] = 'committed'
        live.execute('BEGIN')
        check(live)
        actual = snapshot(live)
        assert actual['courses'] == after['courses']
        assert all(actual[table]['rows'] == 0 for table in REMOVED)
        live.rollback()
        audit['postCommitVerified'] = True
        audit_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
        (OUTPUT / 'ACTIVATION.json').write_text(json.dumps({
            'status': 'applied', 'appliedAt': now.isoformat(),
            'applicationReport': str(audit_path), 'recoveryBackup': str(recovery),
            'database': str(DATABASE),
        }, indent=2), encoding='utf-8')
        print(json.dumps({key: audit[key] for key in (
            'status', 'courseCount', 'totalLehreinheiten', 'recoveryBackup',
            'postCommitVerified',
        )}, indent=2))
    except BaseException:
        live.rollback()
        raise
    finally:
        live.close()


if __name__ == '__main__':
    main()
