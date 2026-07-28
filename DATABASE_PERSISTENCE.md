# Database Persistence Guide

## Overview
This document explains how to ensure your database data persists between Docker container restarts and rebuilds.

## Important: Preserving Data

### ✅ How Data Persists (Default Behavior)
- **MySQL Database**: Uses Docker named volume `db_data:/var/lib/mysql`
- **Reports & Searches**: All stored in the persistent MySQL database
- **Use Cases**: Linked to reports and stored persistently
- **Restart Policy**: Services use `restart: unless-stopped` to automatically recover

### ⚠️ How Data Gets Deleted
Data is **permanently deleted** when you run:
```bash
docker-compose down -v
```
The `-v` flag removes all named volumes.

### ✅ Safe Operations (Data Preserved)
These operations keep your data:
```bash
# Restart containers (data stays)
docker-compose restart

# Stop and start (data stays)
docker-compose stop
docker-compose up

# Rebuild with updated code (data stays)
docker-compose up --build

# Remove containers but keep volumes (data stays)
docker-compose down
docker-compose up
```

### ❌ Operations That Delete Data
```bash
# This DELETES all data permanently
docker-compose down -v

# This also deletes named volumes
docker volume rm aston-ai-research-tool-main_db_data
```

## Viewing Data

You can view and manage your persistent data via phpMyAdmin:
- **URL**: http://localhost:8080
- **Username**: `myuser`
- **Password**: `mypassword`
- **Database**: `mydb`

## Backup Your Data

To backup your database before any operations:
```bash
# Create a backup
docker exec mysql_db mysqldump -u myuser -pmypassword mydb > backup.sql

# Restore from backup
docker exec -i mysql_db mysql -u myuser -pmypassword mydb < backup.sql
```

## Troubleshooting

### Data Lost After Docker Rebuild
This typically happens if:
1. You ran `docker-compose down -v`
2. The volume was accidentally deleted
3. The volume name changed in docker-compose.yml

**Solution**: 
- Don't use the `-v` flag unless you want to reset everything
- Always backup before major changes
- Check `docker volume ls` to see available volumes

### Check Volume Status
```bash
# List all volumes
docker volume ls

# Inspect a specific volume
docker volume inspect aston-ai-research-tool-main_db_data

# See volume location
docker volume inspect aston-ai-research-tool-main_db_data --format='{{.Mountpoint}}'
```

## Environment Setup

The docker-compose.yml file includes:
- **Persistent Volume**: `db_data:/var/lib/mysql`
- **Restart Policy**: `restart: unless-stopped`
- **Health Checks**: Ensures database is ready before services start
- **Named Volume**: `db_data` is created automatically and persists

## Recent Searches Feature

Recent searches are now displayed throughout the app:
- **Report Generation Page**: Shows up to 8 recent searches
- **Impact Case Study Page**: Shows up to 5 previous impact case studies
- **Reports List Page**: View all historical reports
- **Search Widget**: Appears on both pages for quick access

All searches are stored in the database and persist indefinitely.
