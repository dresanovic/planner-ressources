# Resource Planner User Manual

## Quick Start

### What the system does

Resource Planner helps a university planner maintain scheduling data, generate one-Course draft teaching schedules, review a semester, correct sessions manually, and see schedule warnings. It is currently a planner-only application: there are no accounts or separate user roles.

### Before you start

You need:

- Python with the packages in `backend/requirements.txt`
- Node.js and npm with the packages in `client/package.json`
- two terminal windows
- planning records for the semester, courses, cohorts, study types, time windows, lecturers, and rooms

If your organization already hosts the application and has prepared its data, open the supplied application address and continue with [First-use setup](#first-use-setup).

### Open the system locally

1. In the first PowerShell terminal, open the `backend` directory.
2. Install the backend packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Optional: create or refresh the idempotent demonstration dataset:

   ```powershell
   python scripts/seed_dummy_planning_data.py
   ```

4. Start the backend:

   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

5. In the second PowerShell terminal, open the `client` directory.
6. Install the client packages:

   ```powershell
   npm install
   ```

7. Point the client at the backend and start it:

   ```powershell
   $env:VITE_API_BASE_URL='http://127.0.0.1:8000'
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

8. Open `http://127.0.0.1:5173` in a browser.

**Expected result:** The application opens on **Schedule**. The left navigation contains **Schedule** and **Academic Data**. The backend health address `http://127.0.0.1:8000/health` returns `{"status":"ok"}`.

The default database is `backend/planner.db`. Set `DATABASE_URL` before starting the backend only when your environment uses a different SQLAlchemy database URL.

### First-use setup

If planning data already exists, skip this section.

1. Expand **Academic Data** in the left navigation.
2. Create at least one **Semester** and **Cohort**.
3. Create a **Study type**, then create at least one **Time window** for it.
4. Create at least one coded **Lecturer** and one coded, capacity-valid **Room**.
5. Open **Courses** and create a course with its units, session-size range, Semester, Cohort, Study type, initial Lecturer, and initial Room.
6. Return to **Schedule**.

**Expected result:** The course appears for its assigned Semester and can be selected for planning. A course without an active time window, active eligible Lecturer, or usable eligible Room remains visible but unavailable.

### Common use cases

#### Generate a draft for one course

1. Open **Schedule** and select **One course**.
2. Select the **Semester** and **Course** under **Planning inputs**.
3. Review **Inputs for the next draft**. Leave the defaults unchanged for a routine generation.
4. Select **Generate**.

**Expected result:** A complete course draft is saved and appears in **Courses overview**. The planning summary shows scheduled and remaining units. If no complete valid draft can be produced, the application shows all detected reasons and does not replace the existing draft with a partial result.

#### Review a semester and correct a session

1. In **Courses overview**, choose **List** or **Weekly**.
2. Optionally filter by Course, Cohort, Lecturer, Room, or Study type.
3. Select **Edit** on a session.
4. Change its date, start time, end time, Lecturer, or Room.
5. Select **Save**.

**Expected result:** The saved values appear in both review modes and remain available after filters change. Any applicable non-blocking validation alerts are recalculated.

#### Add one missing Draft Session

1. Select a Course and Semester in **One course** mode.
2. Under **Add one Draft Session**, enter the date, start time, and whole-number units.
3. Review the proposed end time and adjust it if needed.
4. Select a capacity-sufficient Room.
5. Select **Add Draft Session**.

**Expected result:** The new session is added without replacing existing sessions. Scheduled units increase, remaining units decrease by the explicit unit count, and validation alerts refresh.

### Where to go next

Use the Detailed Guide for catalog maintenance, custom generation constraints, resource availability and eligibility, validation rules, deletion behavior, limitations, and troubleshooting.

## Detailed Guide

### System concepts

- A **Course** is assigned to exactly one current Semester for new planning.
- A **Draft Schedule** belongs to one Course and one Semester and contains Draft Sessions.
- A **Draft Session** has one date, time interval, explicit unit count, Lecturer, Cohort, and Room.
- One teaching unit is 45 minutes. The calculated default duration includes a 10-minute break between units.
- **Remaining units** equal current Course units minus the units in all saved sessions, never less than zero.
- **Generation constraints** control a future generation. **Overview filters** only change what is visible.
- Catalog edits affect future planning. Saved schedules retain the academic facts captured when they were saved.
- Validation alerts describe current problems but do not automatically move or delete sessions.

### Navigation

On a wide screen, use the persistent left sidebar. **Academic Data** expands to these destinations in order:

1. **Semesters**
2. **Cohorts**
3. **Courses**
4. **Study types**
5. **Time windows**
6. **Lecturers**
7. **Rooms**

On screens 820 pixels wide or narrower:

1. Select **Menu**.
2. Choose a destination, or select **Close menu** or press Escape to close it without navigating.

Selecting a destination closes the panel. Selecting the already active destination does not reset its form, filters, or other page state.

### Maintain Academic Data

Use **Show** to include all, active, or inactive records. Select a record's **Edit**, **Archive**, **Reactivate**, or **Delete** action as appropriate.

| Category | Required user-entered values | Important rules |
| --- | --- | --- |
| Semester | Name, Start date, End date | End cannot precede start; saved sessions must remain inside edited dates. |
| Cohort | Name, Student count | Student count is a positive whole number. |
| Study type | Name | The name is unique within Study types. |
| Time window | Study type, Day of week, Start time, End time | End must be later than start; exact duplicates for one Study type are rejected. |
| Course | Name, Total units, Minimum and Maximum session units, Semester, Cohort, Study type | All units are positive whole numbers; minimum cannot exceed maximum or total, and maximum cannot exceed total. |
| Lecturer | Name, Reference code | Code is unique within Lecturers; duplicate display names are allowed. |
| Room | Name, Reference code, Capacity | Capacity is a positive whole number; code is unique within Rooms. |

Names are compared without capitalization differences or surrounding spaces within each academic category. Resource codes use the same normalization within their own Lecturer or Room catalog.

#### Create a complete planning chain

1. Create the Semester and Cohort.
2. Create the Study type.
3. Create at least one Time window for that Study type.
4. Create the Lecturer and Room records.
5. Create the Course and select every required relationship.

**Expected result:** The Course is selectable only in its assigned Semester when the Course and all required parents and resources are active and valid.

#### Edit or reassign a Course

1. Open **Academic Data** > **Courses**.
2. Select **Edit** for the Course.
3. Change the current values or Semester assignment.
4. Select **Save changes**.

**Expected result:** Future planning uses the new values and Semester assignment. Existing schedules in the previous Semester retain their saved facts and remain reviewable.

#### Archive, reactivate, or delete an academic record

1. Select **Archive** to retire a record without deleting it.
2. Select **Reactivate** to make a valid inactive record available again.
3. Select **Delete**, review **Dependent records** and **Saved schedules**, then select **Delete permanently** only when enabled.

**Expected result:** Unused records can be permanently deleted. Referenced records are protected. Archiving a parent does not change dependent records' own status, but those dependents cannot be used for new planning until every required parent is active.

### Maintain Lecturers and Rooms

#### Find and edit a resource

1. Open **Lecturers** or **Rooms**.
2. Use **Search by name or code** and the **Show** filter.
3. Select **Edit**.
4. Change the name, code, or Room capacity and save.

**Expected result:** Future planning and current validation use the saved values. Existing sessions are not silently reassigned.

#### Record recurring unavailability

1. Edit a Lecturer or Room.
2. Under **Unavailable periods**, select **Recurring weekly**.
3. Select one or more weekdays and enter a start and end time.
4. Select **Add unavailable period**.

**Expected result:** The resource is unavailable in that interval on every selected weekday.

#### Record dated unavailability

1. Edit a Lecturer or Room.
2. Under **Unavailable periods**, select **Dated**.
3. Enter start and end dates and times.
4. Select **Add unavailable period**.

**Expected result:** The resource is unavailable throughout that dated interval. Existing overlapping sessions remain saved and receive an availability alert.

For both types, the end must be later than the start. Exact duplicates are rejected; partially overlapping periods are allowed and combine as unavailable time. A session ending exactly when unavailability starts, or starting exactly when it ends, does not overlap.

#### Remove or reactivate a resource

1. Select **Remove** for a Lecturer or Room.
2. Review active Course and saved-session usage.
3. Confirm **Place inactive** when the resource is referenced, or **Delete permanently** when it is safe to delete.
4. Use **Reactivate** later after correcting any invalid values.

**Expected result:** Referenced resources become inactive and retain their historical relationships. An unreferenced resource is deleted. Reactivation restores the resource to active choices where current capacity and other hard rules permit.

### Maintain Course resource eligibility

1. Open **Academic Data** > **Courses** and edit a Course.
2. Under **Eligible lecturers and rooms**, use Search if necessary.
3. Select one or more Lecturers and capacity-sufficient Rooms.
4. Select **Save eligibility**.

**Expected result:** The Course keeps distinct eligible sets and at least one Lecturer and one Room. Existing session assignments do not change when eligibility changes.

Important behavior:

- A Room cannot be newly added when its capacity is below the Cohort size.
- A planner edit cannot remove the last eligible Lecturer or Room.
- Increasing a Cohort size automatically removes newly insufficient Rooms from affected eligibility sets. Existing sessions keep their assignments and show capacity and eligibility alerts.
- Generation uses active, eligible, available, capacity-sufficient resources.
- Within each Course, generation prefers fewer Lecturer changes and Room reuse when hard rules allow. These are preferences, not rankings or quotas.

### Configure one-Course generation

#### Use default constraints

The default planning period is the Semester start and end. Default weekly windows come from the Course's Study type. Previously saved Course-Semester constraints load instead when they exist.

#### Set custom constraints

1. Select **One course**, a Semester, and a Course.
2. Under **Inputs for the next draft**, change **Start date** and **End date** if needed.
3. Add, edit, or remove allowed weekly windows with Weekday, Start, and End.
4. Select **Generate**.

**Expected result:** Successful generation saves the custom constraints for this Course and Semester. A failed generation leaves the previous saved constraints and draft unchanged.

#### Restore defaults

1. Select **Clear custom constraints**.
2. Review the restored dates and weekly windows.

**Expected result:** The entire saved custom constraint set for that Course-Semester is deleted and Semester/Study type defaults become active. Existing sessions do not change until generation is run again.

Custom dates must stay inside the Semester. At least one valid weekly window is required, and every window must end after it starts.

### Understand generation behavior

For a single Course, generation:

- covers the full Course unit count or fails without saving a partial replacement;
- uses 45-minute units and 10-minute inter-unit breaks;
- prefers the maximum session size and adjusts the final distribution to respect the minimum when possible;
- places at most one session for that Course on a date;
- stays inside the active planning period and allowed windows;
- uses another allowed window and more than one session in a week when needed;
- checks active resource eligibility, availability, and Room capacity;
- replaces the existing draft for the same Course and Semester only after a successful generation.

Generation does not avoid conflicts with other Courses. Review all alerts after generation.

### Review the Courses overview

The overview contains every saved Draft Schedule for the selected Semester, independently of the Course selected in **Planning inputs**.

Use:

- **List** for chronological rows;
- **Weekly** for grouping by week and day;
- Course, Cohort, Lecturer, Room, and Study type filters to narrow visibility;
- **Clear filters** to restore the complete view.

Filters combine: a session must match all active filters. If filters hide everything, the application shows **No sessions match the active filters**. If the Semester has no drafts, it shows **No Draft Schedules for this semester yet**.

### Edit an existing Draft Session

1. Locate the session in List or Weekly view.
2. Select **Edit**.
3. Change the Date, Start, End, Lecturer, or Room.
4. Select **Save** or **Cancel**.

Blocking edit rules include:

- the date must remain inside the Semester;
- end time must be later than start time;
- the Course cannot already have another session on the same date;
- a changed Lecturer or Room must currently be active, eligible, and available;
- a changed Room must have enough capacity.

Overlap and active-window problems do not block an otherwise valid edit; they appear as alerts after save. An unchanged legacy-invalid resource assignment can remain visible with alerts. Regeneration can replace manual edits.

### Add, delete, or clear sessions

#### Add one session

The Course's Lecturer and Cohort are inherited. The Room list contains current Rooms with sufficient capacity. Start time plus units proposes an end time, but the explicit unit count—not clock duration—controls remaining units.

Creation is blocked when:

- the date is outside the Semester;
- end is not later than start;
- units are missing, fractional, non-positive, or exceed remaining units;
- the Course already has a session on that date;
- the Room capacity is insufficient;
- a required source record no longer exists.

Other overlaps, availability, eligibility, and window issues are reported as non-blocking alerts after save.

#### Delete one session

1. Select **Delete** on the session.
2. Review its Course, Semester, units removed, and resulting remaining units.
3. Confirm the deletion.

**Expected result:** Only that session is removed. Deleting the last session also removes the empty Draft Schedule and shows all Course units as remaining.

#### Clear one Course draft

1. Select the Course and Semester in **One course** mode.
2. Select **Clear course draft**.
3. Review the number of sessions, removed coverage, and preservation notice.
4. Confirm the clear action.

**Expected result:** Only that Course-Semester Draft Schedule and its sessions are removed. Course, Semester, Lecturer, Room, Cohort, Study type, and saved generation constraints remain.

Both deletion actions use the current Draft revision. If data changes after the confirmation opens, the operation is cancelled as stale, current state is refreshed, and a new confirmation is required.

### Validation alerts

Alerts are calculated from the complete selected-Semester schedule, even when filters hide a related session.

The implemented alert types include:

- Lecturer, Room, and Cohort overlaps across Courses;
- Room capacity violations;
- sessions outside active Course-Semester generation constraints;
- sessions outside a Study type window when no custom constraints are active;
- assigned Lecturer or Room no longer eligible;
- assigned Lecturer or Room unavailable;
- missing reference data needed for validation.

Back-to-back sessions are not overlaps when one ends exactly as the other begins. A session may have several alerts, and an overlap alert can identify every related conflicting session available in the Semester.

Alerts are informational. They do not make generation conflict-aware and do not automatically repair the schedule.

### Important validation and edge cases

- A Course with no active Study type window remains visible but cannot use default generation.
- An inactive parent leaves dependents visible but unavailable for new planning.
- Changing Semester dates is blocked if saved sessions would fall outside the new range.
- A stale edit, eligibility update, or destructive action does not overwrite a newer saved change.
- Reducing Room capacity keeps existing relationships visible as invalid; increasing Cohort size removes newly insufficient eligible Rooms.
- If saved session units exceed a later-reduced Course total, remaining units display zero rather than a negative value.
- Generation constraints do not edit existing sessions until **Generate** is selected.
- A failed overview refresh keeps the last known schedules visible and offers **Retry refresh**.
- Cancelled edit, replacement, deletion, or clear dialogs make no saved change.

### Known limitations

The current application does not provide:

- a verified, supported **Several courses** workflow in this working-tree snapshot;
- conflict-aware or global semester optimization;
- automatic conflict resolution;
- public-holiday avoidance;
- exam scheduling;
- versioned review or publication states;
- a calendar-centered dashboard or drag-and-drop scheduling;
- lecturer review links, lecturer accounts, authentication, or role-based permissions;
- external planning-data import or synchronization;
- automated email or institutional single sign-on;
- persisted batch-operation history or background generation;
- bulk deletion across an entire Semester;
- session splitting or merging.

The **Several courses** area currently contains in-progress conflict-aware optimization work whose complete verification suite does not pass in this snapshot. Do not rely on those controls until implementation and verification are complete. The weekly view is a grouped review surface, not a full interactive calendar. Treat all alerts as work requiring planner review before a schedule is used operationally.

### Troubleshooting

#### The application does not open

1. Confirm the backend terminal is still running on port 8000.
2. Open `http://127.0.0.1:8000/health` and confirm the healthy response.
3. Confirm the client terminal is running on port 5173.
4. Restart the client after setting `VITE_API_BASE_URL` to the backend address.

#### Planning options are unavailable

The client could not reach or load the backend. Verify `VITE_API_BASE_URL`, the backend health response, and that both processes use the expected ports. The local backend creates or migrates its supported SQLite schema at startup.

#### A Course is missing or marked unavailable

1. Confirm the selected Semester matches the Course's current Semester assignment.
2. Confirm the Course, Semester, Cohort, and Study type are active.
3. Confirm the Study type has an active Time window.
4. Confirm the Course has an active eligible Lecturer and a usable eligible Room.
5. Correct the record in **Academic Data**, then return to **Schedule**.

#### Generation fails

Read every displayed reason. Common verified causes are invalid or overly narrow dates/windows, no fitting time window, invalid session-size values, missing planning data, no usable resource, unavailable resources, or insufficient Room capacity. Correct the named data or constraint and run generation again.

#### A session disappears from the overview

Clear the overview filters and check the selected Semester. A saved edit can move a session outside the current filter values or into another week, but not outside its Semester.

#### A record cannot be deleted

Open the delete dialog and review **Dependent records** and **Saved schedules**. Remove safe catalog dependencies first, or archive the record. Saved schedule references are intentionally protected.

#### A change is reported as stale

Another saved change occurred after the form or confirmation was opened. Refresh or reopen the record/action, review the current values, and submit or confirm again.

#### Alerts remain after an edit

Open the alert details and correct every remaining cause. Alerts are recalculated after saved changes, but resolving one conflict may leave another alert on the same session.

### Glossary

- **Planner:** The single current end-user role with access to scheduling and administration.
- **Generation constraints:** The date range and recurring weekly windows used for the next generation.
- **Overview filters:** Visibility controls that do not change saved schedules or generation inputs.
- **Eligible resource:** A Lecturer or Room the planner permits for a Course.
- **Unavailable period:** A recurring or dated interval during which a resource cannot be selected by generation or a changed edit assignment.
- **Validation alert:** A non-blocking warning attached to a saved Draft Session.
- **Draft revision:** The saved version used to prevent a stale confirmation from deleting newer work.
