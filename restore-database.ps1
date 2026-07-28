# Restore MySQL Database Script
# Use this to restore from a backup SQL file

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupFile
)

$BackupDir = ".\database_backups"

# If no backup file specified, show available backups
if ([string]::IsNullOrEmpty($BackupFile)) {
    Write-Host "Available backups:"
    $Backups = Get-ChildItem "$BackupDir\*.sql" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if ($Backups.Count -eq 0) {
        Write-Host "No backups found in $BackupDir"
        exit 1
    }
    
    for ($i = 0; $i -lt $Backups.Count; $i++) {
        $Size = [math]::Round($Backups[$i].Length/1MB, 2)
        $Modified = $Backups[$i].LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "$i. $($Backups[$i].Name) ($Size MB) - $Modified"
    }
    
    $Selection = Read-Host "Select backup to restore (0-$($Backups.Count-1))"
    $BackupFile = $Backups[$Selection].FullName
}

# Verify backup file exists
if (!(Test-Path $BackupFile)) {
    Write-Host "Error: Backup file not found: $BackupFile"
    exit 1
}

# Check if MySQL container is running
$ContainerStatus = docker ps --filter "name=mysql_db" --format "{{.State}}"
if ($ContainerStatus -ne "running") {
    Write-Host "Error: MySQL container (mysql_db) is not running"
    Write-Host "Start it with: docker compose up -d"
    exit 1
}

# Confirm before restoring
Write-Host ""
Write-Host "WARNING: This will replace all current database data!"
Write-Host "Backup file: $(Resolve-Path $BackupFile)"
$Confirm = Read-Host "Type 'YES' to confirm restore"

if ($Confirm -ne "YES") {
    Write-Host "Restore cancelled"
    exit 0
}

# Restore the database
Write-Host "Restoring database from: $BackupFile"
Get-Content $BackupFile | docker exec -i mysql_db mysql -u root -psecret mydb

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Restore successful!"
} else {
    Write-Host "✗ Restore failed!"
    exit 1
}
