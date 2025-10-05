#!/root/obsidian-livesync/auth-proxy/.venv/bin/python3
"""
CLI tool for managing Obsidian LiveSync device tokens
"""
import sys
import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv("/root/obsidian-livesync/.env")

API_BASE = "http://127.0.0.1:5985/admin"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    print("❌ ERROR: ADMIN_TOKEN not found in .env file")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}


def create_token(device_name: str, expires_in_days: int = None):
    """Create a new device token"""
    params = {"device_name": device_name}
    if expires_in_days:
        params["expires_in_days"] = expires_in_days

    response = requests.post(f"{API_BASE}/tokens/create", headers=HEADERS, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token created for device: {device_name}")
        print(f"\n📱 Device Name: {data['device_name']}")
        print(f"🔑 Token ID: {data['token_id']}")
        print(f"📅 Created: {data['created_at']}")
        if data['expires_at']:
            print(f"⏰ Expires: {data['expires_at']}")
        print(f"\n🎫 JWT Token:")
        print(f"{data['jwt_token']}")
        print(f"\n📋 Usage in Obsidian:")
        print(f"Authorization Header: Bearer {data['jwt_token']}")
        print(f"\n💾 Save this token - it won't be shown again!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def list_tokens(include_revoked: bool = False):
    """List all tokens"""
    params = {"include_revoked": include_revoked}
    response = requests.get(f"{API_BASE}/tokens/list", headers=HEADERS, params=params)

    if response.status_code == 200:
        data = response.json()
        tokens = data['tokens']

        print(f"\n📋 Total tokens: {data['count']}\n")

        if not tokens:
            print("No tokens found.")
            return

        for token in tokens:
            status = "🔴 REVOKED" if token['revoked'] else "🟢 ACTIVE"
            print(f"{status} | {token['device_name']}")
            print(f"  Token ID: {token['token_id']}")
            print(f"  Created: {token['created_at']}")
            if token['expires_at']:
                expires = datetime.fromisoformat(token['expires_at'])
                if datetime.utcnow() > expires:
                    print(f"  Expires: {token['expires_at']} (⚠️ EXPIRED)")
                else:
                    print(f"  Expires: {token['expires_at']}")
            else:
                print(f"  Expires: Never")
            if token['last_used_at']:
                print(f"  Last used: {token['last_used_at']}")
            if token['revoked_at']:
                print(f"  Revoked at: {token['revoked_at']}")
            print()
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def revoke_token(token_id: str):
    """Revoke a token"""
    response = requests.post(f"{API_BASE}/tokens/revoke/{token_id}", headers=HEADERS)

    if response.status_code == 200:
        print(f"✅ Token {token_id} revoked successfully")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def delete_token(token_id: str):
    """Delete a token permanently"""
    response = requests.delete(f"{API_BASE}/tokens/delete/{token_id}", headers=HEADERS)

    if response.status_code == 200:
        print(f"✅ Token {token_id} deleted permanently")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def get_token_info(token_id: str):
    """Get token information"""
    response = requests.get(f"{API_BASE}/tokens/info/{token_id}", headers=HEADERS)

    if response.status_code == 200:
        token = response.json()
        status = "🔴 REVOKED" if token['revoked'] else "🟢 ACTIVE"

        print(f"\n{status} Token Information:\n")
        print(f"Device Name: {token['device_name']}")
        print(f"Token ID: {token['token_id']}")
        print(f"Created: {token['created_at']}")
        if token['expires_at']:
            print(f"Expires: {token['expires_at']}")
        else:
            print(f"Expires: Never")
        if token['last_used_at']:
            print(f"Last used: {token['last_used_at']}")
        if token['revoked_at']:
            print(f"Revoked at: {token['revoked_at']}")
        if token['metadata']:
            print(f"Metadata: {token['metadata']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def cleanup_expired():
    """Delete all expired tokens"""
    response = requests.post(f"{API_BASE}/tokens/cleanup", headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def show_help():
    """Show help message"""
    print("""
Obsidian LiveSync Token Management CLI

Usage:
    ./cli.py create <device-name> [days]    Create a new device token
    ./cli.py list [--all]                   List active tokens (--all includes revoked)
    ./cli.py info <token-id>                Get token information
    ./cli.py revoke <token-id>              Revoke a token
    ./cli.py delete <token-id>              Delete a token permanently
    ./cli.py cleanup                        Delete all expired tokens

Examples:
    ./cli.py create "iPhone"                Create token for iPhone (never expires)
    ./cli.py create "Laptop" 365            Create token that expires in 365 days
    ./cli.py list                           List all active tokens
    ./cli.py list --all                     List all tokens including revoked
    ./cli.py revoke abc123                  Revoke token with ID abc123
    ./cli.py info abc123                    Get information about token abc123
    ./cli.py cleanup                        Remove all expired tokens
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Usage: ./cli.py create <device-name> [days]")
            sys.exit(1)

        device_name = sys.argv[2]
        expires_in_days = int(sys.argv[3]) if len(sys.argv) > 3 else None
        create_token(device_name, expires_in_days)

    elif command == "list":
        include_revoked = "--all" in sys.argv
        list_tokens(include_revoked)

    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Usage: ./cli.py revoke <token-id>")
            sys.exit(1)

        token_id = sys.argv[2]
        revoke_token(token_id)

    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Usage: ./cli.py delete <token-id>")
            sys.exit(1)

        token_id = sys.argv[2]
        delete_token(token_id)

    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Usage: ./cli.py info <token-id>")
            sys.exit(1)

        token_id = sys.argv[2]
        get_token_info(token_id)

    elif command == "cleanup":
        cleanup_expired()

    elif command in ["help", "-h", "--help"]:
        show_help()

    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
