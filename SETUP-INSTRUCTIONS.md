# Obsidian LiveSync - Setup Instructions

**🎯 Easiest Way to Configure New Devices**

---

## Quick Setup (Recommended)

### 1. Generate Setup URI

On your server, run:

```bash
obsidian-setup "Device-Name"
```

**Example:**
```bash
obsidian-setup "My-iPhone"
```

This will output:
- 📋 Setup URI (`obsidian://setuplivesync?settings=...`)
- 🔓 One-time URI passphrase
- 🔐 E2EE encryption passphrase (save this!)
- 🔑 JWT token ID (for tracking/revocation)

### 2. Configure Obsidian

**On your device:**

1. Copy the entire setup URI (starts with `obsidian://setuplivesync?settings=`)
2. Open the URI:
   - **Mobile:** Paste in browser, it will open Obsidian
   - **Desktop:** Paste in browser or use "Open URI" in Obsidian
3. Enter the one-time **URI passphrase** when prompted
4. LiveSync will auto-configure with:
   - ✅ Server URL
   - ✅ JWT authentication token
   - ✅ End-to-end encryption
   - ✅ Path obfuscation
   - ✅ Optimal sync settings

**Done!** Your device is ready to sync.

---

## What Gets Configured

The setup URI automatically configures:

### Connection Settings
- **URI:** `https://obsidian.your-domain.com/obsidian`
- **Database:** `obsidian-sync`
- **Authentication:** JWT Bearer token (per-device)

### Encryption (AES-256-GCM)
- **End-to-End Encryption:** Enabled
- **Encryption Passphrase:** Auto-generated (or custom)
- **Path Obfuscation:** Enabled

### Sync Settings
- **Sync on Start:** Yes
- **Live Sync:** No (saves battery)
- **Batch Operations:** Optimized for performance

---

## Managing Your E2EE Passphrase

### ⚠️ Important: Save Your E2EE Passphrase!

The encryption passphrase displayed when you run `obsidian-setup` encrypts ALL your vault data. You need this passphrase on EVERY device.

**Example:**
```
🔐 End-to-End Encryption Passphrase:
   wise-storm-calm-river-wise-mountain
   ⚠️  Write this down! You'll need it on all devices.
```

**Options:**

1. **Same passphrase for all devices (Recommended):**
   ```bash
   # Use the same E2EE passphrase for all devices
   obsidian-setup "iPhone" "wise-storm-calm-river-wise-mountain"
   obsidian-setup "Laptop" "wise-storm-calm-river-wise-mountain"
   obsidian-setup "iPad" "wise-storm-calm-river-wise-mountain"
   ```

2. **Auto-generate (First device only):**
   ```bash
   # Let the tool generate a passphrase
   obsidian-setup "First-Device"

   # Then copy that passphrase for other devices
   obsidian-setup "Second-Device" "<passphrase-from-first-device>"
   ```

---

## Token Management

### View Active Tokens

```bash
obsidian-tokens list
```

Example output:
```
🟢 ACTIVE | My-iPhone
  Token ID: actNnsfSJO2KLMJdzhSt0Wu12qXGeERH_yaQU0svW_k
  Created: 2025-10-05T18:25:12
  Expires: Never
  Last used: 2025-10-05T19:15:42
```

### Revoke a Device

Lost your phone? Revoke its access instantly:

```bash
obsidian-tokens revoke actNnsfSJO2KLMJdzhSt0Wu12qXGeERH_yaQU0svW_k
```

The device will immediately lose access to sync.

### Delete Token Permanently

```bash
obsidian-tokens delete <token-id>
```

---

## Alternative: Manual Setup

If you prefer manual configuration:

### 1. Create Token
```bash
obsidian-tokens create "Device-Name"
```

Copy the JWT token shown.

### 2. Configure Obsidian Manually

**Remote Database Settings:**
- **URI:** `https://obsidian.your-domain.com/obsidian`
- **Database name:** `obsidian-sync`
- **Username:** (leave empty)
- **Password:** (leave empty)
- **Custom Request Header:** `Bearer <your-jwt-token>`

**Encryption Settings:**
- Enable **End-to-End Encryption**
- Set **Passphrase** (same on all devices)
- Enable **Path Obfuscation**

---

## Troubleshooting

### "Failed to connect to server"

1. Check your internet connection
2. Verify the server is running:
   ```bash
   systemctl status auth-proxy
   curl https://obsidian.your-domain.com/obsidian/health
   ```

### "Authentication failed"

1. Check if token is valid:
   ```bash
   obsidian-tokens info <token-id>
   ```
2. If revoked, generate a new setup URI:
   ```bash
   obsidian-setup "Device-Name"
   ```

### "Encryption passphrase mismatch"

You must use the **exact same E2EE passphrase** on all devices. If you lost it:
1. You cannot decrypt existing data
2. You'll need to rebuild your database
3. Use the same passphrase going forward

### "Setup URI doesn't open"

- **Mobile:** Make sure Obsidian app is installed
- **Desktop:** Try pasting the URI in your browser first
- **Alternative:** Use manual setup method instead

---

## Server Details

- **URL:** `https://obsidian.your-domain.com/obsidian`
- **Database:** `obsidian-sync`
- **SSL Certificate:** Let's Encrypt (auto-renews)
- **Authentication:** Custom JWT (per-device tokens)
- **Encryption:** AES-256-GCM (client-side)

### Security Features

✅ **HTTPS** - TLS 1.2/1.3 encryption in transit
✅ **Per-Device Tokens** - Revoke individual devices
✅ **Instant Revocation** - No waiting for token expiry
✅ **E2E Encryption** - Data encrypted before leaving device
✅ **Path Obfuscation** - File paths encrypted
✅ **Rate Limiting** - 10 req/s with burst protection
✅ **fail2ban** - Automatic IP blocking on abuse

---

## Next Steps

1. Run `obsidian-setup "First-Device"` on the server
2. Copy the setup URI and open it in Obsidian
3. **Save the E2EE passphrase somewhere safe!**
4. For additional devices, use the same E2EE passphrase:
   ```bash
   obsidian-setup "Second-Device" "<your-e2ee-passphrase>"
   ```

**Need help?** Check `/root/obsidian-livesync/CUSTOM-JWT-AUTH.md` for advanced configuration.
