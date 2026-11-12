# Cohort semester teaching calendars

## Confirmed scope
Replace Studienform as a planning dependency. Preserve LV-to-cohort relationships. A cohort has one calendar per semester, with teaching start/end dates, weekly windows and dated intensive windows. Intensive windows replace weekly hours on the same date. Shared holidays always block teaching. No historical compatibility is required in this development installation. Clear all existing plans with recovery backup; preserve all other master data and accounts.

## Acceptance
- Given an LV assigned to cohort A in semester S, all planning and validation use A/S calendar automatically, with no independent calendar choice on the LV.
- Given another cohort or semester, its calendar changes cannot affect A/S.
- Given an intensive date, only its intensive hours apply; regular evening hours remain available on non-intensive dates.
- Given a holiday or a date outside teaching boundaries, no candidate is generated.
- Given the SS2027 baseline, ten unchanged cohorts, 94 unchanged LV-to-cohort links and unit values are preserved; normal availability is weekly and dated availability contains only 37 intensive dates.
- Given current test plans, they and related schedule history/reviews/outcomes are removed only after a recovery backup.

## Contract
Replace study-types with cohort-calendars: each calendar has cohortId, semesterId, startDate, endDate, revision and timeWindows. Calendar ownership is unique for cohort+semester. LVs accept cohortId and semesterId; calendar is derived. Windows remain weekly/dated with isIntensive. Calendar mutations use optimistic revision checks. No separate Studienform field is presented in planning or LV editing.
