# Resource Planner User Manual

## Quick Start

### What the system does

Resource Planner helps a university planner maintain academic data, build conflict-aware teaching and exam schedules, review the semester in a calendar, correct sessions, and publish controlled schedule revisions.

The current application has one planner role. It does not require accounts or separate permissions.

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

3. Optional: create or refresh the demonstration dataset:

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

**Expected result:** The application opens in **Schedule > Calendar**. The backend health address `http://127.0.0.1:8000/health` returns `{"status":"ok"}`.

The default database is `backend/planner.db`. Set `DATABASE_URL` before starting the backend only when your environment uses a different SQLAlchemy database URL.

### First-use setup

If planning data already exists, skip this section.

1. Expand **Academic Data** in the navigation.
2. Create a **Semester** and **Cohort**.
3. Create a **Study type**, then create at least one **Time window** for it.
4. Create at least one coded **Lecturer** and one coded **Room** with sufficient capacity.
5. Open **Courses** and create a course with its units, session-size range, Semester, Cohort, Study type, initial Lecturer, and initial Room.
6. Return to **Schedule > Calendar**.
7. If no revision exists, select **Start Draft**.

**Expected result:** The course is available for planning in its Semester, and an editable working revision exists. A course with missing or inactive required planning data remains visible but unavailable.

### Common use cases

#### Generate a draft for one course

1. Open **Schedule > Calendar** and show **Planning inputs** if they are hidden.
2. Select **One course**, then select the Semester and Course.
3. Review **Inputs for the next draft**. Keep the defaults for routine generation.
4. Select **Generate**.

**Expected result:** A complete course draft is saved in the active working revision and appears in the Calendar. If no complete valid draft can be produced, the application explains the reasons and preserves the existing draft.

#### Review and correct a session in the Calendar

1. In **Schedule > Calendar**, choose **Week**, **Day**, or **Month**.
2. Select a teaching or exam occurrence.
3. In the session pane, select **Edit session**.
4. Change the available fields and select **Save**.

**Expected result:** The occurrence and affected summaries refresh in place. The Calendar mode, date, filters, and selected revision remain unchanged.

#### Optimize several courses together

1. In **Schedule > Calendar**, show **Planning inputs** and select **Several courses**.
2. Select between 1 and 20 courses.
3. Optionally enter future unavailable dates as comma-separated dates.
4. Select **Optimize selected courses**.
5. Review the preparation dialog and confirm.

**Expected result:** The application saves the best valid complete or improved partial results for the prepared snapshot, preserves worse or stale schedules, and explains remaining units and failures per Course.

#### Prepare and generate exams

1. Open **Schedule > Exams** and select a Course in the shared context header.
2. Enable **This course requires an exam**, complete the requirement, and select **Save exam requirement**.
3. Under **Prepare exams**, select one or more eligible courses.
4. Select **Prepare exams**, review the confirmation, and select **Generate confirmed exams**.

**Expected result:** Each selected course receives either one valid active exam or a clear failure reason. Generated exams appear distinctly from teaching sessions in the Calendar.

#### Publish a schedule revision

1. Open **Schedule > Versions**.
2. Select the active working revision.
3. Optionally select **Mark ready for review**.
4. Select **Publish revision**.
5. Review the known gaps and warnings, then select **Publish explicitly**.

**Expected result:** The revision becomes the Semester's immutable **Current publication**. Publishing directly from Draft is also allowed.

### Where to go next

Use the Detailed Guide for catalog maintenance, custom constraints, calendar summaries and filters, resource availability, holidays, manual session management, exam rules, lifecycle recovery, limitations, and troubleshooting.

## Detailed Guide

### System concepts

