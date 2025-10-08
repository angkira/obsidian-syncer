#!/bin/bash
# Backup CouchDB data in Docker environment

set -e

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/couchdb_backup_$TIMESTAMP.tar.gz"
MAX_BACKUPS="${MAX_BACKUPS:-14}"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting CouchDB backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create compressed backup of CouchDB data
if [ -d "/opt/couchdb/data" ]; then
    tar -czf "$BACKUP_FILE" -C /opt/couchdb data 2>&1 | tee -a "$BACKUP_DIR/backup.log"

    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup created: $BACKUP_FILE ($BACKUP_SIZE)" >> "$BACKUP_DIR/backup.log"

        # Remove old backups
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/couchdb_backup_*.tar.gz 2>/dev/null | wc -l)
        if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
            ls -1t "$BACKUP_DIR"/couchdb_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Removed old backups (keeping latest $MAX_BACKUPS)" >> "$BACKUP_DIR/backup.log"
        fi

        echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup completed successfully" >> "$BACKUP_DIR/backup.log"
        echo "✅ Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup failed!" >> "$BACKUP_DIR/backup.log"
        exit 1
    fi
else
    echo "❌ CouchDB data directory not found"
    exit 1
fi
