#!/bin/bash
# PostgreSQL Automatic Backup Script
# Cron: 0 3 * * * /path/to/backup.sh >> /var/log/journal_backup.log 2>&1

set -e

# Configuration
BACKUP_DIR="/home/bobomurod/backups/journal"
CONTAINER_NAME="journal_db"
DB_NAME="journal2"
DB_USER="postgres"
KEEP_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting backup..."

# Dump and compress
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was created successfully
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup successful: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi

# Remove old backups (older than KEEP_DAYS)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l)
echo "[$(date)] Cleanup done. $REMAINING backups remaining."

echo "[$(date)] Backup complete."
