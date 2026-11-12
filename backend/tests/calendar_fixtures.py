"""Explicitly give each seeded cohort/semester its own copy of fixture hours."""
from sqlalchemy import select
from app.models.planning import Course, Semester, CohortCalendar, CohortCalendarTimeWindow

def complete_fixture_calendars(db):
    db.flush()
    template=db.scalar(select(CohortCalendar).order_by(CohortCalendar.id))
    for course in db.scalars(select(Course)).all():
        calendar=db.scalar(select(CohortCalendar).where(CohortCalendar.cohort_id==course.cohort_id,CohortCalendar.semester_id==course.current_semester_id))
        if calendar is not None:continue
        semester=db.get(Semester,course.current_semester_id)
        calendar=CohortCalendar(cohort_id=course.cohort_id,semester_id=semester.id,start_date=semester.start_date,end_date=semester.end_date,name=f"Calendar {course.cohort_id}/{semester.id}")
        db.add(calendar);db.flush()
        for window in list(template.time_windows) if template else []:
            db.add(CohortCalendarTimeWindow(cohort_calendar_id=calendar.id,kind=window.kind,weekday=window.weekday,date=window.date,is_intensive=window.is_intensive,start_time=window.start_time,end_time=window.end_time,sort_order=window.sort_order,is_active=window.is_active))
    db.flush()
    db.expire_all()

def create_api_calendar(client, name):
    semesters=client.get('/api/academic/semesters').json()['items']
    semester=semesters[0] if semesters else client.post('/api/academic/semesters',json={'name':'Fixture semester','startDate':'2026-01-01','endDate':'2028-12-31'}).json()
    cohorts=client.get('/api/academic/cohorts').json()['items']
    calendars=client.get('/api/academic/cohort-calendars').json()['items']
    used={c['cohortId'] for c in calendars if c['semesterId']==semester['id']}
    cohort=next((c for c in cohorts if c['id'] not in used),None)
    if cohort is None:cohort=client.post('/api/academic/cohorts',json={'name':name+str(len(cohorts)+1),'studentCount':30}).json()
    response=client.post('/api/academic/cohort-calendars',json={'cohortId':cohort['id'],'semesterId':semester['id'],'startDate':semester['startDate'],'endDate':semester['endDate']})
    assert response.status_code==201,response.text
    return response.json()
