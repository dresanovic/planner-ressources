[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Backup','Restore','List','Rename','Upload','Download','Update','Status')][string]$Action,
    [string]$Server = '10.155.11.130',
    [int]$Port = 17655,
    [string]$User = 'admin_b50578',
    [string]$RemoteDirectory = '/home/admin_b50578/planner-maintenance',
    [string]$DeploymentDirectory = '/home/admin_b50578/planner-update-2026-11-11',
    [string]$Container = 'planner-ressources-poc',
    [string]$Volume = 'planner-ressources-poc-data',
    [string]$BackupFile,
    [string]$NewName,
    [string]$LocalPath,
    [string]$RemotePath,
    [string]$Image,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ($Server -notmatch '^[A-Za-z0-9.-]+$' -or $User -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid SSH server or user.' }
foreach ($path in @($RemoteDirectory,$DeploymentDirectory)) {
    if ($path -notmatch '^/[A-Za-z0-9_./-]+$' -or $path -match '(^|/)\.\.(/|$)') { throw 'Remote directories must be absolute paths without spaces or parent traversal.' }
}
$connection = "${User}@${Server}"
function Quote-Sh([string]$Value) {
    $quote = [string][char]39
    $escapedQuote = $quote + [char]34 + $quote + [char]34 + $quote
    return $quote + $Value.Replace($quote,$escapedQuote) + $quote
}
function Invoke-Ssh([string]$Command, [switch]$Terminal) {
    $sshArguments = @('-p', "$Port")
    if ($Terminal) { $sshArguments += '-tt' }
    & ssh @sshArguments $connection $Command
    if ($LASTEXITCODE -ne 0) { throw "Remote operation failed (exit $LASTEXITCODE). Read the output above; do not continue with later steps." }
}
function Invoke-Scp([string[]]$Arguments) {
    # Legacy SCP protocol supports servers where the SFTP subsystem is disabled.
    & scp -O -P $Port @Arguments
    if ($LASTEXITCODE -ne 0) { throw "File transfer failed (exit $LASTEXITCODE)." }
}
function Assert-TransferPath([string]$Path) {
    if ($Path -notmatch '^/[A-Za-z0-9_./-]+$' -or $Path -match '(^|/)\.\.(/|$)') { throw 'Remote file paths must be absolute, with letters, numbers, dots, underscores, hyphens or slashes.' }
}

if ($Action -eq 'Upload') {
    if (!$LocalPath -or !$RemotePath) { throw 'Supply -LocalPath and -RemotePath (full destination filename).' }
    Assert-TransferPath $RemotePath
    $source = (Resolve-Path -LiteralPath $LocalPath).Path
    if (!(Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Upload supports one file per call.' }
    $parent = $RemotePath.Substring(0,$RemotePath.LastIndexOf('/'))
    # noclobber reserves the destination; an existing file is never replaced.
    Invoke-Ssh ("umask 077; mkdir -p " + (Quote-Sh $parent) + " && (set -C; : > " + (Quote-Sh $RemotePath) + ')')
    Invoke-Scp @($source, "${connection}:$RemotePath")
    Write-Output "Uploaded: $RemotePath"
    return
}
if ($Action -eq 'Download') {
    if (!$LocalPath -or !$RemotePath) { throw 'Supply -RemotePath and -LocalPath (full destination filename).' }
    Assert-TransferPath $RemotePath
    if (Test-Path -LiteralPath $LocalPath) { throw 'Local destination already exists. Choose a new filename.' }
    Invoke-Scp @("${connection}:$RemotePath", $LocalPath)
    return
}
if ($Action -eq 'Restore' -and !$BackupFile) { throw 'Supply -BackupFile with an absolute server path.' }
if ($Action -eq 'Rename' -and (!$BackupFile -or !$NewName)) { throw 'Supply -BackupFile and -NewName.' }
if ($Action -eq 'Update' -and !$Image) { throw 'Supply -Image with an exact release tag, for example ghcr.io/dresanovic/planner-ressources:v2.1.2.' }

# The release images omit the restore helper. Transfer the reviewed repository
# helpers separately and mount them read-only into a short-lived container.
Invoke-Ssh ("umask 077; mkdir -p " + (Quote-Sh "$RemoteDirectory/helpers"))
Invoke-Scp @((Join-Path $PSScriptRoot 'remote-planner.sh'), "${connection}:$RemoteDirectory/remote-planner.sh")
Invoke-Scp @((Join-Path $repo 'backend/scripts/backup_sqlite_db.py'), (Join-Path $repo 'backend/scripts/restore_sqlite_db.py'), "${connection}:$RemoteDirectory/helpers/")
$remoteArguments = @($Action.ToLowerInvariant(),$RemoteDirectory,$DeploymentDirectory,$Container,$Volume,$BackupFile,$NewName,$Image,([int]$Apply.IsPresent).ToString())
$command = 'bash ' + (Quote-Sh "$RemoteDirectory/remote-planner.sh") + ' ' + (($remoteArguments | ForEach-Object { Quote-Sh $_ }) -join ' ')
Invoke-Ssh $command -Terminal
