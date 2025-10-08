#!/bin/bash
# Initialize CouchDB database for Obsidian LiveSync

set -e

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "❌ .env file not found"
    exit 1
fi

echo "🔧 Initializing CouchDB..."

# Wait for CouchDB to be ready
echo "⏳ Waiting for CouchDB to start..."
for i in {1..30}; do
    if docker exec obsidian-couchdb curl -sf http://localhost:5984/_up > /dev/null 2>&1; then
        echo "✅ CouchDB is ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Create database if it doesn't exist
echo "📁 Creating database: $DB_NAME"
docker exec obsidian-couchdb curl -X PUT \
    -u "$COUCHDB_USER:$COUCHDB_PASSWORD" \
    "http://localhost:5984/$DB_NAME" 2>/dev/null || echo "Database may already exist"

# Set up replication user (sync user)
echo "👤 Setting up sync user: $SYNC_USER"
docker exec obsidian-couchdb curl -X PUT \
    -u "$COUCHDB_USER:$COUCHDB_PASSWORD" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$SYNC_USER\",\"password\":\"$SYNC_PASSWORD\",\"roles\":[],\"type\":\"user\"}" \
    "http://localhost:5984/_users/org.couchdb.user:$SYNC_USER" 2>/dev/null || echo "Sync user may already exist"

# Set database permissions
echo "🔒 Setting database permissions..."
docker exec obsidian-couchdb curl -X PUT \
    -u "$COUCHDB_USER:$COUCHDB_PASSWORD" \
    -H "Content-Type: application/json" \
    -d "{\"admins\":{\"names\":[],\"roles\":[]},\"members\":{\"names\":[\"$SYNC_USER\"],\"roles\":[]}}" \
    "http://localhost:5984/$DB_NAME/_security" 2>/dev/null

echo "✅ CouchDB initialization complete!"
echo ""
echo "📊 Database Info:"
echo "   - Database: $DB_NAME"
echo "   - Admin User: $COUCHDB_USER"
echo "   - Sync User: $SYNC_USER"
echo "   - URL: http://localhost:5984/$DB_NAME"
