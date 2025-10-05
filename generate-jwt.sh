#!/bin/bash
# JWT Token Generator for Obsidian LiveSync
# Generates JWT tokens for CouchDB authentication

set -e

# Load environment variables
source /root/obsidian-livesync/.env

# Default values
USERNAME="${1:-obsidian}"
DURATION="${2:-86400}"  # 24 hours in seconds

# Calculate expiration timestamp
ISSUED_AT=$(date +%s)
EXPIRATION=$((ISSUED_AT + DURATION))

# JWT Header (HS256)
HEADER='{"alg":"HS256","typ":"JWT"}'
HEADER_B64=$(echo -n "$HEADER" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')

# JWT Payload
PAYLOAD=$(cat <<EOF
{
  "sub": "$USERNAME",
  "name": "$USERNAME",
  "iat": $ISSUED_AT,
  "exp": $EXPIRATION,
  "_couchdb.roles": []
}
EOF
)
PAYLOAD_B64=$(echo -n "$PAYLOAD" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')

# Create signature
SIGNATURE_INPUT="${HEADER_B64}.${PAYLOAD_B64}"
SIGNATURE=$(echo -n "$SIGNATURE_INPUT" | openssl dgst -sha256 -hmac "$JWT_HMAC_SECRET" -binary | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')

# Complete JWT
JWT="${HEADER_B64}.${PAYLOAD_B64}.${SIGNATURE}"

# Output
echo "=================================================="
echo "JWT Token Generated for: $USERNAME"
echo "=================================================="
echo ""
echo "Token (valid for $(($DURATION / 3600)) hours):"
echo "$JWT"
echo ""
echo "Issued at:  $(date -d @$ISSUED_AT '+%Y-%m-%d %H:%M:%S %Z')"
echo "Expires at: $(date -d @$EXPIRATION '+%Y-%m-%d %H:%M:%S %Z')"
echo ""
echo "=================================================="
echo "Usage with curl:"
echo "curl -H 'Authorization: Bearer $JWT' http://37.27.209.193/obsidian/"
echo ""
echo "Usage in Obsidian LiveSync plugin:"
echo "Set 'Authorization Header' to: Bearer $JWT"
echo "=================================================="
