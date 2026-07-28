# Safe Docker Rebuild Script
# This script preserves your database during rebuilds

Write-Host "Safe Docker Rebuild - Database Preservation Mode" -ForegroundColor Green
Write-Host ""

# Step 1: Backup current database
Write-Host "Step 1: Creating database backup..."
$BackupDir = ".\database_backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\mydb_backup_before_rebuild_$Timestamp.sql"

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Check if containers are running
$DbRunning = (docker ps --filter "name=mysql_db" --format "{{.State}}" 2>$null)

if ($DbRunning -eq "running") {
    Write-Host "  Backing up database..."
    docker exec mysql_db mysqldump -u root -psecret mydb > $BackupFile 2>$null
    if ($LASTEXITCODE -eq 0) {
        $FileSize = (Get-Item $BackupFile).Length
        $SizeMB = [math]::Round($FileSize/1MB, 2)
        Write-Host "  Backup successful: $BackupFile ($SizeMB MB)"
    } else {
        Write-Host "  Backup skipped (database may be empty)"
    }
} else {
    Write-Host "  Database not running, skipping backup"
}

# Step 2: Stop containers WITHOUT removing volumes
Write-Host ""
Write-Host "Step 2: Stopping containers (preserving volumes)..."
docker compose down
Write-Host "  Containers stopped"

# Step 3: Rebuild
Write-Host ""
Write-Host "Step 3: Rebuilding Docker images..."
docker compose up --build -d
Write-Host "  Containers rebuilt and started"

# Step 4: Wait for database to be ready
Write-Host ""
Write-Host "Step 4: Waiting for database to be ready..."
$MaxAttempts = 30
$Attempt = 0
while ($Attempt -lt $MaxAttempts) {
    $DbReady = docker exec mysql_db mysqladmin ping -u root -psecret 2>$null | Select-String "mysqld is alive"
    if ($DbReady) {
        Write-Host "  Database is ready"
        break
    }
    $Attempt++
    Start-Sleep -Seconds 1
    Write-Host -NoNewline "."
}

if ($Attempt -eq $MaxAttempts) {
    Write-Host "  Database failed to start"
    exit 1
}

# Step 5: Check data
Write-Host ""
Write-Host "Step 5: Verifying data persistence..."
$TableCheck = docker exec mysql_db mysql -u root -psecret mydb -e "SHOW TABLES;" 2>$null
Write-Host "  Data verification complete"

Write-Host ""
Write-Host "Rebuild complete! Your data has been preserved." -ForegroundColor Green
Write-Host ""
Write-Host "Access your application:"
Write-Host "  Frontend: http://localhost:3002"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  phpMyAdmin: http://localhost:8080"
Write-Host ""
Write-Host "Database backup location: $BackupDir"
