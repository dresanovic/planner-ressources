# Planner: backups, restores, file transfers and image updates

All commands marked **PowerShell** run on your Windows computer, including the
remote operations. You do not need to open an Ubuntu SSH shell first. The remote
script uses SSH/SCP and runs a bundled Bash helper on Ubuntu. It asks for your
SSH password, possibly more than once, and for your sudo password as necessary.
No passwords are saved in these scripts. SSH port forwarding is not required.

## 1. Your installation and scripts

Current installation recorded on 12 November 2026:

| Setting | Value |
| --- | --- |
| Windows project | `C:\Codex\planner-resource` |
| Local database | `C:\Codex\planner-resource\backend\planner.db` |
| Local backups | `C:\Codex\planner-resource\backend\backups` |
| SSH | `admin_b50578@10.155.11.130`, port `17655` |
| Active remote container | `planner-ressources-poc` |
| Persistent remote volume | `planner-ressources-poc-data` |
| Database inside container | `/data/planner.db` |
| Existing deployment configuration | `/home/admin_b50578/planner-update-2026-11-11` |
| New maintenance files and host backups | `/home/admin_b50578/planner-maintenance` |
| Application address | <http://10.155.11.130:8081> |
| Last deployed image in this chat | `ghcr.io/dresanovic/planner-ressources:v2.1.1` |
| Environment / algorithm | `development` / `standard_optimized` |

Scripts:

- [Local-Planner.ps1](../scripts/maintenance/Local-Planner.ps1): local source-based application database operations.
- [Remote-Planner.ps1](../scripts/maintenance/Remote-Planner.ps1): remote operations launched from Windows.
- [remote-planner.sh](../scripts/maintenance/remote-planner.sh): Ubuntu implementation, transferred automatically with the Python backup/restore helpers.

These scripts do not change your local application startup process. The local
script targets the Python source installation, not a local Docker volume. The
remote update script targets the specific single-container deployment above;
it refuses unexpected mounts, ports or configuration rather than dropping them.

Start every example from **PowerShell**:

```powershell
Set-Location C:\Codex\planner-resource
```

If PowerShell blocks scripts and company policy permits a session-only change:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This lasts only for the current PowerShell process. Centrally enforced policy
may override it. You need Windows OpenSSH `ssh` and `scp`; remote operations
also require Ubuntu `python3`, Bash, Docker and sudo, as in your current setup.
The SCP wrapper uses legacy SCP mode (`-O`) and accepts simple absolute Linux
paths without spaces or shell characters. Local Windows paths may contain spaces.

## 2. Local application: create a backup

You may leave the local application running. The existing Python helper uses
SQLite's online backup API and checks database integrity.

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action Backup
```

The command prints the new `.db` path. Each invocation creates a unique
`backend\backups\manual-...` directory, preventing filename collisions.

For another local database or Python interpreter:

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action Backup `
  -Database 'D:\PlannerData\planner.db' `
  -BackupDirectory 'D:\PlannerBackups' `
  -Python 'C:\Codex\planner-resource\backend\.venv\Scripts\python.exe'
```

## 3. Local application: replace the database from a backup

First select an actual backup path from the listing in section 4. A preview
validates the source database; it does not prove that every application process
is stopped or that all restore prerequisites will pass.

```powershell
$backup = 'C:\Codex\planner-resource\backend\backups\STAMMDATEN_BASELINE_V2_2026-11-10\STAMMDATEN_ONLY_V2_2026-11-10.db'

.\scripts\maintenance\Local-Planner.ps1 -Action Restore -BackupFile $backup
```

To apply:

1. Stop the local backend cleanly with **Ctrl+C** in its terminal. Stop other
   processes using the same database, including any MCP process that accesses it.
2. Run the command below. `-BackendStopped` is your explicit confirmation; the
   script cannot discover every idle connection.
3. Restart the backend using your normal command and verify login and data.

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action Restore `
  -BackupFile $backup -Apply -BackendStopped
```

The restore helper creates a fresh backup of the database it replaces in a
unique `before-restore-*` directory. It refuses existing WAL/SHM/journal files.
Do not manually delete those files; resolve the SQLite state after a clean stop.

Restoring replaces **all** database state, including accounts, password hashes,
session state, plans and authentication records. It is not a data merge. Account
credentials must match the restored snapshot. Restoring an old snapshot can
also restore old sessions and consumed-credential state.

The supplied clean baseline contains master data and accounts with planning
data removed. Do not run its course-unit reduction again. Before planning,
correct course IDs **69, 70, 80 and 94**: they have 1 LE but retain a minimum of 2.

## 4. Local application: see and rename backups

List all `.db` backups recursively with full paths:

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action List
```

