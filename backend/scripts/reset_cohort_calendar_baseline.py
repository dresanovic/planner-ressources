"""Prepare the SS2027 development master-data reset; source is always read-only.

Activation uses restore_sqlite_db.py after all database users have stopped.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'artifacts/export-import'))
from sqlalchemy import create_engine
from app.db.schema import initialize_database
from create_stammdaten_baseline_v2_20261110 import REMOVED, check, snapshot
from create_stammdaten_baseline_v3_20261112 import PROFILES, START, END, days


def prepare(source_path, output):
    source_path, output = source_path.resolve(), output.resolve()
    output.mkdir(exist_ok=False, parents=True)
    source = sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)
    original = sqlite3.connect(':memory:')
    source.backup(original)
    source.close()
    check(original)
    before = snapshot(original)
    (output / 'FULL_BEFORE_RESET.db').write_bytes(original.serialize())
    target = output / 'STAMMDATEN_COHORT_CALENDARS_SS2027.db'
    engine = create_engine('sqlite:///' + target.as_posix())
    initialize_database(engine)
    engine.dispose()
    db = sqlite3.connect(target)
    db.execute('PRAGMA foreign_keys=OFF')
    copied = []
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        if table in REMOVED or table in ('cohort_calendars', 'cohort_calendar_time_windows'):
            continue
        source_columns = {r[1] for r in original.execute(f'PRAGMA table_info("{table}")')}
        columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")') if r[1] in source_columns]
        if not columns:
            raise ValueError('No source master data for ' + table)
        names = ','.join('"'+c+'"' for c in columns)
        rows = original.execute(f'SELECT {names} FROM "{table}"').fetchall()
        db.executemany(f'INSERT INTO "{table}" ({names}) VALUES ({",".join("?" for _ in columns)})', rows)
        copied.append(table)
    assert db.execute('SELECT id,name FROM semesters').fetchall() == [(1, '2027 S')]
    assert db.execute('SELECT count(*) FROM courses').fetchone()[0] == 94
    assert db.execute('SELECT count(*) FROM cohorts').fetchone()[0] == 10
    db.execute('UPDATE semesters SET start_date=?,end_date=?,revision=revision+1 WHERE id=1', (START.isoformat(), END.isoformat()))
    db.execute("DELETE FROM institution_holidays WHERE date IN ('2027-03-20','2027-03-21')")
    for day in days(date(2027,3,22), date(2027,3,30)):
        db.execute('INSERT INTO institution_holidays(date,name,revision) SELECT ?,?,1 WHERE NOT EXISTS (SELECT 1 FROM institution_holidays WHERE date=?)', (day.isoformat(), 'Osterferien (unterrichtsfrei)', day.isoformat()))
    for name, cohorts, first, regular, intensive_first, intensive_last in PROFILES:
        for cohort_id in cohorts:
            cohort_name = db.execute('SELECT name FROM cohorts WHERE id=?', (cohort_id,)).fetchone()[0]
            name = cohort_name + ' / 2027 S'
            db.execute('INSERT INTO cohort_calendars(id,cohort_id,semester_id,start_date,end_date,name,normalized_name,normalized_name_key,name_repair_required,is_active,revision) VALUES (?,?,1,?,?,?,?,?,0,1,1)', (cohort_id,cohort_id,first.isoformat(),END.isoformat(),name,name.casefold(),name.casefold()))
            for weekday, (start,end) in regular.items():
                db.execute("INSERT INTO cohort_calendar_time_windows(cohort_calendar_id,kind,weekday,start_time,end_time,sort_order,is_active,revision,is_intensive) VALUES (?,'weekly',?,?,?,?,1,1,0)", (cohort_id,weekday,start+':00.000000',end+':00.000000',weekday))
            if intensive_first:
                for day in days(date.fromisoformat(intensive_first),date.fromisoformat(intensive_last)):
                    db.execute("INSERT INTO cohort_calendar_time_windows(cohort_calendar_id,kind,date,start_time,end_time,sort_order,is_active,revision,is_intensive) VALUES (?,'dated',?,'08:15:00.000000','17:00:00.000000',0,1,1,1)", (cohort_id,day.isoformat()))
    db.commit()
    db.execute('PRAGMA foreign_keys=ON')
    check(db)
    after = snapshot(db)
    for table in copied:
        if table not in ('courses','semesters','institution_holidays'):
            assert after[table] == before[table], table
    old_columns = [r[1] for r in original.execute('PRAGMA table_info(courses)')]
    new_columns = [r[1] for r in db.execute('PRAGMA table_info(courses)')]
    old = {r[0]:dict(zip(old_columns,r)) for r in original.execute('SELECT * FROM courses')}
    for row in db.execute('SELECT * FROM courses'):
        assert dict(zip(new_columns,row)) == {k:old[row[0]][k] for k in new_columns}
    assert all(after[t]['rows']==0 for t in REMOVED)
    counts = dict(db.execute('SELECT kind,count(*) FROM cohort_calendar_time_windows GROUP BY kind'))
    assert counts == {'weekly':25,'dated':37}, counts
    db.close()
    original.close()
    report = {'status':'prepared; not activated','baseline':str(target),'source':str(source_path),'before':before,'after':after,'windows':counts,'cohortsPreserved':10,'courseCohortLinksAndUnitsPreserved':94,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'integrityCheck':'ok','foreignKeyCheck':'ok'}
    (output/'VERIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'backend/planner.db')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=prepare(args.source,args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('before','after')},indent=2))
