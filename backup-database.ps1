# Backup MySQL Database Script
# Run this BEFORE rebuilding or stopping Docker to preserve your data

$BackupDir = ".\database_backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\mydb_backup_$Timestamp.sql"

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Host "Created backup directory: $BackupDir"
}

# Check if MySQL container is running
$ContainerStatus = docker ps --filter "name=mysql_db" --format "{{.State}}"
if ($ContainerStatus -ne "running") {
    Write-Host "Error: MySQL container (mysql_db) is not running"
    Write-Host "Start it with: docker compose up -d"
    exit 1
}

# Backup the database
Write-Host "Backing up database to: $BackupFile"
docker exec mysql_db mysqldump -u root -psecret mydb > $BackupFile

if ($LASTEXITCODE -eq 0) {
    $FileSize = (Get-Item $BackupFile).Length
    Write-Host "✓ Backup successful! Size: $([math]::Round($FileSize/1MB, 2)) MB"
    Write-Host "Location: $(Resolve-Path $BackupFile)"
} else {
    Write-Host "✗ Backup failed!"
    exit 1
}
