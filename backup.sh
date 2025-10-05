#!/bin/bash
# Obsidian LiveSync CouchDB Backup Script
# Backs up CouchDB data directory with timestamp

BACKUP_DIR="/root/obsidian-livesync/backups"
DATA_DIR="/root/obsidian-livesync/data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/couchdb_backup_$TIMESTAMP.tar.gz"
MAX_BACKUPS=14  # Keep 14 days of backups

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Log start
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting CouchDB backup..." >> "$BACKUP_DIR/backup.log"

# Create compressed backup
tar -czf "$BACKUP_FILE" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")" 2>&1 | tee -a "$BACKUP_DIR/backup.log"

if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" >> "$BACKUP_DIR/backup.log"

    # Remove old backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/couchdb_backup_*.tar.gz 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
        ls -1t "$BACKUP_DIR"/couchdb_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Removed old backups (keeping latest $MAX_BACKUPS)" >> "$BACKUP_DIR/backup.log"
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup failed!" >> "$BACKUP_DIR/backup.log"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup completed successfully" >> "$BACKUP_DIR/backup.log"
