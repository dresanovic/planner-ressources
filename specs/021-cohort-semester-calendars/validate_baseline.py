"""Read-only SS2027 acceptance check against the requested teaching calendar."""
from datetime import date, time, timedelta
import json
from pathlib import Path
import sqlite3
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.models.planning import Course
from app.services.draft_schedule_repository import load_course_plan, load_semester_plan, load_generation_constraints
from app.services.schedule_generation import window_applies


def validate(path):
    connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    assert connection.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    assert connection.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert all(connection.execute('SELECT count(*) FROM '+t).fetchone()[0]==0 for t in ['draft_sessions','draft_schedules','exam_sessions','schedule_revisions'])
    assert dict(connection.execute('SELECT kind,count(*) FROM cohort_calendar_time_windows GROUP BY kind'))=={'weekly':25,'dated':37}
    holidays={date.fromisoformat(r[0]) for r in connection.execute('SELECT date FROM institution_holidays')}
    for day in range(22,31):assert date(2027,3,day) in holidays
    assert date(2027,3,20) not in holidays and date(2027,3,21) not in holidays
    for day in [1,6,17,27]:assert date(2027,5,day) in holidays
    connection.close()
    weekly={1:{0:('08:15','17:00'),1:('08:15','17:00'),2:('08:15','17:00'),3:('08:15','17:00')}}
    weekly[2]=weekly[3]={d:('08:15','17:00') for d in [0,1]}
    for cohort in [4,5,6]:weekly[cohort]={0:('08:15','16:15'),1:('13:45','21:30'),2:('13:45','19:45')}
    for cohort in [7,8,9,10]:weekly[cohort]={4:('13:45','21:30'),5:('08:00','16:00')}
    intensive={4:('2027-04-26','2027-04-29'),5:('2027-04-19','2027-04-23'),6:('2027-03-15','2027-03-19'),7:('2027-04-26','2027-04-30'),8:('2027-03-01','2027-03-06'),9:('2027-03-08','2027-03-13'),10:('2027-04-05','2027-04-10')}
    engine=create_engine('sqlite://',creator=lambda:sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True))
    checks=0
    with Session(engine) as db:
        courses=list(db.scalars(select(Course)))
        assert len(courses)==94
        for course in courses:
            constraints=load_generation_constraints(db,load_course_plan(db,course.id),load_semester_plan(db,1))
            first=date(2027,3,1) if course.cohort_id<=6 else date(2027,2,26)
            assert constraints.planning_period.start_date==first and constraints.planning_period.end_date==date(2027,7,9)
            day=date(2027,2,19)
            while day<=date(2027,8,17):
                period=intensive.get(course.cohort_id)
                marked=bool(period and period[0]<=day.isoformat()<=period[1])
                hours=('08:15','17:00') if marked else weekly[course.cohort_id].get(day.weekday())
                actual=[w for w in constraints.allowed_windows if window_applies(w,day,constraints.allowed_windows)] if first<=day<=date(2027,7,9) and day not in holidays else []
                expected=bool(hours and first<=day<=date(2027,7,9) and day not in holidays)
                assert len(actual)==int(expected),(course.id,day)
                if actual:assert (actual[0].start_time,actual[0].end_time)==tuple(time.fromisoformat(h) for h in hours)
                checks+=1
                day+=timedelta(days=1)
    engine.dispose()
    return {'status':'passed','courseCount':94,'courseDateChecks':checks,'weeklyWindows':25,'intensiveDates':37,'planningRows':0}


if __name__=='__main__':
    print(json.dumps(validate(Path(sys.argv[1])),indent=2))