Open the backup directory in Windows Explorer:

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action Open
```

Rename a selected backup, keeping it in its current directory:

```powershell
.\scripts\maintenance\Local-Planner.ps1 -Action Rename `
  -BackupFile 'C:\Codex\planner-resource\backend\backups\manual-EXAMPLE\planner-EXAMPLE.db' `
  -NewName 'before-course-changes-2026-11-12.db'
```

Replace example paths with actual files from `List`. Existing destination files
are never overwritten. Rename accepts files under the backup directory only;
it does not rename your active database. Use `-BackupDirectory` for another root.

## 5. Remote server: create a backup

Run on **Windows PowerShell**, while the remote application is running:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Backup
```

The script verifies the `/data` volume and database path, creates an integrity-
checked backup inside the persistent volume, and copies it to a private host
directory under:

```text
/home/admin_b50578/planner-maintenance/backups/operator-TIMESTAMP/
```

The printed host path is suitable for `Download`, `Rename` or `Restore`.
Copy important backups to Windows as well; a copy on the same server does not
protect against losing that server.

## 6. Remote server: see, download and rename backups

List backups in the maintenance host directory and historical backups inside
the Docker volume:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action List
```

Remote files do not appear directly in Windows Explorer. Download one first:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Download `
  -RemotePath '/home/admin_b50578/planner-maintenance/backups/operator-EXAMPLE/planner-EXAMPLE.db' `
  -LocalPath 'C:\Codex\planner-resource\backend\backups\server-before-changes.db'

.\scripts\maintenance\Local-Planner.ps1 -Action Open
```

Choose a new local filename if it already exists. Download expects a complete
destination filename and an existing Windows parent directory.

Rename a **host copy** of a remote backup:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Rename `
  -BackupFile '/home/admin_b50578/planner-maintenance/backups/operator-EXAMPLE/planner-EXAMPLE.db' `
  -NewName 'before-course-changes-2026-11-12.db'
```

Only files under `planner-maintenance/backups` may be renamed. Files listed as
`/data/backups/...` are inside the volume, not directly available to SCP. For an
old volume backup, first copy it to a new host directory in an Ubuntu SSH shell:

```bash
mkdir -m 700 -p ~/planner-maintenance/backups/historical-copy
sudo docker cp planner-ressources-poc:/data/backups/ACTUAL-FILE.db ~/planner-maintenance/backups/historical-copy/
sudo chown "$(id -u):$(id -g)" ~/planner-maintenance/backups/historical-copy/ACTUAL-FILE.db
chmod 600 ~/planner-maintenance/backups/historical-copy/ACTUAL-FILE.db
```

Then use the host path with Download, Rename or Restore. Do not overwrite an
existing historical copy. Backups made during the earlier manual upgrade also
remain under `/home/admin_b50578/planner-update-2026-11-11`.

## 7. Copy a file from Windows to the server

This transfers one file and creates its parent directory. It does not restore
the database, restart the application or activate a configuration file.

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Upload `
  -LocalPath 'C:\Codex\planner-resource\backend\backups\STAMMDATEN_BASELINE_V2_2026-11-10\STAMMDATEN_ONLY_V2_2026-11-10.db' `
  -RemotePath '/home/admin_b50578/planner-maintenance/uploads/clean-baseline.db'
```

The destination must be a new filename. If a transfer fails, it may leave an
empty or partial file; retry with another destination filename. SQLite restore
validation will reject an invalid database.

You can transfer other ordinary files the same way. To transfer a folder, zip
it first and upload the zip. Do not send a live database by raw file copy; create
a consistent backup first. Keep `.env` files, keys and backups private.

## 8. Remote server: replace the database from a backup

`BackupFile` here is an **absolute path on the Ubuntu host**, not a Windows
path and not `/data/...` inside the container. Use an uploaded file or a host
backup from section 5.

Preview (the application keeps running):

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Restore `
  -BackupFile '/home/admin_b50578/planner-maintenance/uploads/clean-baseline.db'
```

Apply during a maintenance window, after active optimization runs finish:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Restore `
  -BackupFile '/home/admin_b50578/planner-maintenance/uploads/clean-baseline.db' `
  -Apply
