# Calendar capacity example: 2027 S, eleven Master courses

Read-only observation on 05.11.2026, course IDs49–59. This is diagnostic evidence
for I-007, not a new timetable, a full feasibility proof, or a production check.

The current data has358requiredLE =16,110teachingminutes =268h30min.
The semester runs19.02.2027–17.08.2027. Current default teaching windows are
Friday15:55–22:00 (365minutes) and Saturday08:15–15:00 (405minutes). After
institutional holidays,25Fridays and23Saturdays remain:18,440calendar minutes,
or307h20min. There are no saved course-window overrides in this observation.

With allowed whole session sizes2–4LE and10minute breaks **within each session**,
an optimistic per-day packing calculation yields:

| Day | Usable dates | Minutes per date | Optimistic LE per date | Total LE ceiling |
| --- | ---: | ---: | ---: | ---: |
| Friday |25|365|7|175|
| Saturday |23|405|8|184|
| Total |48|18,440| |359|

Friday can contain3LE(155min)+4LE(210min)=365min. Saturday can contain four
2LEsessions(100min each)=400min. This calculation allows unconstrained use of
eligible session sizes and ignores limited lecturers/rooms, resource
unavailability, fixed teaching/exams, course-specific distribution and the
per-course/date restriction. It also imposes no extra break between separate
sessions, matching the current duration formula. Those are optimistic
assumptions: their relaxation makes this an upper bound, not an achievable plan.

Demand358LE is only1LE below that ceiling. The simple calendar test therefore
does **not** prove insufficient capacity, but reveals very little slack. It
cannot explain every open LE or rule out resource/packing/search limitations.
The raw difference between calendar and teaching minutes cannot be converted
directly into schedulable LE: breaks and fragmented daily windows consume it.

Repeating the same optimistic calculation with five-minute within-session breaks
still yields359LE, so shorter breaks do not raise this particular coarse ceiling.
They do provide different packing choices: two4LEsessions would take390minutes
instead of420minutes, and could fit Saturday's405minutes. Whether that improves
the real joint timetable must be validated against all actual constraints.
Five-minute breaks are a confirmed proposal scope for I-008, not an implemented
or approved exception for any current appointment.

The analysis must be recomputed when selection, dates, windows, holidays,
resources, fixed occupancy or rules change. It does not establish how much more
LE a longer search will find, nor a minimum necessary additional-slot duration.
