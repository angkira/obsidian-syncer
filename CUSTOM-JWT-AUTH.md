# Custom JWT Authentication System

**✅ WORKING - Production Ready**

## Overview

Custom FastAPI-based JWT authentication proxy with per-device token management and instant revocation capabilities. This system provides:

- 🔐 **Per-Device Tokens**: Each device gets its own unique JWT token
- ⚡ **Instant Revocation**: Revoke tokens immediately, no waiting
- 📊 **Token Tracking**: Monitor which devices are active, when last used
- ⏰ **Expiration Support**: Optional token expiration dates
- 🔄 **Async Architecture**: High-performance FastAPI with uvicorn
- 📦 **SQLite Backend**: Simple, reliable token storage

---

## Architecture

```
Client (Obsidian)
    ↓ JWT Token
Nginx (Port 80)
    ↓ Proxy to localhost:5985
FastAPI Auth Proxy
    ↓ Validates JWT against SQLite DB
    ↓ Proxies to CouchDB with Basic Auth
CouchDB (Port 5984)
```

---

## Quick Start

### Option 1: Auto-Setup with Setup URI (Recommended)

Generate a setup URI that auto-configures everything in Obsidian:

```bash
# Generate setup URI for a device
obsidian-setup "iPhone"

# The command will:
# - Create a JWT token for the device
# - Generate an E2EE encryption passphrase
# - Create an encrypted setup URI
# - Display everything you need
```

Copy the `obsidian://setuplivesync?settings=...` URI and open it in Obsidian to auto-configure!

### Option 2: Manual Token Creation

```bash
# Create token for a device (never expires)
obsidian-tokens create "iPhone"

# Create token that expires in 365 days
obsidian-tokens create "Laptop" 365

# Create token for temporary access (7 days)
obsidian-tokens create "Guest-Device" 7
```

### List Tokens

```bash
# List active tokens
obsidian-tokens list

# List all tokens including revoked
obsidian-tokens list --all
```

### Revoke a Token

```bash
# Revoke by token ID
obsidian-tokens revoke <token-id>

# Example
obsidian-tokens revoke upJIkCgOIByOV3rUSKlL607CKglwxoJ49BrynfbBHyc
```

### Get Token Info

```bash
obsidian-tokens info <token-id>
```

### Delete Token Permanently

```bash
obsidian-tokens delete <token-id>
```

### Cleanup Expired Tokens

```bash
obsidian-tokens cleanup
```

---

## Configuring Obsidian

After creating a token, configure Obsidian LiveSync:

1. **Install Self-hosted LiveSync plugin**
2. **Configure Remote Database:**
   - **URL:** `https://obsidian.your-domain.com/obsidian`
   - **Database:** `obsidian-sync`
   - **Username:** Leave empty
   - **Password:** Leave empty
   - **Custom Request Header:** Paste the full `Authorization: Bearer <token>` line

**Example:**
```
URL: https://obsidian.your-domain.com/obsidian
Database: obsidian-sync
Custom Request Header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl9pZCI6InVwSklrQ2dPSUJ5T1YzclVTS2xMNjA3Q0tnbHd4b0o0OUJyeW5mYkJIeWMiLCJkZXZpY2VfbmFtZSI6IlRlc3QtRGV2aWNlIiwiaWF0IjoxNzU5NjgyMzM1LCJleHAiOjE3NjIyNzQzMzV9.JLBEDy05sONbqPaIymo2nuSUDPLvuRWY7Wp1NQrjXQk
```

3. **Test Connection** - should succeed
4. **Start syncing!**

---

## CLI Commands Reference

```bash
# Setup URI (Easiest)
obsidian-setup <device-name> [e2ee-passphrase] # Generate auto-setup URI

# Token Management
obsidian-tokens create <device-name> [days]    # Create new token
obsidian-tokens list [--all]                   # List tokens
obsidian-tokens info <token-id>                # Get token details
obsidian-tokens revoke <token-id>              # Revoke token
obsidian-tokens delete <token-id>              # Delete permanently
obsidian-tokens cleanup                        # Remove expired tokens
```

---

## Management API

For programmatic access, use the REST API:

### Authentication

All admin endpoints require the admin token:

```bash
Authorization: Bearer 2a9b8963a0aff94ef0c58c2617b8df044070e4cea4315b1a274f48ae9fba254f
```

### Endpoints

**Create Token**
```http
POST http://127.0.0.1:5985/admin/tokens/create?device_name=MyDevice&expires_in_days=30
Authorization: Bearer <ADMIN_TOKEN>
```

**List Tokens**
```http
GET http://127.0.0.1:5985/admin/tokens/list?include_revoked=false
Authorization: Bearer <ADMIN_TOKEN>
```

**Revoke Token**
```http
POST http://127.0.0.1:5985/admin/tokens/revoke/<token-id>
Authorization: Bearer <ADMIN_TOKEN>
```

**Get Token Info**
```http
GET http://127.0.0.1:5985/admin/tokens/info/<token-id>
Authorization: Bearer <ADMIN_TOKEN>
```

**Delete Token**
```http
DELETE http://127.0.0.1:5985/admin/tokens/delete/<token-id>
Authorization: Bearer <ADMIN_TOKEN>
```

**Cleanup Expired**
```http
POST http://127.0.0.1:5985/admin/tokens/cleanup
Authorization: Bearer <ADMIN_TOKEN>
```

---

## Token Structure

Each JWT token contains:

```json
{
  "token_id": "upJIkCgOIByOV3rUSKlL607CKglwxoJ49BrynfbBHyc",
  "device_name": "iPhone",
  "iat": 1759682335,
  "exp": 1762274335
}
```