```

The script validates the source, stops the active container, checks that no
other running container mounts the database volume, creates a pre-restore
backup under `/data/backups/before-restore-*`, applies the restore using the
existing image user, then restarts the application **only after success**.
The automatic pre-restore backup stays inside the volume; copy it off-host if
needed. Consider running `Backup` and `Download` first for a separate recovery copy.

If restore fails after shutdown, the application remains stopped. Read the
error and resolve it before restarting; do not delete WAL or journal files.
The preview does not modify target data. Applying does replace it, including
accounts and authentication state.

Check the restarted application:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Status
```

Allow roughly 30 seconds for Docker's health check, then sign in and check the
semester/master data. `Status` shows all matching retained containers as well
as the active container's recent logs.

## 9. Create and publish a new container image

Changing local source files does not update a published image. This project's
`publish-container.yml` builds and pushes images when a GitHub release is
**published**. The release workflow first runs its own CI verification.

### A. Commit the intended changes and merge them into master

In PowerShell:

```powershell
Set-Location C:\Codex\planner-resource
git status
git diff
```

Stage only the intended files, commit, push your feature branch and merge your
pull request through your normal workflow. Do not use `git add .` when unrelated
work is present. If you are intentionally working directly on `master`, stage
the selected paths, commit, then `git push origin master`.

Wait for the merged `master` commit's CI to be green:

