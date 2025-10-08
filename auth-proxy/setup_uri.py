#!/usr/bin/env python3
"""
Generate Obsidian LiveSync Setup URI
Creates an encrypted setup URI that can be opened in Obsidian to auto-configure LiveSync
"""
import json
import base64
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import sys
from datetime import datetime, timezone

def generate_passphrase(length=8):
    """Generate a friendly random passphrase"""
    words = []
    # Simple word list for memorable passphrases
    adjectives = ['happy', 'bright', 'swift', 'calm', 'brave', 'quick', 'kind', 'wise']
    nouns = ['ocean', 'mountain', 'river', 'forest', 'valley', 'cloud', 'storm', 'wind']

    for _ in range(length // 2):
        words.append(secrets.choice(adjectives))
        words.append(secrets.choice(nouns))

    return '-'.join(words)

def derive_key(passphrase: str, salt: bytes, iterations: int = 100000) -> bytes:
    """Derive encryption key from passphrase using PBKDF2 (matches Obsidian LiveSync)"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase.encode('utf-8'))

def encrypt_config(config_json: str, uri_passphrase: str) -> str:
    """
    Encrypt configuration JSON for setup URI
    Matches Obsidian LiveSync format: %[iv_hex][salt_hex][base64_ciphertext]
    """
    # Calculate iterations based on passphrase length (matches octagonal-wheels)
    passphrase_len = len(uri_passphrase)
    iterations = passphrase_len * 1000 + 121 - passphrase_len

    # Generate salt (16 bytes) and IV (16 bytes for compatibility, only 12 used)
    salt = secrets.token_bytes(16)
    iv_full = secrets.token_bytes(16)
    nonce = iv_full[:12]  # AES-GCM uses 12-byte nonce

    # Derive key
    key = derive_key(uri_passphrase, salt, iterations)

    # Encrypt using AES-GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, config_json.encode('utf-8'), None)

    # Format: %[iv_hex(32 chars)][salt_hex(32 chars)][base64_ciphertext]
    iv_hex = iv_full.hex()
    salt_hex = salt.hex()
    ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')

    return f"%{iv_hex}{salt_hex}{ciphertext_b64}"

def generate_setup_uri(
    couchdb_uri: str,
    couchdb_user: str,
    couchdb_password: str,
    couchdb_dbname: str,
    e2ee_passphrase: str = None,
    uri_passphrase: str = None,
    use_encryption: bool = True,
    use_path_obfuscation: bool = True,
    device_name: str = "Device"
) -> tuple[str, str]:
    """
    Generate Obsidian LiveSync setup URI

    Returns:
        tuple: (setup_uri, uri_passphrase)
    """

    # Generate passphrases if not provided
    if uri_passphrase is None:
        uri_passphrase = generate_passphrase(4)

    if e2ee_passphrase is None and use_encryption:
        e2ee_passphrase = generate_passphrase(6)

    # Build configuration object (matches Obsidian LiveSync structure)
    config = {
        "couchDB_URI": couchdb_uri,
        "couchDB_USER": couchdb_user,
        "couchDB_PASSWORD": couchdb_password,
        "couchDB_DBNAME": couchdb_dbname,
        "liveSync": False,
        "syncOnSave": False,
        "syncOnStart": True,
        "savingDelay": 200,
        "lessInformationInLog": False,
        "gcDelay": 0,
        "versionUpFlash": "",
        "minimumChunkSize": 20,
        "longLineThreshold": 250,
        "showOwnPluginUpdateNotice": False,
        "showRegularNotificationOnMobile": False,
        "batchSave": False,
        "deviceAndVaultName": device_name,
        "usePluginSettings": False,
        "showStatusOnEditor": True,
        "showStatusOnStatusbar": True,
        "showOnlyIconsOnEditor": False,
        "usePluginSync": False,
        "autoSweepPlugins": False,
        "autoSweepPluginsPeriodic": False,
        "notifyPluginOrSettingUpdated": False,
        "checkIntegrityOnSave": False,
        "batch_size": 50,
        "batches_limit": 50,
        "useHistory": False,
        "disableRequestURI": True,
        "skipOlderFilesOnSync": True,
        "checkConflictOnlyOnOpen": False,
        "syncInternalFiles": False,
        "syncInternalFilesBeforeReplication": False,
        "syncInternalFilesIgnorePatterns": "\\/node_modules\\/, \\/\\.git\\/, \\/obsidian-livesync\\/",
        "syncInternalFilesInterval": 60,
        "additionalSuffixOfDatabaseName": "",
        "ignoreVersionCheck": False,
        "lastReadUpdates": "",
        "deleteMetadataOfDeletedFiles": False,
        "syncIgnoreRegEx": "",
        "syncOnlyRegEx": "",
        "customChunkSize": 0,
        "readChunksOnline": True,
        "watchInternalFileChanges": True,
        "trashInsteadDelete": True,
        "periodicReplication": False,
        "periodicReplicationInterval": 60,
        "syncAfterMerge": False,
        "configPassphraseStore": "",
        "encryptedPassphrase": "",
        "encryptedCouchDBConnection": "",
        "permitEmptyPassphrase": False,
        "useIndexedDBAdapter": False,
        "useTimeoutAPI": False,
        "writeLogToTheFile": False,
        "doNotPaceReplication": False,
        "hashCacheMaxCount": 300,
        "hashCacheMaxAmount": 50,
        "concurrencyOfReadChunksOnline": 30,
        "minimumIntervalOfReadChunksOnline": 333,
        "hashAlg": "xxhash64",
    }

    # Add encryption settings
    if use_encryption and e2ee_passphrase:
        config["encrypt"] = True
        config["passphrase"] = e2ee_passphrase
        config["usePathObfuscation"] = use_path_obfuscation
    else:
        config["encrypt"] = False
        config["passphrase"] = ""
        config["usePathObfuscation"] = False

    # Convert to JSON
    config_json = json.dumps(config, separators=(',', ':'))

    # Encrypt configuration
    encrypted_config = encrypt_config(config_json, uri_passphrase)

    # Build setup URI
    setup_uri = f"obsidian://setuplivesync?settings={encrypted_config}"

    return setup_uri, uri_passphrase, e2ee_passphrase

def main():
    if len(sys.argv) < 2:
        print("""
Usage: setup_uri.py <device-name> [e2ee-passphrase]

Examples:
    setup_uri.py "iPhone"                    # Auto-generate E2EE passphrase
    setup_uri.py "Laptop" "my-vault-secret"  # Use specific E2EE passphrase

This will create a JWT token for the device and generate a setup URI.
        """)
        sys.exit(1)

    device_name = sys.argv[1]
    e2ee_passphrase = sys.argv[2] if len(sys.argv) > 2 else None

    # Import the database module to create token
    from database import TokenDatabase
    import asyncio

    async def create_setup():
        # Load environment variables
        from dotenv import load_dotenv

        ENV_FILE = os.getenv("ENV_FILE", "/root/obsidian-livesync/.env")
        if os.path.exists(ENV_FILE):
            load_dotenv(ENV_FILE)

        # Create JWT token for device
        db = TokenDatabase()
        await db.init_db()

        token_data = await db.create_token(device_name, expires_in_days=None)

        # Generate JWT
        import jwt
        from datetime import datetime

        JWT_SECRET = os.getenv("JWT_HMAC_SECRET")

        # Get configuration from environment
        PUBLIC_URL = os.getenv("PUBLIC_URL", "https://obsidian.example.com")
        SYNC_USER = os.getenv("SYNC_USER", "obsidian")
        DB_NAME = os.getenv("DB_NAME", "obsidian-sync")

        # Build CouchDB URL path
        # For nginx with /obsidian path: PUBLIC_URL/DB_NAME
        couchdb_uri = f"{PUBLIC_URL}/obsidian" if not PUBLIC_URL.endswith("/obsidian") else PUBLIC_URL
        couchdb_dbname = f"obsidian/{DB_NAME}"

        jwt_payload = {
            "token_id": token_data["token_id"],
            "device_name": device_name,
            "iat": datetime.now(timezone.utc),
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

        # Generate setup URI
        setup_uri, uri_passphrase, e2ee_pass = generate_setup_uri(
            couchdb_uri=couchdb_uri,
            couchdb_user=SYNC_USER,  # Username for Basic Auth
            couchdb_password=jwt_token,  # JWT token as password (Basic Auth)
            couchdb_dbname=couchdb_dbname,
            e2ee_passphrase=e2ee_passphrase,
            device_name=device_name
        )

        print("\n" + "="*80)
        print(f"✅ Setup URI Generated for: {device_name}")
        print("="*80)
        print(f"\n📱 Device Name: {device_name}")
        print(f"🔑 Token ID: {token_data['token_id']}")
        print(f"📅 Created: {token_data['created_at']}")
        print(f"⏰ Expires: Never")

        print(f"\n🔐 End-to-End Encryption Passphrase:")
        print(f"   {e2ee_pass}")
        print(f"   ⚠️  Write this down! You'll need it on all devices.")

        print(f"\n🔓 Setup URI Passphrase (one-time use):")
        print(f"   {uri_passphrase}")

        print(f"\n📋 Setup URI:")
        print(f"{setup_uri}")

        print(f"\n📖 Instructions:")
        print(f"1. On your device, copy the setup URI above")
        print(f"2. Open it (paste in browser or use Obsidian URI handler)")
        print(f"3. Enter the URI passphrase: {uri_passphrase}")
        print(f"4. LiveSync will auto-configure!")
        print(f"5. Save your E2EE passphrase: {e2ee_pass}")
        print("="*80 + "\n")

    asyncio.run(create_setup())

if __name__ == "__main__":
    main()