- A **Course** is assigned to one current Semester for new planning.
- A **Draft Schedule** belongs to one Course and Semester and contains teaching sessions.
- A teaching session has a date, interval, explicit unit count, Lecturer, Cohort, and Room.
- One teaching unit is 45 minutes. Default session duration includes a 10-minute break between units.
- **Remaining units** equal current Course units minus saved session units, never less than zero.
- **Generation constraints** affect the next generation. Calendar filters only affect what is visible.
- The Semester has at most one editable **Working revision** and one **Current publication**.
- A Working revision may be **Draft** or **Ready for review**. A Published or superseded revision is read-only.
- Validation warnings describe current problems but do not automatically move or delete sessions.
- Saved Published content remains unchanged when current catalog data changes; current warnings may still reflect new validation conditions.

### Navigation and workspace layout

The primary navigation contains:

- **Schedule**
  - **Calendar**
  - **Versions**
  - **Exams**
- **Academic Data**
  - **Semesters**
  - **Holidays**
  - **Cohorts**
  - **Courses**
  - **Study types**
  - **Time windows**
  - **Lecturers**
  - **Rooms**

Only the selected Schedule workspace is shown. The compact Schedule context header keeps the relevant Semester, Revision, and Course selectors available.

On wide screens, select **Unpin navigation** to reclaim workspace width. Use **Open navigation** and **Pin navigation** to restore it. The wide-screen pin choice is retained on the same device.

At 820 pixels or narrower, select **Menu** to open the temporary navigation. **Close menu** or Escape closes it.

In Calendar, **Hide Planning inputs** reclaims additional width without changing the navigation. This choice is not retained after the application is revisited.

### Maintain Academic Data

Use **Academic Data** to create, edit, archive, reactivate, and safely delete the records used by scheduling.

#### Create a complete planning chain

1. Create the Semester and Cohort.
2. Create the Study type.
3. Create one or more Time windows for that Study type.
4. Create Lecturers and Rooms.
5. Create the Course last, linking the required records.

Courses, Cohorts, and Rooms require positive whole-number values where applicable. A Course's minimum session size cannot exceed its maximum.

#### Archive, reactivate, or delete a record

1. Select the record.
2. Select its archive, reactivate, or delete action.
3. Review the usage dialog.
4. Confirm only after reviewing dependent records and saved schedule references.

Permanent deletion is available only when it is safe. Otherwise, archive the record. Archived parents remain visible for historical context but are unavailable for new planning.

Changing Semester dates is blocked when saved sessions would fall outside the new range. Reassigning a Course affects future planning; existing schedule snapshots retain their saved context.

### Maintain Lecturers and Rooms

Lecturers and Rooms have a name, unique reference code, lifecycle state, and unavailable periods. Rooms also have capacity.

#### Record recurring unavailability

1. Open **Academic Data > Lecturers** or **Rooms**.
2. Select the resource and add an unavailable period.
3. Choose the weekday, start time, and end time.
4. Save the resource.

#### Record dated unavailability

1. Select the resource.
2. Add the start and end date.
3. Add the start and end time.
4. Save the resource.

Generation avoids ineligible, inactive, unavailable, or undersized resources. Existing sessions are not moved automatically when availability or capacity changes; they receive current validation warnings when applicable.

### Maintain Course resource eligibility

1. Open **Academic Data > Courses** and edit the Course.
2. Search and select its eligible Lecturers and Rooms.
3. Save the Course.

One session uses exactly one Lecturer and one Room. Generation prefers contiguous Lecturer blocks and Room reuse where hard eligibility, availability, capacity, and conflict rules permit.

Inactive or insufficient-capacity choices cannot be newly added. Previously saved invalid relationships remain visible so the planner can repair them.

### Maintain institution holidays

1. Open **Academic Data > Holidays**.
2. Enter the full-date **Date** and **Name**.
3. Select **Create holiday**.
4. Use **Edit** to correct a holiday or **Delete** to remove it after confirmation.

Future teaching and exam generation treats holidays as unavailable full dates. A saved session already on a newly added holiday is not moved; the Calendar shows a current warning.

Removing a holiday stops it from constraining future generation. It does not change saved sessions.

### Work with schedule revisions

If a Semester has no lifecycle revision, select **Start Draft** in Calendar or Versions. Schedule mutations are unavailable until the Draft is created.