- [CI runs](https://github.com/dresanovic/planner-ressources/actions/workflows/ci.yml)
- [Container publication runs](https://github.com/dresanovic/planner-ressources/actions/workflows/publish-container.yml)

### B. Publish the release

Use a new, unused version tag. `v2.1.2` below is an example: check existing
releases first and increase the version if it is already published.

In [GitHub's release form](https://github.com/dresanovic/planner-ressources/releases/new):

1. Create the new tag, for example `v2.1.2`.
2. Select `master` as the target and verify it contains the intended change.
3. Enter a title, generate release notes and review them.
4. Publish the release. Saving only a draft does not trigger the image build.
5. Wait for **Publish container image** to finish successfully, including its
   Verify release and Build and publish image jobs.

Alternatively, if GitHub CLI is installed and authenticated, pin the release
to the exact remote master commit you checked:

```powershell
gh release list --repo dresanovic/planner-ressources --limit 10
$version = 'v2.1.2' # Replace with a new unused version.
$revision = gh api repos/dresanovic/planner-ressources/commits/master --jq .sha
if ($LASTEXITCODE -ne 0) { throw 'Could not read remote master.' }
gh run list --repo dresanovic/planner-ressources --workflow ci.yml --commit $revision --limit 5
# Check that the CI run for this exact commit succeeded before continuing.
gh release create $version --repo dresanovic/planner-ressources `
  --target $revision --title "Planner $version" --generate-notes
if ($LASTEXITCODE -ne 0) { throw 'Release publication failed.' }
gh run list --repo dresanovic/planner-ressources --workflow publish-container.yml --limit 5
```

The publishing run may take a few moments to appear. Check its release tag
and commit, then wait for it to turn green. To watch a specific run:

```powershell
gh run watch ACTUAL_RUN_ID --repo dresanovic/planner-ressources --exit-status
```

The resulting image is:

```text
ghcr.io/dresanovic/planner-ressources:v2.1.2
```

It contains both `linux/amd64` and `linux/arm64` variants. Your Ubuntu server
pulls the matching variant. Keep the old application running during the build.
Do not move an existing release tag to new code; publish a new version.

### Optional: build locally for testing only

Docker Desktop must be running:

```powershell
docker build --file infrastructure/docker/Dockerfile `
  --tag planner-ressources:local .
if ($LASTEXITCODE -ne 0) { throw 'Local image build failed.' }
```

This creates a local test image only. It does not publish a release or update
the remote server. The supported server update below uses the published GHCR
release image; no manual `docker save`/`docker load` is needed.

## 10. Update the remote application using the published image

After the release image workflow is green, run from **Windows PowerShell**:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Update `
  -Image 'ghcr.io/dresanovic/planner-ressources:v2.1.2'
```

Use the actual version you just published. The update script:

1. Checks the expected database, port, mounts, restart policy and saved runtime
   configuration. Additional/custom mounts require a reviewed script adjustment.
2. Pulls the exact release and uses its downloaded immutable image ID for startup.
3. Makes a fresh online database backup and copies it to the host backup folder.
4. Stops and renames the existing container with a unique `-before-TIMESTAMP` suffix.
5. Starts the new image with the same volume, IP/port, `planner.env`, fingerprint
   key and optimization policy directory.
6. Waits up to roughly two minutes for Docker health. If startup fails, it prints
   logs and stops the new container, retaining the backup and old container.

This upgrade does **not** restore the clean baseline. Your current database is
retained; normal startup migrations may update its schema. It does not change
`APP_ENV=development` or your `standard_optimized` selection.

Avoid updating while optimization or edits are active. The online backup is
created shortly before shutdown; changes made after the backup could be lost
if that backup is later used for recovery.

After success:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Status
```

Open <http://10.155.11.130:8081>, press **Ctrl+F5**, sign in, check master data
and try optimization. These scripts preserve the existing temporary HTTP
setup; they do not provide HTTPS encryption.

## 11. Recovery and common errors

| Symptom | Next action |
| --- | --- |
| SSH/password prompt repeats | Several SSH/SCP connections are used; enter the password when requested. Nothing is hard-coded. |
| `administratively prohibited` from an SSH tunnel | These scripts do not use tunnels or request port forwarding. Run the PowerShell maintenance command directly. |
| `Permission denied` / sudo failure | Stop and check access. Do not change SSH security settings to make the scripts work. |
| Private registry denies pull | Authenticate on Ubuntu using `sudo docker login ghcr.io`; keep tokens out of scripts and `.env`. |
| Docker reports an unexpected mount or configuration | Inspect the active deployment. Update the maintenance script to preserve intentional configuration changes before proceeding. |
| Restore helper missing in the image | The wrapper automatically transfers both Python helpers and mounts them read-only. No image rebuild is needed for the maintenance helper. |
| Preview succeeds but apply fails | Preview validates the source; offline checks, permissions and sidecar checks happen during apply. Read the actual apply error. |
| WAL, SHM or journal exists | Leave files intact and investigate SQLite state after a clean stop. |
| New image unhealthy | The update script stops it. Inspect logs with `Status`; retain the generated recovery backup. |
| Login changes after restore | Use an account from the restored snapshot. Accounts/session state were replaced too. |
| Browser still runs the old frontend | Press Ctrl+F5, then verify the active image using `Status`. |

All retained containers share the **same database volume**. Starting an old
container is not a database rollback and can be incompatible after migrations.
Never run two application containers against this SQLite volume.

To recover after a failed upgrade: record the printed host backup path and old
image, keep all application containers stopped, and assess whether the old image
can read the current schema. If not, restore the pre-upgrade snapshot offline
using the transferred helper before starting the compatible old image. Do not
blindly automate an image-only rollback. Keep the failed container/logs until
the cause is understood. Restoring a backup also loses changes made after it.

Do not use `docker volume rm`, `docker compose down -v` or volume pruning during
maintenance. They can delete the persistent database and its in-volume backups.
Passwords, `planner.env`, the fingerprint key, inspection JSON and database
backups must not be committed to Git.

## 12. Script parameters for another installation

The local script accepts `-Database`, `-BackupDirectory` and `-Python`.
The remote wrapper accepts:

```powershell
.\scripts\maintenance\Remote-Planner.ps1 -Action Status `
  -Server '10.155.11.130' -Port 17655 -User 'admin_b50578' `
  -RemoteDirectory '/home/admin_b50578/planner-maintenance' `
  -DeploymentDirectory '/home/admin_b50578/planner-update-2026-11-11' `
  -Container 'planner-ressources-poc' -Volume 'planner-ressources-poc-data'
```

For another user, change both home-directory parameters too. `Update` deliberately
retains this installation's binding `10.155.11.130:8081:8080`; another deployment
requires reviewing and changing that binding and its preflight check in
`remote-planner.sh`. The scripts do not discover an arbitrary deployment.

## 13. Offline verification

Run the supplied smoke checks from PowerShell:

```powershell
.\scripts\maintenance\Test-Maintenance.ps1
```

These use disposable SQLite databases in your Windows temporary directory and
mock SSH/SCP commands. They check backup integrity, preview behavior, restore,
preservation of replaced data, rename limits, listing, shell argument quoting
and transfer overwrite protection. They never connect to the server or touch
the real local database. Temporary fixtures are removed afterward.

The scripts were checked with these offline tests, PowerShell parsing and a
Bash syntax check. Remote Docker execution has not been tested against your
live server as part of creating this guide. Start with `Status`, then `Backup`
and a restore preview before scheduling an actual restore or update.
