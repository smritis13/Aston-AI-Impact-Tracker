# Database Persistence & Backup Guide

## ⚠️ Important: Preventing Data Loss

Your database data is stored in a Docker volume called `db_data`. To prevent losing your data during rebuilds:

### ❌ DO NOT Run These Commands
```bash
# These WILL DELETE your data!
docker compose down -v
docker volume rm db_data
docker volume prune
```

### ✅ DO Run These Commands

#### Option 1: Safe Rebuild (Recommended)
```bash
# Automatically backs up database, rebuilds, and restores
.\rebuild-safe.ps1
```

This script:
1. Automatically backs up your current database
2. Stops containers WITHOUT removing volumes
3. Rebuilds Docker images
4. Starts everything up with your data intact

#### Option 2: Manual Rebuild
```bash
# Safe way - preserves database volumes
docker compose down
docker compose up --build
```

## 📊 Backup & Restore Scripts

### Backup Your Database
```bash
# Creates a SQL backup file
.\backup-database.ps1
```
Backups are stored in `.\database_backups\` with timestamps.

### Restore from Backup
```bash
# Interactive - shows available backups
.\restore-database.ps1

# Or specify a backup file directly
.\restore-database.ps1 -BackupFile ".\database_backups\mydb_backup_20260527_120000.sql"
```

## 📁 Database Volume Persistence

Your Docker setup uses named volumes for data persistence:

```yaml
volumes:
  db_data:           # Persists MySQL data
  frontend_node_modules:  # Caches frontend node_modules
```

### Checking Volume Status
```bash
# List all volumes
docker volume ls

# See volume details
docker volume inspect db_data
```

## 🔄 Workflow: Safe Development & Rebuilds

1. **Before Major Changes**
   ```bash
   .\backup-database.ps1
   ```

2. **Rebuild Docker**
   ```bash
   .\rebuild-safe.ps1
   ```

3. **If Something Goes Wrong**
   ```bash
   .\restore-database.ps1
   ```

## 📋 What Gets Persisted

✅ Persisted (Saved Between Rebuilds):
- MySQL database (all reports, use cases, themes)
- All uploaded data

❌ Not Persisted (Reset on Rebuild):
- Docker container logs
- Temp files in `/tmp`

## 🆘 Emergency Recovery

If you accidentally deleted a volume:

1. Check for backups:
   ```bash
   dir .\database_backups\
   ```

2. Restore from most recent backup:
   ```bash
   .\restore-database.ps1
   ```

3. If no backups exist:
   - Your data may be recoverable from Docker volume backups
   - Contact support with your situation

## 🎯 Best Practices

1. **Always backup before major changes**
   ```bash
   .\backup-database.ps1
   ```

2. **Use `docker compose down` (not `down -v`)**
   ```bash
   # ✅ Good - preserves data
   docker compose down
   
   # ❌ Bad - deletes data
   docker compose down -v
   ```

3. **Regular automated backups** (future enhancement)
   - Consider setting up automated nightly backups
   - Keep multiple backup versions

## 🐛 Troubleshooting

**Q: My data disappeared after rebuild!**
- A: Check if you ran `docker compose down -v` - this deletes volumes
- Use `.\restore-database.ps1` to restore from backup

**Q: Volume shows but database is empty**
- A: Data might not have synced. Check logs:
  ```bash
  docker logs mysql_db
  ```

**Q: Can't connect to database after rebuild**
- A: Wait a few seconds for MySQL to start, then:
  ```bash
  docker exec mysql_db mysqladmin ping -u root -psecret
  ```

## 📞 Quick Commands Reference

```bash
# View database contents
docker exec mysql_db mysql -u root -psecret mydb -e "SHOW TABLES;"

# Backup database
.\backup-database.ps1

# Restore database
.\restore-database.ps1

# Safe rebuild
.\rebuild-safe.ps1

# Check database size
docker exec mysql_db du -sh /var/lib/mysql

# Monitor database in real-time
docker logs -f mysql_db
```
