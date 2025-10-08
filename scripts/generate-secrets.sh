#!/bin/bash
# Generate all required secrets for Obsidian LiveSync Server

set -e

echo "🔐 Generating secrets..."

# Generate random secrets using openssl
generate_secret() {
    openssl rand -hex 32
}

generate_password() {
    openssl rand -base64 32
}

# Generate all secrets
COUCHDB_PASSWORD=$(generate_password)
COUCHDB_SECRET=$(generate_secret)
SYNC_PASSWORD=$(generate_password)
JWT_HMAC_SECRET=$(generate_secret)
ADMIN_TOKEN=$(generate_secret)

# Output in .env format
cat <<EOF

# Generated Secrets - $(date)
COUCHDB_PASSWORD=$COUCHDB_PASSWORD
COUCHDB_SECRET=$COUCHDB_SECRET
SYNC_PASSWORD=$SYNC_PASSWORD
JWT_HMAC_SECRET=$JWT_HMAC_SECRET
ADMIN_TOKEN=$ADMIN_TOKEN
EOF

echo "" >&2
echo "✅ Secrets generated successfully!" >&2
echo "⚠️  Save these values securely!" >&2
