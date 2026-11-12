[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Backup','Restore','List','Open','Rename')][string]$Action,
    [string]$Database,
    [string]$BackupDirectory,
    [string]$BackupFile,
    [string]$NewName,
    [string]$Python,
    [switch]$Apply,
    [switch]$BackendStopped
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (!$Database) { $Database = Join-Path $repo 'backend/planner.db' }
if (!$BackupDirectory) { $BackupDirectory = Join-Path $repo 'backend/backups' }
if (!$Python) { $Python = Join-Path $repo 'backend/.venv/Scripts/python.exe' }

function Invoke-Python([string[]]$Arguments) {
    if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python. Supply -Python." }
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python operation failed (exit $LASTEXITCODE)." }
}

switch ($Action) {
    Backup {
        # A unique subdirectory also prevents same-second backup name collisions.
        $destination = Join-Path $BackupDirectory ('manual-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8))
        Invoke-Python @((Join-Path $repo 'backend/scripts/backup_sqlite_db.py'), '--database', $Database, '--output-dir', $destination)
    }
    Restore {
        if (!$BackupFile) { throw 'Supply -BackupFile with the source .db file.' }
        if ($Apply -and !$BackendStopped) { throw 'Stop all processes using this database, then supply -Apply -BackendStopped.' }
        $arguments = @((Join-Path $repo 'backend/scripts/restore_sqlite_db.py'), '--backup', $BackupFile, '--database', $Database, '--backup-dir', $BackupDirectory)
        if ($Apply) { $arguments += @('--apply','--backend-stopped') }
        Invoke-Python $arguments
    }
    List {
        Get-ChildItem -LiteralPath $BackupDirectory -Filter '*.db' -File -Recurse -ErrorAction Continue |
            Sort-Object LastWriteTime -Descending | Select-Object LastWriteTime, Length, FullName
    }
    Open { Start-Process explorer.exe -ArgumentList ('"' + (Resolve-Path -LiteralPath $BackupDirectory).Path + '"') }
    Rename {
        if (!$BackupFile -or !$NewName) { throw 'Supply -BackupFile and -NewName.' }
        if ($NewName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*\.db$') { throw 'NewName must be a simple .db filename (letters, numbers, dots, underscores, hyphens).' }
        $source = (Resolve-Path -LiteralPath $BackupFile).Path
        $root = [IO.Path]::GetFullPath($BackupDirectory).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
        if (!$source.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Rename is limited to files inside BackupDirectory.' }
        $target = Join-Path (Split-Path $source -Parent) $NewName
        if (Test-Path -LiteralPath $target) { throw "Already exists: $target" }
        Rename-Item -LiteralPath $source -NewName $NewName
        Write-Output "Renamed to: $target"
    }
}