- `token_id`: Unique ID stored in SQLite database
- `device_name`: Human-readable device identifier
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp (optional)

---

## Database Schema

SQLite database location: `/root/obsidian-livesync/auth-proxy/tokens.db`

```sql
CREATE TABLE device_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id TEXT UNIQUE NOT NULL,
    device_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    last_used_at TEXT,
    revoked INTEGER DEFAULT 0,
    revoked_at TEXT,
    metadata TEXT
);
```

---

## Service Management

### Auth Proxy Service

```bash
# Status
systemctl status auth-proxy

# Start/Stop/Restart
systemctl start auth-proxy
systemctl stop auth-proxy
systemctl restart auth-proxy

# Logs
journalctl -u auth-proxy -f

# View application logs
journalctl -u auth-proxy --since "1 hour ago"
```

### Configuration Files

| File | Purpose |
|------|---------|
| `/root/obsidian-livesync/auth-proxy/main.py` | FastAPI application |
| `/root/obsidian-livesync/auth-proxy/database.py` | SQLite database layer |
| `/root/obsidian-livesync/auth-proxy/cli.py` | CLI tool |
| `/root/obsidian-livesync/auth-proxy/pyproject.toml` | Dependencies (uv) |
| `/root/obsidian-livesync/auth-proxy/tokens.db` | Token database |
| `/root/obsidian-livesync/.env` | Secrets (ADMIN_TOKEN, JWT_SECRET) |
| `/etc/systemd/system/auth-proxy.service` | systemd service |

---

## Security Features

✅ **HMAC-SHA256 Signing**: All JWTs signed with 512-bit secret
✅ **Database Validation**: Every request checks token status in DB
✅ **Instant Revocation**: Revoked tokens rejected immediately
✅ **Last Used Tracking**: Monitor token activity
✅ **Optional Expiration**: Set expiry dates on tokens
✅ **Admin Token Protection**: Management API secured
✅ **Async Architecture**: Non-blocking I/O for performance

---

## Secrets

**Admin Token (for CLI/API):**
```
2a9b8963a0aff94ef0c58c2617b8df044070e4cea4315b1a274f48ae9fba254f
```

**JWT Signing Secret:**
```
a478647a0766fb5aec2b1dcd8e044c709924993056790b042520f5fcb2adefc47af78955e069ba1b407b824b4bf98bacc298ebc0082540f5c3a73050a37091fd
```

Both stored in `/root/obsidian-livesync/.env`

---

## Troubleshooting

### Token Not Working

1. Check if token is valid:
   ```bash
   obsidian-tokens list
   ```

2. Check if token is revoked:
   ```bash
   obsidian-tokens info <token-id>
   ```

3. Check auth proxy logs:
   ```bash
   journalctl -u auth-proxy -f
   ```

### Auth Proxy Not Running

```bash
systemctl status auth-proxy
systemctl restart auth-proxy
journalctl -u auth-proxy --since "10 minutes ago"
```

### Database Issues

```bash
# Check database exists
ls -lah /root/obsidian-livesync/auth-proxy/tokens.db

# View database directly
sqlite3 /root/obsidian-livesync/auth-proxy/tokens.db "SELECT * FROM device_tokens;"
```

---

## Backup & Restore

### Backup Token Database

```bash
cp /root/obsidian-livesync/auth-proxy/tokens.db \
   /root/obsidian-livesync/backups/tokens-$(date +%Y%m%d).db
```

### Restore Token Database

```bash
systemctl stop auth-proxy
cp /root/obsidian-livesync/backups/tokens-20251005.db \
   /root/obsidian-livesync/auth-proxy/tokens.db
systemctl start auth-proxy
```

---

## Performance

- **Technology:** FastAPI + uvicorn with 2 workers
- **Database:** SQLite with indexed lookups
- **Concurrency:** Async/await throughout
- **Timeout:** 5 minutes for large sync operations
- **Rate Limiting:** Nginx handles rate limiting (10 req/s)

---

## Migration from Basic Auth

To migrate devices from Basic Auth to JWT:

1. Create a token for each device:
   ```bash
   obsidian-tokens create "Device1"
   obsidian-tokens create "Device2"
   ```

2. Update Obsidian configuration on each device:
   - Remove username/password
   - Add `Authorization: Bearer <token>` as custom header

3. Test connection

4. Verify in token list:
   ```bash
   obsidian-tokens list
   ```

---

## Development

Built with:
- **FastAPI** - Modern async web framework
- **uvicorn** - ASGI server
- **aiosqlite** - Async SQLite
- **PyJWT** - JWT encoding/decoding
- **httpx** - Async HTTP client
- **uv** - Fast Python package installer

### Local Development

```bash
cd /root/obsidian-livesync/auth-proxy

# Install dependencies
/root/.local/bin/uv sync

# Run locally
.venv/bin/uvicorn main:app --reload --port 5985
```

---

## API Documentation

When auth proxy is running, visit:

- **Interactive Docs:** `http://127.0.0.1:5985/docs`
- **OpenAPI Schema:** `http://127.0.0.1:5985/openapi.json`

---

## Comparison: Old vs New

| Feature | Basic Auth | Custom JWT |
|---------|-----------|------------|
| Per-Device Tokens | ❌ | ✅ |
| Revocation | ❌ | ✅ Instant |
| Expiration | ❌ | ✅ Optional |
| Last Used Tracking | ❌ | ✅ |
| Programmatic API | ❌ | ✅ |
| Token Management | ❌ | ✅ CLI Tool |
| Security | Good | Better |

---

**System Status:** ✅ **PRODUCTION READY**
**Last Updated:** 2025-10-05
**Version:** 1.0.0