Use the shared context header to choose:

- Semester in all Schedule destinations
- Revision in Calendar and Versions
- Course in Calendar and Exams

When both exist, Calendar lets you switch between **Working R…** and **Published R…**. Only the Working revision is editable. Historical revisions remain available as read-only content.

### Configure and generate one Course

#### Use default constraints

The default planning period comes from the Semester. Weekly teaching windows come from the Course's active Study type Time windows.

Select **Generate** without changing the defaults.

#### Set custom constraints

1. Select the Course and Semester.
2. Set a planning start and end date inside the Semester.
3. Add one or more valid weekly windows.
4. Select **Generate**.

Successful generation saves the constraints for that Course and Semester. A failed attempt does not overwrite the saved constraints or replace the existing draft.

#### Restore defaults

Select **Clear custom constraints** in the constraint editor. Existing sessions do not move until generation is run again.

### Optimize several Courses

The several-Course workflow coordinates the selected Courses as one conflict-aware problem.

1. Select **Several courses** under Planning inputs.
2. Select 1 to 20 Courses.
3. Optionally enter comma-separated future unavailable dates in `YYYY-MM-DD` format.
4. Select **Optimize selected courses**.
5. Review the prepared input and existing schedules.
6. Confirm the operation.

The optimizer:

- maximizes scheduled teaching units
- avoids new Lecturer, Room, and Cohort overlaps
- respects active periods, eligibility, availability, Room capacity, generation windows, and holidays
- preserves unselected sessions as fixed Semester occupancy
- may retain an improved partial schedule with understandable remaining-unit reasons
- does not replace an existing Course result with fewer units or an otherwise worse approved comparison
- applies stable preference priorities when several maximum-unit arrangements are possible

An approved replacement may replace manual edits in a selected Course. Cancel the confirmation to keep all current schedules unchanged.

After the operation, review **Saved optimization result**. It separates complete, improved partial, unchanged, failed, and stale outcomes. Use **Retry failed or stale courses** to prepare those Courses again from current data.

The optimality statement applies to the prepared snapshot. If inputs became stale, preserved stale outcomes are not described as globally optimal for the refreshed Semester.

### Review the Calendar

Calendar opens in **Week** mode. Available modes are:

- **Week** for the main operational view
- **Day** for one date
- **Month** for broad date navigation
- **List** for the dense Courses overview and its List/Weekly review controls

Use the previous, **Current**, and next controls or choose a calendar date. List mode does not use date navigation.

Calendar filters include Course, Cohort, Lecturer, Room, Study type, Session type, Lifecycle, and Validation. Filters do not change saved data.

The operational summary contains:

- **Unscheduled work**
- **Conflicts**
- **Capacity issues**
- **Planning failures**
- **Needs review**

Select a summary card to inspect its contributors. A dated contributor opens the affected date or occurrence; an undated Course or outcome moves to List mode. Filtered summaries clearly identify that they describe a subset rather than the complete revision.

### Inspect, edit, or delete a session

Select a teaching or exam occurrence to open the session pane. It shows identifying details, revision context, and current warnings.

For an editable Working revision:

1. Select **Edit session**.
2. Change the available values.
3. Select **Save** or **Cancel**.

Teaching edits can change date, start time, end time, Lecturer, and Room. Exam edits can change date, start time, responsible Lecturer, and Room; configured duration remains fixed.

Select **Delete with confirmation** to remove only the selected teaching or exam session.

If you have unsaved pane changes and try to close it or change context, the application asks whether to **Keep editing** or discard the changes. Keeping the edit is the safe default.

On a wide Calendar, the pane docks beside the Calendar when enough content width is available. It overlays at smaller widths and becomes a full-screen modal pane at 820 pixels or narrower.

### Add, delete, or clear teaching sessions

#### Add one Draft Session

1. Select a Course and Semester in **One course** mode.
2. Under **Add one Draft Session**, enter the date, start time, and whole-number units.
3. Review or change the proposed end time.
4. Select the Lecturer, Cohort, and capacity-sufficient Room.
5. Select **Add Draft Session**.

