# Cohort calendars: development setup and use

The application now derives each LV's calendar from its existing cohort and semester. The LV-to-cohort relationship and all LV units are preserved. There is no independently editable calendar selection on an LV.

In Stammdaten:
1. Create/select a cohort and a semester.
2. Under **Kohortenkalender**, create the calendar for that pair and enter Unterrichtsbeginn/Unterrichtsende. Only one calendar is allowed per pair.
3. Under **Zeitfenster**, select that calendar. Enter normal hours as weekly windows; enter intensive dates as dated windows marked Intensivwoche. Intensive windows replace weekly windows on those dates. Shared holidays block teaching.
4. Assign LVs to their cohort and semester. Their calendar follows automatically.

The SS2027 baseline contains ten calendars, 25 weekly windows and 37 intensive dates. WI/Master starts 26 February; BSD/AI starts 1 March; teaching ends 9 July. Easter is 22-30 March inclusive; the four specified May holidays remain blocked.

## Development reset

Old Studienform databases require an explicit reset; they are not automatically upgraded at startup. Historical migration files remain unchanged for reference. The reset keeps master data/accounts and removes all teaching/exam plans, schedule versions/history, generation overrides, reviews and optimization results.

Prepare a fresh isolated candidate (source is opened read-only):

```powershell
.\backend\.venv\Scripts\python.exe backend/scripts/reset_cohort_calendar_baseline.py --output backend/backups/NEW_UNIQUE_DIRECTORY
```

Review VERIFICATION.json and the new database. Stop every backend/database user, then restore the generated file with `backend/scripts/restore_sqlite_db.py --backup FULL_PATH --database C:/Codex/planner-resource/backend/planner.db --apply --backend-stopped`. The restore creates another full recovery backup. Restart the backend and refresh the browser.

Backups using the former Studienform schema (including the earlier V3) are recovery sources for the previous application version; do not restore them directly into this application version.

Known preserved master-data issue: LV IDs 69,70,80,94 have 1 LE but minimum session size 2 LE. Resolve their session settings before planning those LVs.
