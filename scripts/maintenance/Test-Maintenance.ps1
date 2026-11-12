# Offline checks only: temporary SQLite fixtures and mocked SSH/SCP. No server access.
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $repo 'backend/.venv/Scripts/python.exe'
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('planner-maintenance-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratch | Out-Null
function Assert([bool]$Condition, [string]$Message) { if (!$Condition) { throw $Message } }
function Expect-Failure([scriptblock]$Operation) {
    $failed = $false
    try { & $Operation | Out-Null } catch { $failed = $true }
    Assert $failed 'Expected operation to fail.'
}
try {
    $database = Join-Path $scratch 'planner.db'
    $backups = Join-Path $scratch 'backups'
    & $python -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.executescript("CREATE TABLE courses(id INTEGER); CREATE TABLE semesters(id INTEGER); INSERT INTO courses VALUES(1);"); c.commit(); c.close()' $database
    Assert ($LASTEXITCODE -eq 0) 'Could not create fixture.'
    $local = Join-Path $PSScriptRoot 'Local-Planner.ps1'
    & $local -Action Backup -Database $database -BackupDirectory $backups -Python $python
    $backup = (Get-ChildItem $backups -Filter '*.db' -Recurse -File | Select-Object -First 1).FullName
    Assert ([bool]$backup) 'Backup was not created.'
    & $python -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute("UPDATE courses SET id=2"); c.commit(); c.close()' $database
    Assert ($LASTEXITCODE -eq 0) 'Could not modify fixture.'
    & $local -Action Restore -Database $database -BackupDirectory $backups -BackupFile $backup -Python $python
    $value = & $python -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("SELECT id FROM courses").fetchone()[0])' $database
    Assert ($value -eq '2') 'Preview changed the database.'
    Expect-Failure { & $local -Action Restore -Database $database -BackupDirectory $backups -BackupFile $backup -Python $python -Apply }
    & $local -Action Restore -Database $database -BackupDirectory $backups -BackupFile $backup -Python $python -Apply -BackendStopped
    $value = & $python -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("SELECT id FROM courses").fetchone()[0])' $database
    Assert ($value -eq '1') 'Restore did not replace fixture data.'
    $safety = @(Get-ChildItem $backups -Directory -Filter 'before-restore-*')
    Assert ($safety.Count -eq 1) 'Pre-restore backup not created.'
    $saved = (Get-ChildItem $safety[0].FullName -Filter '*.db').FullName
    $value = & $python -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("SELECT id FROM courses").fetchone()[0])' $saved
    Assert ($value -eq '2') 'Pre-restore backup lost the replaced data.'
    & $local -Action Rename -BackupDirectory $backups -BackupFile $backup -NewName 'named-backup.db'
    $renamed = Join-Path (Split-Path $backup -Parent) 'named-backup.db'
    Assert (Test-Path $renamed) 'Rename failed.'
    Expect-Failure { & $local -Action Rename -BackupDirectory $backups -BackupFile $renamed -NewName 'named-backup.db' }
    Expect-Failure { & $local -Action Rename -BackupDirectory $backups -BackupFile $database -NewName 'active.db' }
    $listing = @(& $local -Action List -BackupDirectory $backups)
    Assert ($listing.Count -eq 2) 'List did not include both backup files.'

    # Shadow native commands to verify generated remote commands without a connection.
    $global:PlannerMaintenanceCalls = [Collections.Generic.List[object]]::new()
    function global:ssh {
        $global:PlannerMaintenanceCalls.Add(@('ssh') + $args)
        $global:LASTEXITCODE = 0
    }
    function global:scp {
        $global:PlannerMaintenanceCalls.Add(@('scp') + $args)
        $global:LASTEXITCODE = 0
    }
    $remote = Join-Path $PSScriptRoot 'Remote-Planner.ps1'
    & $remote -Action Restore -BackupFile "/home/admin_b50578/backup's-file.db"
    $command = $global:PlannerMaintenanceCalls[$global:PlannerMaintenanceCalls.Count-1][-1]
    Assert ($command.Contains("'restore'")) 'Restore action missing from SSH command.'
    Assert ($command.EndsWith("'0'")) 'Restore should default to preview.'
    Assert (!$command.Contains("backup's-file")) 'Single quote was not escaped.'
    & $remote -Action Restore -BackupFile '/home/admin_b50578/backup.db' -Apply
    $command = $global:PlannerMaintenanceCalls[$global:PlannerMaintenanceCalls.Count-1][-1]
    Assert ($command.EndsWith("'1'")) 'Apply flag missing from SSH command.'
    & $remote -Action Upload -LocalPath $renamed -RemotePath '/home/admin_b50578/uploads/test.db'
    Assert ($global:PlannerMaintenanceCalls[$global:PlannerMaintenanceCalls.Count-2][-1].Contains('set -C')) 'Upload should refuse overwrites.'
    Expect-Failure { & $remote -Action Upload -LocalPath $renamed -RemotePath '/home/a;bad.db' }
    Write-Output 'PASS: local backup/preview/restore/recovery/rename/list and mocked remote command/transfer checks.'
} finally {
    Remove-Item Function:/ssh,Function:/scp -ErrorAction SilentlyContinue
    Remove-Variable PlannerMaintenanceCalls -Scope Global -ErrorAction SilentlyContinue
    # Verify the generated absolute path before recursively removing only the fixture.
    $resolved = [IO.Path]::GetFullPath($scratch)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf) -like 'planner-maintenance-test-*') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