The explicit unit count controls Course progress. The end time may be adjusted for merged teaching or a longer pause.

#### Delete one teaching session

Open the selected session and choose **Delete with confirmation**, or use the action in List mode. The confirmation shows removed coverage and resulting remaining units.

#### Clear one Course draft

Select the Course under Planning inputs and choose **Clear course draft**. The confirmation identifies the exact Course and Semester. Source records and saved generation constraints remain.

Cancelled, failed, or stale confirmations make no saved change.

### Understand validation warnings

Current warnings can identify:

- Lecturer, Room, or Cohort overlaps
- insufficient Room capacity
- a session outside active Course generation constraints
- a session outside its Study type Time windows
- a session on an institution holiday
- inactive, unavailable, ineligible, or missing planning resources
- an exam that no longer satisfies a hard constraint

Back-to-back sessions are not overlaps when one ends exactly as the next begins. One session may have several warnings.

Warnings are non-blocking for manual teaching edits and lifecycle publication. They do not automatically repair the schedule. Exam creation and correction use stricter hard-constraint validation and reject invalid placements.

### Configure and schedule exams

Open **Schedule > Exams**. The selected Course's **Exam requirement** includes:

- enabled or disabled state
- identifier
- positive whole duration in minutes
- positive required Room capacity
- required free-text exam type
- responsible eligible Lecturer
- optional override of the recommended date range

The default recommendation is seven through fourteen calendar days after the final teaching session. It is a soft preference. Manual placement may occur outside it when all hard constraints pass.

An enabled Course without a final teaching session can be saved but is unavailable for placement. A Course with an active exam is also unavailable for another active exam, and its consumed configuration is read-only.

#### Generate exams

1. Save valid requirements for the Courses.
2. Under **Prepare exams**, select 1 to 100 eligible Courses.
3. Select **Prepare exams**.
4. Review the preparation and select **Generate confirmed exams**.

Automatic generation considers all selected exams together. It requires:

- a final teaching session and placement after it
- a date inside the Semester and not on a holiday
- an eligible, active, available responsible Lecturer
- an eligible, active, available Room with sufficient capacity
- no Lecturer, Room, or Cohort overlap with teaching or exams
- a start time proposed from an active Study type Time window

The recommended date range is preferred but not required. Teaching sessions are never moved by exam generation.

#### Place or correct an exam manually

Select **Place exam manually** for an eligible unscheduled configuration, or select an exam in Calendar and choose **Edit session**. Set the date, start time, Lecturer, and Room, then save.

Manual placement may use a start time outside Study type proposal times, but every hard constraint still applies.

Deleting an active exam leaves its current requirement enabled and unscheduled. Deleting a past exam removes only that historical exam.

### Manage Versions and publication

Open **Schedule > Versions** to see:

- Active working revision
- Current publication
- selected revision state and permitted actions
- collapsed revision history and ordered lifecycle events

The lifecycle is:

`Draft → Ready for review → Published`

**Ready for review** is optional and informational. It does not lock editing or require approval. A planner may publish directly from Draft or from Ready for review.

Before publication, the confirmation lists known incomplete work and warnings. These do not block an explicit publication.

After publication:

- the Published snapshot is immutable
- a new revision starts as a copy of the Current publication
- working changes do not alter the Current publication
- publishing the successor makes the former publication superseded

Use **Abandon revision** to remove an unpublished revision from active work without deleting its history. Use **Restore revision** only when no other Working revision exists. Superseded publications remain immutable and cannot be restored directly.

### Important rules and edge cases

- No scheduling change can be saved without an active Working revision.
- Draft and Ready for review are editable; Current Published, superseded, abandoned, and historical selections are read-only.
- A stale edit, optimization, lifecycle action, or destructive confirmation never overwrites newer saved state.
- Existing sessions are not moved when catalog data, holidays, availability, or capacity changes.
- Failed one-Course generation preserves the previous draft.
- Semester optimization may save useful improved partial results but never silently worsens protected schedules.
- Generation constraints do not edit existing sessions until generation is selected.
- Removing a holiday affects future generation but not saved sessions.
- An active exam prevents creation of a second active exam for that Course and Semester.
- A failed refresh keeps the last known complete view where available and presents a retry action.
- Navigation, filters, mode changes, pinning, and hiding Planning inputs do not mutate schedule data.

