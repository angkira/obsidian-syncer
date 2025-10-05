#!/usr/bin/env python3
"""
JWT Token Generator for Obsidian LiveSync CouchDB
Provides a more user-friendly interface with Python
"""

import sys
import hmac
import hashlib
import base64
import json
import time
from datetime import datetime, timedelta

def base64url_encode(data):
    """Base64 URL-safe encoding without padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def generate_jwt(username, secret, duration_hours=24):
    """Generate JWT token for CouchDB authentication"""

    # JWT Header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    # JWT Payload
    issued_at = int(time.time())
    expiration = issued_at + (duration_hours * 3600)

    payload = {
        "sub": username,
        "name": username,
        "iat": issued_at,
        "exp": expiration,
        "_couchdb.roles": []
    }

    # Encode header and payload
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')))

    # Create signature
    message = f"{header_b64}.{payload_b64}"
    # Convert hex secret to bytes
    secret_bytes = bytes.fromhex(secret)
    signature = hmac.new(
        secret_bytes,
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    # Complete JWT
    jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"

    return jwt_token, issued_at, expiration

def main():
    # Read JWT secret from .env file
    try:
        with open('/root/obsidian-livesync/.env', 'r') as f:
            for line in f:
                if line.startswith('JWT_HMAC_SECRET='):
                    jwt_secret = line.split('=', 1)[1].strip()
                    break
            else:
                print("ERROR: JWT_HMAC_SECRET not found in .env file")
                sys.exit(1)
    except FileNotFoundError:
        print("ERROR: .env file not found at /root/obsidian-livesync/.env")
        sys.exit(1)

    # Parse arguments
    username = sys.argv[1] if len(sys.argv) > 1 else "obsidian"
    duration_hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    # Generate JWT
    token, issued_at, expiration = generate_jwt(username, jwt_secret, duration_hours)

    # Display results
    print("=" * 60)
    print(f"JWT Token Generated for: {username}")
    print("=" * 60)
    print()
    print(f"Token (valid for {duration_hours} hours):")
    print(token)
    print()
    print(f"Issued at:  {datetime.fromtimestamp(issued_at).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Expires at: {datetime.fromtimestamp(expiration).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    print("=" * 60)
    print("Usage with curl:")
    print(f"curl -H 'Authorization: Bearer {token}' http://37.27.209.193/obsidian/")
    print()
    print("Usage in Obsidian LiveSync plugin:")
    print(f"Set 'Authorization Header' to: Bearer {token}")
    print("=" * 60)

if __name__ == "__main__":
    main()
