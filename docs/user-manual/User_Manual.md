# Resource Planner User Manual

## Quick Start

### What the system does

Resource Planner helps a university planner maintain academic data, build conflict-aware teaching and exam schedules, review the semester in a calendar, correct sessions, coordinate feedback with lecturers, and publish controlled schedule revisions.

The planner application is German. Accountless lecturers can review only the assignments shared through a temporary link and cannot change planning data. Selected German terms may differ between customer installations; this manual names the shipped defaults.

### Before you start

Choose one way to access the application:

- **Hosted installation:** use the address supplied by your organization.
- **Docker Desktop installation:** use a current Docker Desktop installation, an exact Resource Planner image tag supplied by the maintainer, and a dedicated local data folder.
- **Developer start:** use Python with `backend/requirements.txt`, Node.js and npm with `client/package.json`, and two terminal windows.

If your organization already hosts the application and has prepared its data, open the supplied application address and continue with [First-use setup](#first-use-setup).

### Install and open with Docker Desktop on Windows

This procedure is for a local single-computer installation. It runs the complete browser application and backend in one Linux container. Docker Desktop's current Windows requirements and installer are available in the [official Docker Desktop installation guide](https://docs.docker.com/desktop/setup/install/windows-install/).

#### Install Docker Desktop

1. Download and run the official Docker Desktop installer.
2. Use the recommended per-user installation and WSL 2 backend unless your organization requires another supported configuration.
3. Start **Docker Desktop**, accept its terms when prompted, and wait until the container engine is running.
4. On Windows, confirm Docker Desktop is using **Linux containers**.

#### Download the Resource Planner image

1. In Docker Desktop, open the integrated terminal from the bottom-right corner.
2. Pull the exact release tag supplied by the maintainer:

   ```powershell
   docker pull ghcr.io/dresanovic/planner-ressources:<release-tag>
   ```

3. If the package is private, authenticate first with the GitHub username and package-read token supplied by your deployment administrator. Never put the token in the container settings, `.env`, or this manual.

**Expected result:** The image appears under **Images** in Docker Desktop. Do not substitute `latest` when a tested exact release tag is available.

#### Prepare persistent data and the required key

1. Create a dedicated folder such as `C:\DockerData\planner-ressources`. Keep it outside OneDrive or another synchronized folder.
2. Open PowerShell and generate the required private key:

   ```powershell
   $key = New-Object byte[] 32
   $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
   $rng.GetBytes($key)
   $rng.Dispose()
   [BitConverter]::ToString($key).Replace('-', '').ToLowerInvariant()
   ```

3. Copy the displayed 64-character value to a secure location. Keep the same value across container restarts and upgrades.

#### Create and run the container

1. In Docker Desktop, open **Images**.
2. Find the pulled Resource Planner image and select **Run**.
3. Expand **Optional settings** and enter:

   | Setting | Value |
   | --- | --- |
   | Container name | `planner-ressources` |
   | Host port | `8080` |
   | Container port | `8080` |
   | Host path | `C:\DockerData\planner-ressources` or your dedicated folder |
   | Container path | `/data` |
   | Environment variable | `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` |
   | Environment value | The generated 64-character key |

4. Select **Run**.
5. Open **Containers** and wait until `planner-ressources` is running and healthy.
6. Open `http://localhost:8080` in a browser.

**Expected result:** Resource Planner opens through one address. Its database is stored in the mapped host folder and remains available when the container is restarted or replaced. The health address `http://localhost:8080/health` returns `{"status":"ok"}`.

If port `8080` is already occupied, use host port `8081`, keep container port `8080`, and open `http://localhost:8081`.

### Open the system locally

Use this developer procedure only when you need to run the frontend and backend from source instead of Docker Desktop.

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

**Expected result:** The application opens in **Planung > Kalender**. The backend health address `http://127.0.0.1:8000/health` returns `{"status":"ok"}`.

The default database is `backend/planner.db`. Set `DATABASE_URL` before starting the backend only when your environment uses a different SQLAlchemy database URL.

### First-use setup

If planning data already exists, skip this section.

1. Expand **Stammdaten** in the navigation.
2. Create a **Semester** and **Kohorte**.
3. Create a **Studienform**, then create at least one **Zeitfenster** for it.
4. Create at least one coded **Lehrende Person** and one coded **Raum** with sufficient capacity.
5. Open **Lehrveranstaltungen** and create a record with its units, session-size range, Semester, Kohorte, Studienform, initial lecturer, and initial room.
6. Return to **Planung > Kalender**.
7. If no revision exists, select **Entwurf starten**.

**Expected result:** The Lehrveranstaltung is available for planning in its Semester, and an editable Arbeitsrevision exists. A record with missing or inactive required planning data remains visible but unavailable.

### Common use cases

#### Generate a draft for one Lehrveranstaltung

1. Open **Planung > Kalender** and select **Planungseingaben anzeigen** if necessary.
2. Select **Eine Lehrveranstaltung**, then select the Semester and Lehrveranstaltung.
3. Review **Eingaben für den nächsten Entwurf**. Keep the defaults for routine generation.
4. Select **Erzeugen**.

**Expected result:** A complete Lehrveranstaltung draft is saved in the active Arbeitsrevision and appears in the Kalender. If no complete valid draft can be produced, the application explains the reasons and preserves the existing draft.

#### Review and correct a session in the Kalender

1. In **Planung > Kalender**, choose **Woche**, **Tag**, or **Monat**.
2. Select a teaching or exam occurrence.
3. In the session pane, select **Im vorhandenen Editor bearbeiten**.
4. Change the available fields and select **Speichern**.

**Expected result:** The occurrence and affected summaries refresh in place. The Kalender mode, date, filters, and selected revision remain unchanged.

#### Optimize several Lehrveranstaltungen together

1. In **Planung > Kalender**, show **Planungseingaben** and select **Mehrere Lehrveranstaltungen**.
2. Select between 1 and 20 Lehrveranstaltungen.
3. Optionally enter future unavailable dates as comma-separated `TT.MM.JJJJ` values.
4. Select **Ausgewählte Lehrveranstaltungen optimieren**.
5. Review the preparation dialog and confirm.

**Expected result:** The application saves the best valid complete or improved partial results for the prepared snapshot, preserves worse or stale schedules, and explains remaining units and failures per Lehrveranstaltung.

#### Prepare and generate exams

1. Open **Planung > Prüfungen** and select a Lehrveranstaltung in the shared context header.
2. Enable its exam requirement, complete the fields, and save it.
3. Under exam preparation, select one or more eligible Lehrveranstaltungen.
4. Prepare the selection, review the confirmation, and generate the confirmed exams.

**Expected result:** Each selected Lehrveranstaltung receives either one valid active exam or a clear failure reason. Generated exams appear distinctly from teaching sessions in the Kalender.

#### Publish a schedule revision

1. Open **Planung > Versionen**.
2. Select the active working revision.
3. Optionally select **Als prüfbereit markieren**.
4. Select **Revision veröffentlichen**.
5. Review each known gap and warning, then select **Bewusst veröffentlichen**.

**Expected result:** The revision becomes the Semester's immutable **Aktuelle Veröffentlichung**. Publishing directly from Entwurf is also allowed.

#### Review assignments through a lecturer link

1. Open the private link supplied by the planner.
2. Review the fixed lecturer, Semester, revision, and access-expiry context.
3. Use **Woche**, **Tag**, **Monat**, or **Liste** and the available filters to find an assignment.
4. Open a session to send a **Terminkommentar** or select **Als nicht möglich kennzeichnen**.
5. Use **Revisionskommentar senden** for feedback about the complete revision.

**Expected result:** The feedback is saved against the shared revision or session and becomes visible to the planner. It does not edit or approve the schedule and does not block publication.

### Where to go next

Use the Detailed Guide for catalog maintenance, custom constraints, calendar summaries and filters, resource availability, holidays, manual session management, exam rules, lifecycle recovery, limitations, and troubleshooting.

## Detailed Guide

### System concepts

- A **Lehrveranstaltung** is assigned to one current Semester for new planning.
- A teaching draft belongs to one Lehrveranstaltung and Semester and contains teaching sessions.
- A teaching session has a date, interval, explicit unit count, Lehrende Person, Kohorte, and Raum.
- One teaching unit is 45 minutes. Default session duration includes a 10-minute break between units.
- **Remaining units** equal current Lehrveranstaltung units minus saved session units, never less than zero.
- **Generation constraints** affect the next generation. Kalender filters only affect what is visible.
- The Semester has at most one editable **Arbeitsrevision** and one **Aktuelle Veröffentlichung**.
- An Arbeitsrevision may be **Entwurf** or **Bereit zur Prüfung**. A published or superseded revision is read-only.
- Validation warnings describe current problems but do not automatically move or delete sessions.
- Saved Published content remains unchanged when current catalog data changes; current warnings may still reflect new validation conditions.

### Navigation and workspace layout

With the shipped terminology, the primary navigation contains:

- **Planung**
  - **Kalender**
  - **Versionen**
  - **Prüfungen**
  - **Abstimmung mit Lehrenden**
- **Stammdaten**
  - **Semester**
  - **Feiertage**
  - **Kohorten**
  - **Lehrveranstaltungen**
  - **Studienformen**
  - **Zeitfenster**
  - **Lehrende**
  - **Räume**

Only the selected Planung workspace is shown. Its compact context header keeps the relevant Semester, Revision, and Lehrveranstaltung selectors available.

On wide screens, use the pin icon to detach or permanently display the navigation. The wide-screen pin choice is retained on the same device. When the detached navigation is open, use the red **×** to close it.

At 820 pixels or narrower, select **Menü** to open the temporary navigation. The red **×** or Escape closes it. Pinning is intentionally unavailable in this narrow presentation.

In Kalender, **Planungseingaben ausblenden** reclaims additional width without changing the navigation. This choice is not retained after the application is revisited.

### Operate a Docker Desktop installation

These procedures are for the person responsible for the local installation.

#### Start, stop, and inspect the application

1. Open Docker Desktop and select **Containers**.
2. Use the action beside `planner-ressources` to start, stop, or restart it.
3. Select the container to view its status and **Logs**.
4. After a start or restart, wait for the container to become healthy before opening the application.

Run only one Resource Planner application container against a data folder. The current SQLite deployment is not designed for multiple application containers sharing the same database.

#### Import or export planning setup data

The image contains an optional JSON-based setup script. It imports catalog and configuration records, but it does not create schedules, teaching sessions, exam sessions, or generation constraints.

1. Start the container and wait until it is healthy.
2. In **Containers**, open the actions for `planner-ressources` and select **Open in terminal**.
3. To import the bundled baseline JSON, run:

   ```text
   python scripts/seed_dummy_planning_data.py
   ```

4. To export the current non-scheduling setup to editable JSON in the persistent `/data` volume, run:

   ```text
   python scripts/create_seed_data.py --output-file /data/planning-setup.json
   ```

5. Copy `/data/planning-setup.json` from the mapped Docker volume if the file must be stored outside the container.
6. To import an edited JSON file, place it in a mounted container path and run:

   ```text
   python scripts/seed_dummy_planning_data.py --data-file /data/planning-setup.json
   ```

**Expected result:** The configured catalog is available in the application. Repeating the command updates or reuses configured records instead of duplicating them. Review demonstration values before using them for a real institution.

#### Create a database backup

1. Open the running container's terminal in Docker Desktop.
2. Run:

   ```text
   python scripts/backup_sqlite_db.py --output-dir /data/backups
   ```

3. Confirm that a backup was reported and appears in the `backups` subfolder of the mapped host data folder.
4. Copy backups to separate protected storage and test the restore process before relying on them.

#### Upgrade the application image

1. Create a verified database backup.
2. Pull the new exact release tag through Docker Desktop's integrated terminal.
3. Stop and remove the old application container, but do not delete the mapped host data folder.
4. Run the new image with the same `/data` host folder, container name, port mapping, and fingerprint key.
5. Wait for the new container to become healthy and verify the application and saved data.

The image is replaceable; the mapped `/data` folder and its key are installation data and must be preserved.

### Language, terminology, and date format

The application uses one German terminology set per installation. There is no language switch or in-application label editor. With the shipped defaults, the configurable concepts include **Lehrveranstaltung**, **Lehrende Person**, **Kohorte**, **Raum**, **Planung**, and **Stammdaten**. A customer installation may use different wording for these concepts while retaining the same functions and stored record names.

Every human-visible numeric calendar date uses `DD.MM.YYYY`, for example `11.09.2026`. Date fields display the permanent hint **Format: TT.MM.JJJJ** and accept that format by keyboard or paste. Times remain in the existing 24-hour format.

To enter a date:

1. Type all eight digits and both dots, for example `07.11.2026`.
2. Correct any incomplete, impossible, or out-of-range value in the field identified by the message.
3. Continue with the form action only after the field is valid.

**Expected result:** The same calendar day is saved and displayed. Invalid date text is not silently changed to another date, and the application does not send the form until the field is corrected.

#### Configure customer terminology during deployment

This procedure is for the deployment operator, not planner users.

1. Edit `config/terminology-overrides.json` beside `compose.yaml`.
2. Change only the values on the right. Keep every stable key on the left unchanged.
3. For a direct local backend start, set `CUSTOMER_TERMINOLOGY_FILE` to the file's absolute host path before starting the backend.
4. For Docker, set `CUSTOMER_TERMINOLOGY_FILE=/config/terminology-overrides.json` and enable the documented read-only volume mapping in `compose.yaml`.
5. Restart the application. An image rebuild and database change are not required.
6. Open representative navigation, list, form, and schedule surfaces and verify the selected terms.

Omitted keys use the shipped German defaults. The application refuses to start when the configured file is missing, unreadable, malformed, contains unknown keys, or supplies blank or non-text values. Customer terminology changes labels only; it does not rename stored academic records or user-entered content.

### Maintain Stammdaten

Use **Stammdaten** to create, edit, archive, reactivate, and safely delete the records used by scheduling.

#### Create a complete planning chain

1. Create the Semester and Kohorte.
2. Create the Studienform.
3. Create one or more Zeitfenster for that Studienform.
4. Create Lehrende and Räume.
5. Create the Lehrveranstaltung last, linking the required records.

Lehrveranstaltungen, Kohorten, and Räume require positive whole-number values where applicable. A Lehrveranstaltung's minimum session size cannot exceed its maximum.

#### Archive, reactivate, or delete a record

1. Select the record.
2. Select its archive, reactivate, or delete action.
3. Review the usage dialog.
4. Confirm only after reviewing dependent records and saved schedule references.

Permanent deletion is available only when it is safe. Otherwise, archive the record. Archived parents remain visible for historical context but are unavailable for new planning.

Changing Semester dates is blocked when saved sessions would fall outside the new range. Reassigning a Lehrveranstaltung affects future planning; existing schedule snapshots retain their saved context.

### Maintain Lehrende and Räume

Lehrende and Räume have a name, unique reference code, lifecycle state, and unavailable periods. Räume also have capacity.

#### Record recurring unavailability

1. Open **Stammdaten > Lehrende** or **Räume**.
2. Select the resource and add an unavailable period.
3. Choose the weekday, start time, and end time.
4. Save the resource.

#### Record dated unavailability

1. Select the resource.
2. Add the start and end date.
3. Add the start and end time.
4. Save the resource.

Generation avoids ineligible, inactive, unavailable, or undersized resources. Existing sessions are not moved automatically when availability or capacity changes; they receive current validation warnings when applicable.

### Maintain Lehrveranstaltung resource eligibility

1. Open **Stammdaten > Lehrveranstaltungen** and edit the record.
2. Search and select its eligible Lehrende and Räume.
3. Save the Lehrveranstaltung.

One session uses exactly one Lehrende Person and one Raum. Generation prefers contiguous lecturer blocks and room reuse where hard eligibility, availability, capacity, and conflict rules permit.

Inactive or insufficient-capacity choices cannot be newly added. Previously saved invalid relationships remain visible so the planner can repair them.

### Maintain institution holidays

1. Open **Stammdaten > Feiertage**.
2. Enter **Datum** in `TT.MM.JJJJ` and enter the **Name**.
3. Create the holiday.
4. Use **Bearbeiten** to correct a holiday or **Löschen** to remove it after confirmation.

Future teaching and exam generation treats holidays as unavailable full dates. A saved session already on a newly added holiday is not moved; the Kalender shows a current warning.

Removing a holiday stops it from constraining future generation. It does not change saved sessions.

### Work with schedule revisions

If a Semester has no lifecycle revision, select **Entwurf starten** in Kalender or Versionen. Planning changes are unavailable until the draft is created.

Use the shared context header to choose:

- Semester in all Planung destinations
- Revision in Kalender and Versionen
- Lehrveranstaltung in Kalender and Prüfungen

When both exist, Kalender lets you switch between **Arbeitsrevision R…** and **Veröffentlichung R…**. Only the Arbeitsrevision is editable. Historical revisions remain available as read-only content.

### Configure and generate one Lehrveranstaltung

#### Use default constraints

The default planning period comes from the Semester. Weekly teaching windows come from the Lehrveranstaltung's active Studienform time windows.

Select **Erzeugen** without changing the defaults.

#### Set custom constraints

1. Select the Lehrveranstaltung and Semester.
2. Set a planning start and end date inside the Semester.
3. Add one or more valid weekly windows.
4. Select **Erzeugen**.

Successful generation saves the constraints for that Lehrveranstaltung and Semester. A failed attempt does not overwrite the saved constraints or replace the existing draft.

#### Restore defaults

Select **Clear custom constraints** in the constraint editor. Existing sessions do not move until generation is run again.

### Optimize several Lehrveranstaltungen

The several-Lehrveranstaltungen workflow coordinates the selected records as one conflict-aware problem.

1. Select **Mehrere Lehrveranstaltungen** under **Planungseingaben**.
2. Select 1 to 20 Lehrveranstaltungen.
3. Optionally enter comma-separated future unavailable dates in `TT.MM.JJJJ` format, for example `26.10.2026, 02.11.2026`.
4. Select **Ausgewählte Lehrveranstaltungen optimieren**.
5. Review the prepared input and existing schedules.
6. Confirm the operation.

The optimizer:

- maximizes scheduled teaching units
- avoids new lecturer, Raum, and Kohorte overlaps
- respects active periods, eligibility, availability, Raum capacity, generation windows, and holidays
- preserves unselected sessions as fixed Semester occupancy
- may retain an improved partial schedule with understandable remaining-unit reasons
- does not replace an existing Lehrveranstaltung result with fewer units or an otherwise worse approved comparison
- applies stable preference priorities when several maximum-unit arrangements are possible

An approved replacement may replace manual edits in a selected Lehrveranstaltung. Cancel the confirmation to keep all current schedules unchanged.

After the operation, review **Gespeichertes Optimierungsergebnis**. It separates complete, improved partial, unchanged, failed, and stale outcomes. Use **Fehlgeschlagene oder veraltete Lehrveranstaltungen erneut versuchen** to prepare those records again from current data.

The optimality statement applies to the prepared snapshot. If inputs became stale, preserved stale outcomes are not described as globally optimal for the refreshed Semester.

### Review the Kalender

Kalender opens in **Woche** mode. Available modes are:

- **Woche** for the main operational view
- **Tag** for one date
- **Monat** for broad date navigation
- **Liste** for the dense overview and its list/weekly review controls

Use the previous, **Aktuell**, and next controls or choose a calendar date. Liste mode does not use date navigation.

The calendar filters are combined: an appointment must match every selected value. **Alle** means that the corresponding criterion is not restricted.

| Filter | Effect |
| --- | --- |
| **Lehrveranstaltung** | Shows appointments belonging to one selected course record. |
| **Kohorte** | Shows appointments for one student cohort. |
| **Lehrende Person** | Shows appointments assigned to the selected lecturer. |
| **Raum** | Shows appointments scheduled in the selected room; unscheduled items without a room are excluded. |
| **Studienart** | Restricts courses by their study model, such as full-time or part-time. |
| **Terminart** | Shows teaching appointments or exam appointments. |
| **Revisionsstatus** | Restricts the loaded planning context by working, draft, review-ready, or published status; it does not open a different revision. |
| **Prüfstatus** | Restricts appointments by validation result, such as conflict, capacity, holiday, exam-validity, planning-failure, stale-result, or no-known-issue categories when available. It does not mean exam lifecycle status. |

Select **Filter zurücksetzen** to return every dropdown to **Alle** and remove an active summary-detail selection. Filters do not change saved data.

The operational summary contains:

- **Offener Planungsumfang**
- **Konflikte**
- **Kapazitätsprobleme**
- **Planungsfehler**
- **Prüfung erforderlich**

Select a summary card to inspect its contributors. A dated contributor opens the affected date or occurrence; an undated Lehrveranstaltung or outcome moves to Liste mode. Filtered summaries clearly identify that they describe a subset rather than the complete revision.

### Inspect, edit, or delete a session

Select a teaching or exam occurrence to open the session pane. It shows identifying details, revision context, and current warnings.

For an editable Arbeitsrevision:

1. Select **Im vorhandenen Editor bearbeiten**.
2. Change the available values.
3. Select **Speichern** or **Abbrechen**.

Teaching edits can change date, start time, end time, Lehrende Person, and Raum. Exam edits can change date, start time, responsible lecturer, and Raum; configured duration remains fixed.

Select **Mit Bestätigung löschen** to remove only the selected teaching or exam session.

If you have unsaved pane changes and try to close it or change context, the application asks whether to **Weiter bearbeiten** or **Änderungen verwerfen**. Continuing the edit is the safe default.

On a wide Kalender, the pane docks beside the Kalender when enough content width is available. It overlays at smaller widths and becomes a full-screen modal pane at 820 pixels or narrower.

### Add, delete, or clear teaching sessions

#### Add one teaching draft appointment

1. Select a Lehrveranstaltung and Semester in **Eine Lehrveranstaltung** mode.
2. Under **Entwurfstermin hinzufügen**, enter the date, start time, and whole-number units.
3. Review or change the proposed end time.
4. Select the Lehrende Person, Kohorte, and capacity-sufficient Raum.
5. Select **Entwurfstermin hinzufügen**.

The explicit unit count controls Lehrveranstaltung progress. The end time may be adjusted for merged teaching or a longer pause.

#### Delete one teaching session

Open the selected session and choose **Mit Bestätigung löschen**, or use **Löschen** in Liste mode. The confirmation shows removed coverage and resulting remaining units.

#### Clear one Lehrveranstaltung draft

Select the Lehrveranstaltung under **Planungseingaben** and choose **Lehrveranstaltung-Entwurf leeren**. The confirmation identifies the exact record and Semester. Source records and saved generation constraints remain.

Cancelled, failed, or stale confirmations make no saved change.

### Understand validation warnings

Current warnings can identify:

- lecturer, Raum, or Kohorte overlaps
- insufficient Raum capacity
- a session outside active Lehrveranstaltung generation constraints
- a session outside its Studienform time windows
- a session on an institution holiday
- inactive, unavailable, ineligible, or missing planning resources
- an exam that no longer satisfies a hard constraint

Back-to-back sessions are not overlaps when one ends exactly as the next begins. One session may have several warnings.

Warnings are non-blocking for manual teaching edits and lifecycle publication. They do not automatically repair the schedule. Exam creation and correction use stricter hard-constraint validation and reject invalid placements.

Known messages are presented as separate problem items. Each item identifies the affected action, record, or field; explains the known rule or values; says whether work is blocked and whether the current data remains saved when known; and gives a correction, retry, refresh, or intentional-retention option that is actually available.

When several problems occur, handle them one at a time rather than reading them as one combined failure. A blocking field problem moves focus to the first invalid control after an attempted save. Other entered values remain in the form where the message says they are preserved.

#### An exam is outside its recommended period

The warning identifies the Lehrveranstaltung or exam, scheduled date, and recommended start and end dates. It also states that the condition is non-blocking and that the saved placement remains available.

Choose one of the two stated paths:

1. Open the affected exam and change its date; or
2. Keep the intentional placement and continue after reviewing the warning.

The recommendation is guidance only. Hard exam constraints still determine whether a placement can be saved.

### Configure and schedule exams

Open **Planung > Prüfungen**. The selected Lehrveranstaltung's exam requirement includes:

- enabled or disabled state
- identifier
- positive whole duration in minutes
- positive required Raum capacity
- required free-text exam type
- responsible eligible lecturer
- optional override of the recommended date range

The default recommendation is seven through fourteen calendar days after the final teaching session. It is a soft preference. Manual placement may occur outside it when all hard constraints pass.

An enabled Lehrveranstaltung without a final teaching session can be saved but is unavailable for placement. A Lehrveranstaltung with an active exam is also unavailable for another active exam, and its consumed configuration is read-only.

#### Generate exams

1. Save valid requirements for the Lehrveranstaltungen.
2. In exam preparation, select 1 to 100 eligible Lehrveranstaltungen.
3. Select **Prüfungen vorbereiten**.
4. Review the preparation and select **Bestätigte Prüfungen erzeugen**.

Automatic generation considers all selected exams together. It requires:

- a final teaching session and placement after it
- a date inside the Semester and not on a holiday
- an eligible, active, available responsible lecturer
- an eligible, active, available Raum with sufficient capacity
- no lecturer, Raum, or Kohorte overlap with teaching or exams
- a start time proposed from an active Studienform time window

The recommended date range is preferred but not required. Teaching sessions are never moved by exam generation.

#### Place or correct an exam manually

Select **Prüfung manuell eintragen** for an eligible unscheduled configuration, or select an exam in Kalender and choose **Im vorhandenen Editor bearbeiten**. Set the date, start time, responsible lecturer, and Raum, then save.

Manual placement may use a start time outside Studienform proposal times, but every hard constraint still applies.

Deleting an active exam leaves its current requirement enabled and unscheduled. Deleting a past exam removes only that historical exam.

### Coordinate accountless lecturer feedback

Open **Planung > Abstimmung mit Lehrenden** for the selected revision.

Initial links can be created from an Arbeitsrevision in Entwurf or Bereit zur Prüfung. The interface shows when the selected lecturer or revision is not eligible.

#### Create and send a review link

1. Select the intended **Lehrende Person**.
2. Select a validity of one, two, or three days; three days is the default.
3. Select **Zugangslink erstellen**.
4. Select **Link kopieren** while the one-time URL is visible.
5. Send it manually through an appropriate private channel, then close the one-time result.

The link is bound to one lecturer and one revision. Anyone possessing it can read that scoped schedule and submit advisory feedback until access ends. The URL is not restored after the one-time result is closed.

Use **Link widerrufen** to end active access. Use **Link ersetzen** to invalidate the old link and create a new one. If a link operation has an unknown outcome, reload the current state before issuing another link; the application does not invent or redisplay a secret URL.

#### Review lecturer feedback

The coordination area shows counts for entries, comments, open **Nicht möglich** flags, and affected sessions. Filter by lecturer, Lehrveranstaltung, appointment type, or feedback type. Select **Aktuellen Termin öffnen** when current navigation is available.

Feedback is advisory and immutable. It does not approve, reject, move, or delete an appointment and never blocks publication. When the referenced appointment is changed, removed, or reassigned, its **Nicht möglich** feedback no longer counts as open and is shown as resolved or historical. The captured session context remains available for traceability even when the current appointment is no longer navigable.

#### Lecturer workflow and privacy

The temporary page displays every and only the teaching and exam assignments in the link's current lecturer/revision scope. The lecturer identity is fixed and cannot be changed through a filter. Planner edit, creation, deletion, generation, and publication controls are not available.

Before leaving an open session or changing to a filter that would hide it, the application warns about unsent feedback. Select **Weiter schreiben** to preserve the draft or **Rückmeldung verwerfen** only when the text is no longer needed.

Expired, revoked, replaced, or revision-ended links expose no schedule data. Reloading the page obtains the current assignment scope; sessions reassigned away from the lecturer are no longer shown.

### Manage Versions and publication

Open **Planung > Versionen** to see:

- Aktive Arbeitsrevision
- Aktuelle Veröffentlichung
- selected revision state and permitted actions
- collapsed revision history and ordered lifecycle events

The lifecycle is:

`Draft → Ready for review → Published`

**Bereit zur Prüfung** is optional and informational. It does not lock editing or require approval. A planner may publish directly from Entwurf or from Bereit zur Prüfung.

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
- Failed one-Lehrveranstaltung generation preserves the previous draft.
- Semester optimization may save useful improved partial results but never silently worsens protected schedules.
- Generation constraints do not edit existing sessions until generation is selected.
- Removing a holiday affects future generation but not saved sessions.
- An active exam prevents creation of a second active exam for that Lehrveranstaltung and Semester.
- A failed refresh keeps the last known complete view where available and presents a retry action.
- Navigation, filters, mode changes, pinning, and hiding Planungseingaben do not mutate schedule data.
- Human-visible dates use `DD.MM.YYYY`; API, database, export, and other machine formats remain unchanged.
- A customer terminology override changes selected labels only and never changes identifiers, routing, business rules, or stored record names.
- Raw error codes and internal diagnostics are not the primary explanation. When the exact cause is unavailable, the application says so and gives only a safe available next step.

### Known limitations

The current application does not provide:

- lecturer accounts or authenticated ongoing lecturer access
- authentication or role-based permissions
- external planning-data import or synchronization
- automated email delivery or institutional single sign-on
- drag-and-drop, resize, duplicate, split, or merge actions in Kalender
- automatic repair of saved sessions after a warning appears
- multiple institutional or partial-day holiday calendars
- student registration, grading, invigilator management, or external room booking
- background optimization, algorithm selection, or persisted optimization-result history
- an independently published Lehrveranstaltung; publication always covers the Semester revision
- runtime language switching, multiple active languages, or an in-application terminology editor
- automated delivery of lecturer review links; planners must send them manually

The current limit is 20 Lehrveranstaltungen per teaching optimization and 100 Lehrveranstaltungen per exam-generation request.

### Troubleshooting

#### The application does not open

1. Confirm the backend is running on port 8000.
2. Open `http://127.0.0.1:8000/health`.
3. Confirm the client is running on port 5173.
4. Verify `VITE_API_BASE_URL` points to the backend address.

If startup reports a terminology configuration problem, verify `CUSTOMER_TERMINOLOGY_FILE`, JSON syntax, stable keys, and non-empty text values. Remove the optional setting to use the shipped German defaults, or correct the file and restart.

For a Docker Desktop installation:

1. Open **Containers** and confirm `planner-ressources` is running and healthy.
2. Open the container and read **Logs**.
3. Confirm host port `8080` maps to container port `8080`, or use the alternate host port you configured.
4. Confirm `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` contains the complete generated 64-character value.
5. Confirm the host data folder still exists and is mapped to `/data`.

If the image pull is denied, the GitHub Container Registry package may be private. Ask the deployment administrator for package-read access and authenticate through Docker without storing the registry token in container configuration.

#### Docker starts with an empty application

The container was probably started without the previous `/data` mapping or with a different host folder. Stop it, locate the original data folder, and recreate the container with that folder mapped to `/data`. Do not initialize or copy over the original database until a backup exists.

#### A date cannot be saved

1. Enter the date as `TT.MM.JJJJ`, including leading zeroes.
2. Correct impossible dates such as `31.02.2026`.
3. Check the minimum, maximum, and start/end range described beside the field.
4. Retry the form action after the field error is cleared.

The application preserves partial text while you correct it and does not submit an invalid calendar date.

#### Planning actions are unavailable

Open **Planung > Versionen** or Kalender and select **Entwurf starten**. Published and historical revisions are read-only; choose the Arbeitsrevision to make changes.

#### A Lehrveranstaltung is missing or unavailable

1. Confirm the selected Semester matches the Lehrveranstaltung.
2. Confirm the Lehrveranstaltung, Semester, Kohorte, and Studienform are active.
3. Confirm an active Zeitfenster exists.
4. Confirm the Lehrveranstaltung has an active eligible lecturer and usable eligible Raum.
5. Correct the record in Stammdaten and return to Planung.

#### One-Lehrveranstaltung generation fails

Read every displayed reason. Check the selected period and windows, session-size values, active planning data, eligible resources, availability, Raum capacity, and holidays.

#### Optimization leaves a Lehrveranstaltung unchanged

Review its outcome. The prepared solution may not have been strictly better, the Lehrveranstaltung may have become stale, or hard constraints may prevent improvement. Use the displayed reasons and retry stale or failed records after correcting the inputs.

#### A Lehrveranstaltung cannot be selected for exam generation

Read its reason under **Nicht verfügbare Lehrveranstaltungen**. Common verified causes are a disabled or invalid requirement, no final teaching session, an existing active exam, or unavailable current planning data.

#### Session editing is not available

Confirm you are viewing the Active working revision and that the selected occurrence still has current editable backing data. Published and historical content cannot be edited in place.

#### The application asks about unsaved changes

Select **Weiter bearbeiten** to return to the pane without losing the draft. Select **Änderungen verwerfen** only when you want to continue to the requested destination or context without saving.

#### A record cannot be deleted

Review **Abhängige Datensätze** and **Gespeicherte Planungen** in the deletion dialog. Remove safe dependencies first or archive the record.

#### A change is reported as stale

Another saved change occurred after the form or confirmation opened. Refresh or reopen the action, review current values, and try again.

When the message says your unsent text remains in the field, copy it before any full-page reload. Do not repeat an operation with an unknown outcome until you have checked the newly loaded state.

#### Several problems are displayed

Read and resolve each separate problem item. Start with blocking field problems, then refresh or retry only through the action offered by the corresponding item. A warning explicitly marked non-blocking may be retained intentionally after review.

#### A lecturer review link is unavailable

The link may have expired, been revoked or replaced, or ended with its revision. Ask the planner for a new link. Do not forward an old link or attempt to edit its URL.

#### A review link was closed before it was copied

The one-time URL cannot be recovered from link history. Replace or revoke the link and create a new one, then copy and send only the newly displayed URL.

#### Warnings remain after a correction

Open **Aktuelle Hinweise** and correct each remaining cause. Resolving one issue may leave another warning on the same session.

#### Last-known data is shown

The latest refresh failed. The application preserves the last complete view where possible. Select the visible **Erneut laden** or **Erneut versuchen** action before making decisions from the displayed data.

### Glossary

- **Planner:** The current end-user role with scheduling and administration access.
- **Arbeitsrevision:** The single editable Semester revision in Entwurf or Bereit zur Prüfung state.
- **Aktuelle Veröffentlichung:** The immutable published revision currently designated for the Semester.
- **Generation constraints:** The date range and weekly windows used for the next one-Lehrveranstaltung generation.
- **Eligible resource:** A lecturer or Raum permitted for a Lehrveranstaltung.
- **Unavailable period:** A recurring or dated interval during which a resource cannot be assigned.
- **Validation warning:** A current, non-blocking issue attached to a saved occurrence.
- **Prepared snapshot:** The exact input state approved before optimization or generation executes.
- **Stale outcome:** A result not saved because relevant planning state changed after preparation.
- **Active exam:** An exam dated today or later; only one is allowed per Lehrveranstaltung and Semester.
- **Past exam:** An exam dated before today that remains available as historical schedule content.
- **Terminology catalog:** The installation-wide German labels for selected reusable concepts. Customer overrides change presentation only.
- **Problem item:** One separately presented warning or error containing its own context and next action.
- **Accountless review link:** A temporary private URL that grants one lecturer read-only access to personal assignments in one revision and permits advisory feedback.