### Known limitations

The current application does not provide:

- lecturer review links or lecturer accounts
- authentication or role-based permissions
- external planning-data import or synchronization
- automated email delivery or institutional single sign-on
- drag-and-drop, resize, duplicate, split, or merge actions in Calendar
- automatic repair of saved sessions after a warning appears
- multiple institutional or partial-day holiday calendars
- student registration, grading, invigilator management, or external room booking
- background optimization, algorithm selection, or persisted optimization-result history
- an independently published Course; publication always covers the Semester revision

The current limit is 20 Courses per teaching optimization and 100 Courses per exam-generation request.

### Troubleshooting

#### The application does not open

1. Confirm the backend is running on port 8000.
2. Open `http://127.0.0.1:8000/health`.
3. Confirm the client is running on port 5173.
4. Verify `VITE_API_BASE_URL` points to the backend address.

#### Schedule actions are unavailable

Open **Schedule > Versions** or Calendar and select **Start Draft**. Published and historical revisions are read-only; choose the Working revision to make changes.

#### A Course is missing or unavailable

1. Confirm the selected Semester matches the Course.
2. Confirm the Course, Semester, Cohort, and Study type are active.
3. Confirm an active Time window exists.
4. Confirm the Course has an active eligible Lecturer and usable eligible Room.
5. Correct the record in Academic Data and return to Schedule.

#### One-Course generation fails

Read every displayed reason. Check the selected period and windows, session-size values, active planning data, eligible resources, availability, Room capacity, and holidays.

#### Optimization leaves a Course unchanged

Review its outcome. The prepared solution may not have been strictly better, the Course may have become stale, or hard constraints may prevent improvement. Use the displayed reasons and retry stale or failed Courses after correcting the inputs.

#### A Course cannot be selected for exam generation

Read its reason under **Unavailable courses**. Common verified causes are a disabled or invalid requirement, no final teaching session, an existing active exam, or unavailable current planning data.

#### Edit session is not available

Confirm you are viewing the Active working revision and that the selected occurrence still has current editable backing data. Published and historical content cannot be edited in place.

#### The application asks about unsaved changes

Select **Keep editing** to return to the pane without losing the draft. Discard only when you want to continue to the requested destination or context without saving.

#### A record cannot be deleted

Review **Dependent records** and **Saved schedules** in the deletion dialog. Remove safe dependencies first or archive the record.

#### A change is reported as stale

Another saved change occurred after the form or confirmation opened. Refresh or reopen the action, review current values, and try again.

#### Warnings remain after a correction

Open **Current warnings** and correct each remaining cause. Resolving one issue may leave another warning on the same session.

#### Last-known data is shown

The latest refresh failed. The application preserves the last complete view where possible. Select the visible **Retry** action before making decisions from the displayed data.

### Glossary

- **Planner:** The current end-user role with scheduling and administration access.
- **Working revision:** The single editable Semester revision in Draft or Ready for review state.
- **Current publication:** The immutable Published revision currently designated for the Semester.
- **Generation constraints:** The date range and weekly windows used for the next one-Course generation.
- **Eligible resource:** A Lecturer or Room permitted for a Course.
- **Unavailable period:** A recurring or dated interval during which a resource cannot be assigned.
- **Validation warning:** A current, non-blocking issue attached to a saved occurrence.
- **Prepared snapshot:** The exact input state approved before optimization or generation executes.
- **Stale outcome:** A result not saved because relevant planning state changed after preparation.
- **Active exam:** An exam dated today or later; only one is allowed per Course and Semester.
- **Past exam:** An exam dated before today that remains available as historical schedule content.
